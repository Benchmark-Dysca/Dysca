import torch
import numpy as np
import random
import argparse
import os
import json
import string
import random
from transformers import CLIPTextModel, CLIPTokenizer
from diffusers import (
    AutoencoderKL,
    DDPMScheduler,
    UNet2DConditionModel,
)
from tqdm import tqdm
from PIL import Image
from PIL import Image, ImageFont
from fastchat.model import get_conversation_template
from transformers import AutoTokenizer, AutoModelForCausalLM
from cog import BasePredictor, Input, Path, BaseModel


device = torch.device("cuda:2") if torch.cuda.is_available() else "cpu"

def parse_args():
    parser = argparse.ArgumentParser(
        prog='Imagenette Generator',
        description='A script for generating specific image class of imagenette')
    parser.add_argument('--input_file', default='./Dysca.json', help="The input json file")  
    parser.add_argument('--output_dir', default='./Dysca', help='The output folder path')  
    parser.add_argument('--seed', type=int, default=2024)
    parser.add_argument('--sd_model',default=None)
    parser.add_argument('--textdiffuser_model',default=None)
    parser.add_argument('--textdiffuser_full_ft',default=None)
    parser.add_argument('--device', default="cuda:0")
    
    return parser.parse_args()

def set_seed(seed: int = 42):
    '''set the radom seed'''
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    # # When running on the CuDNN backend, two further options must be set
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    generator = torch.Generator("cuda").manual_seed(seed)
    print(f"Random seed set as {seed}")
    
    return generator
    
alphabet = (
    string.digits
    + string.ascii_lowercase
    + string.ascii_uppercase
    + string.punctuation
    + " "
)  # len(aphabet) = 95
"""alphabet
0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ 
"""

font_layout = ImageFont.truetype("./Arial.ttf", 16)


class ModelOutput(BaseModel):
    output_images: list[Path]
    composed_prompt: str


class Predictor(BasePredictor):
    def setup(self,textdiffuser_model,textdiffuser_full_ft,sd_model) -> None:
        """Load the model into memory to make running multiple predictions efficient"""
        cache_dir = "model_cache"
        local_files_only = False  # set to True if the models are saved in cache_dir

        self.m1_model_path = textdiffuser_model
        self.m1_tokenizer = AutoTokenizer.from_pretrained(
            self.m1_model_path
        )
        self.m1_model = AutoModelForCausalLM.from_pretrained(
            self.m1_model_path,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        ).to(device)

        self.text_encoder = (
            CLIPTextModel.from_pretrained(
                textdiffuser_full_ft,
                subfolder="text_encoder",
                cache_dir=cache_dir,
                local_files_only=local_files_only,
            )
            .to(device)
            .half()
        )
        self.tokenizer = CLIPTokenizer.from_pretrained(
            sd_model,
            subfolder="tokenizer",
            cache_dir=cache_dir,
            local_files_only=local_files_only,
        )

        #### additional tokens are introduced, including coordinate tokens and character tokens
        print("***************")
        print(f"tokenizer size: {len(self.tokenizer)}")
        for i in range(520):
            self.tokenizer.add_tokens(["l" + str(i)])  # left
            self.tokenizer.add_tokens(["t" + str(i)])  # top
            self.tokenizer.add_tokens(["r" + str(i)])  # width
            self.tokenizer.add_tokens(["b" + str(i)])  # height
        for c in alphabet:
            self.tokenizer.add_tokens([f"[{c}]"])
        print(f"new tokenizer size: {len(self.tokenizer)}")
        print("***************")

        self.vae = (
            AutoencoderKL.from_pretrained(
                sd_model,
                subfolder="vae",
                cache_dir=cache_dir,
                local_files_only=local_files_only,
            )
            .half()
            .to(device)
        )
        self.unet = (
            UNet2DConditionModel.from_pretrained(
                textdiffuser_full_ft,
                subfolder="unet",
                cache_dir=cache_dir,
                local_files_only=local_files_only,
            )
            .half()
            .to(device)
        )
        self.text_encoder.resize_token_embeddings(len(self.tokenizer))
        self.scheduler = DDPMScheduler.from_pretrained(
            sd_model,
            subfolder="scheduler",
            cache_dir=cache_dir,
            local_files_only=local_files_only,
        )
        
    def predict(
        self,
        prompt: str = Input(
            description="Input Prompt. You can let language model automatically identify keywords, or provide them below.",
            default="A beautiful city skyline stamp of Shanghai",
        ),
        keywords: str = Input(
            description="(Optional) Keywords. Should be seperated by / (e.g., keyword1/keyword2/...).",
            default=None,
        ),
        positive_prompt: str = Input(
            description="(Optional) Positive prompt.",
            default=", digital art, very detailed, fantasy, high definition, cinematic light, dnd, trending on artstation",
        ),
        use_lcm: bool = Input(
            description="Use Latent Consistent Model.", default=False
        ),
        generate_natural_image: bool = Input(
            description="If set to True, the text position and content info will not be incorporated.",
            default=False,
        ),
        num_images: int = Input(
            description="Number of Output images.", default=1, ge=1, le=4
        ),
        num_inference_steps: int = Input(
            description="Number of denoising steps. You may decease the step to 4 when using LCM.",
            ge=1,
            le=50,
            default=20,
        ),
        guidance_scale: float = Input(
            description="Scale for classifier-free guidance. The scale is set to 7.5 by default. When using LCM, guidance_scale is set to 1.",
            ge=1,
            le=20,
            default=7.5,
        ),
        temperature: float = Input(
            description="Control the diversity of layout planner. Higher value indicates more diversity.",
            ge=0.1,
            le=2,
            default=1.4,
        ),
        idx: int = Input(
            description="the id of the output image.",
            ge = 1,
            default=0,
        )
    ) -> ModelOutput:
        """Run a single prediction on the model"""
        if positive_prompt is not None and not len(positive_prompt.strip()) == 0:
            prompt += positive_prompt

        with torch.no_grad():
            user_prompt = prompt

            if generate_natural_image:
                composed_prompt = user_prompt
                prompt = self.tokenizer.encode(user_prompt)
            else:
                if keywords is None or len(keywords.strip()) == 0:
                    template = f"Given a prompt that will be used to generate an image, plan the layout of visual text for the image. The size of the image is 128x128. Therefore, all properties of the positions should not exceed 128, including the coordinates of top, left, right, and bottom. All keywords are included in the caption. You dont need to specify the details of font styles. At each line, the format should be keyword left, top, right, bottom. So let us begin. Prompt: {user_prompt}"
                else:
                    keywords = keywords.split("/")
                    keywords = [i.strip() for i in keywords]
                    template = f"Given a prompt that will be used to generate an image, plan the layout of visual text for the image. The size of the image is 128x128. Therefore, all properties of the positions should not exceed 128, including the coordinates of top, left, right, and bottom. In addition, we also provide all keywords at random order for reference. You dont need to specify the details of font styles. At each line, the format should be keyword left, top, right, bottom. So let us begin. Prompt: {prompt}. Keywords: {str(keywords)}"

                msg = template
                conv = get_conversation_template(self.m1_model_path)
                conv.append_message(conv.roles[0], msg)
                conv.append_message(conv.roles[1], None)
                prompt = conv.get_prompt()
                inputs = self.m1_tokenizer([prompt], return_token_type_ids=False)
                inputs = {k: torch.tensor(v).to(device) for k, v in inputs.items()}
                output_ids = self.m1_model.generate(
                    **inputs,
                    do_sample=True,
                    temperature=temperature,
                    repetition_penalty=1.0,
                    max_new_tokens=512,
                )

                if self.m1_model.config.is_encoder_decoder:
                    output_ids = output_ids[0]
                else:
                    output_ids = output_ids[0][len(inputs["input_ids"][0]) :]

                outputs = self.m1_tokenizer.decode(
                    output_ids,
                    skip_special_tokens=True,
                    spaces_between_special_tokens=False,
                )
                print(f"[{conv.roles[0]}]\n{msg}")
                print(f"[{conv.roles[1]}]\n{outputs}")

                ocrs = outputs.split("\n")
                current_ocr = ocrs

                ocr_ids = []
                print("user_prompt", user_prompt)
                print("current_ocr", current_ocr)

                for ocr in current_ocr:
                    ocr = ocr.strip()

                    if len(ocr) == 0 or "###" in ocr or ".com" in ocr:
                        continue

                    items = ocr.split()
                    pred = " ".join(items[:-1])
                    box = items[-1]

                    l, t, r, b = box.split(",")
                    l, t, r, b = int(l), int(t), int(r), int(b)
                    ocr_ids.extend(
                        ["l" + str(l), "t" + str(t), "r" + str(r), "b" + str(b)]
                    )

                    char_list = list(pred)
                    char_list = [f"[{i}]" for i in char_list]
                    ocr_ids.extend(char_list)
                    ocr_ids.append(self.tokenizer.eos_token_id)

                caption_ids = (
                    self.tokenizer(user_prompt, truncation=True, return_tensors="pt")
                    .input_ids[0]
                    .tolist()
                )

                try:
                    ocr_ids = self.tokenizer.encode(ocr_ids)
                    prompt = caption_ids + ocr_ids
                except:
                    prompt = caption_ids

                user_prompt = self.tokenizer.decode(prompt)
                composed_prompt = self.tokenizer.decode(prompt)

            prompt = prompt[:77]
            while len(prompt) < 77:
                prompt.append(self.tokenizer.pad_token_id)

            if not use_lcm:
                prompts_cond = prompt
                prompts_nocond = [self.tokenizer.pad_token_id] * 77

                prompts_cond = [prompts_cond] * num_images
                prompts_nocond = [prompts_nocond] * num_images

                prompts_cond = torch.Tensor(prompts_cond).long().to(device)
                prompts_nocond = torch.Tensor(prompts_nocond).long().to(device)

                scheduler = self.scheduler
                scheduler.set_timesteps(num_inference_steps)
                noise = torch.randn((num_images, 4, 64, 64)).to(device).half()
                input = noise

                encoder_hidden_states_cond = self.text_encoder(prompts_cond)[0].to(device).half()
                encoder_hidden_states_nocond = self.text_encoder(prompts_nocond)[
                    0
                ].half()

                for t in tqdm(scheduler.timesteps):
                    with torch.no_grad():  # classifier free guidance
                        noise_pred_cond = self.unet(
                            sample=input,
                            timestep=t,
                            encoder_hidden_states=encoder_hidden_states_cond[
                                :num_images
                            ],
                        ).sample  # b, 4, 64, 64
                        noise_pred_uncond = self.unet(
                            sample=input,
                            timestep=t,
                            encoder_hidden_states=encoder_hidden_states_nocond[
                                :num_images
                            ],
                        ).sample  # b, 4, 64, 64
                        noisy_residual = noise_pred_uncond + guidance_scale * (
                            noise_pred_cond - noise_pred_uncond
                        )  # b, 4, 64, 64
                        input = scheduler.step(noisy_residual, t, input).prev_sample
                        del noise_pred_cond
                        del noise_pred_uncond

                        torch.cuda.empty_cache()

                # decode
                input = 1 / self.vae.config.scaling_factor * input
                images = self.vae.decode(input, return_dict=False)[0]
                width, height = 512, 512
                results = []
                new_image = Image.new("RGB", (2 * width, 2 * height))
                for index, image in enumerate(images.cpu().float()):
                    image = (image / 2 + 0.5).clamp(0, 1).unsqueeze(0)
                    image = image.cpu().permute(0, 2, 3, 1).numpy()[0]
                    image = Image.fromarray(
                        (image * 255).round().astype("uint8")
                    ).convert("RGB")
                    results.append(image)
                    row = index // 2
                    col = index % 2
                    new_image.paste(image, (col * width, row * height))
            else:
                pass
        torch.cuda.empty_cache()

        sample = results[0]

        return sample

def main():

    args = parse_args()
    
    use_lcm = False
    generate_natural_image = False
    positive_prompt = ''
    num_images = 1
    num_inference_steps = 50
    guidance_scale = 7.5
    temperature = 0.5

    tg = Predictor()
    tg.setup(args.textdiffuser_model,args.textdiffuser_full_ft,args.sd_model)

    # set random seed
    generator = set_seed(args.seed)

    # Read Dysca file
    with open(args.input_file,'r',encoding='utf8') as fin:
        json_data = json.load(fin)
    
    stored_prompt = ''
    for data in json_data: 
        prompt = data["prompt"]
        idx = data['id']
        image_name = data['images'][0].split("/")[-1]
        if prompt != stored_prompt:
            if data['task'] == 'OCR':
                start_quote = prompt.find("'")
                end_quote = prompt.find("'",start_quote+1)
                keywords = prompt[start_quote+1:end_quote]
                image = tg.predict(prompt,keywords,positive_prompt,use_lcm,generate_natural_image,num_images,num_inference_steps,guidance_scale,temperature,idx)
        
                image.save(os.path.join(args.output_dir,image_name))
            stored_prompt = prompt


if __name__ == '__main__':
    main()
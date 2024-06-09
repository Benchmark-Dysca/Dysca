import torch
import numpy as np
import random
import argparse
import os
import json
from diffusers import (
    AutoPipelineForText2Image,
)
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca Benchmark Generator',
        description='A script for generating evaluating images of Dysca Benchmark')
    parser.add_argument('--input_file', default='./Dysca.json', help="The input json file")  
    parser.add_argument('--output_dir', default='./Dysca', help='The output folder path')  
    parser.add_argument('--seed', type=int, default=2024)
    parser.add_argument('--sdxl_model', default="stabilityai/stable-diffusion-xl-base-1.0")
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
    
def main():

    args = parse_args()
    
    device = torch.device(args.device)

    # read the base model
    pipeline_text2image = AutoPipelineForText2Image.from_pretrained(
        args.sdxl_model, torch_dtype=torch.float16
    ).to(device)

    # set random seed
    generator = set_seed(args.seed)

    # Read PQA file
    with open(args.input_file,'r',encoding='utf8') as fin:
        json_data = json.load(fin)
        
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    stored_prompt = ''
    for data in tqdm(json_data): 
        prompt = data["prompt"]
        image_name = data['images'][0].split("/")[-1]
        if prompt != stored_prompt:
            negative_prompt = data["negative_prompt"]
            image = pipeline_text2image(prompt=prompt,negative_prompt=negative_prompt,generator=generator,guidance_scale=7.5,num_inference_steps=50).images[0]
            
            image.save(os.path.join(args.output_dir,image_name))
            stored_prompt = prompt

if __name__ == '__main__':
    main()
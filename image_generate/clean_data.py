import torch
from PIL import Image
import json
from tqdm import tqdm 
import os
import argparse
from PIL import Image
from tqdm import tqdm
import os
from transformers import CLIPProcessor, CLIPModel

def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca Benchmark Generator',
        description='A script for generating evaluating images of Dysca Benchmark')
    parser.add_argument('--input_file', default='./Dysca.json', help="The input json file")  
    parser.add_argument('--output_file', default='./Dysca_clean.json', help="The output json file") 
    parser.add_argument('--image_folder', default='./Dysca_clean', help='The image folder path')  
    parser.add_argument('--seed', type=int, default=2024)
    parser.add_argument('--clip_model', default=None)
    parser.add_argument('--device', default="cuda:0")
    
    return parser.parse_args()

if __name__ == "__main__":
    
    args = parse_args()
    device = torch.device(args.device)

    model = CLIPModel.from_pretrained(args.clip_model).to(device)
    processor = CLIPProcessor.from_pretrained(args.clip_model)

    path = args.input_file
    with open(path, 'r',encoding='utf-8') as file:
        data = json.load(file)
        
    delete_list = []
    num=0
    store= ''
    with torch.no_grad():
        for value in tqdm(data):
            file_name = value['images'][0].split("/")[-1]
            id = value['idx']
            if file_name != store:
                image_path = os.path.join(args.image_folder,file_name)
                prompt = value["prompt"]
                im = Image.open(image_path)
                inputs = processor(text=prompt, images=im, return_tensors="pt", padding=True).to(device)
                outputs = model(**inputs)
                clip_score = outputs.logits_per_image[0][0].detach().cpu() # this is the image-text similarity score
                # print(file_name,prompt,clip_score)
                if clip_score <= 25:
                    delete_list.append(id)
                store = file_name
        
    clean_input_file = []
        
    i=1
        
    for idx in tqdm(range(len(data))):
        if idx in delete_list:
            continue
        else:
            data[idx]["id"] = i 
            clean_input_file.append(data[idx])
            i+=1
            
    b = json.dumps(clean_input_file, indent=2)
    f2 = open(args.output_file, 'w')
    f2.write(b)
    f2.close()

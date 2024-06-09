from PIL import Image, ImageDraw, ImageFont
import random
import os
import warnings
warnings.filterwarnings('ignore')
from tqdm import tqdm
import json
import numpy as np
import argparse

def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    print(f"Random seed set as {seed}")
    
def print_attack(image_path,output_path,texts):
    # Load the image
    image = Image.open(image_path)

    # Convert the image to RGBA format
    image_rgba = image.convert('RGBA')

    # Create a transparent overlay image
    overlay = Image.new('RGBA', image_rgba.size, (0, 0, 0, 0))

    # Define the text parameters
    font_path = './Arial.ttf'

    for text in texts:
        # size
        font_sizes = [112,128,144,160]
        font_size = random.choice(font_sizes)

        # color
        colors = [(0, 0, 255),(255, 165, 0 ),(255, 255, 0),(0, 128, 0),(0,255,255),(255, 0, 0),(128, 0, 128),(255, 255, 255),(0, 0, 0)]
        color = random.choice(colors)

        # transparency
        transparencys = [102,153,204,256]
        transparency = random.choice(transparencys)

        # angle
        angles = [0,-15,15,-25,25,-35,35]
        rotation_angle = random.choice(angles)

        text_color = (*color, transparency)

        # Load the font
        font = ImageFont.truetype(font_path, font_size)

        # Create a drawing object
        draw = ImageDraw.Draw(overlay)

        # Calculate the text position
        text_width, text_height = draw.textsize(text, font=font)
        x = (image_rgba.width - text_width) // 2
        y = (image_rgba.height - text_height) // 2
        positions = [-256,-128,0,128,256]
        x += random.choice(positions)
        y += random.choice(positions)
        text_position = (x,y)

        # Draw the text on the rotated overlay image
        draw_rotated = ImageDraw.Draw(overlay)
        draw_rotated.text(text_position, text, font=font, fill=text_color)

        # Rotate the overlay image
        rotated_overlay = overlay.rotate(rotation_angle, resample=Image.BILINEAR, expand=True)

        # Resize the rotated overlay image to match the original image size
        rotated_overlay = rotated_overlay.resize(image_rgba.size, resample=Image.BILINEAR)

        # Composite the rotated overlay image with the original image
        image_with_text = Image.alpha_composite(image_rgba, rotated_overlay)

    # Save the image with the rotated text
    image_with_text.save(output_path)
    
def print_text_generator(value,current_set):
    answer = value['answer']
    options = value['options']
    current = ''
    if len(options) != 0:
        options.remove(answer)
        print_text = random.choices(options)
        current = print_text[0]
    else:
        print_text = current_set
    
    return print_text,current

def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca Benchmark Generator',
        description='A script for generating print-attacking images of Dysca Benchmark')
    parser.add_argument('--input_file', default='./Dysca.json', help="The input json file")  
    parser.add_argument('--input_image_dir', default='./Dysca', help="The input image folder path")  
    parser.add_argument('--output_image_dir', default='./Dysca_print_attack', help='The output image folder path')  
    parser.add_argument('--seed', type=int, default=2024)
    
    return parser.parse_args()
    
if __name__ == '__main__':
    set_seed(42)
    args = parse_args()
    
    with open(args.input_file, 'r',encoding='utf-8') as file:
        data = json.load(file)
        
    if not os.path.exists(args.output_image_dir):
        os.mkdir(args.output_image_dir)
        
    output_file = []
    current_set = ['a man','line sketch']
    num=0
    for value in tqdm(data):
        if value["task"] != 'OCR':
            input_file_name = value['images'][0].split("/")[-1]
            file_name = str(value['id'])+'.png'
            image_path = os.path.join(args.input_image_dir,input_file_name)
            output_path = os.path.join(args.output_image_dir,file_name)
            text,current = print_text_generator(value,current_set)
            if value["question_type"] == "image caption":
                current_set = value["answer"].split(",")
            print_attack(image_path,output_path,text)
            
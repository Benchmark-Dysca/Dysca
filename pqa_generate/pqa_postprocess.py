import json
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca Benchmark Generator',
        description='A script for post-processing')
    parser.add_argument('--file_folder', default='./source', help="The source json file")  
    parser.add_argument('--output_file', default='./Dysca.json', help="The output file") 
    
    return parser.parse_args()

if __name__ == "__main__":
    # python pqa_postprocess.py --file_folder ./source --output_file ./Dysca.json
    args = parse_args()

    data = []

    file_name = os.listdir(args.file_folder)

    for file in file_name:
        path = os.path.join(args.file_folder,file)
        with open(path, 'r',encoding='utf-8') as file:
            data_c = json.load(file)
        data += data_c

    output_file = []

    def query(va):
        prompt = "" 
        # question
        prompt += f"Question: {va['question']}"
        options = va['options']
        # choices
        if len(va["options"]) != 0 :
            texts = ["\nChoices:"]
            for i, choice in enumerate(options):
                if choice == 'unknown' or choice == 'other':
                    continue
                texts.append(f"({chr(ord('A')+i)}) {choice}")
            prompt += "\n" + "\n".join(texts)
            # Hint
            hint = "\nHint: Please answer the question and provide the correct option letter, e.g., (A), (B), (C), (D), at the end. Do not contain the analysis progress.\nYour answer is:"

            prompt += hint
        else:
            hint = "\nYour answer is:"
                
            prompt += hint
            
        return prompt
        
    id = 1
    idx = 1
    for value in data:
        for i in range(len(value['q_a'])):
            new = {}
            new["id"] = id
            new["images"] = [f'images/{str(idx)}.png']
            new["prompt"] = value["prompt"]
            new["negative_prompt"] = value["negative_prompt"]
            new["instruction"] =  query(value['q_a'][i])
            new["answer"] = value['q_a'][i]['answer']
            new["question_type"] = value['q_a'][i]["question_type"]
            new["task"] = value['q_a'][i]['task']
            new["options"] = value['q_a'][i]['options']
            new['question_majority'] = value['q_a'][i]['question_majority']
            output_file.append(new)
            id += 1
        idx+=1


    b = json.dumps(output_file, indent=2)
    f2 = open(args.output_file, 'w')
    f2.write(b)
    f2.close()
    
    
'''
The output file will be a json file, which will be used for benchmarking, like:
[
  {
    "id": 1,
    "images": [
      "images/1.png"
    ],
    "prompt": "a person doing aerobics, desert scenery background, tilt-shift photo of, selective focus, miniature effect, blurred background, highly detailed, vibrant, perspective control",
    "negative_prompt": "blurry, noisy, deformed, flat, low contrast, unrealistic, oversaturated, underexposed",
    "instruction": "Question: What is the person doing in the picture?\n\nChoices:\n(A) painting\n(B) doing aerobics\n(C) rowing a boat\n(D) playing the flute\nHint: Please answer the question and provide the correct option letter, e.g., (A), (B), (C), (D), at the end. Do not contain the analysis progress.\nYour answer is:",
    "answer": "doing aerobics",
    "question_type": "multi choice",
    "task": "recognition",
    "options": [
      "painting",
      "doing aerobics",
      "rowing a boat",
      "playing the flute"
    ],
    "question_majority": "action"
  },
  ...
  {
      "id": 1000,
      ...
  }
]
'''
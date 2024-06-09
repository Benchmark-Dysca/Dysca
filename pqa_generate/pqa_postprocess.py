import argparse
import json
import os
import numpy as np
import random

def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca Benchmark Generator',
        description='A script for post-processing')
    parser.add_argument('--file_folder', required=True, default='./source', help="The source json file")  
    parser.add_argument('--output_file', required=False, default='./Dysca.json', help="The output file") 
    
    return parser.parse_args()

def set_seed(seed: int = 42):
    '''set the radom seed'''
    np.random.seed(seed)
    random.seed(seed)
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    print(f"Random seed set as {seed}")

# Read all the json files under the source folder
def read_json_files(path):
    json_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files

if __name__ == '__main__':
    args = parse_args()
    set_seed(2024)
    
    json_files = read_json_files(args.file_folder)

    # Read all JSON files and save them to a list
    data_of_all_files = []
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            data_of_all_files.append(data)

    # For each JSON data, for each item within it, randomly delete 1, 2, or 3 q_a pairs,
    # and if 3 q_a pairs are deleted, then remove the entire item
    for data in data_of_all_files:
        for item in data:
            # Randomly delete 1, 2, or 3 q_a pairs with equal probabilities
            num_to_delete = random.randint(1, 4)
            if num_to_delete == 3 or num_to_delete == 4:
                data.remove(item)
            else:
                if num_to_delete == 1:
                    item['q_a'].pop(random.randint(0, len(item['q_a']) - 1))
                elif num_to_delete == 2:
                    item['q_a'].pop(random.randint(0, len(item['q_a']) - 1))
                    item['q_a'].pop(random.randint(0, len(item['q_a']) - 1))

    # Calculate the total quantity of all items currently
    total_num = 0
    for data in data_of_all_files:
        total_num += len(data)


    # Merge all the data into one list
    all_data = []
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            all_data.extend(data)

    # For each item's q_a, for each question_majority's q_a, randomly delete 1 or 2
    # if originally there is only 1, then do not delete
    for item in all_data:
        # Count the quantity of each question_majority within each item
        question_majority_counts = {}
        for q_a in item['q_a']:
            question_majority = q_a['question_majority']
            if question_majority in question_majority_counts:
                question_majority_counts[question_majority] += 1
            else:
                question_majority_counts[question_majority] = 1
        
        # For each question_majority, determine whether and how to delete q_a based on its quantity
        new_q_a_list = []
        for q_m, count in question_majority_counts.items():
            q_as = [q_a for q_a in item['q_a'] if q_a['question_majority'] == q_m]
            if count == 1:
                # If there is only 1 q_a, there is a 2/3 probability of deletion
                if random.random() < 2/3:
                    continue  # Not adding it to the new list is considered as deletion
            elif count ==2:
                # If there are 2 q_a pairs, then delete one
                q_as.pop(random.randint(0, 1))
            else:
                num_to_delete = random.randint(1, 4)
                if num_to_delete == 1:
                    q_as.pop(random.randint(0, 2))
                else:
                    q_as.pop(random.randint(0, 2))
                    q_as.pop(random.randint(0, 1))
                
                
            new_q_a_list.extend(q_as)  # Add the processed q_a to a new list

        item['q_a'] = new_q_a_list  # Update the item's q_a with the new list
                    

    # Re-number the id for each item, starting from 1
    for i, item in enumerate(all_data):
        item['id'] = i + 1

    # Extract the id, image name (images/id.png), prompt,
    # and negative_prompt for each item and save them to a new JSON file
    image_prompts = []
    for item in all_data:
        image_prompts.append({
            'id': item['id'],
            'images': [f"images/{item['id']}.png"], # e.g.,'images/1.png'
            'prompt': item['prompt'],
            'negative_prompt': item['negative_prompt']
        })
        
    for item in all_data:
        item['images'] = [f"images/{item['id']}.png"]

    # Re-format the data:
    all_q_a = []
    idx=1
    for item in all_data:
        for q_a in item['q_a']:
            new_item = {
                'id': idx,
                'images': item['images'],
                'prompt': item['prompt'],
                'negative_prompt': item['negative_prompt'],
                'question': q_a['question'],
                'answer': q_a['answer'],
                'question_type': q_a['question_type'],
                'task': q_a['task'],
                'options': q_a['options'],
                'question_majority': q_a['question_majority']
            }
            all_q_a.append(new_item)
            idx += 1

    # Add the instruction for each item
    """
    For each item, the instruction will be different based on the question_type:
    - For multi choice question, the instruction will be: "Question: {question} \nChoices:\n(A) {option1}\n(B) {option2}\n(C) {option3}\n(D) {option4}\nHint: Please answer the question and provide the correct option letter, e.g., (A), (B), (C), (D), at the end. Do not contain the analysis progress.\nYour answer is:"
    - For true or false question, the instruction will be: "Question: {question}\nChoices:\n(A) True\n(B) False\nHint: Please answer the question and provide the correct option letter, e.g., (A), (B), (C), (D), at the end. Do not contain the analysis progress.\nYour answer is:"
    - For image caption question, the instruction will be: "{question}\nYour answer is:"
    """
    for item in all_q_a:
        if item['question_type'] == 'multi choice':
            instruction = f"Question: {item['question']} \n"
            for i, option in enumerate(item['options']):
                instruction += f"({chr(65 + i)}) {option}\n"
            instruction += "Hint: Please answer the question and provide the correct option letter, e.g., (A), (B), (C), (D), at the end. Do not contain the analysis progress.\nYour answer is:"
            item['instruction'] = instruction
        elif item['question_type'] == 'true or false':
            instruction = f"Question: {item['question']}\nChoices:\n(A) True\n(B) False\nHint: Please answer the question and provide the correct option letter, e.g., (A), (B), (C), (D), at the end. Do not contain the analysis progress.\nYour answer is:"
            item['instruction'] = instruction
        elif item['question_type'] == 'image caption':
            instruction = f"{item['question']}\nYour answer is:"
            item['instruction'] = instruction

    # Re-format the data again:
    all_q_a = [{k: item[k] for k in ['id', 'images', 'prompt', 'negative_prompt', 'instruction', 'question', 'answer', 'question_type', 'task', 'options', 'question_majority']} for item in all_q_a]

    # Add the granularity for each item
    for item in all_q_a:
        if item['question_majority'] in ['style', 'background', 'color']:
            item['granularity'] = 'coarse'
        else:
            item['granularity'] = 'fine'
            

    # Split the data into style_q_a, background_q_a, and color_q_a
    style_q_a = [item for item in all_q_a if item['question_majority'] == 'style']
    background_q_a = [item for item in all_q_a if item['question_majority'] == 'background']
    color_q_a = [item for item in all_q_a if item['question_majority'] == 'color']

    # Randomly select 13000 items for each question_majority
    all_q_a = [item for item in all_q_a if item['question_majority'] not in ['style', 'background', 'color']]

    try:
        style_q_a = random.sample(style_q_a, 13000)
    except:
        pass
    try:
        background_q_a = random.sample(background_q_a, 13000)
    except:
        pass
    try:
        color_q_a = random.sample(color_q_a, 13000)
    except:
        pass
    
    # Combine all the question_majority data
    all_q_a.extend(style_q_a)
    all_q_a.extend(background_q_a)
    all_q_a.extend(color_q_a)

    # Re-number the id for each item, starting from 1
    for i, item in enumerate(all_q_a):
        item['id'] = i + 1
        

    # Output the final data to a JSON file
    with open(args.output_file, 'w') as f:
        json.dump(all_q_a, f, indent=4)
        
    """
    The output file will be a json file, which will be used for benchmarking, like:
    [
    {
        "id": 1,
        "images": [
        "images/1.png"
        ],
        "prompt": "face portrait of George Clooney ,sunset background, long exposure photo of, Blurred motion, streaks of light, surreal, dreamy, ghosting effect, highly detailed",
        "negative_prompt": "static, noisy, deformed, shaky, abrupt, flat, low contrast",
        "instruction": "Question: Who is the celebrity in the image?\nChoices:\n(A) Brad Pitt\n(B) Spencer Tracy\n(C) George Clooney\n(D) Tom Cruise\nHint: Please answer the question and provide the correct option letter, e.g., (A), (B), (C), (D), at the end. Do not contain the analysis progress.\nYour answer is:",
        "answer": "George Clooney",
        "question_type": "multi choice",
        "task": "recognition",
        "options": [
        "Brad Pitt",
        "Spencer Tracy",
        "George Clooney",
        "Tom Cruise"
        ],
        "question_majority": "celebrity"
    },
        ...
    ]
    """
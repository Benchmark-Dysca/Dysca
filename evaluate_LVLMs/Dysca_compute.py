import json
import os
# !pip install python-Levenshtein
from Levenshtein import distance
import re
import json
from tqdm import tqdm

import argparse
import pandas as pd

from sentence_transformers import SentenceTransformer


class DyscaDataset():
    def __init__(self, dataset_file='./Dysca.json', data_root='./data/', **kwargs):
        self.data_root = data_root
        with open(dataset_file) as file:
            self.data = json.load(file)
        self.num_samples = len(self.data)
        self.remove_list = []
        self.model = SentenceTransformer("all-MiniLM-L6-v2",device='cuda:0')
        
    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < self.num_samples:
            sample = self.data[self.index]
            sample['images'][0] = os.path.join(self.data_root, sample['images'][0])
            self.index += 1
            return sample
        else:
            raise StopIteration
        
    def get_most_similar(self,prediction, choices):
        """
        Use the Levenshtein distance (or edit distance) to determine which of the choices is most similar to the given prediction.
        """
        distances = [distance(prediction, choice) for choice in choices]
        min_dis = min(distances)
        if distances.count(min_dis) > 1:
            ind  = len(distances) - distances[::-1].index(min_dis) - 1
        else:
            ind = distances.index(min(distances))
        return choices[ind]

    def normalize_extracted_answer(self, question, extraction, question_type) -> str:
        """
        Normalize the extracted answer to match the answer type
        """
        if question_type == 'multi choice' or 'true or false':
            # make sure the extraction is a string
            if isinstance(extraction, str):
                extraction = extraction.strip()
            else:
                try:
                    extraction = str(extraction)
                except:
                    extraction = ""
        
            # extract "A" from "(A) text"
            letter = re.findall(r'\(([a-zA-Z])\)', extraction)
            if len(letter) == 0:
                letter = re.findall(r'[A-Z]', extraction)
            if len(letter) > 0:
                extraction = letter[-1].upper()
             
            question = question.split("Choices:\n")[-1].split("\nHint:")[0]
            choices = question.split("\n")
            
            options = [chr(ord('A') + i) for i in range(len(choices))]
                
            if extraction in options:
                # convert option letter to text, e.g. "A" -> "text"
                ind = options.index(extraction)
                extraction = choices[ind].split(" ")[1:]
                extraction = ' '.join(extraction)
            else:
                # select the most similar option
                extraction = self.get_most_similar(extraction, choices)
                extraction = extraction.split(" ")[1:]
                extraction = ' '.join(extraction)

        return extraction
    
    def caption_sent_transformer(self,sent1,sent2):
        sent1 = [sent1]
        sent2 = [sent2]
        
        embed1 = self.model.encode(sent1,device='cuda:0')
        embed2 = self.model.encode(sent2,device='cuda:0')
        
        similarities = self.model.similarity(embed1, embed2)
        
        similarities = round(similarities.item(),2)
        
        return similarities
    
    
    def safe_equal(self, prediction, gt):
        """
        Check if the prediction is equal to the gt, even if they are of different types
        """
        try:
            if prediction == gt:
                return True
            return False
        except Exception as e:
            print(e)
        return False
        
    def calculate_result(self, results, question_majority=None):
        """
        results: (json) the output of the dataset stored in json format, with each sample in the format {"id": XXX, "instruction": XXX, "in_images": XXX, "answer": XXX, "out_image": XXX, ... }
        question_majority: (str) fine-grained level of recognition tasks, e.g., age, gender. Set None to compute on all questions.
        Return: (dict) question_majority + question number + a quantized score
        """
        with open(results, 'r') as file:
            self.results = json.load(file)        
        assert len(self.results) == len(self.data)
        
        total = 0
        multi_choice_correct,true_or_false_correct,caption_score = 0.0,0.0,0.0
        multi_choice_total,true_or_false_total,caption_total = 0.0,0.0,0
        for idx in range(self.num_samples):
            if self.data[idx]["question_majority"] == question_majority or question_majority == None:
                question_type = self.data[idx]["question_type"]
                question = self.data[idx]["instruction"]
                answer = self.results[idx]["answer"]
                gt = self.data[idx]["answer"]
                if idx in self.remove_list:
                    continue
                total += 1
                if question_type == 'multi choice':
                    # normalize the extracted answer to match the answer type
                    prediction = self.normalize_extracted_answer(question,answer,question_type)
                    
                    # verify the prediction is true or false
                    true_false = self.safe_equal(prediction, gt)
                    if true_false:
                        multi_choice_correct+=1
                    else:
                        # normalize the extracted answer to match the answer type
                        prediction = self.normalize_extracted_answer(question,answer,question_type)
                        
                        # verify the prediction is true or false
                        true_false = self.safe_equal(prediction, gt)
                    multi_choice_total += 1
                elif question_type == "true or false":
                    # normalize the extracted answer to match the answer type
                    prediction = self.normalize_extracted_answer(question,answer,question_type)
                    
                    # verify the prediction is true or false
                    true_false = self.safe_equal(prediction, gt)
                    if true_false:
                        true_or_false_correct+=1
                    else:
                        # normalize the extracted answer to match the answer type
                        prediction = self.normalize_extracted_answer(question,answer,question_type)
                        
                        # verify the prediction is true or false
                        true_false = self.safe_equal(prediction, gt)
                    true_or_false_total += 1
                elif question_type == 'image caption':
                    caption_score += self.caption_sent_transformer(answer,gt)
                    caption_total += 1
                else:
                    pass
        if multi_choice_total == 0:
            multi_choice_accuracy = 0.0
        else:
            multi_choice_accuracy = round(multi_choice_correct / multi_choice_total * 100, 2)
        if true_or_false_total == 0:
            true_or_false_accuracy = 0.0
        else: 
            true_or_false_accuracy = round(true_or_false_correct / true_or_false_total * 100, 2)
        if caption_total == 0:
            caption_score_final = 0.0
        else: 
            caption_score_final = round(caption_score / caption_total * 100, 2)
        average = multi_choice_accuracy + true_or_false_accuracy + caption_score_final
        if question_majority == None:
            res = {
                'question_majority':question_majority, # fine-grained level
                'vqa_num':total, # the number of questions
                'multi_choice_accuracy':multi_choice_accuracy,
                'true_or_false_accuracy':true_or_false_accuracy,
                'caption_score':caption_score_final,
                'average':round(average/3,2)
            }
        else:
            res = {
                f'{question_majority}_multi_choice_accuracy':multi_choice_accuracy,
                f'{question_majority}_true_or_false_accuracy':true_or_false_accuracy,
                f'{question_majority}_caption_score':caption_score_final,
            }
        
        return res,multi_choice_accuracy,true_or_false_accuracy,caption_score_final
    
def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca Benchmark Generator',
        description='A script for generating evaluating images of Dysca Benchmark')
    parser.add_argument('--file_ground_truth', required=True, default='./Dysca.json', help="The ground truth file")  
    parser.add_argument('--file_model_output', required=True, default='./output_example.json', help='The model results file path') 
    parser.add_argument('--evaluation_score', required=True, default='./score_example.xlsx', help='The evaluation result file path')
    parser.add_argument('--model_name', required=True, default=None, help='The name of the model')
    
    return parser.parse_args()

if __name__ == '__main__':
    
    args = parse_args()
    
    Dysca_Dataset = DyscaDataset(dataset_file=args.file_ground_truth, data_root='./data/')
    print("===================")
    print("Now test Dysca!")
    print("===================")
    
    results_list = []
    avg_mc,avg_tf,avg_ic=0.0,0.0,0.0

    question_majorities = ['movie', 'action', 'tv show', 'profession', 'landmark', 'anime', 
        'clothes', 'celebrity', 'food', 'plant', 'age', 'gender', 'emotion',
        'race', 'animal', 'object', 'style', 'text','background', 'color','face']
    accuracys = []
    res = {'name':args.model_name}
    nan_mc,nan_tf,nan_ic = 0,0,0
    for qm in tqdm(question_majorities):
        accuracy,mc,tf,ic = Dysca_Dataset.calculate_result(results=args.file_model_result,question_majority=qm)
        res.update(accuracy)
        avg_mc += mc
        avg_tf += tf
        avg_ic += ic
        if ic == 0:
            nan_ic += 1
        if mc == 0:
            nan_mc += 1
        if tf == 0:
            nan_tf += 1

    res.update({'avg_mc':round(avg_mc/(len(question_majorities)-nan_mc),2)})
    res.update({'avg_tf':round(avg_tf/(len(question_majorities)-nan_tf),2)})
    res.update({'avg_ic':round(avg_ic/(len(question_majorities)-nan_ic),2)})
    accuracys.append(res)

    results_list.append(res)

    df = pd.DataFrame(results_list)
    df.to_excel(args.evaluation_result, index=False)
    
    print('avg_mc:',round(avg_mc/(len(question_majorities)-nan_mc),2))
    print('avg_tf:',round(avg_tf/(len(question_majorities)-nan_tf),2))
    print('avg_ic:',round(avg_ic/(len(question_majorities)-nan_ic),2))
import json
import random
import time
import numpy as np
import os
import argparse
from tqdm import tqdm
import shutil

dict_path = {
    "style": "./metadata/Styles.json",
    "action": "./metadata/Actions.txt",
    "animal": "./metadata/Animal.txt",
    "anime": "./metadata/Anime.txt",
    "background": "./metadata/Background.txt",
    "brand": "./metadata/Brand.txt",
    "celebrity": "./metadata/Celebrity.txt",
    "clothes": "./metadata/Clothes.txt",
    "food": "./metadata/Food.txt",
    "landmark": "./metadata/Landmarks.txt",
    "movie": "./metadata/Movie.txt",
    "object": "./metadata/Object.txt",
    "plant": "./metadata/Plant.txt",
    "profession": "./metadata/Profession.txt",
    "tv show": "./metadata/TV shows.txt",
    "age": "./metadata/People/Age.txt",
    "color": "./metadata/Color.txt",
    "expression": "./metadata/People/Expression.txt",
    "race": "./metadata/People/Race.txt",
    "gender": "./metadata/People/Gender.txt",
    "text_template": "./metadata/ocr_text.json",
    "text": "./metadata/text.txt"
}

style_file = "./metadata/Styles.json"

with open(style_file, 'r', encoding='utf-8') as file:
    all_styles = json.load(file)
    
def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca PQA (Prompt Question Answer) Generator')  
    
    parser.add_argument('--tasks', 
                        type=str, 
                        nargs='*',
                        required=True,
                        default=['overall'],
                        help="The subtask of the prompt question answer generation")
    parser.add_argument('--prompt_num',
                        required=True, 
                        default=2500, 
                        type=int, 
                        help="The number of prompt question answer generation")
    parser.add_argument('--save_dir', 
                        required=True,
                        default='./source/', 
                        help="The directory to save the prompt question answer generation")
    
    return parser.parse_args()


class Attribute:
    def __init__(self, type=None, number=1, color=None, age=None, gender=None, expression=None, race=None):
        self.type = type
        # for object stuff
        self.number = number
        self.color = color
        # for human face stuff
        self.age = age
        self.gender = gender
        self.expression = expression
        self.race = race


class PictureInfo:
    def __init__(self, foreground=None, attribute=None, background=None, style=None):
        self.foreground = foreground
        self.attribute = attribute
        self.background = background
        self.style = style


class Prompt:

    def __init__(self, attribute=None, foreground=None, background=None, style=None):
        self.attribute = attribute
        self.foreground = foreground
        self.background = background
        self.style = style
        prompt_pair = self.generate_prompt_pair()
        self.prompt = prompt_pair[0]
        self.negative_prompt = prompt_pair[1]

    def generate_prompt_pair(self):
        prompt = self.style["prompt"]
        negative_prompt = self.style["negative_prompt"]

        content = self.generate_content() + ", "

        prompt = prompt.replace(" {}.", ",")

        prompt = content + prompt

        return [prompt, negative_prompt]

    def generate_content(self):

        content = ""

        if self.attribute.type == "text":
            content = self.foreground

        elif self.attribute.type == "celebrity":
            content = "face portrait of {name} ,{background}".format(name=self.foreground, background=self.background)

        elif self.attribute.type == "object":
            if self.attribute.number != "":
                number = self.attribute.number + " "
            else:
                number = ""
            if self.attribute.color != "":
                color = self.attribute.color + " "
            else:
                color = ""

            content = "{number}{color}{foreground},{background}".format(number=number,
                                                                        color=color,
                                                                        foreground=self.foreground,
                                                                        background=self.background)

        elif self.attribute.type in ["animal", "plant", "food"]:
            if self.attribute.number != "":
                number = self.attribute.number + " "
            else:
                number = ""
            if self.attribute.color != "":
                color = self.attribute.color + " "
            else:
                color = ""

            content = "{number}{color}{foreground}, {background}".format(number=number,
                                                                         color=color,
                                                                         foreground=self.foreground,
                                                                         background=self.background)
        elif self.attribute.type in ["food"]:
            if self.attribute.number != "":
                number = self.attribute.number + " "
            else:
                number = ""
            if self.attribute.color != "":
                color = self.attribute.color + " "
            else:
                color = ""

            content = "the delicious {color}{foreground}, {background}".format(color=color,
                                                                               foreground=self.foreground,
                                                                               background=self.background)

        elif self.attribute.type == "clothes":
            if self.attribute.color != "":
                color = self.attribute.color + " "
            else:
                color = ""
            if self.attribute.number != "":
                number = self.attribute.number + " "
            else:
                number = ""
            content = "{number}{color}{foreground}".format(number=number, color=color, foreground=self.foreground)


        elif self.attribute.type == "landmark":
            content = "the overall {foreground}".format(foreground=self.foreground,
                                                        background=self.background)
        elif self.attribute.type == "profession":
            content = "{number} {foreground}".format(number=self.attribute.number,
                                                     foreground=self.foreground)
        elif self.attribute.type in ["tv show", "movie", "anime"]:
            content = "a scene from {foreground}".format(foreground=self.foreground)
        elif self.attribute.type == "face":
            content = "face portrait of a {age} {gender}, {race}, {expression}, {background}".format(
                age=self.attribute.age, gender=self.attribute.gender, race=self.attribute.race,
                expression=self.attribute.expression, background=self.background, foreground=self.foreground)
        elif self.attribute.type == "action":
            content = "a person {foreground}, {background}".format(foreground=self.foreground,
                                                                   background=self.background)
        return content


class QA:
    def __init__(self, task=None, question_type=None, majority=None, picture_info=None):
        self.all_styles = all_styles
        self.task = task
        self.question_type = question_type
        self.majority = majority
        self.picture_info = picture_info
        self.question, self.answer, self.options = self.generate_qa()

    def generate_qa(self):
        question = ""
        options = []
        answer = ""
        if self.question_type == "multi choice":
            if self.task == "recognition":
                if self.majority == "celebrity":

                    question = "Who is the celebrity in the image?"
                    answer = self.picture_info.foreground
                    options.append(self.picture_info.foreground)
                    with open(dict_path["celebrity"], 'r', encoding='utf-8') as file:
                        celebrities = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_celebrity = random.choice(celebrities)
                        while neg_celebrity == self.picture_info.foreground or neg_celebrity in options:
                            neg_celebrity = random.choice(celebrities)
                        options.append(neg_celebrity)

                elif self.majority in ["animal", "plant", "clothes", "object", "food"]:
                    question = "What is the {majority} in the image?".format(majority=self.majority)
                    answer = self.picture_info.foreground
                    options.append(self.picture_info.foreground)
                    with open(dict_path[self.majority], 'r', encoding='utf-8') as file:
                        items = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_item = random.choice(items)
                        while neg_item == self.picture_info.foreground or neg_item in options:
                            neg_item = random.choice(items)
                        options.append(neg_item)

                elif self.majority == "landmark":
                    question = "What is the landmark in the image?"
                    answer = self.picture_info.foreground
                    options.append(self.picture_info.foreground)
                    with open(dict_path["landmark"], 'r', encoding='utf-8') as file:
                        landmarks = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_landmark = random.choice(landmarks)
                        while neg_landmark == self.picture_info.foreground or neg_landmark in options:
                            neg_landmark = random.choice(landmarks)
                        options.append(neg_landmark)

                elif self.majority == "profession":
                    question = "What is the occupation of the person in the picture?"
                    answer = self.picture_info.foreground
                    options.append(self.picture_info.foreground)
                    with open(dict_path["profession"], 'r', encoding='utf-8') as file:
                        professions = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_profession = random.choice(professions)
                        while neg_profession == self.picture_info.foreground or neg_profession in options:
                            neg_profession = random.choice(professions)
                        options.append(neg_profession)


                elif self.majority in ["tv show", "movie", "anime"]:
                    question = "Which {majority} is the scene in the picture from?".format(majority=self.majority)
                    answer = self.picture_info.foreground
                    options.append(self.picture_info.foreground)
                    with open(dict_path[self.majority], 'r', encoding='utf-8') as file:
                        items = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_item = random.choice(items)
                        while neg_item == self.picture_info.foreground or neg_item in options:
                            neg_item = random.choice(items)
                        options.append(neg_item)

                elif self.majority == "age":
                    question = "How old is the person in the image?"
                    answer = self.picture_info.attribute.age
                    options.append(self.picture_info.attribute.age)
                    with open(dict_path["age"], 'r', encoding='utf-8') as file:
                        ages = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_age = random.choice(ages)
                        while neg_age == self.picture_info.attribute.age or neg_age in options:
                            neg_age = random.choice(ages)
                        options.append(neg_age)


                elif self.majority == "gender":
                    question = "What is the gender of the person in the picture?"
                    answer = self.picture_info.attribute.gender
                    options = ["male", "female"]

                elif self.majority == "race":
                    question = "What is the race of the person in the picture?"
                    answer = self.picture_info.attribute.race
                    options.append(self.picture_info.attribute.race)
                    with open(dict_path["race"], 'r', encoding='utf-8') as file:
                        races = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_race = random.choice(races)
                        while neg_race == self.picture_info.attribute.race or neg_race in options:
                            neg_race = random.choice(races)
                        options.append(neg_race)


                elif self.majority == "expression":
                    question = "What is the expression of the person in the picture"
                    answer = self.picture_info.attribute.expression
                    options = ["smiling happily", "shouting furiously", "calm and placid"]


                elif self.majority == "action":
                    question = "What is the person doing in the picture?"
                    answer = self.picture_info.foreground
                    options.append(self.picture_info.foreground)
                    with open(dict_path["action"], 'r', encoding='utf-8') as file:
                        actions = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_action = random.choice(actions)
                        while neg_action == self.picture_info.foreground or neg_action in options:
                            neg_action = random.choice(actions)
                        options.append(neg_action)

                elif self.majority == "style":
                    question = "What is the style of the picture?"
                    answer = self.picture_info.style["name"]
                    options.append(self.picture_info.style["name"])
                    style_file = "./metadata/Styles.json"
                    with open(style_file, 'r', encoding='utf-8') as file:
                        all_styles = json.load(file)
                    for i in range(3):
                        neg_style = random.choice(all_styles)
                        while neg_style == self.picture_info.style or neg_style in options:
                            neg_style = random.choice(all_styles)
                        options.append(neg_style["name"])

                elif self.majority == "color":
                    question = "What is the color of the {foreground} in the picture?".format(
                        foreground=self.picture_info.foreground)
                    answer = self.picture_info.attribute.color
                    options.append(self.picture_info.attribute.color)
                    with open(dict_path["color"], 'r', encoding='utf-8') as file:
                        colors = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_color = random.choice(colors)
                        while neg_color == self.picture_info.attribute.color or neg_color in options:
                            neg_color = random.choice(colors)
                        options.append(neg_color)


                elif self.majority == "background":
                    question = "What is the background in the picture?"
                    answer = self.picture_info.background
                    options.append(self.picture_info.background)
                    with open(dict_path["background"], 'r', encoding='utf-8') as file:
                        backgrounds = [line.strip() for line in file.readlines()]
                    for i in range(3):
                        neg_background = random.choice(backgrounds)
                        while neg_background == self.picture_info.background or neg_background in options:
                            neg_background = random.choice(backgrounds)
                        options.append(neg_background)

            elif self.task == "OCR":
                question = "What are all the scene text in the image?"
                answer = self.picture_info.foreground
                options.append(self.picture_info.foreground)
                with open(dict_path["text"], 'r', encoding='utf-8') as file:
                    texts = [line.strip() for line in file.readlines()]
                for i in range(3):
                    neg_text = random.choice(texts)
                    while neg_text == self.picture_info.foreground or neg_text in options:
                        neg_text = random.choice(texts)
                    options.append(neg_text)

        elif self.question_type == "true or false":

            if self.task == "recognition":
                if self.majority == "celebrity":
                    options.append("True")
                    options.append("False")

                    if random.random() > 0.5:
                        with open(dict_path["celebrity"], 'r', encoding='utf-8') as file:
                            celebrities = [line.strip() for line in file.readlines()]
                        neg_celebrity = random.choice(celebrities)
                        while neg_celebrity == self.picture_info.foreground:
                            neg_celebrity = random.choice(celebrities)
                        question = f"Is the celebrity in the picture {neg_celebrity} ?"
                        answer = "False"
                    else:
                        question = f"Is the celebrity in the picture {self.picture_info.foreground} ?"
                        answer = "True"


                elif self.majority in ["animal", "plant", "clothes", "object", "food"]:
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path[self.majority], 'r', encoding='utf-8') as file:
                            items = [line.strip() for line in file.readlines()]
                        neg_item = random.choice(items)
                        while neg_item == self.picture_info.foreground:
                            neg_item = random.choice(items)
                        question = f"Is there a {neg_item} in the picture?"
                        answer = "False"
                    else:
                        question = f"Is there a {self.picture_info.foreground} in the picture?"
                        answer = "True"

                elif self.majority == "landmark":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["landmark"], 'r', encoding='utf-8') as file:
                            landmarks = [line.strip() for line in file.readlines()]
                        neg_landmark = random.choice(landmarks)
                        while neg_landmark == self.picture_info.foreground:
                            neg_landmark = random.choice(landmarks)
                        question = f"Is the landmark in the picture {neg_landmark} ?"
                        answer = "False"
                    else:
                        question = f"Is the landmark in the picture {self.picture_info.foreground} ?"
                        answer = "True"

                elif self.majority == "profession":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["profession"], 'r', encoding='utf-8') as file:
                            professions = [line.strip() for line in file.readlines()]
                        neg_profession = random.choice(professions)
                        while neg_profession == self.picture_info.foreground:
                            neg_profession = random.choice(professions)
                        question = f"Is the person in the picture a {neg_profession} ?"
                        answer = "False"
                    else:
                        question = f"Is the person in the picture a {self.picture_info.foreground} ?"
                        answer = "True"


                elif self.majority in ["tv show", "movie", "anime"]:
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path[self.majority], 'r', encoding='utf-8') as file:
                            items = [line.strip() for line in file.readlines()]
                        neg_item = random.choice(items)
                        while neg_item == self.picture_info.foreground:
                            neg_item = random.choice(items)
                        question = f"Is the scene in the picture from the {self.majority} {neg_item} ?"
                        answer = "False"
                    else:
                        question = f"Is the scene in the picture from the {self.majority} {self.picture_info.foreground} ?"
                        answer = "True"

                elif self.majority == "age":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["age"], 'r', encoding='utf-8') as file:
                            ages = [line.strip() for line in file.readlines()]
                        neg_age = random.choice(ages)
                        while neg_age == self.picture_info.attribute.age:
                            neg_age = random.choice(ages)
                        question = f"Is the age of the person in the picture about {neg_age} ?"
                        answer = "False"
                    else:
                        question = f"Is the age of the person in the picture about {self.picture_info.attribute.age} ?"
                        answer = "True"



                elif self.majority == "gender":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        if self.picture_info.attribute.gender == "male":
                            neg_gender = "female"
                        else:
                            neg_gender = "male"
                        question = f"Is the person in the picture a {neg_gender}?"
                        answer = "False"
                    else:
                        question = f"Is the person in the picture a {self.picture_info.attribute.gender} ?"
                        answer = "True"


                elif self.majority == "race":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["race"], 'r', encoding='utf-8') as file:
                            races = [line.strip() for line in file.readlines()]
                        neg_race = random.choice(races)
                        while neg_race == self.picture_info.attribute.race:
                            neg_race = random.choice(races)
                        question = f"Is the person in the picture {neg_race} ?"
                        answer = "False"
                    else:
                        question = f"Is the person in the picture {self.picture_info.attribute.race} ?"
                        answer = "True"


                elif self.majority == "expression":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["expression"], 'r', encoding='utf-8') as file:
                            expressions = [line.strip() for line in file.readlines()]
                        neg_expression = random.choice(expressions)
                        while neg_expression == self.picture_info.attribute.expression:
                            neg_expression = random.choice(expressions)
                        question = f"Is the person in the picture {neg_expression} ?"
                        answer = "False"
                    else:
                        question = f"Is the person in the picture {self.picture_info.attribute.expression} ?"
                        answer = "True"


                elif self.majority == "action":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["action"], 'r', encoding='utf-8') as file:
                            actions = [line.strip() for line in file.readlines()]
                        neg_action = random.choice(actions)
                        while neg_action == self.picture_info.foreground:
                            neg_action = random.choice(actions)
                        question = f"Is the person in the picture {neg_action} ?"
                        answer = "False"
                    else:
                        question = f"Is the person in the picture {self.picture_info.foreground} ?"
                        answer = "True"

                elif self.majority == "style":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        neg_style = random.choice(self.all_styles)
                        while neg_style == self.picture_info.style["name"]:
                            neg_style = random.choice(self.all_styles)

                        neg_style = neg_style["name"]
                        question = f"Is the picture {neg_style} style ?"
                        answer = "False"
                    else:
                        question = f"Is the picture {self.picture_info.style['name']} style ?"
                        answer = "True"

                elif self.majority == "color":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["color"], 'r', encoding='utf-8') as file:
                            colors = [line.strip() for line in file.readlines()]
                        neg_color = random.choice(colors)
                        while neg_color == self.picture_info.attribute.color:
                            neg_color = random.choice(colors)
                        question = f"Is the color of the {self.picture_info.foreground} in the picture {neg_color} ?"
                        answer = "False"
                    else:
                        question = f"Is the color of the {self.picture_info.foreground} in the picture {self.picture_info.attribute.color} ?"
                        answer = "True"



                elif self.majority == "background":
                    options.append("True")
                    options.append("False")
                    if random.random() > 0.5:
                        with open(dict_path["background"], 'r', encoding='utf-8') as file:
                            backgrounds = [line.strip() for line in file.readlines()]
                        neg_background = random.choice(backgrounds)
                        while neg_background == self.picture_info.background:
                            neg_background = random.choice(backgrounds)
                        question = f"Is the background in the picture {neg_background} ?"
                        answer = "False"
                    else:
                        question = f"Is the background in the picture {self.picture_info.background} ?"
                        answer = "True"


            elif self.task == "OCR":
                options.append("True")
                options.append("False")
                if random.random() > 0.5:
                    with open(dict_path["text"], 'r', encoding='utf-8') as file:
                        texts = [line.strip() for line in file.readlines()]
                    neg_text = random.choice(texts)
                    while neg_text == self.picture_info.foreground:
                        neg_text = random.choice(texts)
                    question = f"Is the scene text in the picture '{neg_text}' ?"
                    answer = "False"
                else:
                    question = f"Is the scene text in the picture '{self.picture_info.foreground}' ?"
                    answer = "True"

        elif self.question_type == "image caption":
            if self.task == "recognition":
                if self.majority == "celebrity":
                    question = "Please describe the image. You can describe it from these aspects: the identity of the person, the background, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    background = self.picture_info.background + " background"
                    style = self.picture_info.style["name"] + " style"
                    answer = foreground + ", " + background + ", " + style

                elif self.majority in ["object", "animal"]:
                    question = "Please describe the image. You can describe it from these aspects: the subject of the image, its color, the background, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    color = self.picture_info.attribute.color
                    background = self.picture_info.background + " background"
                    style = self.picture_info.style["name"] + " style"
                    answer = color + " " + foreground + ", " + background + ", " + style

                elif self.majority == "clothes":
                    question = "Please describe the image. You can describe it from these aspects: the subject of the image, its color, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    color = self.picture_info.attribute.color
                    style = self.picture_info.style["name"] + " style"
                    answer = color + " " + foreground + ", " + style

                elif self.majority in ["plant", "food"]:
                    question = "Please describe the image. You can describe it from these aspects: the subject of the image, the background, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    background = self.picture_info.background + " background"
                    style = self.picture_info.style["name"] + " style"
                    answer = foreground + ", " + background + ", " + style

                elif self.majority == "landmark":
                    question = "Please describe the image. You can describe it from these aspects: the subject of the image, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    style = self.picture_info.style["name"] + " style"
                    answer = foreground + ", " + style

                elif self.majority == "profession":
                    question = "Please describe the image. You can describe it from these aspects: the subject of the image, the profession of the person, the background, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    style = self.picture_info.style["name"] + " style"
                    answer = foreground + ", " + style


                elif self.majority in ["tv show", "movie", "anime"]:
                    question = f"Please describe the image. You can describe it from these aspects: the {self.majority} from which the scene is made, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    style = self.picture_info.style["name"] + " style"
                    answer = foreground + ", " + style

                elif self.majority == "face":
                    question = "Please describe the image. You can describe it from these aspects: the person's gender, age, facial expression, race, the background, the artistic style of the image."
                    gender = self.picture_info.attribute.gender
                    age = self.picture_info.attribute.age
                    expression = self.picture_info.attribute.expression
                    race = self.picture_info.attribute.race
                    background = self.picture_info.background + " background"
                    style = self.picture_info.style["name"] + " style"
                    answer = gender + ", " + age + ", " + expression + ", " + race + ", " + background + ", " + style


                elif self.majority == "action":
                    question = "Please describe the image. You can describe it from these aspects: the action of the person, the background, the artistic style of the image."
                    foreground = self.picture_info.foreground
                    background = self.picture_info.background + " background"
                    style = self.picture_info.style["name"] + " style"
                    answer = foreground + ", " + background + ", " + style

            elif self.task == "OCR":
                question = "Please describe all the scene text in the image."
                foreground = self.picture_info.foreground
                answer = foreground

        if "True" not in options:
            random.shuffle(options)

        return question, answer, options


class P_Q_A:
    '''
    P: Prompt
    Q: Question
    A: Answer
    '''
    def __init__(self, prompt=None, qas=None):
        self.Prompt = prompt
        self.QA_list = qas


class QuestionMajority:
    def __init__(self, foreground=None, attributes=None, background=None, style=None):
        '''
        Define the main attributes when generating questions.
        
        Attributes:
            - param foreground: Type of subject, possible values are "face", "animal", "plant", "clothes", "object", "food", "landmark",
                                "action", "celebrity", "profession", "movie", "tv show", "anime", "text".
            - param attributes: List of attributes, possible values are "age", "gender", "race", "expression", "color".
            - param background: Type of background, possible values are "background" or None.
            - param style: Type of style, possible values are "style" or None.
        '''
        self.foreground = foreground
        self.attributes = attributes
        self.background = background
        self.style = style


def txt2list(path):
    l = []
    with open(path, 'r', encoding='utf-8') as file:
        l += [line.strip() for line in file.readlines()]
    return l

def remove_duplicate_prompts(pqa_list):
    seen_prompts = set()
    unique_pqa = []

    for item in pqa_list:
        prompt = item['prompt']
        if prompt not in seen_prompts:
            unique_pqa.append(item)
            seen_prompts.add(prompt)

    return unique_pqa

def main(tasks, styles, ques_majority, question_types, prompt_num=2500, save_dir="./"):
    '''
    Generate prompts and their corresponding QA pairs.
    
    Attributes:
        - param tasks: List of tasks, possible values are "recognition" and "OCR".
        - param styles: List of styles, if empty, all styles will be used.
        - param ques_majority: `QuestionMajority` object, defines the main attributes when generating questions
        - param question_types: List of question types, possible values are "multi choice", "true or false", "image caption" (i.e., free-form).
        - param prompt_num: Number of prompts of each ques_majority to generate, default value is set to 2500.
        - param save_dir: Directory to save the results
    '''
    all_prompt_ques_ans = []

    background_list = txt2list(dict_path["background"])
    style_list = []
    if len(styles) == 0:
        style_list = all_styles
    else:
        for style in styles:
            for s in all_styles:
                if style == s["name"]:
                    style_list.append(s)

    if ques_majority.foreground is not None:
        if ques_majority.foreground == "text":
            text_list = txt2list(dict_path["text"])
            with open(dict_path["text_template"], 'r', encoding='utf-8') as file:
                text_template_list = json.load(file)

            for i in range(prompt_num):
                text = random.choice(text_list)
                txt_template = random.choice(text_template_list)
                text_template = txt_template.copy()

                text_template["template"] = text_template["template"].format(text)
                text_template["text"] = text

                attr = Attribute(type="text")
                style = random.choice(style_list)
                this_prompt = Prompt(attribute=attr, foreground=text_template["template"], background=None, style=style)
                picture_info = PictureInfo(foreground=text, attribute=attr, background=None, style=style)
                qas = []
                for task in tasks:
                    for question_type in question_types:
                        if question_type == "image caption":
                            qa = QA(task=task, question_type="image caption", majority=ques_majority.foreground,
                                    picture_info=picture_info)
                            qas.append(qa)
                        else:
                            if ques_majority.foreground is not None:
                                qa = QA(task=task, question_type=question_type, majority=ques_majority.foreground,
                                        picture_info=picture_info)
                                qas.append(qa)

                pqa = P_Q_A(prompt=this_prompt, qas=qas)
                all_prompt_ques_ans.append(pqa)

        if ques_majority.foreground == "face":
            age_list = txt2list(dict_path["age"])
            gender_list = txt2list(dict_path["gender"])
            race_list = txt2list(dict_path["race"])
            expression_list = txt2list(dict_path["expression"])

            for i in range(prompt_num):
                age = random.choice(age_list)
                gender = random.choice(gender_list)
                race = random.choice(race_list)
                expression = random.choice(expression_list)
                attr = Attribute(type="face", age=age, gender=gender, expression=expression, race=race)
                background = random.choice(background_list)
                style = random.choice(style_list)
                this_prompt = Prompt(attribute=attr, foreground=ques_majority.foreground, background=background,
                                     style=style)
                picture_info = PictureInfo(foreground=ques_majority.foreground, attribute=attr, background=background,
                                           style=style)
                qas = []
                for task in tasks:
                    for question_type in question_types:
                        if question_type == "image caption":
                            qa = QA(task=task, question_type="image caption", majority="face",
                                    picture_info=picture_info)
                            qas.append(qa)
                        else:
                            if "age" in ques_majority.attributes:
                                qa = QA(task=task, question_type=question_type, majority="age",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if "gender" in ques_majority.attributes:
                                qa = QA(task=task, question_type=question_type, majority="gender",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if "expression" in ques_majority.attributes:
                                qa = QA(task=task, question_type=question_type, majority="expression",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if "race" in ques_majority.attributes:
                                qa = QA(task=task, question_type=question_type, majority="race",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if ques_majority.background is not None:
                                qa = QA(task=task, question_type=question_type, majority="background",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if ques_majority.style is not None:
                                qa = QA(task=task, question_type=question_type, majority="style",
                                        picture_info=picture_info)
                                qas.append(qa)

                pqa = P_Q_A(prompt=this_prompt, qas=qas)
                all_prompt_ques_ans.append(pqa)


        elif ques_majority.foreground in ["animal", "plant", "clothes", "object", "food", "landmark"]:
            object_list = txt2list(dict_path[ques_majority.foreground])
            color_list = []
            number_list = ["1"]
            if ques_majority.attributes is not None:
                if "color" in ques_majority.attributes:
                    color_list = txt2list(dict_path["color"])
            for i in range(prompt_num):
                obj = random.choice(object_list)
                color = random.choice(color_list) if len(color_list) > 0 else ""
                number = random.choice(number_list)
                attr = Attribute(type=ques_majority.foreground, color=color, number=number)
                background = random.choice(background_list)
                style = random.choice(style_list)
                this_prompt = Prompt(attribute=attr, foreground=obj, background=background,
                                     style=style)

                picture_info = PictureInfo(foreground=obj, attribute=attr, background=background,
                                           style=style)
                qas = []
                for task in tasks:
                    for question_type in question_types:
                        if question_type == "image caption":
                            qa = QA(task=task, question_type="image caption", majority=ques_majority.foreground,
                                    picture_info=picture_info)
                            qas.append(qa)
                        else:

                            if ques_majority.foreground is not None:
                                qa = QA(task=task, question_type=question_type, majority=ques_majority.foreground,
                                        picture_info=picture_info)
                                qas.append(qa)
                            if "color" in ques_majority.attributes:
                                qa = QA(task=task, question_type=question_type, majority="color",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if ques_majority.background is not None:
                                qa = QA(task=task, question_type=question_type, majority="background",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if ques_majority.style is not None:
                                qa = QA(task=task, question_type=question_type, majority="style",
                                        picture_info=picture_info)
                                qas.append(qa)

                pqa = P_Q_A(prompt=this_prompt, qas=qas)
                all_prompt_ques_ans.append(pqa)

        elif ques_majority.foreground in ["action", "celebrity", "profession"]:
            list_foreground = txt2list(dict_path[ques_majority.foreground])

            for i in range(prompt_num):
                this_foreground = random.choice(list_foreground)
                attr = Attribute(type=ques_majority.foreground)
                background = random.choice(background_list)
                style = random.choice(style_list)
                this_prompt = Prompt(attribute=attr, foreground=this_foreground, background=background,
                                     style=style)
                picture_info = PictureInfo(foreground=this_foreground, attribute=attr, background=background,
                                           style=style)
                qas = []
                for task in tasks:
                    for question_type in question_types:
                        if question_type == "image caption":
                            qa = QA(task=task, question_type="image caption", majority=ques_majority.foreground,
                                    picture_info=picture_info)
                            qas.append(qa)
                        else:
                            if ques_majority.foreground is not None:
                                qa = QA(task=task, question_type=question_type, majority=ques_majority.foreground,
                                        picture_info=picture_info)
                                qas.append(qa)
                            if ques_majority.background is not None:
                                qa = QA(task=task, question_type=question_type, majority="background",
                                        picture_info=picture_info)
                                qas.append(qa)
                            if ques_majority.style is not None:
                                qa = QA(task=task, question_type=question_type, majority="style",
                                        picture_info=picture_info)
                                qas.append(qa)

                pqa = P_Q_A(prompt=this_prompt, qas=qas)
                all_prompt_ques_ans.append(pqa)

        elif ques_majority.foreground in ["tv show", "movie", "anime"]:
            list_foreground = txt2list(dict_path[ques_majority.foreground])
            for i in range(prompt_num):
                this_foreground = random.choice(list_foreground)
                attr = Attribute(type=ques_majority.foreground)
                style = random.choice(style_list)
                this_prompt = Prompt(attribute=attr, foreground=this_foreground, background=None,
                                     style=style)
                picture_info = PictureInfo(foreground=this_foreground, attribute=attr, background=None,
                                           style=style)
                qas = []
                for task in tasks:
                    for question_type in question_types:
                        if question_type == "image caption":
                            qa = QA(task=task, question_type="image caption", majority=ques_majority.foreground,
                                    picture_info=picture_info)
                            qas.append(qa)
                        else:
                            if ques_majority.foreground is not None:
                                qa = QA(task=task, question_type=question_type, majority=ques_majority.foreground,
                                        picture_info=picture_info)
                                qas.append(qa)
                            if ques_majority.style is not None:
                                qa = QA(task=task, question_type=question_type, majority="style",
                                        picture_info=picture_info)
                                qas.append(qa)
                pqa = P_Q_A(prompt=this_prompt, qas=qas)
                all_prompt_ques_ans.append(pqa)

        all_pqa = []
        i = 1
        for pqa in all_prompt_ques_ans:
            this_pqa = {}
            id = i
            i += 1
            prompt = pqa.Prompt.prompt
            negative_prompt = pqa.Prompt.negative_prompt
            questions = []
            if pqa.QA_list is not None:
                for qa in pqa.QA_list:
                    task = qa.task
                    question = qa.question
                    answer = qa.answer
                    options = qa.options
                    question_type = qa.question_type
                    majority = qa.majority
                    questions.append({"question": question, "answer": answer,
                                      "options": options,
                                      "task": task,
                                      "question_type": question_type,
                                      "question_majority": majority})
            this_pqa["id"] = id
            this_pqa["prompt"] = prompt
            this_pqa["negative_prompt"] = negative_prompt
            this_pqa["q_a"] = questions
            all_pqa.append(this_pqa)

        all_pqa = remove_duplicate_prompts(all_pqa)

        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())

        save_path = save_dir + "PQA_" + ques_majority.foreground + '_' +str(len(all_pqa)) + "_" + timestamp + ".json"
        with open(save_path, 'w', encoding='utf-8') as file:
            json.dump(all_pqa, file, ensure_ascii=False, indent=4)


def set_seed(seed: int = 42):
    '''set the radom seed'''
    np.random.seed(seed)
    random.seed(seed)
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    print(f"Random seed set as {seed}")

if __name__ == "__main__":
    set_seed(2024)
    args = parse_args()
    
    mapping_dict = {
        "face": (["age", "gender", "expression", "race"], "background"), 
        "animal": (["color"], "background"),
        "plant": ([], "background"),
        "clothes": (["color"], []),
        "object": (["color"], "background"),
        "food": ([], "background"),
        "landmark": ([], []),
        "action": ([], "background"),
        "celebrity": ([], "background"),
        "profession": ([], []),
        "movie": ([], []),
        "tv show": ([], []),
        "anime": ([], []),
        "text": ([], [])
    }
    
    if not os.path.exists(args.save_dir):
        os.mkdir(args.save_dir)
    else:
        shutil.rmtree(args.save_dir)
        os.mkdir(args.save_dir)
    
    if args.tasks[0] == 'overall':
        for task in tqdm(mapping_dict.keys()):
            main(tasks=["recognition"],
                styles=[], # all styles are available if not specified
                ques_majority=QuestionMajority(foreground = task, 
                                            attributes = mapping_dict[task][0],
                                            background = mapping_dict[task][1],
                                            style="style"),
                question_types=['multi choice', 'true or false', 'image caption'],
                prompt_num=args.prompt_num,
                save_dir=args.save_dir)
    else:      
        for task in args.tasks:
            main(tasks=["recognition"],
                styles=[], # all styles are available if not specified
                ques_majority=QuestionMajority(foreground = task, 
                                            attributes = mapping_dict[task][0],
                                            background = mapping_dict[task][1],
                                            style="style"),
                question_types=['multi choice', 'true or false', 'image caption'],
                prompt_num=args.prompt_num,
                save_dir=args.save_dir)

    '''
    The file will generate the PQA lists, like:
    # each image corresponds to at least 1 question
    [
        {
            "id": 1,
            "prompt": "face portrait of a 25 years old male, African race, smiling happily, countryside with rolling hills background, thick layered papercut art of, deep 3D, volumetric, dimensional, depth, thick paper, high stack, heavy texture, tangible layers",
            "negative_prompt": "2D, flat, thin paper, low stack, smooth texture, painting, drawing, photo, deformed",
            "q_a": [
                {
                    "question": "What is the background in the picture?",
                    "answer": "countryside with rolling hills background",
                    "options": [
                        "snow-covered landscape background",
                        "under the water background",
                        "desert scenery background",
                        "countryside with rolling hills background"
                    ],
                    "task": "recognition",
                    "question_type": "multi choice",
                    "question_majority": "background"
                },
                {
                    "question": "What is the style of the picture?",
                    "answer": "thick layered papercut",
                    "options": [
                        "fairy tale",
                        "iphone photographic",
                        "zelda",
                        "thick layered papercut"
                    ],
                    "task": "recognition",
                    "question_type": "multi choice",
                    "question_majority": "style"
                },
                ...
            ]
        },
        ...
    ]
    
    '''
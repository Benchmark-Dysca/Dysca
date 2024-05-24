# User Manual: Generating Prompts and QA Pairs for Visual Question Answering Tasks

## Contents
1. [Introduction](#introduction)
2. [Code Structure](#code-structure)
3. [Parameters](#parameters)
4. [Example Usage](#example-usage)
5. [Notes](#notes)

## Introduction
The purpose of this project is to generate prompts and QA pairs for visual question answering (VQA) tasks. The generated data can be used to train and test VQA models. The code reads various category text files and JSON files, generates prompts and QA pairs for specific tasks and question types, and saves the results as JSON files.

## Code Structure
The project mainly consists of the following parts:
- `Attribute` Class: Represents attributes of a subject, including type, number, color, age, gender, expression, race, etc.
- `PictureInfo` Class: Represents information of a picture, including the subject, attributes, background, and style.
- `Prompt` Class: Generates prompts and their corresponding negative samples.
- `QA` Class: Generates questions and their answers, supporting multiple question types.
- `P_Q_A` Class: Represents a prompt and all its QA pairs.
- `QuestionMajority` Class: Defines the main attributes when generating questions.
- Helper functions: `txt2list` and `remove_duplicate_prompts`.
- Main function: The `main` function generates prompts and their corresponding QA pairs and saves the results as JSON files.

## Parameters
### `main` Function
The `main` function is the entry point of the code, responsible for  The parameters are as follows:

```python
def main(tasks, styles, ques_majority, question_types, prompt_num=1000, save_dir="./"):
```
- `tasks`: List of tasks, possible values are "recognition" and "OCR".
- `styles`: List of styles, if empty, all styles will be used.
- `ques_majority`: `QuestionMajority` object, defines the main attributes when generating questions.
- `question_types`: List of question types, possible values are "multi choice", "true or false", "image caption" (i.e., free-form).
- `prompt_num`: Number of prompts to generate, default is 1000.
- `save_dir`: Directory to save the results, default is the current directory.

### `QuestionMajority` Class
The `QuestionMajority` class is used to  The parameters are as follows:

```python
class QuestionMajority:
    def __init__(self, foreground=None, attributes=None, background=None, style=None):
```
- `foreground`: Type of subject, possible values are "face", "animal", "plant", "clothes", "object", "food", "landmark", "action", "celebrity", "profession", "movie", "tv show", "anime", "text".
- `attributes`: List of attributes, possible values are "age", "gender", "race", "expression", "color".
- `background`: Type of background, possible values are "background" or None.
- `style`: Type of style, possible values are "style" or None.

## Example Usage
The following is an example usage that generates 9000 prompts and their corresponding QA pairs, and saves the results to the current directory:

```python
if __name__ == "__main__":
    main(
        tasks=["recognition"],
        styles=[],  # all styles are available if not specified
        ques_majority=QuestionMajority(foreground="face", attributes=["age","gender","expression","race"], background="background", style="style"),
        question_types=["multi choice", "true or false"],
        prompt_num=1000,
        save_dir="./"
    )
```

## Notes

Various foreground types and their compatible attributes, as well as whether they can specify background or style:

1. **face**:
    - attributes: age, gender, race, expression
    - background: background
    - style: style
2. **animal**:
    - attributes: color
    - background: background
    - style: style
3. **plant**:
    - attributes: None
    - background: background
    - style: style
4. **clothes**:
    - attributes: color
    - background: None
    - style: style
5. **object**:
    - attributes: color
    - background: background
    - style: style
6. **food**:
    - attributes: None
    - background: background
    - style: style
7. **landmark**:
    - attributes: None
    - background: None
    - style: style
8. **action**:
    - attributes: None
    - background: background
    - style: style
9. **celebrity**:
    - attributes: None
    - background: background
    - style: style
10. **profession**:
    - attributes: None
    - background: None
    - style: style
11. **movie**:
    - attributes: None
    - background: None
    - style: style
12. **tv show**:
    - attributes: None
    - background: None
    - style: style
13. **anime**:
    - attributes: None
    - background: None
    - style: style
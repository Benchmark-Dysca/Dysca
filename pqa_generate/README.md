#  Usage
> Generating Prompts and QA Pairs for Visual Question Answering Tasks

- generating pqa files in 20 subtask:

```
# generate all subtasks
python pqa_generate.py --tasks 'overall' --prompt_num 2500 --save_dir "./source/"
Or
# generate specifc subtask (optional)
python pqa_generate.py --tasks 'face' --prompt_num 2500 --save_dir "./source/"
```

- post-process the file

```
python pqa_postprocess.py --file_folder ./source --output_file ./Dysca.json
```

The output file will be a json file, which will be used for benchmarking, like:

```
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
      "id": 2500,
      ...
  }
]
```
- copy the output json file to ../image_generate 
```
cp ./Dysca.json ../image_generate/
```
Then, please follow the instructions in the README of ../image_generate to generate the images.
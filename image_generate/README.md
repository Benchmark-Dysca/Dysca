## Generate data by you own

#### Clean scenario

> Generate images from json file:

```
# generate text images
python generate_data_ocr.py --input_file ./Dysca.json --output_file ./Dysca --seed 2024 --sd_model stabilityai/stable-diffusion-1.5 --textdiffuser_model --textdiffuser_full_ft

# generate other images
python generate_data.py --input_file Dysca.json --output_file ./Dysca --seed 2024 --sdxl_model stabilityai/stable-diffusion-xl-base-1.0 --device "cuda:0" 
```

#### Corruption Scenario

```
python corruption.py --input_file ./Dysca.json --input_image_dir ./Dysca --output_image_dir ./Dysca_corruption --seed 2024
```

#### Print-attacking Scenario

```
python print_attack.py --input_file ./Dysca.json --input_image_dir ./Dysca --output_image_dir ./Dysca_print_attack --seed 2024
```

Then, please follow the instructions in the README of ../evaluate_LVLMs to calculate score.

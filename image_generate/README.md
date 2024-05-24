## Generate data by you own

#### Clean scenario

1. Generate json file from the metadata

```
# generate MQAI file for each subtask

# generate json file for generate
python rewrite.py --
```



1. Generate images from json file:

```
# generate text images
python generate_data_ocr.py --input_file ./Dysca.json --output_file ./Dysca --seed 2024 --sd_model stable-diffusion-1.5 --textdiffuser_model --textdiffuser_full_ft --device "cuda:0" 

# generate other images
python generate_data.py --input_file Dysca.json --output_file ./Dysca --seed 2024 --sdxl_model stable-diffusion-xl-base-1.0 --device "cuda:0" 
```

3. Clean the dataset

```
# clean text images

# clean other images
python clean_data.py --input_file ./Dysca.json --output_file ./Dysca_clean.json --image_folder ./Dysca --seed 2024 --clip_model  --device "cuda:0"
```

#### Corruption Scenario

We incorporate 29 distinct types of image corruption, sourced from the image corruptions library and img aug. These corruptions are methodically categorized into several groups:

- **Noise-Related:** Gaussian Noise, Shot Noise, Impulse Noise, Speckle Noise
- **Blur-Related:** Defocus Blur, Glass Blur, Motion Blur, Zoom Blur, Gaussian Blur
- **Weather Conditions:** Snow, Frost, Fog
- **Digital:** Brightness, Contrast, Pixelate, JPEG Compression, Spatter, Saturate, Gamma Contrast
- **Arithmetic:** Cutout, Salt and Pepper, Coarse Dropout
- **Geometric:** Scale, Rotate, Shear, Piecewise Affine, Jigsaw
- **Edge:** Canny
## Evaluate LVLMs

```
# evaluate LVLMs
python Dysca_compute.py --file_ground_truth ./Dysca.json --file_model_output model_output_file (json file) --evaluation_score score_result_file (excel file) --model_name your_model_name

for exmaple:
python Dysca_compute.py --file_ground_truth ./Dysca_example.json --file_model_output ./output_example.json --evaluation_score ./score_example.xlsx --model_name Dysca
```

The result is saved in the excel where each the multi-grained evaulation scores are shown in each column.
# Qwen-VL benchmark data layouts

The evaluation scripts assume a predictable local `data/` tree. Keep the layout close to the source docs so the bundled scripts can be run without editing code.

## Captioning

- `data/flickr/`
  - `flickr30k_karpathy_test.json`
  - `flickr30k_karpathy_train.json`
  - Flickr30K images
- `data/nocaps/`
  - `nocaps_val.json`
  - nocaps validation images

## VQA / document QA / grounding

- `data/vqav2/`
  - `v2_OpenEnded_mscoco_val2014_questions.json`
  - `v2_mscoco_val2014_annotations.json`
  - `vqav2_train.jsonl`
  - `vqav2_val.jsonl`
  - `vqav2_testdev.jsonl`
- `data/okvqa/`
  - `OpenEnded_mscoco_val2014_questions.json`
  - `mscoco_val2014_annotations.json`
  - `okvqa_train.jsonl`
  - `okvqa_val.jsonl`
- `data/textvqa/`
  - `textvqa_val_questions.json`
  - `textvqa_val_annotations.json`
  - `textvqa_train.jsonl`
  - `textvqa_val.jsonl`
- `data/vizwiz/`
  - `vizwiz_val_questions.json`
  - `vizwiz_val_annotations.json`
  - `vizwiz_train.jsonl`
  - `vizwiz_val.jsonl`
  - `vizwiz_test.jsonl`
- `data/docvqa/`
  - `train.jsonl`
  - `val.jsonl`
  - `test.jsonl`
  - `val/val_v1.0.json` for score computation
- `data/chartqa/`
  - `train_human.jsonl`
  - `train_augmented.jsonl`
  - `test_human.jsonl`
  - `test_augmented.jsonl`
- `data/gqa/`
  - `train.jsonl`
  - `testdev_balanced.jsonl`
- `data/ocrvqa/`
  - `ocrvqa_train.jsonl`
  - `ocrvqa_val.jsonl`
  - `ocrvqa_test.jsonl`
- `data/ai2diagram/`
  - `train.jsonl`
  - `test.jsonl`
- `data/refcoco/`, `data/refcoco+/`, `data/refcocog/`
  - split-specific `.jsonl` files with image path, sentence, bbox, width, and height

## ScienceQA and MMBench

- `data/scienceqa/scienceqa_test_img.jsonl`
- `data/mmbench/mmbench_dev_20230712/mmbench_dev_20230712.tsv`
- `data/mmbench/mmbench_test_20230712/mmbench_test_20230712.tsv`
- converter outputs are written beside those TSVs as JSONL and extracted image folders

## SEED-Bench

- `SEED-Bench.json` or another explicit input JSON provided by the user
- image assets under a configurable CC3M-style root
- optional video roots for SEED-Bench video dimensions
- `image_input.jsonl` and `video_input_<n>.jsonl` are the standard converter outputs

## General rules

1. The evaluation scripts read files relative to the current working directory unless the user passes a different path.
2. The bundled converters and scorers are designed to keep the output layout predictable, but they still expect the external benchmark files to be downloaded by the user.
3. If a dataset is missing, prepare the command and report the missing prerequisite rather than guessing a path.

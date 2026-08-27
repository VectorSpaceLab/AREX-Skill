# CLI Reference

`evaluate.py` parses its top-level evaluation flags first, then forwards the leftover arguments to the selected model module as `EvalModel` construction arguments. For OpenFlamingo, the leftover model args are the checkpoint and encoder settings listed below.

## Common evaluation flags

| Flag | Meaning |
| --- | --- |
| `--model` | Model module name. This sub-skill targets `open_flamingo`. |
| `--results_file` | JSON file for the per-dataset summary results written by rank 0. |
| `--shots` | One or more shot counts to evaluate, for example `0 4 8 16 32`. |
| `--num_trials` | Number of demo-sampling trials per shot count. |
| `--trial_seeds` | Seed list matched positionally to `--num_trials`. |
| `--num_samples` | Cap on test samples; `-1` means the full test split. |
| `--query_set_size` | Random query-set size used when RICES is off. |
| `--batch_size` | Evaluation batch size. |
| `--no_caching_for_classification` | Disable key-value caching for classification scoring. |
| `--classification_prompt_ensembling` | Average classification logprobs over prompt permutations. |
| `--rices` | Use RICES exemplars instead of random exemplars. |
| `--cached_demonstration_features` | Directory containing dataset-specific RICES feature pickles. |

## OpenFlamingo model args

These are passed after the known evaluation flags and consumed by `open_flamingo.eval.models.open_flamingo.EvalModel`.

| Flag | Meaning |
| --- | --- |
| `--vision_encoder_path` | Vision encoder name or checkpoint path, for example `ViT-L-14`. |
| `--vision_encoder_pretrained` | Vision encoder weights tag, for example `openai`. |
| `--lm_path` | Language model name or checkpoint path. |
| `--lm_tokenizer_path` | Tokenizer path for the language model. |
| `--cross_attn_every_n_layers` | Cross-attention interval for the Flamingo backbone. |
| `--checkpoint_path` | OpenFlamingo checkpoint `.pt` file. |
| `--precision` | Precision mode passed into the model wrapper. Common values are `amp_bf16` / `amp_bfloat16`, `amp`, `bf16`, and `fp16`. |

## Dataset selectors and path flags

Select one or more datasets with the matching boolean flags.

### Captioning

- `--eval_coco`
  - `--coco_train_image_dir_path`
  - `--coco_val_image_dir_path`
  - `--coco_karpathy_json_path`
  - `--coco_annotations_json_path`
- `--eval_flickr30`
  - `--flickr_image_dir_path`
  - `--flickr_karpathy_json_path`
  - `--flickr_annotations_json_path`

### VQA

- `--eval_vqav2`
  - `--vqav2_train_image_dir_path`
  - `--vqav2_train_questions_json_path`
  - `--vqav2_train_annotations_json_path`
  - `--vqav2_test_image_dir_path`
  - `--vqav2_test_questions_json_path`
  - `--vqav2_test_annotations_json_path` when you have local annotations
  - `--vqav2_final_test_questions_json_path` when you need an EvalAI-style submission fill file
- `--eval_ok_vqa`
  - `--ok_vqa_train_image_dir_path`
  - `--ok_vqa_train_questions_json_path`
  - `--ok_vqa_train_annotations_json_path`
  - `--ok_vqa_test_image_dir_path`
  - `--ok_vqa_test_questions_json_path`
  - `--ok_vqa_test_annotations_json_path`
- `--eval_textvqa`
  - `--textvqa_image_dir_path`
  - `--textvqa_train_questions_json_path`
  - `--textvqa_train_annotations_json_path`
  - `--textvqa_test_questions_json_path`
  - `--textvqa_test_annotations_json_path`
- `--eval_vizwiz`
  - `--vizwiz_train_image_dir_path`
  - `--vizwiz_train_questions_json_path`
  - `--vizwiz_train_annotations_json_path`
  - `--vizwiz_test_image_dir_path`
  - `--vizwiz_test_questions_json_path`
  - `--vizwiz_test_annotations_json_path` when you have local annotations

### Classification

- `--eval_imagenet`
  - `--imagenet_root`
- `--eval_hateful_memes`
  - `--hateful_memes_image_dir_path`
  - `--hateful_memes_train_annotations_json_path`
  - `--hateful_memes_test_annotations_json_path`

## RICES flags

- `--rices_vision_encoder_path`
- `--rices_vision_encoder_pretrained`
- `--cached_demonstration_features`

The cache script `cache_rices_features.py` also requires:

- `--output_dir`
- the same dataset selector flags as evaluation
- the dataset training-side path flags for the chosen datasets

## Distributed flags

- `--dist-url`
- `--dist-backend`
- `--horovod`
- `--no-set-device-rank`

Runtime environment variables that matter for distributed launch:

- `MASTER_ADDR`
- `MASTER_PORT`
- `WORLD_SIZE`
- `RANK`
- `LOCAL_RANK`

The launcher uses those values to pick a device, initialize process groups, and decide whether to run single-process, DDP, or Horovod.

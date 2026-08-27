# Public dataset suite

Otter also bundles an OpenFlamingo-style public dataset evaluation suite separate from `pipeline.benchmarks.evaluate`. Use it when the target task is COCO/Flickr captioning, VQA-style public datasets, or classification/logprob evaluation rather than MagnifierBench/MMBench/MME/MM-VET/MathVista/POPE/ScienceQA/SeedBench.

## Entry point and supported tasks

Current module path:

```bash
python -m pipeline.benchmarks.public_datasets_suite.evaluate --help
```

Supported dataset flags and metrics:

| Flag | Dataset | Task | Metric / method |
|---|---|---|---|
| `--eval_coco` | COCO | Captioning | CIDEr generation metric. |
| `--eval_flickr30` | Flickr-30K | Captioning | CIDEr generation metric. |
| `--eval_vqav2` | VQAv2 | VQA | VQA accuracy by generation. |
| `--eval_ok_vqa` | OK-VQA | VQA | VQA accuracy by generation. |
| `--eval_textvqa` | TextVQA | VQA | VQA accuracy by generation. |
| `--eval_vizwiz` | VizWiz | VQA | VQA accuracy by generation. |
| `--eval_hateful_memes` | Hateful Memes | Classification | ROC AUC using logprobs. |
| `--eval_imagenet` | ImageNet | Classification | Top-1 accuracy using logprobs. |

Model modules under this suite include `otter`, `idefics`, `open_flamingo`, and `blip`. The suite dynamically imports `pipeline.benchmarks.public_datasets_suite.models.<model>`.

## Core options

Common evaluator options:

| Option | Purpose |
|---|---|
| `--model` | Suite model module key, for example `otter`, `idefics`, or `open_flamingo`. |
| `--results_file` | JSON file where rank 0 writes accumulated metrics. |
| `--shots` | One or more in-context shot counts; defaults to `0 4 8`. Non-OpenFlamingo/Otter/Idefics models are restricted to zero-shot in code. |
| `--num_trials`, `--trial_seeds` | Repeated sampling controls for demonstrations/eval subsets. |
| `--num_samples` | Number of evaluation examples; `-1` means all examples. |
| `--query_set_size` | Demonstration pool size for few-shot evaluation. |
| `--batch_size` | Evaluation batch size. |
| `--no_caching_for_classification` | Disables KV caching for classification. The source notes classification caching can underperform for MPT models. |
| `--world_size`, `--dist-url`, `--dist-backend`, `--no-set-device-rank` | Distributed evaluation setup. Environment variables such as `MASTER_ADDR` and `MASTER_PORT` are usually needed for multi-process runs. |

Model-specific options are parsed from leftover `--key=value` arguments and passed into the selected model wrapper. Typical examples:

```bash
python -m pipeline.benchmarks.public_datasets_suite.evaluate \
  --model=otter \
  --eval_coco \
  --num_samples=128 \
  --batch_size=4 \
  --results_file=./logs/public-suite-otter.json \
  --coco_train_image_dir_path=/path/to/coco/train2014 \
  --coco_val_image_dir_path=/path/to/coco/val2014 \
  --coco_karpathy_json_path=/path/to/coco/dataset_coco.json \
  --coco_annotations_json_path=/path/to/coco/captions_val2014.json \
  --model_path=/path/to/otter-hf-model \
  --checkpoint_path=/path/to/optional/final_weights.pt \
  --precision=bf16
```

For Idefics:

```bash
python -m pipeline.benchmarks.public_datasets_suite.evaluate \
  --model=idefics \
  --eval_vqav2 \
  --num_samples=128 \
  --results_file=./logs/public-suite-idefics.json \
  --vqav2_train_image_dir_path=/path/to/vqav2/train2014 \
  --vqav2_train_annotations_json_path=/path/to/vqav2/train_annotations.json \
  --vqav2_train_questions_json_path=/path/to/vqav2/train_questions.json \
  --vqav2_test_image_dir_path=/path/to/vqav2/val2014 \
  --vqav2_test_annotations_json_path=/path/to/vqav2/val_annotations.json \
  --vqav2_test_questions_json_path=/path/to/vqav2/val_questions.json \
  --model_path=HuggingFaceM4/idefics-9b-instruct \
  --precision=bf16
```

## Required dataset path groups

Each selected `--eval_*` flag requires its matching local images and annotation/question files. Common groups:

- COCO: `--coco_train_image_dir_path`, `--coco_val_image_dir_path`, `--coco_karpathy_json_path`, `--coco_annotations_json_path`.
- Flickr-30K: `--flickr_image_dir_path`, `--flickr_karpathy_json_path`, `--flickr_annotations_json_path`.
- VQAv2: train/test image dirs, train/test questions JSON, and train/test annotations JSON.
- OK-VQA: train/test image dirs, train/test questions JSON, and train/test annotations JSON.
- TextVQA: image dir plus train/test questions and annotations in the suite's expected VQA-style format.
- VizWiz: train/test image dirs plus train/test questions and annotations in the suite's expected VQA-style format.
- Hateful Memes: image dir plus train/test annotation JSON files.
- ImageNet: `--imagenet_root`.

## Caveats and skip reasons

- The bundled shell scripts are examples with machine-specific paths; do not copy their paths. Rebuild commands with placeholders replaced by user-supplied locations.
- Some example scripts use an older module spelling (`pipeline.eval.evaluate`). Prefer the current module path shown above.
- VQAv2 test-dev/test-std annotations are not public; use validation split locally or submit to the official evaluation service when required.
- TextVQA and VizWiz expect converted VQA-style annotation/question JSON files, not necessarily the raw upstream format.
- The suite initializes distributed evaluation helpers. For multi-GPU runs, set `MASTER_ADDR`, `MASTER_PORT`, and related rank/world variables or launch with the user's distributed runner.
- Public-suite evaluation is skipped or blocked when datasets are not already present locally, when model checkpoints are absent, when a selected model wrapper dependency is missing, or when the user has not approved large downloads/GPU time.

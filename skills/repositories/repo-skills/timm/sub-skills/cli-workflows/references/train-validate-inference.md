# Train, Validation, and Inference Commands

The timm repository root includes reference scripts for training, validation, and inference. They are not guaranteed to be installed with a pip release, so commands assume the user runs them from a checkout or points `--script-path` at copied scripts.

## Command Shape

| Mode | Script | Primary purpose | Minimal shape |
| --- | --- | --- | --- |
| `train` | `train.py` | Train or fine-tune an image classifier and periodically validate/checkpoint. | `python train.py --data-dir DATA_ROOT --model MODEL --batch-size N` |
| `validate` | `validate.py` | Evaluate pretrained weights or a checkpoint on a labeled validation split. | `python validate.py --data-dir VAL_DIR --model MODEL --pretrained` |
| `inference` | `inference.py` | Write top-k predictions for an image folder/dataset to CSV/JSON/parquet. | `python inference.py --data-dir IMAGE_DIR --model MODEL --checkpoint CKPT` |

Prefer explicit `--data-dir` over the deprecated positional dataset path. Use `--dataset TYPE/NAME` only when the target is not plain ImageFolder/ImageTar or when a torch/tfds/webdataset/huggingface dataset backend is intentionally selected.

## Dataset Layouts

| Workflow | `--data-dir` should point to | Relevant split flags |
| --- | --- | --- |
| Training ImageFolder | Base folder containing `train/` and `validation/` by default. | `--train-split train`, `--val-split validation`; set `--val-split ''` only when training without validation. |
| Validation ImageFolder | Folder containing validation images/classes, commonly `.../validation/`. | `--split validation` is default, but ImageFolder validation commonly receives the split folder itself. |
| Inference ImageFolder | Folder containing images to score, often the validation or unlabeled image folder. | `--split validation` remains default for dataset backends that honor splits. |
| Iterable/remote datasets | Dataset root or cache location expected by the selected backend. | `--train-num-samples`, `--val-num-samples`, or `--num-samples` may be required. |

For ImageFolder classification, class-map files must match folder names/classes. For inference labels, ImageNet label names/descriptions are inferred only when the model class space identifies an ImageNet subset.

## Training Essentials

Common training flags:

| Concern | Flags |
| --- | --- |
| Model/weights | `--model`, `--pretrained`, `--pretrained-path`, `--initial-checkpoint`, `--resume`, `--num-classes` |
| Batch/learning rate | `--batch-size`, `--validation-batch-size`, `--grad-accum-steps`, `--lr`, `--lr-base`, `--lr-base-size`, `--lr-base-scale` |
| Schedule | `--sched`, `--epochs`, `--warmup-epochs`, `--decay-epochs`, `--decay-rate`, `--min-lr` |
| Augmentation | `--no-aug`, `--scale`, `--ratio`, `--aa`, `--reprob`, `--remode`, `--mixup`, `--cutmix`, `--smoothing` |
| Device/perf | `--device`, `--amp`, `--amp-dtype`, `--model-dtype`, `--channels-last`, `--workers`, `--pin-mem`, `--no-prefetcher` |
| Checkpoints/output | `--output`, `--experiment`, `--checkpoint-hist`, `--recovery-interval`, `--eval-metric`, `--log-wandb` |
| Config files | `--config CONFIG.yaml` loads YAML defaults before parsing remaining CLI args. |

Training calculates learning rate from effective global batch size when `--lr` is omitted: `batch_size * world_size * grad_accum_steps` is scaled from `--lr-base-size`, with linear scaling for most optimizers and sqrt scaling for adaptive/LAMB-like optimizers unless overridden.

### Tiny CPU/Debug Training

Use a tiny image-folder fixture when smoke-testing command wiring:

```bash
python train.py --data-dir tiny-imagenet-layout --model resnet18 --batch-size 2 --device cpu --workers 0 --epochs 1 --val-interval 1 --no-aug --log-interval 1 --output ./output/debug
```

The dataset root still needs the training layout, for example `tiny-imagenet-layout/train/class_a/*.jpg` and `tiny-imagenet-layout/validation/class_a/*.jpg`.

### Full ImageNet-Style Training

```bash
python train.py --data-dir /data/imagenet --model resnet50 --batch-size 128 --sched cosine --epochs 200 --warmup-epochs 5 --amp --workers 8 --output ./output --experiment resnet50-cosine
```

For multi-GPU, wrap this with `torchrun` as described in `distributed-training.md`.

## Validation Essentials

Common validation flags:

| Concern | Flags |
| --- | --- |
| Model/weights | `--model`, `--pretrained`, `--checkpoint`, `--use-ema`, `--num-classes`, `--model-kwargs` |
| Dataset | `--data-dir`, `--dataset`, `--split`, `--class-map`, `--num-samples`, `--real-labels`, `--valid-labels` |
| Device/perf | `--device`, `--amp`, `--amp-dtype`, `--model-dtype`, `--batch-size`, `--workers`, `--num-gpu`, `--channels-last` |
| Output | `--results-file`, `--results-format csv|json` |
| Bulk/retry | `--model all`, wildcard model filters, model-list file, checkpoint directory, `--retry` |

Validation sets `--pretrained` implicitly when no checkpoint is provided. If `--checkpoint` is a directory, it validates matching `.pth.tar` and `.pth` files for the selected model. If `--model` is `all`, a wildcard, or a file of model names, validation can run in bulk.

`--retry` catches recognized out-of-memory style runtime errors, decays batch size, and retries single-model validation. It is useful for finding a safe batch size but does not fix bad paths, unsupported devices, or model/dataset mismatches.

Example:

```bash
python validate.py --data-dir /data/imagenet/validation --model resnet50 --pretrained --batch-size 256 --amp --workers 8 --results-file ./results/resnet50.csv
```

## Inference Essentials

Common inference flags:

| Concern | Flags |
| --- | --- |
| Model/weights | `--model`, `--pretrained`, `--checkpoint`, `--num-classes`, `--model-kwargs` |
| Dataset | `--data-dir`, `--dataset`, `--split`, `--class-map` |
| Device/perf | `--device`, `--amp`, `--amp-dtype`, `--model-dtype`, `--batch-size`, `--workers`, `--num-gpu`, `--channels-last` |
| Result files | `--results-dir`, `--results-file`, `--results-format csv json json-split parquet`, `--no-console-results` |
| Columns/top-k | `--topk`, `--include-index`, `--label-type none|name|description|detailed`, `--results-separate-col`, `--filename-col`, `--index-col`, `--label-col`, `--output-col`, `--output-type prob|logit` |

Inference sets `--pretrained` implicitly when no checkpoint is provided. Results default to a filename derived from model name and image size, and each requested format is written with the matching extension. If `--results-file` already includes a known extension, the script strips it before adding the selected format extension.

Example:

```bash
python inference.py --data-dir ./images --model mobilenetv3_large_100 --checkpoint ./output/train/model_best.pth.tar --batch-size 64 --device cuda --amp --results-dir ./predictions --results-file mobilev3 --results-format csv json --topk 5 --include-index
```

## NaFlex CLI Notes

NaFlex loading is available in `train.py` and `validate.py`, not `inference.py`.

| Workflow | Flags |
| --- | --- |
| Train with variable sequence lengths | `--model naflex...` or compatible model plus `--model-kwargs use_naflex=True`, `--naflex-loader`, `--naflex-train-seq-lens 128 256 576`, `--naflex-max-seq-len 576` |
| Variable patch sizes | `--model-kwargs enable_patch_interpolator=True`, `--naflex-patch-sizes 12 16 24`, optional `--naflex-patch-size-probs ...` |
| Loss scaling | `--naflex-loss-scale none|sqrt|linear` |
| Patch layout | `--naflex-patchify-channels-first` for models expecting channels-first flattened patch layout. |
| Validate NaFlex | `--naflex-loader`, `--naflex-max-seq-len N`, and model kwargs needed to create a NaFlex-compatible model. |

NaFlex requires a compatible model path. Standard ViT models may need `--model-kwargs use_naflex=True`; patch-size interpolation flags must align with model support. If the loader and model disagree on patch layout, sequence length, or patch-size capabilities, expect assertion errors or shape mismatches.

## Config File Pattern

Training supports YAML defaults via `--config`:

```yaml
model: resnet50
batch_size: 128
epochs: 100
sched: cosine
amp: true
workers: 8
```

Run it as:

```bash
python train.py --config recipe.yaml --data-dir /data/imagenet --output ./output --experiment resnet50-recipe
```

CLI arguments parsed after `--config` can override YAML defaults. Validation and inference do not use this two-stage config parser.

## Legacy Script Caveat

`legacy_train.py` resembles older training flow and remains useful as historical reference, but command guidance should target `train.py`. Prefer migrating old examples to `train.py` flags unless the user explicitly needs to reproduce an older behavior.

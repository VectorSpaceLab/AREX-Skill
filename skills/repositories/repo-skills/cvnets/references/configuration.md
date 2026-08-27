# CVNets Configuration Guide

## Purpose

Read this when a user needs to edit, validate, or inspect a CVNets YAML config or a command-line override. The loader and parser use dotted option names, task-specific registries, and a small set of shared top-level sections.

## How CVNets configs work

- Config files are YAML files under `config/<task>/` and the recipe folders in `examples/`.
- The loader flattens nested YAML into dotted option names such as `dataset.root_train`, `model.classification.name`, or `scheduler.max_epochs`.
- CLI flags still use hyphenated spellings such as `--common.config-file`, but the parsed `opts` object exposes dotted keys with underscores after Python attribute conversion.
- `--common.override-kwargs` accepts `key=value` pairs without leading dashes. Values are typed using the parser definition for the matched key.
- Unknown YAML entries produce warnings unless they are recognized meta keys or `local_` keys.

## Common sections you will see

| Section | Typical purpose | Examples of keys |
| --- | --- | --- |
| `common` | run metadata and training controls | `config-file`, `results-loc`, `run-label`, `resume`, `finetune`, `auto-resume`, `mixed-precision`, `channels-last`, `override-kwargs` |
| `dataset` | dataset name, roots, batch sizes, workers, and collate functions | `category`, `name`, `root_train`, `root_val`, `root_test`, `train_batch_size0`, `val_batch_size0`, `eval_batch_size0`, `workers`, `collate-fn-name-*` |
| `sampler` | train/eval sampling strategy and crop sizes | `name`, `bs.*`, `vbs.*`, video sampler settings |
| `image_augmentation` / `audio_augmentation` / `video_augmentation` | input preprocessing and byte/audio/video transforms | resize, crop, flip, byte encoding, noise, video clip settings |
| `model` | task-specific architecture family and pretrained weights | `classification.name`, `detection.name`, `segmentation.name`, `multi_modal_img_text.name`, `audio_classification.name`, `pretrained`, `n-classes` |
| `optim` / `scheduler` | optimization and learning-rate policy | optimizer name, weight decay, momentum, warmup, max epochs, max iterations |
| `ema` | exponential moving average model state | `enable`, `momentum` |
| `stats` | metrics and checkpoint policy | `val`, `train`, `checkpoint-metric`, `checkpoint-metric-max` |
| `text_tokenizer` | CLIP and other text-tokenizer settings | `name`, CLIP merges/encoder files |
| `conversion` | CoreML export settings | `coreml-extn`, `input-image-path` |
| `benchmark` | throughput settings | `batch-size`, `warmup-iter`, `n-iter`, `use-jit-model` |
| `loss-landscape` | loss-landscape grid settings | `n-points`, `min-x`, `max-x`, `min-y`, `max-y` |

## Practical rules

- Effective training batch size depends on `train_batch_size0`, the number of GPUs, and gradient accumulation frequency.
- Dataset roots are not optional for real training or evaluation runs. If the config points at a placeholder path, fix the path before touching the model.
- Use `dataset.category` to decide which `model.<category>.name` field matters.
- For CLIP and other multimodal flows, check the tokenizer and text-dataset keys as well as the model keys.
- For video workflows, confirm the video-reader name and frame-stack format before assuming the sampled tensor shape.

## Safe inspection workflow

1. Run `scripts/inspect_config.py` with a repo root and the config path.
2. Verify the resolved dataset roots, model name, batch sizes, and task-specific settings.
3. Apply only the smallest override needed for the run.
4. If the config warning mentions an unknown key, compare the key spelling against the parser or against this guide before retrying.

## Common mistakes

- Using underscores in YAML keys where the parser expects dotted names derived from hyphenated CLI flags.
- Leaving `dataset.root_train`, `dataset.root_val`, or `dataset.root_test` pointed at a placeholder path.
- Setting the wrong `model.<category>.name` for the task category in the dataset section.
- Assuming `--common.override-kwargs` can create completely new options; it only overrides options the parser already knows about.

## Read next

- `references/api-reference.md` for the parser and loader contracts.
- `sub-skills/data-and-config/references/data-formats.md` for dataset- and modality-specific layouts.
- `sub-skills/data-and-config/references/troubleshooting.md` when config loading or override validation fails.

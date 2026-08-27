---
name: training-and-evaluation
description: "Routes EasyCV config-driven training, evaluation, validation, and
  distributed launch workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training and evaluation

Use this sub-skill when the task is to train, fine-tune, validate, resume, or compare an EasyCV checkpoint against a config-driven pipeline.

It covers the repo's common training front doors:

- `python -m easycv.tools.train`
- `python -m easycv.tools.eval`
- `easycv.tools.train(...)`
- `easycv.tools.eval(...)`
- `easycv.apis.train_model`
- `easycv.apis.single_gpu_test`
- `easycv.apis.multi_gpu_test`

## Read these references first

- `references/workflows.md` for the training / evaluation command patterns.
- `references/config-templates.md` for choosing a config family or `--model_type` starter.
- `references/troubleshooting.md` for common launcher, seed, fp16, and validation failures.
- Root `references/model-zoo-overview.md` for the full family map.

## What belongs here

Include tasks such as:

- picking a classification, detection, segmentation, pose, SSL, metric-learning, video, or OCR config
- editing dataset roots, `work_dir`, `load_from`, `resume_from`, or `pretrained`
- running validation hooks and metric evaluation
- distributed launch setup and `--launcher` selection
- fp16 / SyncBN / seed / logging / visualization setup during training
- training-time result comparison across configs or checkpoints

## What stays elsewhere

- Batch prediction and predictor API usage -> `sub-skills/prediction-and-inference/`
- Export, pruning, quantization, and other inference packaging -> `sub-skills/export-and-optimization/`
- Dataset conversion, file layout checks, and OSS I/O setup -> `sub-skills/data-preparation/`

## Typical decision flow

1. Choose a config family or explicit config path.
2. Confirm the dataset layout and required labels or class list.
3. Set `work_dir`, checkpoint resume / load settings, and the launcher.
4. Decide whether fp16, validation, and logging hooks are needed.
5. Run the smallest safe train or eval command first, then expand.

## Common training surfaces

- `--model_type` only works for the starter keys listed in the model-zoo reference.
- `--user_config_params` overrides config values without editing the source file.
- `eval_pipelines` controls validation during training and post-training evaluation.
- DALI-backed datasets, OSS I/O, and TorchAccelerator configs have extra runtime expectations.

## Common success signals

- The config loads without path or template errors.
- The trainer constructs the model, dataloaders, and hooks.
- Validation metrics are emitted for the chosen dataset family.
- The checkpoint metadata includes the EasyCV version and config text.


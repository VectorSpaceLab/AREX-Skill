---
name: training-recipes
description: "Train and evaluate Asteroid recipes with System, datasets, losses,
  metrics, and schedulers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Training recipes and evaluation

Use this sub-skill when the user wants to run, adapt, or debug an Asteroid recipe rather than apply a pretrained checkpoint.

## Typical triggers

- `run.sh`, `train.py`, `eval.py`, `local/`, stage numbers, or `storage_dir`
- `System`, `Trainer`, `make_optimizer`, `NoamScheduler`, `DPTNetScheduler`, `ReduceLROnPlateau`
- `PITLossWrapper`, `SinkPITLossWrapper`, `pairwise_neg_sisdr`, `SingleSrcPMSQE`, `SingleSrcNegSTOI`
- `MetricTracker`, `get_metrics`, or `compute_metrics`
- dataset names such as `WhamDataset`, `LibriMix`, `Wsj0mixDataset`, `DNSDataset`, `MUSDB18Dataset`, `FUSSDataset`, `AVSpeechDataset`, `SmsWsjDataset`, `KinectWsjMixDataset`, or `LibriVADDataset`

## What to do first

1. Identify the recipe family and the dataset/task.
2. Decide whether the user needs:
   - a dry-run of the config and stage logic
   - a real data-backed recipe execution plan
   - a tiny synthetic training smoke
3. Check whether the recipe is CPU-friendly, GPU-friendly, or data-heavy.

## Standard workflow

- Read `references/recipes.md` for the stage-based `run.sh` pattern and the most common recipe knobs.
- Read `references/datasets-and-losses.md` for the dataset and loss/metric surface that recipes build on.
- Read `references/troubleshooting.md` when a recipe expects a missing dataset helper, a mismatched stage, or an unavailable optional dependency.
- Use `scripts/smoke_training.py --device cpu` from the root skill for a self-contained runtime training smoke.
- Use `scripts/smoke_system_training.py --device cpu` for the focused `System` + `Trainer` engine smoke inside this sub-skill; use `--device cuda` only when CUDA is intentionally being checked.

## Recipe pattern to remember

Most recipes follow this flow:

1. Parse YAML config into grouped arguments.
2. Prepare dataset-specific files or manifests.
3. Build train and validation dataloaders.
4. Instantiate a model, optimizer, scheduler, and loss.
5. Wrap them in `System`.
6. Train with PyTorch Lightning.
7. Evaluate on the test split.
8. Save a publishable checkpoint and metrics.

## Common decision points

- Use `--stage` to resume from a later recipe step.
- Use `--tag` when you want a stable experiment name.
- Use `--id` / `CUDA_VISIBLE_DEVICES` when you want to control GPU visibility.
- Use CPU when the task is only a smoke or when data access is unavailable.

## Troubleshooting reminders

- Missing dataset helper packages are common for SMS-WSJ, AVSpeech, and some music recipes.
- `librosa` is required for some dataset imports.
- Some recipes need `espnet_model_zoo`, `jiwer`, or other optional packages only for evaluation metrics such as WER.
- Music or audio-visual recipes can be memory heavy; keep them reference-only unless the user explicitly wants full execution planning.

## Inputs to inspect

- dataset family and task name
- sample rate, segment length, and number of sources
- whether the recipe depends on a special helper package
- whether the user wants a smoke, a plan, or a full execution path

## Smoke sequence

1. Build a tiny synthetic dataset or use a tiny fixture.
2. Instantiate a small model and a compatible loss.
3. Wrap them in `System`.
4. Run a `fast_dev_run` Lightning fit.
5. Confirm the metric or scheduler path that the user cares about.

## What to avoid

- Do not turn the skill into a dataset-download manual.
- Do not assume every recipe can be run without the recipe-specific helper packages.
- Do not claim a GPU requirement unless the selected recipe path truly needs it.
- Do not tell the user to run the original long experiment as a default check.

## Recipe signals to remember

- `stage` and `tag` almost always mean a `run.sh` recipe.
- `compute_wer` often means an optional ASR metric branch.
- `eval_use_gpu` is a recipe-level toggle, not a package-wide requirement.
- `storage_dir` usually signals that the task may involve a large dataset download.

## Good questions to ask when unclear

- Which dataset family is being used?
- Is the request about training, evaluation, or both?
- Do you need a dry run or the full recipe shape?
- Is the user expecting CPU planning or GPU planning?

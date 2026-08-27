---
name: "training-evaluation"
description: "Routes BasicTS training and evaluation workflows for forecasting,
  classification, imputation, and foundation-model launches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-evaluation

Use this sub-skill when the task is to launch, resume, or evaluate a BasicTS run rather than to redesign the model, dataset layout, or callback logic.

## Typical triggers

- "Train a BasicTS forecasting model"
- "Run the classification demo"
- "Evaluate a saved checkpoint"
- "Launch an imputation job"
- "Show me the BasicTS quick start"

## What this sub-skill covers

- `BasicTSLauncher.launch_training`
- `BasicTSLauncher.launch_evaluation`
- `BasicTSForecastingConfig`
- `BasicTSClassificationConfig`
- `BasicTSImputationConfig`
- `BasicTSFoundationModelConfig`
- checkpoint save/load flow
- CPU-safe smoke runs and quick-start usage
- common task selection for forecasting, classification, imputation, and foundation-model runs

## Read these bundled references first

- `references/workflows.md` for verified launch patterns and config selection.
- `references/troubleshooting.md` for dataset, checkpoint, and launch failures.
- `scripts/run_mini_forecasting_smoke.py` for a safe CPU smoke run that creates its own tiny fixture.

## Route here when the user asks for

- a new training run or a resumed run
- a saved-model evaluation
- a quick start example that uses `BasicTSLauncher`
- a task-specific config choice for forecasting, classification, imputation, or foundation-model work
- checkpoint path selection or evaluation after training

## Route elsewhere when the user asks for

- dataset file layout, raw conversion, or fixture validation → `data-preparation`
- custom model forward contracts or model family selection → `model-development`
- callbacks, metrics, scalers, taskflows, or config behavior beyond basic launch usage → `pipeline-extension`

## Working guidance

1. Choose the right task config class before writing a runnable command.
2. Match `dataset_name` and `dataset_params` to the dataset files that exist or that your helper creates.
3. Keep `gpus=None` for CPU smoke unless the user explicitly wants a GPU run.
4. Use `num_epochs` or `num_steps`, but not both.
5. Use `launch_evaluation` only after you know the checkpoint path you want to load.

## When to read the helper script

Run `scripts/run_mini_forecasting_smoke.py` when you want a safe CPU proof that the launcher, config packing, and checkpoint flow still work. It creates a tiny temporary dataset and does not depend on the original repository checkout.

## Why this sub-skill exists

BasicTS is often used through a launcher plus config object. This sub-skill keeps that entry path separate from the lower-level dataset, model, and pipeline customization routes so future agents can answer common run requests quickly.

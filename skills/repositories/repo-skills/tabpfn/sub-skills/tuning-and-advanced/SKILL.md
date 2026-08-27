---
name: tuning-and-advanced
description: "Guides TabPFN tuning, differentiable-input workflows, prompt
  tuning, and fine-tuning wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TabPFN tuning and advanced workflows

Use this sub-skill when the user is calibrating predictions, tuning thresholds,
backpropagating through inputs, prompt-tuning, or fine-tuning the underlying
TabPFN model.

## Start here

- Read `references/tuning-workflows.md` for ordinary tuning config and metric selection.
- Read `references/finetuning.md` for `FinetunedTabPFNClassifier` and `FinetunedTabPFNRegressor`.
- Read `references/differentiable-workflows.md` for `differentiable_input=True` and prompt-tuning workflows.
- Read `references/troubleshooting.md` for early stopping, validation, and categorical-input failures.
- Run `scripts/tuning_config_template.py --help` to print a safe config template.

## Use this sub-skill when

- The task mentions `eval_metric`, `tuning_config`, `calibrate_temperature`, or decision thresholds.
- The user wants prompt tuning, feature gradients, or other differentiable-input behavior.
- The task mentions `FinetunedTabPFNClassifier` or `FinetunedTabPFNRegressor`.
- The user wants to know how early stopping, validation frequency, or checkpoints behave during fine-tuning.

## Route elsewhere

- Basic estimator usage and outputs: `../tabular-prediction/SKILL.md`.
- Data cleaning, feature detection, or config fields: `../preprocessing-config/SKILL.md`.
- Batched CV, fused multi-dataset scoring, or cache performance: `../batched-performance/SKILL.md`.
- Model downloads, auth, cache, persistence, or checkpoint conversion: `../model-management/SKILL.md`.

## What this route owns

- Prediction calibration and decision-threshold tuning.
- Fine-tuning wrappers with early stopping and validation.
- Differentiable-input gradients and prompt-tuning loops.
- Advanced training / inference knobs that go beyond the base sklearn estimators.

## What to remember

- Tuning is not the same as fine-tuning.
- Differentiable-input workflows require extra care with categorical columns.
- Fine-tuning wraps a TabPFN estimator but uses a different training loop.
- Validation and checkpointing matter because fine-tuning can be expensive.

---
name: "pipeline-extension"
description: "Routes BasicTS callback, metric, scaler, taskflow, and
  config-extension workflows that customize the training pipeline."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# pipeline-extension

Use this sub-skill when the task is about changing how BasicTS trains, validates, masks, scales, measures, or dispatches data through the runner pipeline.

## Typical triggers

- "Add a callback to BasicTS"
- "How do I use auxiliary losses?"
- "Write a custom metric or scaler"
- "Customize the forecasting taskflow"
- "What do the config shortcuts do?"

## What this sub-skill covers

- `BasicTSRunner`
- `BasicTSTaskFlow` and the task-specific taskflows
- `BasicTSCallback` and the built-in callback catalog
- metrics, meters, and loss-handling behavior
- `ZScoreScaler` and `MinMaxScaler`
- config shortcuts, checkpoint settings, and serialization behavior

## Read these bundled references first

- `references/configuration.md` for config packing, shortcut fields, and checkpoint defaults.
- `references/taskflow-and-callbacks.md` for hook order, taskflow behavior, and metric wiring.
- `references/troubleshooting.md` for callback, metric, scaler, and config failures.
- `scripts/inspect_pipeline_contract.py` for a safe inspection helper.

## Route here when the user asks for

- custom callbacks or callback ordering
- auxiliary-loss wiring
- metric functions or metric selection
- scaler behavior or inverse transforms
- taskflow preprocessing/postprocessing/masking
- config shortcut behavior or checkpoint save strategy

## Route elsewhere when the user asks for

- dataset file formats or raw conversion → `data-preparation`
- built-in model selection or custom model `forward` rules → `model-development`
- launcher commands, training entry points, or checkpoint evaluation → `training-evaluation`

## Working guidance

1. Identify whether the user wants a hook, a metric, a scaler, or a taskflow change.
2. Keep the runner contract in mind: the taskflow preprocesses data before the forward pass and postprocesses it before metrics.
3. Match metric signatures to the keys that the runner returns.
4. Attach `AddAuxiliaryLoss` when the model emits named auxiliary losses.
5. Check `ckpt_save_strategy`, `val_interval`, and `test_interval` together when debugging save behavior.

## When to read the helper script

Run `scripts/inspect_pipeline_contract.py` when you want a quick read-only summary of the installed BasicTS runner/taskflow/callback/metric/scaler contract or a tiny synthetic validation of the masking and metric helpers.

## Why this sub-skill exists

BasicTS is highly configurable, and a small hook or metric change often affects multiple parts of the pipeline. This sub-skill keeps those extension points together so future agents can reason about the runtime behavior without opening the source repository again.

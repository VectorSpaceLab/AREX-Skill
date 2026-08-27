---
name: long-forecasting
description: "Train, test, predict, sweep, and visualize the core forecasting
  models: Linear, DLinear, NLinear, Informer, Transformer, and Autoformer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Long Forecasting

Use this sub-skill when the task is about the root long-term forecasting route
for the core model families:

- Linear
- DLinear
- NLinear
- Informer
- Transformer
- Autoformer

It owns the common train/test/predict flow, model selection, look-back window
sweeps, embedding sweeps, and DLinear weight visualization.

## Start here

- [CLI reference](references/cli-reference.md)
- [Model overview](references/model-overview.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Forecasting launcher](scripts/run_long_forecasting.py)
- [DLinear weight plotter](scripts/plot_linear_weights.py)
- [Tiny smoke check](scripts/smoke_long_forecasting.py)

## What this sub-skill owns

- Root `run_longExp.py` long-horizon training, testing, and prediction.
- Model choice among the six core forecasting families above.
- Benchmark-style presets for `scripts/EXP-LongForecasting/`.
- Look-back window studies from `scripts/EXP-LookBackWindow/`.
- Embedding studies from `scripts/EXP-Embedding/`.
- DLinear weight plotting from checkpoint files.

## What this sub-skill does not own

- Statistical baselines such as Naive, ARIMA, SARIMA, or GBRT.
- FEDformer subrepo workflows.
- Pyraformer workflows or preprocessing helpers.
- Optional TVM internals.

## Operating rules

1. Treat `run_longExp.py` as the canonical root launcher. Use the bundled
   wrapper for safer path handling, CPU forcing, and a small amount of
   validation.
2. Keep dataset roots explicit. The common layout is a dataset directory such
   as `dataset/` that contains the benchmark CSVs or a custom CSV with a
   `date` column plus feature columns.
3. Use `--individual` for Linear-family runs when following the benchmark
   scripts.
4. Prefer CUDA for Autoformer test or predict runs. The tiny smoke helper can
   still run a forward check in train mode.
5. Use the plotting helper only on Linear-family checkpoints with seasonal and
   trend weights.

## Routing hints

- Route baseline comparisons to `../statistical-baselines/`.
- Route FEDformer-only tasks to `../fedformer/`.
- Route Pyraformer tasks and preprocessing to `../pyraformer/`.
- If a request is ambiguous between this route and one of those sibling
  workflows, prefer the sibling route instead of growing this one.

The shared CSV layout and dataset root convention are the same as the repo-level
root workflow and the FEDformer route. See the workflow reference for the exact
file expectations and model-specific argument patterns.

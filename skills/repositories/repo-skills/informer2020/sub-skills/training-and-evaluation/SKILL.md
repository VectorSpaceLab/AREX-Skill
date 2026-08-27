---
name: training-and-evaluation
description: "Train, validate, test, smoke-check, and interpret Informer2020
  forecasting runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and evaluation

Use this sub-skill for the forecasting run loop: choose the model and attention, set sequence lengths and feature mode, launch train/validate/test cycles, read checkpoints and results, and compare benchmark presets.

## What it covers
- Model family: `informer` vs `informerstack`.
- Attention: `prob` vs `full`.
- Feature modes: `M`, `S`, `MS`.
- Lengths: `seq_len`, `label_len`, `pred_len`.
- Training controls: `itr`, `train_epochs`, `batch_size`, `patience`, `learning_rate`, `lradj`, AMP, and multi-GPU.
- Outputs: checkpoints, prediction arrays, metrics, and future-prediction artifacts.
- Benchmark presets distilled from the shipped ETTh1 / ETTh2 / ETTm1 / WTH run families.

## Route out
- Custom CSV shape, date extension for future prediction, target / `cols` handling, and dataset validation: [`../custom-data-and-prediction/SKILL.md`](../custom-data-and-prediction/SKILL.md).
- Tiny fixture generation and smoke orchestration: [`../../scripts/make_tiny_forecast_csv.py`](../../scripts/make_tiny_forecast_csv.py), [`../../scripts/check_forecast_csv.py`](../../scripts/check_forecast_csv.py), [`../../scripts/run_forecasting_smoke.py`](../../scripts/run_forecasting_smoke.py).

## Fast facts
- The source CLI always trains first, then tests once per `itr`; `do_predict` appends future prediction after test.
- Built-in dataset presets for ETTh1 / ETTh2 / ETTm1 / ETTm2 / WTH / ECL / Solar override `data_path`, `target`, `enc_in`, `dec_in`, and `c_out`.
- `informerstack` uses `s_layers`; `informer` uses `e_layers`.
- `--distil` and `--mix` are disable flags: adding them turns those features off.
- `checkpoints/<setting>/checkpoint.pth` holds the best model; `results/<setting>/` holds `metrics.npy`, `pred.npy`, `true.npy`, and `real_prediction.npy` when prediction is enabled.
- For CPU smoke, hide CUDA or use the smoke helper's CPU backend option; `--use_gpu False` is not a reliable CPU switch.

## Read next
- [`references/workflows.md`](references/workflows.md)
- [`references/cli-reference.md`](references/cli-reference.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

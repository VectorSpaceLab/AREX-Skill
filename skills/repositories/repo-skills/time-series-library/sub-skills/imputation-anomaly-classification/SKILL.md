---
name: imputation-anomaly-classification
description: "Configure and debug Time-Series-Library imputation, reconstruction
  anomaly detection, and UEA time-series classification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TSLib Imputation, Anomaly Detection, and Classification

Use this sub-skill when the task uses `--task_name imputation`, `anomaly_detection`, or `classification`, or when the user needs help with `mask_rate`, `anomaly_ratio`, PSM/MSL/SMAP/SMD/SWAT layouts, UEA `.ts` files, classification accuracy, or reconstruction-style anomaly metrics.

## Route Here

- Build or debug masked imputation commands over ETT/custom CSV datasets.
- Configure reconstruction anomaly detection with PSM, MSL, SMAP, SMD, or SWAT folders.
- Configure UEA time-series classification with `<DatasetName>_TRAIN.ts` and `<DatasetName>_TEST.ts`.
- Interpret imputation MAE/MSE, anomaly threshold/accuracy/precision/recall/F-score, and classification accuracy outputs.
- Decide when augmentation flags are relevant to classification or detection experiments.

## Reroute

- Generic local file validation, `run.py` parser flags, output folders, or GPU/CPU preflight: use `../data-and-cli/SKILL.md`.
- Forecasting, TimeXer, M4, or zero-shot forecast tasks: use `../forecasting/SKILL.md`.
- Optional model dependency installation, custom models, and augmentation implementation details: use `../foundation-models-and-customization/SKILL.md`.

## Quick Patterns

### Imputation

```bash
python -u run.py \
  --task_name imputation --is_training 1 \
  --root_path ./dataset/ETT-small/ --data_path ETTh1.csv \
  --model_id ETTh1_mask_0.125 --mask_rate 0.125 \
  --model TimesNet --data ETTh1 --features M \
  --seq_len 96 --label_len 0 --pred_len 0 \
  --enc_in 7 --dec_in 7 --c_out 7 \
  --train_epochs 1 --num_workers 0 --no_use_gpu
```

### Anomaly detection

```bash
python -u run.py \
  --task_name anomaly_detection --is_training 1 \
  --root_path ./dataset/PSM --model_id PSM \
  --model TimesNet --data PSM --features M \
  --seq_len 100 --pred_len 0 --enc_in 25 --c_out 25 \
  --anomaly_ratio 1.0 --train_epochs 1 --num_workers 0
```

### UEA classification

```bash
python -u run.py \
  --task_name classification --is_training 1 \
  --root_path ./dataset/Heartbeat/ --model_id Heartbeat \
  --model TimesNet --data UEA \
  --e_layers 2 --d_model 64 --d_ff 128 --top_k 3 \
  --batch_size 16 --train_epochs 1 --num_workers 0 --no_use_gpu
```

## Important Task Differences

- Imputation randomly masks entries in `batch_x` according to `--mask_rate` and computes MAE/MSE only on masked positions.
- Anomaly detection trains a reconstruction model, computes reconstruction energy on train and test windows, thresholds by `100 - anomaly_ratio` percentile, then applies event-level adjustment.
- Classification builds model dimensions from the TRAIN and TEST `.ts` files; `seq_len`, `enc_in`, and `num_class` are inferred before model construction.

## References

- `references/task-workflows.md` gives complete task recipes and data requirements.
- `references/metrics-and-results.md` explains task metrics and output files.
- `references/troubleshooting.md` covers task-specific data, metric, and shape failures.
- `../data-and-cli/scripts/validate_tslib_data.py` validates local anomaly/UEA/CSV files without running training.

## Avoid

- Do not use anomaly or classification benchmark scripts as smoke tests without rewriting GPU, epoch, data path, and worker settings.
- Do not compare tiny synthetic anomaly/classification metrics to paper results.
- Do not force forecasting channel-count assumptions onto UEA classification; classification derives data dimensions from `.ts` files.

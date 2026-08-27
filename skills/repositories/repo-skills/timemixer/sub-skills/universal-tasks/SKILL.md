---
name: universal-tasks
description: "Use and debug TimeMixer imputation, anomaly detection, and
  classification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TimeMixer Universal Tasks

Use this sub-skill for TimeMixer's non-forecast branches: imputation, anomaly detection, and classification.

## Route here for

- Building or checking `run.py` commands for imputation, anomaly detection, or classification, using the explicit helper path `/path/to/timemixer-skill/sub-skills/universal-tasks/scripts/build_universal_task_command.py`.
- Understanding task-specific args such as `mask_rate`, `anomaly_ratio`, UEA padding, and `channel_independence`.
- Locating result files, saved metrics, and checkpoint paths for the non-forecast branches.
- Debugging dataset-name, mask, threshold, or classification shape issues that are specific to these tasks.
  The helper prints commands only; run generated `run.py` commands from `/path/to/TimeMixer-checkout`, not from the skill directory.
## Safe defaults

1. Use the command builder to assemble a command before any training run. Its source-compatible downsampling defaults are `--down-sampling-layers 1 --down-sampling-window 2`; overrides must keep layers >= 1, window >= 2, and the smallest scale non-empty.
2. M4 imputation is rejected by the builder because this source M4 loader cannot safely use the universal branch's `pred_len=0`; use the forecasting M4 presets instead.
3. Keep `c_out` aligned with the input channel count for imputation and anomaly detection.
4. For multi-feature UEA classification, prefer `channel_independence=0`.
5. Treat `anomaly_ratio` as a percent value in the source threshold calculation.
6. Do not launch benchmark-scale training or dataset downloads from this sub-skill.

## Route elsewhere

- Forecasting benchmark scripts, custom forecast presets, or M4/PEMS/ECL/ETT/Solar recipes: `forecasting-experiments`.
- Dataset file layout, CSV/NPY/TS placement, or validation of raw inputs: `data-preparation`.
- TimeMixer tensor internals, PDM/FMM shapes, or decomposition/downsampling behavior: `model-architecture`.

## Task map

| Task | Source branch | Typical data key | Main metric | Main outputs |
| --- | --- | --- | --- | --- |
| Imputation | `Exp_Imputation` | `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, `custom`, `m4`, `PEMS`, `Solar` | Masked-value `MSELoss` during training; MAE/MSE/RMSE/MAPE/MSPE on test | `result_imputation.txt`, `results/<setting>/metrics.npy`, `pred.npy`, `true.npy` |
| Anomaly detection | `Exp_Anomaly_Detection` | `PSM`, `MSL`, `SMAP`, `SMD`, `SWAT` | Accuracy, precision, recall, F-score after thresholding and adjustment | `result_anomaly_detection.txt` |
| Classification | `Exp_Classification` | `UEA` | Cross-entropy loss; accuracy for validation/test | `results/<setting>/result_classification.txt` |

## Bundled assets

- `references/task-workflows.md`
- `references/troubleshooting.md`
- `scripts/build_universal_task_command.py`

## Safe defaults

1. Use the command builder to assemble a command before any training run.
2. Keep `c_out` aligned with the input channel count for imputation and anomaly detection.
3. For multi-feature UEA classification, prefer `channel_independence=0`.
4. Treat `anomaly_ratio` as a percent value in the source threshold calculation.
5. Do not launch benchmark-scale training or dataset downloads from this sub-skill.

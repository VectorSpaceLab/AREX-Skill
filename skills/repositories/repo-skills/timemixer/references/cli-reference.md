# TimeMixer CLI Reference

Read this when you need to build or audit a `run.py` command. The source CLI is a single entry point with required arguments even though some defaults are present in the parser.

## Core entry point

- `run.py` is the main CLI script.
- The code routes by `--task_name` to forecasting, imputation, anomaly detection, or classification experiment classes.
- `run.py --help` is unreliable because one help string contains an unescaped percent sign; use this reference and the bundled command builders instead of relying on parser help.

## Required top-level arguments

These are required by the source parser and should always appear in generated commands:

| Argument | Meaning |
| --- | --- |
| `--task_name` | One of `long_term_forecast`, `short_term_forecast`, `imputation`, `classification`, `anomaly_detection`. |
| `--is_training` | `1` for train-then-test, `0` for test-only. |
| `--model_id` | Experiment identifier used in checkpoint/result names. |
| `--model` | Model name; the inspected repository uses `TimeMixer`. |
| `--data` | Dataset family or key used by the data provider. |

## Common data flags

| Argument | Notes |
| --- | --- |
| `--root_path` | Root directory containing the selected dataset files. |
| `--data_path` | File name for CSV, `.npz`, or other data files when the loader expects one. |
| `--features` | `M`, `S`, or `MS` for forecasting/imputation-style loaders. |
| `--target` | Target column name used by CSV-style loaders. |
| `--freq` | Time-feature frequency string, mainly for CSV-style loaders. |
| `--seq_len` | Input window length. |
| `--label_len` | Decoder label length for forecasting paths; the non-forecast builders normalize it to a self-consistent value. |
| `--pred_len` | Forecast horizon. |
| `--seasonal_patterns` | M4 seasonal family. |

## Model and optimization flags

| Argument | Notes |
| --- | --- |
| `--enc_in`, `--dec_in`, `--c_out` | Input/output channel counts. Keep them aligned with the selected loader and feature mode. |
| `--d_model`, `--d_ff`, `--n_heads`, `--e_layers`, `--d_layers` | Core model widths/depth. |
| `--moving_avg`, `--decomp_method`, `--top_k` | Decomposition controls for the model internals. |
| `--down_sampling_layers`, `--down_sampling_window`, `--down_sampling_method` | Multiscale construction controls. |
| `--channel_independence` | `1` is the default for most forecasting/reconstruction paths; classification typically uses `0` for multivariate inputs. |
| `--use_norm`, `--use_future_temporal_feature` | Forecast/anomaly normalization and future mark injection controls. |
| `--mask_rate` | Imputation mask fraction. |
| `--anomaly_ratio` | Anomaly threshold percentile value used by the source thresholding code. |
| `--train_epochs`, `--batch_size`, `--patience`, `--learning_rate` | Training controls. |
| `--checkpoints`, `--num_workers`, `--itr`, `--des`, `--comment`, `--lradj`, `--pct_start` | Experiment and scheduler controls. |
| `--use_amp`, `--use_gpu`, `--gpu`, `--use_multi_gpu`, `--devices` | Hardware flags. |

## Task families and the right sub-skill

| Task family | Typical `--task_name` / `--data` combo | Route |
| --- | --- | --- |
| Long-term forecasting | `long_term_forecast` with ETT, ECL, Traffic, Weather, Solar, PEMS, or custom CSV data | `sub-skills/forecasting-experiments/` |
| Short-term forecasting | `short_term_forecast` with `data=m4` | `sub-skills/forecasting-experiments/` |
| Imputation | `imputation` with generic loaders, `m4`, `PEMS`, or `Solar` | `sub-skills/universal-tasks/` |
| Anomaly detection | `anomaly_detection` with `PSM`, `MSL`, `SMAP`, `SMD`, or `SWAT` | `sub-skills/universal-tasks/` |
| Classification | `classification` with `data=UEA` | `sub-skills/universal-tasks/` |
| Shape/debugging | Any of the above when the issue is tensor shape, decomposition, or embedding behavior | `sub-skills/model-architecture/` |
| Raw data validation | Any of the above when the issue is file layout or dataset schema | `sub-skills/data-preparation/` |

## Safe command-generation rules

- Use the forecasting or universal-task command builders to print commands instead of typing them from memory.
- Use `CUDA_VISIBLE_DEVICES=''` for a reliable CPU fallback rather than `--use_gpu False`.
- Treat reduced `train_epochs`, `batch_size`, or worker counts as debug/smoke commands, not benchmark reproductions.
- For `short_term_forecast`, the source implementation is M4-specific.
- For `data=PEMS` and `data=Solar`, calendar marks are not used the way they are for ETT/custom CSVs.

## Quick routing cues from CLI text

- `--mask_rate` or `--anomaly_ratio` usually means the universal-task branches.
- `--seasonal_patterns` with `data=m4` means short-term forecasting.
- `--root_path` plus `--data_path` and channel-count mismatches usually means the data-preparation sub-skill should be read next.
- `--channel_independence`, `--moving_avg`, or `--dft_decomp` usually means the model-architecture sub-skill should be read next.

# Unified `run.py` CLI Reference

TSLib uses one Python entry point:

```bash
python -u run.py --task_name <task> --is_training <0-or-1> --model_id <id> --model <ModelName> --data <dataset> ...
```

The required flags are `--task_name`, `--is_training`, `--model_id`, `--model`, and `--data`. Most task behavior then depends on shared flags.

## Task dispatch

| `--task_name` | Experiment class | Main sub-skill |
| --- | --- | --- |
| `long_term_forecast` | long-term forecast experiment | `sub-skills/forecasting/` |
| `short_term_forecast` | M4/short-term forecast experiment | `sub-skills/forecasting/` |
| `zero_shot_forecast` | LTSM zero-shot forecast experiment | `sub-skills/forecasting/` plus optional dependency guidance |
| `imputation` | masked reconstruction experiment | `sub-skills/imputation-anomaly-classification/` |
| `anomaly_detection` | reconstruction anomaly detection experiment | `sub-skills/imputation-anomaly-classification/` |
| `classification` | UEA classification experiment | `sub-skills/imputation-anomaly-classification/` |

`run.py` defaults unknown task names to the long-term forecast class. Future agents should not rely on that fallback; set a valid task name explicitly.

## Data flags

- `--data`: loader key. Important keys include `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, `custom`, `m4`, `PSM`, `MSL`, `SMAP`, `SMD`, `SWAT`, and `UEA`.
- `--root_path`: directory containing local data files.
- `--data_path`: CSV filename for ETT/custom forecasting and imputation.
- `--features`: forecasting channel mode: `M` multivariate-to-multivariate, `S` univariate-to-univariate, `MS` multivariate-to-single target.
- `--target`: target column for `S` and `MS`; default is `OT`.
- `--freq`: timestamp frequency for time features; common values include `h`, `t`, `d`, `w`, `m`, or detailed strings like `15min`.

## Window and task flags

- Forecasting: `--seq_len`, `--label_len`, `--pred_len`, `--seasonal_patterns`, `--inverse`, `--use_dtw`.
- Imputation: `--mask_rate`; examples often use `--label_len 0 --pred_len 0`.
- Anomaly detection: `--anomaly_ratio` controls percentile thresholding after reconstruction.
- Classification: `--model_id` doubles as the UEA dataset name; `Exp_Classification` derives `seq_len`, `enc_in`, and `num_class` from data.

## Model flags

- `--model` must match a file basename under `models/` such as `DLinear`, `TimesNet`, `TimeXer`, `PatchTST`, or `Transformer`.
- Common architecture flags: `--e_layers`, `--d_layers`, `--d_model`, `--d_ff`, `--n_heads`, `--factor`, `--top_k`, `--num_kernels`, `--dropout`, `--activation`, `--embed`.
- Mamba/MambaSL flags: `--expand`, `--d_conv`, `--tv_dt`, `--tv_B`, `--tv_C`, `--use_D`.
- TimeXer uses `--patch_len`; many exogenous recipes also use `features MS` or target-specific settings.

## Optimization and runtime flags

- `--train_epochs`, `--batch_size`, `--learning_rate`, `--patience`, `--itr`, `--num_workers`, `--loss`, `--lradj`, `--des`.
- `--use_gpu` is effectively default-on in `run.py`; use `--no_use_gpu` for CPU.
- `--gpu`, `--gpu_type`, `--use_multi_gpu`, and `--devices` control device selection.
- `--use_amp` enables automatic mixed precision and is CUDA-specific in practice.

## Output naming and locations

Training builds a `setting` string from task, model id, model, data, feature mode, window lengths, model dimensions, and description. Outputs use that setting:

| Output | Location |
| --- | --- |
| Checkpoint | `<checkpoints>/<setting>/checkpoint.pth` |
| Forecast/imputation/anomaly/classification plots | `test_results/<setting>/` |
| Forecast/imputation/zero-shot arrays | `results/<setting>/metrics.npy`, `pred.npy`, `true.npy` |
| M4 forecasts | `m4_results/<model>/<SeasonalPattern>_forecast.csv` |
| Text summary files | `result_long_term_forecast.txt`, `result_imputation.txt`, `result_anomaly_detection.txt`, `result_zero_shot_forecast_search.txt`, or classification result under `results/<setting>/` |

Use the data-and-cli sub-skill when users need to inspect or redirect these folders.

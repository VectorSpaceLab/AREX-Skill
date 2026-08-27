# Statistical Baseline Troubleshooting

## `ModuleNotFoundError: No module named 'pmdarima'`

`models/Stat_models.py` imports `pmdarima` unconditionally. This means `python run_stat.py --help` and `Naive` runs fail before parsing arguments if `pmdarima` is missing.

Fix:

```bash
python -m pip install pmdarima
python - <<'PY'
import pmdarima, sklearn, pandas, torch
print('pmdarima ok')
PY
```

If `pmdarima` fails to import after installation, check NumPy/SciPy binary compatibility in the active environment.

## ARIMA or SARIMA appears hung

Expected cause: `ARIMA` and `SARIMA` call `pmdarima.auto_arima` for each sampled batch item and feature channel, using one Python thread per series/channel. SARIMA also searches seasonal models.

Reduce work before retrying:

- Use `--sample 0.01` or lower. The wrapper defaults to conservative values when `--sample` is omitted for ARIMA/SARIMA.
- Use a smaller `--batch-size`; sampled series per batch is `max(int(sample * batch_size), 1) * channels`.
- Run a single `--pred-len` and one dataset before launching a sweep.
- Start with `Naive` or `GBRT` to validate data layout, then switch to ARIMA/SARIMA.
- Avoid `--allow-slow` unless the requested workload is deliberately large.

## Sampling results look unfair or unexpectedly small

`--sample` is not a global fraction of the test set. In `exp/exp_stat.py`, each test batch is sliced to:

```python
samples = max(int(args.sample * args.batch_size), 1)
batch_x = batch_x[:samples]
```

Implications:

- `--sample 0.01 --batch_size 100` evaluates one item per batch.
- Increasing `batch_size` can increase the number of sampled series even when `sample` is unchanged.
- For fair model comparisons, keep `sample`, `batch_size`, dataset, features, and horizon identical across model keys.

## CSV feature or target errors

Common symptoms include `KeyError: 'date'`, `ValueError: list.remove(x): x not in list`, empty datasets, or shape errors.

Checks:

- CSV files must contain a `date` column.
- For `features=S`, the selected `--target` column must exist. The loader removes that column from the feature list and then appends it as the only modeled series.
- For `features=M` and `features=MS`, all non-date columns are used as inputs; `MS` keeps only the last output channel after model prediction.
- `custom` uses a 70/10/20 split. Ensure the final 20% test slice has more than `seq_len + pred_len` rows.
- ETT loader keys (`ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`) use fixed borders and expect the full benchmark CSVs, not small custom fixtures.

For tiny custom fixtures, use `--data custom`, small `--seq-len`, small `--pred-len`, and `--num-workers 0`.

## Output files are missing or written in the wrong place

`run_stat.py` writes outputs relative to the current process working directory, not necessarily relative to `--root_path`:

- `results/<setting>/metrics.npy`, `pred.npy`, `true.npy`
- `test_results/<setting>/*.pdf`
- `result.txt`
- redirected logs or wrapper logs under `logs/LongForecasting/`

Fix:

- Run from the repository root for source-compatible behavior, or pass `--work-dir` to the bundled wrapper to intentionally isolate outputs.
- Use `--dry-run` on the wrapper to inspect the exact command and paths before execution.

## `KeyError` for model name

`exp/exp_stat.py` accepts only these statistical keys:

```text
Naive, ARIMA, SARIMA, GBRT
```

The class names differ (`Naive_repeat`, `Arima`, `SArima`, `GBRT`), but the CLI must use the exact keys above.

## SARIMA seasonal period is surprising

The source `SArima` class starts with `season = 24`, switches to `12` only if the case-sensitive substring `Ettm` is found in `data_path`, switches to `1` if `ILI` is found, and also uses `1` if `season >= seq_len`.

If SARIMA seasonality matters for an experiment, inspect the exact `data_path` string and consider recording the effective season in the run notes. This sub-skill reports the source behavior rather than silently changing it.

## Time feature or date parsing failures

The data loaders parse the `date` column with pandas and create time features according to `--freq`. Use a frequency compatible with the timestamps:

- ETT-hour and most hourly custom data: `--freq h`.
- ETT-minute data: the source default often still works, but `--freq t` or a minute-level alias may be more explicit for custom minute data.
- Weekly ILI-style data may need a weekly-compatible frequency if time feature parsing is part of the failure.

For baseline models, time features are carried by the loader but not consumed by `models/Stat_models.py`; date parsing must still succeed.

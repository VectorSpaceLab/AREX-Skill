# Statistical Baseline Workflows

Use these workflows for non-neural baseline runs through `run_stat.py`. They intentionally avoid FEDformer, Pyraformer, root neural forecasting models, and weight visualization.

## 1. Smoke-check the route

Create a tiny synthetic `custom` CSV and run the Naive baseline end-to-end:

```bash
python scripts/smoke_stat_baselines.py --models Naive
```

To include GBRT in the smoke, use:

```bash
python scripts/smoke_stat_baselines.py --models Naive GBRT
```

The smoke helper writes data and outputs in a temporary directory by default, then verifies that `metrics.npy`, `pred.npy`, and `true.npy` were created.

## 2. Single baseline run

Use the wrapper for one dataset/horizon pair:

```bash
python scripts/run_stat_baselines.py \
  --model Naive \
  --data custom \
  --data-root dataset \
  --data-path exchange_rate.csv \
  --features M \
  --seq-len 96 \
  --label-len 48 \
  --pred-len 96 \
  --batch-size 100 \
  --des Exp
```

For univariate target forecasting:

```bash
python scripts/run_stat_baselines.py \
  --model Naive \
  --data custom \
  --data-root dataset \
  --data-path weather.csv \
  --features S \
  --target OT \
  --seq-len 96 \
  --label-len 48 \
  --pred-len 96
```

## 3. Dry-run the source statistical sweep

The source shell sweep `scripts/EXP-LongForecasting/Stat_Long.sh` creates `logs/LongForecasting/` and runs Naive over ETT, Exchange, Weather, Electricity, Traffic, and ILI horizons. It also comments that `Naive GBRT ARIMA SARIMA` are the intended model family, while only `Naive` is active in the checked-in loop.

Preview the adapted command matrix without running it:

```bash
python scripts/run_stat_baselines.py \
  --sweep stat-long \
  --models Naive \
  --dry-run
```

Run a small subset:

```bash
python scripts/run_stat_baselines.py \
  --sweep stat-long \
  --datasets ETTh1 exchange_rate \
  --models Naive GBRT \
  --pred-lens 96
```

## 4. Source sweep matrix

The adapted `stat-long` sweep uses these source-script defaults when `--pred-lens` is not supplied.

| Dataset label | `--data` | `--data_path` | `--seq_len` | `--label_len` | Default `--pred_len` values | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `ETTh1` | `ETTh1` | `ETTh1.csv` | 96 | 48 | 96, 192, 336, 720 | Fixed-border ETT-hour loader. |
| `ETTh2` | `ETTh2` | `ETTh2.csv` | 96 | 48 | 96, 192, 336, 720 | Fixed-border ETT-hour loader. |
| `ETTm1` | `ETTm1` | `ETTm1.csv` | 96 | 48 | 96, 192, 336, 720 | Fixed-border ETT-minute loader. |
| `ETTm2` | `ETTm2` | `ETTm2.csv` | 96 | 48 | 96, 192, 336, 720 | Source script uses `--batch_size 300`. |
| `exchange_rate` | `custom` | `exchange_rate.csv` | 96 | 48 | 96, 192, 336, 720 | Custom ratio split. |
| `weather` | `custom` | `weather.csv` | 96 | 48 | 96, 192, 336, 720 | Custom ratio split. |
| `electricity` | `custom` | `electricity.csv` | 96 | 48 | 96, 192, 336, 720 | Custom ratio split. |
| `traffic` | `custom` | `traffic.csv` | 96 | 48 | 96, 192, 336, 720 | Custom ratio split. |
| `ili` | `custom` | `national_illness.csv` | 36 | 18 | 24, 36, 48, 60 | ILI horizon family from source script. |

All source sweep rows use `--features M`, `--root_path ./dataset/`, `--des Exp`, and `--itr 1`.

## 5. Sampled ARIMA/SARIMA comparisons

ARIMA and SARIMA fit a new model for every sampled batch item and feature channel. Start with a tiny sample and narrow horizon before expanding:

```bash
python scripts/run_stat_baselines.py \
  --model ARIMA \
  --data custom \
  --data-root dataset \
  --data-path exchange_rate.csv \
  --features M \
  --seq-len 96 \
  --pred-len 96 \
  --batch-size 50 \
  --sample 0.01
```

For a four-model sampled comparison on one dataset/horizon:

```bash
python scripts/run_stat_baselines.py \
  --models Naive GBRT ARIMA SARIMA \
  --data custom \
  --data-root dataset \
  --data-path exchange_rate.csv \
  --features M \
  --seq-len 96 \
  --pred-len 96 \
  --sample 0.01
```

The wrapper rejects large ARIMA/SARIMA samples unless `--allow-slow` is set. Use `--allow-slow` only after confirming the expected number of sampled series is acceptable:

```text
sampled series per batch = max(int(sample * batch_size), 1) * number_of_channels
```

The wrapper also supports these sweep-control flags:

- `--print-command` prints each generated command before execution.
- `--skip-data-check` skips the preflight file-existence check when you already know the paths are valid.
- `--continue-on-failure` keeps the remaining commands running after one command fails.

## 6. Keep outputs isolated

By default the source script writes `results/`, `test_results/`, `result.txt`, and logs relative to the process working directory. To avoid mixing experiments with repository-root outputs, use a dedicated work directory:

```bash
mkdir -p runs/stat-baselines
python scripts/run_stat_baselines.py \
  --work-dir runs/stat-baselines \
  --model Naive \
  --data custom \
  --data-root dataset \
  --data-path exchange_rate.csv \
  --features M \
  --pred-len 96
```

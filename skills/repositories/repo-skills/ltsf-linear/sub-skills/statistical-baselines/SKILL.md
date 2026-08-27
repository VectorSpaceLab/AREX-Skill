---
name: statistical-baselines
description: "Run and troubleshoot Naive, GBRT, ARIMA, and SARIMA statistical
  baseline workflows for long-term time-series forecasting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Statistical Baselines

Use this sub-skill when the task is to run, compare, smoke-test, or troubleshoot the repository's statistical long-forecasting baselines: `Naive`, `GBRT`, `ARIMA`, or `SARIMA` through `run_stat.py` and `models/Stat_models.py`.

## Route here

- Run a repeat-last-value baseline (`Naive`, also described as Repeat-C / closest repeat in the source sweep notes).
- Run `GBRT` for a non-neural Gradient Boosting Regressor baseline.
- Run `ARIMA` or `SARIMA`, especially with a small `--sample` for expensive sampled comparisons.
- Adapt the long-forecast statistical sweep family from `scripts/EXP-LongForecasting/Stat_Long.sh`.
- Debug baseline-specific issues such as missing `pmdarima`, ARIMA/SARIMA slowness, per-batch sampling, or CSV feature/target mismatches.

## Reroute

- Neural root models (`Linear`, `DLinear`, `NLinear`, `Informer`, `Transformer`, `Autoformer`) and weight visualization: use `../long-forecasting/SKILL.md`.
- FEDformer Fourier/Wavelets workflows: use `../fedformer/SKILL.md`.
- Pyraformer long-range, single-step, preprocessing, or TVM-related workflows: use `../pyraformer/SKILL.md`.
- Common dataset layout questions that are not baseline-specific: use `../../references/data-layout.md` when present.

## Start fast

1. Confirm the requested model key is exactly one of `Naive`, `GBRT`, `ARIMA`, or `SARIMA`.
2. Confirm the CSV has a `date` column and the selected feature/target columns. For `features=S` or `features=MS`, set `--target` to an existing target column, commonly `OT`.
3. For a quick environment and data-path check, run the bundled smoke helper from this sub-skill directory or pass `--repo-root` explicitly:

   ```bash
   python scripts/smoke_stat_baselines.py --models Naive
   ```

4. For a single baseline run, prefer the bundled wrapper so paths, logging, sampling, and slow-model guards are explicit:

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
     --batch-size 100
   ```

5. For ARIMA/SARIMA, start with sampled comparisons. The wrapper supplies conservative defaults when `--sample` is omitted, but pass `--allow-slow` only when deliberately running a large or full sample.

## Bundled references

- `references/cli-reference.md` explains `run_stat.py` arguments, model behavior, output files, and sampling semantics.
- `references/workflows.md` gives single-run, smoke, source-sweep, and sampled comparison recipes.
- `references/troubleshooting.md` maps common dependency, slowness, sampling, data-layout, and output-location failures to fixes.

## Bundled scripts

- `scripts/run_stat_baselines.py` wraps `run_stat.py` for single runs or a safe adaptation of the source statistical long-forecast sweep.
- `scripts/smoke_stat_baselines.py` creates a tiny synthetic custom CSV and runs one or more baseline models through the wrapper.

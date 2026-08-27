# Workflows

## Purpose

Read this when you want a quick recipe for choosing the right route before
opening the sub-skill docs.

## 1. Shared preflight

Start with the shared environment and data checks when the request is vague or
new:

```bash
python scripts/check_env.py --scope all --device auto
python scripts/check_data_layout.py --kind root --data-root dataset --data-path exchange_rate.csv
```

Use the shared preflight when the issue is likely to be a missing dependency, a
CUDA mismatch, a wrong dataset path, or a malformed CSV.

## 2. Root long forecasting

Use `long-forecasting` for the core benchmark family:

- `Linear`
- `DLinear`
- `NLinear`
- `Informer`
- `Transformer`
- `Autoformer`

Typical flow:

1. Check the dataset layout.
2. Choose the model family.
3. Run the bundled wrapper or the raw launcher.
4. If the task is about a checkpoint plot, use the weight-plot helper instead of
   the training launcher.

Example:

```bash
python sub-skills/long-forecasting/scripts/run_long_forecasting.py \
  --model DLinear \
  --data custom \
  --root_path dataset \
  --data_path exchange_rate.csv \
  --features M \
  --seq_len 96 \
  --pred_len 96 \
  --itr 1
```

For a checkpoint plot:

```bash
python sub-skills/long-forecasting/scripts/plot_linear_weights.py --checkpoint checkpoints/<setting>/checkpoint.pth
```

## 3. Statistical baselines

Use `statistical-baselines` when you want a classical comparator or a sampled
ARIMA/SARIMA run.

Typical flow:

1. Confirm the CSV has a `date` column and the right target.
2. Start with `Naive` or `GBRT` if you only need a quick sanity check.
3. Use a small `--sample` for ARIMA or SARIMA.
4. Increase the batch size only if you intentionally want more sampled series.

Example smoke:

```bash
python sub-skills/statistical-baselines/scripts/smoke_stat_baselines.py --models Naive
```

## 4. FEDformer

Use `fedformer` when the user specifically means the FEDformer subrepo or its
Fourier/Wavelets variants.

Typical flow:

1. Confirm the dataset root and feature mode.
2. Choose `--version Fourier` or `--version Wavelets`.
3. Set `--model FEDformer` explicitly.
4. Run the CUDA smoke before a heavier training pass.

Example smoke:

```bash
python sub-skills/fedformer/scripts/smoke_fedformer.py --version Wavelets
```

## 5. Pyraformer

Use `pyraformer` for long-range or single-step forecasting, preprocessing, or
synthetic data generation.

Typical flow:

1. Check the `Pyraformer/data/` layout.
2. Decide whether you need long-range or single-step forecasting.
3. Run the appropriate launcher or preprocessing helper.
4. Leave `-use_tvm` off unless you explicitly want the optional TVM route.

Example smoke:

```bash
python sub-skills/pyraformer/scripts/smoke_pyraformer.py --repo-root .
```

## 6. Keep outputs isolated

The source scripts write `checkpoints/`, `results/`, `test_results/`, `logs/`,
and `weights_plot/` relative to the current working directory. If you want to
avoid mixing experiments with the repo root, prefer the bundled wrappers and a
separate run directory when the wrapper offers one.

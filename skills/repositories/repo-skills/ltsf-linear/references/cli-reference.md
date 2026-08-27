# CLI Reference

## Purpose

Read this when you want the main entry points and the flags that matter most
across the repo's workflow families.

## Main entry points

| Entry point | Owned by | Use it for | Notes |
| --- | --- | --- | --- |
| `run_longExp.py` | `long-forecasting` | Root Linear/DLinear/NLinear/Informer/Transformer/Autoformer runs | Main benchmark launcher. The `--use_gpu` parser is fragile, so prefer the bundled wrapper when you want explicit CPU/GPU control. |
| `run_stat.py` | `statistical-baselines` | Naive, GBRT, ARIMA, SARIMA comparisons | Imports `pmdarima` immediately. |
| `FEDformer/run.py` | `fedformer` | FEDformer Fourier or Wavelets runs | Set `--model` explicitly; the parser default is not a valid FEDformer family member. |
| `Pyraformer/long_range_main.py` | `pyraformer` | Pyraformer long-range runs | Optional TVM support lives behind `-use_tvm`. |
| `Pyraformer/single_step_main.py` | `pyraformer` | Pyraformer single-step runs | Uses a separate dataset family and predictor head. |
| `weight_plot.py` | `long-forecasting` | Plot Linear-family checkpoint weights | The bundled helper is safer because it searches checkpoints and validates the weight keys. |

## Shared flags

| Flag | Where it matters | Meaning / caveat |
| --- | --- | --- |
| `--data` | root, FEDformer, Pyraformer, baselines | Dataset key. Common root keys: `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, `custom`. |
| `--root_path` / `--data-root` | all routes | Directory containing the dataset files. Root scripts often default to `dataset/`; Pyraformer has its own `data/` tree. |
| `--data_path` | all routes | CSV or data file name under the root path. |
| `--features` | root, FEDformer, baselines | `M`, `S`, or `MS`. If you choose `S` or `MS`, make sure `--target` exists. |
| `--target` | root, FEDformer, baselines | Target column, commonly `OT`. |
| `--seq_len` | all forecasting routes | Input window length. |
| `--label_len` | sequence-to-sequence routes | Decoder warm-up length. |
| `--pred_len` | all forecasting routes | Prediction horizon. |
| `--model` | root, FEDformer, Pyraformer | Model family key. Validate it before launching a sweep. |
| `--embed_type` | root, FEDformer | Embedding variant selector. |
| `--version` | FEDformer | `Fourier` or `Wavelets`. |
| `--mode_select`, `--modes`, `--L`, `--base`, `--cross_activation` | FEDformer | FEDformer-specific Fourier/Wavelet knobs. |
| `-eval` | FEDformer, Pyraformer | Evaluation mode for the subrepo entry points. |
| `-decoder` | Pyraformer | `FC` or `attention`. |
| `-use_tvm` | Pyraformer | Optional TVM-backed path. Keep it off unless you deliberately want that backend. |
| `--sample` | statistical baselines | Per-batch sampling fraction, not a global dataset fraction. |

## Common command shapes

From the skill root, the bundled wrappers are usually easier to use than the raw
source CLIs:

```bash
python sub-skills/long-forecasting/scripts/run_long_forecasting.py --help-root
python sub-skills/statistical-baselines/scripts/run_stat_baselines.py --dry-run --sweep stat-long
python sub-skills/fedformer/scripts/run_fedformer.py --help
python sub-skills/pyraformer/scripts/run_pyraformer_long.py --help
```

For a shared environment and data preflight, use:

```bash
python scripts/check_env.py --scope all --device auto
python scripts/check_data_layout.py --kind root --data-root dataset --data-path exchange_rate.csv
```

## Gotchas

- `run_longExp.py` parses `--use_gpu` as a `bool`, so `False` on the command
  line is not a safe string literal. Use the wrapper or pass the intent through a
  helper that normalizes it.
- `run_stat.py` imports `pmdarima` before argument parsing.
- FEDformer's default `--model` value is not a supported key.
- Pyraformer's optional TVM path has extra layout assumptions and is not part of
  the minimum smoke surface.

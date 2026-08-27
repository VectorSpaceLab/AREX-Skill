# Model Overview

## Purpose

Read this when you need a quick map of the repo's model families before diving
into a sub-skill.

## Route map

| Route | Models / entry points | Best for | Notes |
| --- | --- | --- | --- |
| Core long forecasting | `Linear`, `DLinear`, `NLinear`, `Informer`, `Transformer`, `Autoformer` via `run_longExp.py` | Standard benchmark training, testing, prediction, benchmark sweeps, and DLinear weight plots | The root route uses the shared `exp/`, `data_provider/`, `models/`, `layers/`, and `utils/` trees. |
| Statistical baselines | `Naive`, `GBRT`, `ARIMA`, `SARIMA` via `run_stat.py` | Fast repeat-value or classical baseline comparisons | `pmdarima` is imported at module load time, so the dependency must be present even for help output. |
| FEDformer | `FEDformer`, `Autoformer`, `Informer`, `Transformer` via `FEDformer/run.py` | Fourier or Wavelets time-series variants with GPU smoke checks | The FEDformer subrepo has its own `exp/`, `models/`, `layers/`, and `utils/` trees. |
| Pyraformer | `Pyraformer` via `Pyraformer/long_range_main.py` and `Pyraformer/single_step_main.py` | Pyramidal attention for long-range or single-step forecasting, plus preprocessing | The optional TVM path is separate from the default route and is not part of the minimum smoke surface. |

## Core model notes

- `Linear` is the simplest baseline: one linear layer over the input window.
- `DLinear` decomposes the series into seasonal and trend components before two
  linear projections.
- `NLinear` normalizes by the last observed value, applies a linear layer, and
  adds the last value back.
- `Informer`, `Transformer`, and `Autoformer` use encoder/decoder style
  sequence-to-sequence forecasting.
- `Autoformer` is the only root model that explicitly relies on the series
  decomposition path in `layers/Autoformer_EncDec.py`.
- `FEDformer` adds Fourier or Wavelet attention variants and has a separate
  entry point because of its extra dependency surface.
- `Pyraformer` uses pyramidal attention and separate preprocessing helpers for
  its data layout.

## Choosing a route quickly

- Need a quick, practical benchmark route: start with `long-forecasting`.
- Need a classical baseline or sampled ARIMA/SARIMA comparison: use
  `statistical-baselines`.
- Need the FEDformer subrepo or Fourier/Wavelets choice: use `fedformer`.
- Need Pyraformer preprocessing or TVM guidance: use `pyraformer`.

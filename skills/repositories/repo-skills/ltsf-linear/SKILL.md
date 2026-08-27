---
name: ltsf-linear
description: "Routes the repo's long-term forecasting, statistical baselines,
  FEDformer, and Pyraformer workflows, plus shared setup and data-layout
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LTSF-Linear

This is the root router for the LTSF-Linear repository. Use it when the task is
about the repo as a whole, when you need shared setup or data checks, or when
you need to choose between the repo's four major workflow families.

## Read first

- `references/repo-provenance.md` when checking whether this skill matches the
  current checkout or before refreshing it.
- `references/data-layout.md` for the shared CSV and dataset-directory
  conventions.
- `references/model-overview.md` for the quick model-family map.
- `references/cli-reference.md` for the main entry points and the most useful
  flags.
- `references/workflows.md` for common run patterns and route selection.
- `references/troubleshooting.md` for cross-cutting install, import, backend,
  and data-layout failures.
- `scripts/check_env.py` for a fast import and CUDA readiness check.
- `scripts/check_data_layout.py` for a small dataset-layout sanity check.

## Route map

- `sub-skills/long-forecasting/SKILL.md` — Linear, DLinear, NLinear,
  Informer, Transformer, Autoformer, benchmark sweeps, and weight plotting.
- `sub-skills/statistical-baselines/SKILL.md` — Naive, GBRT, ARIMA, and
  SARIMA baselines.
- `sub-skills/fedformer/SKILL.md` — the FEDformer subrepo and its Fourier /
  Wavelets variants.
- `sub-skills/pyraformer/SKILL.md` — Pyraformer long-range forecasting,
  single-step forecasting, preprocessing, and synthetic data generation.

## Install and preflight

1. Create a Python environment with the repo's runtime stack. The verified
   inspection environment used a CUDA-capable PyTorch 1.9.0+cu111 build on
   x86_64 Linux.
2. Install the root requirements first, then add route-specific extras only
   when you need them:
   - root `requirements.txt`
   - `pmdarima` for statistical baselines
   - `sympy` and `einops` for FEDformer Wavelets
   - `fbm` for Pyraformer synthetic generation
   - `Pyraformer/requirements.txt` for Pyraformer routes
3. Run a fast shared smoke before any heavier workflow:

   ```bash
   python scripts/check_env.py --scope all --device auto
   ```

4. Run a quick layout check for the dataset you expect to use:

   ```bash
   python scripts/check_data_layout.py --kind root --data-root dataset --data-path exchange_rate.csv
   ```

## Root workflow hints

- The main benchmark launcher is `run_longExp.py`.
- The statistical baseline launcher is `run_stat.py`.
- The FEDformer launcher lives in `FEDformer/run.py`.
- The Pyraformer launchers live in `Pyraformer/long_range_main.py` and
  `Pyraformer/single_step_main.py`.
- `run_longExp.py` uses a fragile `--use_gpu` boolean parser; prefer the
  bundled wrapper scripts when you want explicit CPU or CUDA control.
- `run_stat.py` imports `pmdarima` at module import time, so missing that
  dependency fails even `--help`.
- FEDformer's parser default model is not a valid FEDformer family name, so
  always pass an explicit `--model`.
- Pyraformer's optional TVM path is separate from the minimum smoke surface.

## When to stay at the root

Use the root skill and the shared scripts when you only need:

- a quick environment or import check,
- dataset/path validation,
- a model-family decision,
- or a high-level routing answer before choosing a sub-skill.

Move to a sub-skill once the user has picked a concrete workflow family.

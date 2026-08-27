---
name: fedformer
description: "Routes FEDformer training, comparison, and sweep workflows for the
  FEDformer subrepo, including Fourier and Wavelets variants, model-selection
  knobs, and the bundled CUDA smoke check."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FEDformer

Use this route when the task is about the FEDformer subrepo entry point `FEDformer/run.py`, the FEDformer model stack in `FEDformer/exp`, `FEDformer/models`, `FEDformer/layers`, `FEDformer/utils`, or the FEDformer sweep scripts.

Natural triggers:
- FEDformer
- Fourier
- Wavelets
- `mode_select`
- `modes`
- `L`
- `base`
- `cross_activation`
- compare FEDformer against Autoformer, Informer, or Transformer within this subrepo

## What this sub-skill covers

- The native CLI in `FEDformer/run.py`.
- The FEDformer architecture variants implemented in `FEDformer/models/FEDformer.py`.
- The exp, layer, and utility trees that support training, testing, and prediction.
- Dataset loading and shape alignment for the FEDformer entry point.
- The sweep patterns encoded in `FEDformer/scripts/LongForecasting.sh` and `FEDformer/scripts/LookBackWindow.sh`.
- CUDA-only smoke validation for the Fourier or Wavelets path.

## What it does not cover

- The repo-wide Linear, DLinear, and NLinear benchmark routes.
- Statistical baseline workflows.
- Pyraformer workflows.
- Maintainer-only or release-only tasks.

If the user really means the root long-forecasting benchmark, the statistical baselines, or Pyraformer, route them to the sibling route for that workflow instead of staying here.

## Start here

Read these bundled files first:

- `scripts/run_fedformer.py` for a safe wrapper that resolves a checkout and builds a FEDformer command.
- `scripts/smoke_fedformer.py` for a tiny CUDA forward pass on synthetic data.
- `references/cli-reference.md` for the FEDformer CLI flags and the arguments that matter most.
- `references/model-overview.md` for Fourier vs. Wavelets, embedding choices, and comparison guidance.
- `references/data-layout.md` when the CSV format, split rule, or channel counts are unclear.
- `references/workflows.md` for one-off runs, sweep recipes, and comparison loops.
- `references/troubleshooting.md` when the run fails, the parser defaults look suspicious, or the dataset layout does not match.

## Environment expectations

This route is verified for a CUDA build of PyTorch 1.9.0+cu111 on GPU hardware.
Wavelets also needs `sympy`, `einops`, and `scipy` in addition to the standard FEDformer stack.

## Common decisions

- Use `--model FEDformer` for the FEDformer family.
- Use `--version Fourier` when you want mode selection over frequency bins.
- Use `--version Wavelets` when you want the multiresolution branch with `L`, `base`, and `cross_activation`.
- Use `--model Autoformer`, `Informer`, or `Transformer` only when the comparison is still anchored in this subrepo.
- Keep the dataset, lengths, and feature mode fixed when comparing model families.
- Leave the `--moving_avg` parser default alone unless you are programmatically building a real Python list.

## Key runtime outputs

A successful run usually writes checkpoints and evaluation artifacts under the current working directory, including:

- `checkpoints/<setting>/checkpoint.pth`
- `results/<setting>/metrics.npy`
- `results/<setting>/pred.npy`
- `results/<setting>/true.npy`
- `test_results/<setting>/`

## Troubleshooting shortcut

Before debugging a failed FEDformer run, check these first:

1. CUDA is available in the active environment.
2. `--model` is set explicitly; the parser default is not a valid FEDformer family member.
3. `root_path`, `data_path`, `features`, and channel counts match the dataset.
4. You are not relying on the pred-only or test-only path without checking its caveats.
5. The version-specific knobs match the selected `--version`.

See `references/troubleshooting.md` for the full failure map.

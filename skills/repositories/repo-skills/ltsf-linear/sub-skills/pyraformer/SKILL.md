---
name: pyraformer
description: "Routes Pyraformer long-range forecasting, single-step forecasting,
  preprocessing, synthetic data generation, and optional TVM questions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# pyraformer

Use this sub-skill when the task is about Pyraformer long-range forecasting, Pyraformer single-step forecasting, preprocessing the Pyraformer datasets, or generating synthetic input files for that route.

## Route here for

- Running or explaining `Pyraformer/long_range_main.py`.
- Running or explaining `Pyraformer/single_step_main.py`.
- Preparing the Pyraformer single-step inputs from raw electricity, flow, or wind data.
- Generating `synthetic.npy` for the synthetic route.
- Questions about `use_tvm`, `truncate`, or other advanced Pyraformer runtime flags when the user explicitly wants the optional CUDA/TVM path.

## Route away

- The `graph_attention.py` debug helper and other TVM-only internals are reference-only and stay out of the default runtime surface.
- Root LTSF-Linear workflows, baseline models, and FEDformer tasks belong in their sibling routes.

## Read first

- `references/cli-reference.md` for long-range and single-step flags, dataset defaults, and model switches.
- `references/data-layout.md` for expected CSV, `.npy`, and checkpoint locations.
- `references/preprocessing.md` for electricity, flow, wind, and synthetic preparation details.
- `references/workflows.md` for the common run recipes and sweep-script summary.
- `references/troubleshooting.md` for dataset, mask, checkpoint, and TVM failure modes.

## Skill-owned scripts

- `scripts/run_pyraformer_long.py` — repo-root-aware launcher for long-range runs.
- `scripts/run_pyraformer_single.py` — repo-root-aware launcher for single-step runs.
- `scripts/prepare_pyraformer_data.py` — bundled data-preparation helper for elect, flow, wind, and synthetic outputs.
- `scripts/smoke_pyraformer.py` — CLI help and dry-run smoke for the route.

## Typical workflow

1. Confirm whether the user needs long-range forecasting, single-step forecasting, or preprocessing.
2. Check the dataset family and file layout in `references/data-layout.md`.
3. Use the matching wrapper or source CLI with the dataset-specific flags from `references/cli-reference.md`.
4. If the user asks about `use_tvm`, confirm they want the optional CUDA/TVM path before enabling it.
5. If a run fails, compare the error with `references/troubleshooting.md` before changing model settings.

## Cross-links

- Use `references/workflows.md` for the upstream benchmark sweep summary and command patterns.
- Use `scripts/smoke_pyraformer.py` before asking for a heavier training or preprocessing run.
- For shared CSV layout and repo-wide missing-file or import issues, see the root skill references at `../../references/data-layout.md` and `../../references/troubleshooting.md`.

---
name: metrics
description: "Routes evo_ape and evo_rpe workflows, metric helper APIs,
  alignment and synchronization choices, result zip creation, and metric
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Metrics

Use this sub-skill for absolute pose error (APE) and relative pose error (RPE) workflows.

## Route here when the user asks for
- `evo_ape` or `evo_rpe`
- `evo.main_ape.ape` or `evo.main_rpe.rpe`
- pose relation choices, delta/delta_unit, `--align`, `--align_origin`, or `--correct_scale`
- timestamp association, `--downsample`, `--motion_filter`, `--project_to_plane`
- `--save_results`, `--save_plot`, or `--rerun`
- metric-specific failures or result zip inspection

## Do not route here when the task is mainly about
- trajectory file-format minutiae or converters
- `evo_res` table/comparison/export workflows
- `evo_config`, package info, or settings editing
- notebooks, custom app wiring, or broader plotting APIs

## Start with
1. [references/api-reference.md](references/api-reference.md)
2. [references/workflows.md](references/workflows.md)
3. [references/troubleshooting.md](references/troubleshooting.md)
4. [scripts/metric_smoke.py](scripts/metric_smoke.py)

## Rules of thumb
- `tum`, `euroc`, `bag`, `bag2`, and `mcap` route through timestamp association; `kitti` does not.
- `--align` and `--align_origin` cannot be combined.
- `--correct_scale` may be used by itself or with `--align`; with `--align` it becomes Sim(3) alignment.
- `--downsample` and `--motion_filter` happen before synchronization.
- The Python helpers mutate trajectories in place, so copy inputs if you need them later.
- `--rerun` requires the optional Rerun dependency; if it is missing, the command exits early.

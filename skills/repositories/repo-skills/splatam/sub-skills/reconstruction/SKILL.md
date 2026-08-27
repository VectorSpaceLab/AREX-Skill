---
name: reconstruction
description: "Guides SplaTAM offline RGB-D SLAM, reconstruction config edits,
  evaluation, visualization, PLY export, post-SplaTAM optimization, and GT-pose
  Gaussian splatting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Reconstruction Sub-Skill

Use this sub-skill for SplaTAM reconstruction and saved-output workflows: offline SLAM, benchmark configs, checkpoint resume, post-SplaTAM optimization, Gaussian splatting with GT poses, novel-view evaluation, final/online visualization, and PLY export.

Route iPhone/NeRFCapture streaming and dataset collection to [../capture/SKILL.md](../capture/SKILL.md). Capture-produced datasets return here for offline SLAM once the dataset layout is valid.

## Required preconditions

- A SplaTAM checkout root with the repo script/config layout.
- A CUDA-capable PyTorch runtime and importable `diff_gaussian_rasterization`.
- A dataset matching the chosen config family.
- W&B disabled or configured when using public benchmark configs that default to `use_wandb=True`.

Run the root environment gate before expensive reconstruction:

```bash
python scripts/check_env.py --require-cuda --require-rasterizer
```

Read root [data/config guidance](../../references/data-and-configs.md) before editing dataset paths.

## Workflow routing

| Task | Entry point | Read |
| --- | --- | --- |
| Run RGB-D SLAM/tracking/mapping on Replica, TUM, ScanNet, ScanNet++, Replica-V2, or iPhone dataset | `python scripts/splatam.py <config.py>` | [references/workflows.md](references/workflows.md#offline-rgb-d-slam) |
| Resume from saved checkpoint | `scripts/splatam.py` with `load_checkpoint=True` and `checkpoint_time_idx` | [references/configuration.md](references/configuration.md#checkpoint-and-resume-fields) |
| Export a completed run to PLY | `python scripts/export_ply.py <config.py>` | [references/workflows.md](references/workflows.md#ply-export) |
| Validate a saved result before export/eval | Bundled `sub-skills/reconstruction/scripts/check_result_bundle.py` | [references/workflows.md](references/workflows.md#result-validation) |
| Visualize reconstruction | `python viz_scripts/final_recon.py <config.py>` or `python viz_scripts/online_recon.py <config.py>` | [references/workflows.md](references/workflows.md#visualization) |
| Refine a SplaTAM checkpoint with post optimization | `python scripts/post_splatam_opt.py <config.py>` | [references/workflows.md](references/workflows.md#post-splatam-optimization) |
| Run Gaussian splatting from GT poses | `python scripts/gaussian_splatting.py <config.py>` | [references/workflows.md](references/workflows.md#gaussian-splatting-with-gt-poses) |
| Train/test or novel-view evaluation | `python scripts/eval_novel_view.py <config.py>` | [references/workflows.md](references/workflows.md#novel-view-and-split-evaluation) |

## Safe operating sequence

1. Pick the closest public config family under the checkout's `configs/` tree.
2. Copy the config to a working file before editing benchmark defaults.
3. Set dataset paths, frame range, `run_name`, and `use_wandb` deliberately.
4. For smoke checks, reduce frame count and iteration counts; do not infer benchmark quality from a reduced run.
5. Launch only after the root environment check passes.
6. Validate `workdir/run_name/params.npz` with the bundled result checker before export, visualization, or downstream reporting.
7. Use the nearest troubleshooting reference for failures:
   - [root troubleshooting](../../references/troubleshooting.md) for install/import/data/W&B/Open3D issues.
   - [references/troubleshooting.md](references/troubleshooting.md) for reconstruction-specific output, memory, config, or eval issues.

## Bundled helper

Run this helper against a saved result directory:

```bash
python sub-skills/reconstruction/scripts/check_result_bundle.py \
  --result-dir <workdir>/<run_name> --require-params
```

It checks the shape and presence of key `params.npz` arrays without importing CUDA or opening a viewer.

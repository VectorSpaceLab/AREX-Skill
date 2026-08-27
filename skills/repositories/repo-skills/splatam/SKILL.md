---
name: splatam
description: "Routes agents working with SplaTAM RGB-D SLAM, Gaussian-splat
  reconstruction, iPhone/NeRFCapture capture, evaluation, export, and
  troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# SplaTAM Repo Skill

Use this repo skill when a task involves SplaTAM: dense RGB-D SLAM with 3D Gaussians, post-SplaTAM Gaussian-splat optimization, reconstruction evaluation/export/visualization, or iPhone/NeRFCapture live capture.

## Fit and boundaries

Use this skill when the user asks to:

- Prepare or repair a SplaTAM runtime environment.
- Run, adapt, or debug SplaTAM reconstruction configs for Replica, Replica-V2, TUM RGB-D, ScanNet, ScanNet++, or iPhone/NeRFCapture data.
- Export `params.npz` outputs to PLY splats or inspect/evaluate saved reconstructions.
- Capture RGB-D frames from the NeRFCapture iOS app or run the live iPhone demo.

Avoid this skill when the task is generic 3D Gaussian Splatting unrelated to SplaTAM, pure dataset conversion with no SplaTAM config/output target, or paper-level reproduction without a SplaTAM checkout.

## First checks

1. Work from a SplaTAM checkout root that has the expected `scripts/`, `configs/`, `datasets/`, `utils/`, and `viz_scripts/` layout.
2. Read [references/environment.md](references/environment.md) before installing or changing dependencies. SplaTAM is CUDA-first; CPU-only is not a supported substitute for the selected workflows.
3. If you still need to set up the runtime, follow the baseline install in [references/environment.md](references/environment.md) (`conda create`, `conda install`, then `pip install -r requirements.txt`) before any workflow-specific changes.
4. Run the bundled environment check before expensive work:

   ```bash
   python scripts/check_env.py --require-cuda --require-rasterizer
   ```

5. Read [references/data-and-configs.md](references/data-and-configs.md) before editing Python config modules or relocating datasets.
6. Read [references/troubleshooting.md](references/troubleshooting.md) when imports, CUDA, dataset paths, W&B, Open3D, or the custom rasterizer fail.

## Routing

| User intent | Route | Read next |
| --- | --- | --- |
| Offline RGB-D SLAM, mapping/tracking config, checkpoints, export PLY, final/online visualization, post-SplaTAM optimization, GT-pose Gaussian splatting, novel-view evaluation | `sub-skills/reconstruction/` | [sub-skills/reconstruction/SKILL.md](sub-skills/reconstruction/SKILL.md) |
| iPhone or LiDAR Apple device capture, NeRFCapture DDS streaming, online demo, capture-only dataset writing, capture-to-offline reconstruction | `sub-skills/capture/` | [sub-skills/capture/SKILL.md](sub-skills/capture/SKILL.md) |
| Cross-cutting install/backend/data/config failures | Root references | [references/environment.md](references/environment.md), [references/troubleshooting.md](references/troubleshooting.md) |

## Core operating facts

- Main scripts load a Python config file with `SourceFileLoader` and expect a module-level `config` dictionary.
- Main reconstruction outputs are under `config["workdir"] / config["run_name"]`, usually including a copied `config.py`, `params.npz`, evaluation image/metric folders, optional checkpoints, and optional `splat.ply` after export.
- All primary reconstruction and live demo paths call CUDA tensors and `diff_gaussian_rasterization`; a working NVIDIA CUDA PyTorch stack is required.
- Public configs set `use_wandb=True` for some benchmark presets. Disable or redirect W&B before local non-credentialed runs.
- Bash capture wrappers adjust kernel UDP socket buffers with `sudo sysctl`; do not run them without explicit authorization. Prefer the Python capture entry points when avoiding system mutation.

## Bundled helpers

- `scripts/check_env.py` checks Python imports, torch/CUDA readiness, and the custom rasterizer without running a dataset.
- `sub-skills/reconstruction/scripts/check_result_bundle.py` validates a saved reconstruction directory and `params.npz` schema before export/eval handoff.
- `sub-skills/capture/scripts/validate_nerfcapture_dataset.py` validates a captured NeRFCapture dataset layout before using it in SplaTAM.

## Provenance and refresh

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout. If the SplaTAM commit, dirty state, public configs, main scripts, dataset loaders, or dependency requirements changed materially, refresh this repo skill before relying on it.

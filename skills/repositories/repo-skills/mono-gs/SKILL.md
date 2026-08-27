---
name: mono-gs
description: "Use MonoGS for CUDA Gaussian-splatting SLAM, dataset/config setup,
  offline evaluation, and RealSense live demos."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MonoGS

Use this repo skill when a task is about MonoGS / Gaussian Splatting SLAM:
installing the runtime, preparing datasets/configs, running monocular/RGB-D/stereo
SLAM, evaluating results, or operating the RealSense live GUI demo.

MonoGS is CUDA-first. Core SLAM and evaluation workflows require CUDA-capable
PyTorch plus the `simple_knn` and `diff_gaussian_rasterization` native
extensions; a CPU-only environment is not a valid substitute for those workflows.

## Quick route map

| User intent | Read |
| --- | --- |
| Install MonoGS, build submodules, verify CUDA/backend imports | [environment-setup](sub-skills/environment-setup/SKILL.md) |
| Download/validate TUM, Replica, EuRoC data or edit YAML configs | [data-and-configs](sub-skills/data-and-configs/SKILL.md) |
| Run offline monocular, RGB-D, or stereo SLAM with `slam.py` | [offline-slam](sub-skills/offline-slam/SKILL.md) |
| Use `--eval`, inspect result folders, ATE/render metrics, W&B behavior | [evaluation-and-results](sub-skills/evaluation-and-results/SKILL.md) |
| Run/debug live Intel RealSense capture or the Open3D/OpenGL GUI | [live-demo](sub-skills/live-demo/SKILL.md) |

## Minimal install shape

From a MonoGS checkout, the documented baseline is a Conda environment with
Python 3.7, PyTorch 1.12.1, CUDA 11.6, Open3D, evo, W&B, GUI dependencies, and
the two recursive submodules built as editable CUDA extensions. Read
[environment-setup](sub-skills/environment-setup/SKILL.md) before installing;
that sub-skill has the build order and troubleshooting gates.

After installation, run the bundled diagnostic:

```bash
python scripts/check_monogs_environment.py --repo-root <mono-gs-checkout> --require-cuda
```

## Main commands

```bash
# Monocular TUM
python slam.py --config configs/mono/tum/fr3_office.yaml

# RGB-D TUM
python slam.py --config configs/rgbd/tum/fr3_office.yaml

# RGB-D Replica single-process-style config
python slam.py --config configs/rgbd/replica/office0_sp.yaml

# Stereo EuRoC
python slam.py --config configs/stereo/euroc/mh02.yaml

# Headless evaluation with W&B disabled by environment
WANDB_MODE=disabled python slam.py --config configs/mono/tum/fr3_office.yaml --eval
```

Validate dataset roots before launching long runs with the helper in
[data-and-configs](sub-skills/data-and-configs/SKILL.md), and use the planner in
[offline-slam](sub-skills/offline-slam/SKILL.md) when constructing commands for
custom configs.

## Shared references and scripts

- [Architecture](references/architecture.md) maps the CLI, config loader,
  dataset wrappers, frontend/backend, GUI, and evaluation flow.
- [Troubleshooting](references/troubleshooting.md) routes common failures to the
  right sub-skill.
- [Repository provenance](references/repo-provenance.md) records the source
  snapshot used to build this skill; read it before deciding whether a checkout
  needs `refresh-repo-skill`.
- [scripts/check_monogs_environment.py](scripts/check_monogs_environment.py)
  checks Python, CUDA, native extension imports, repo modules, and optional GUI
  or RealSense dependencies without running SLAM.

## Avoid this skill when

- The task is about generic 3D Gaussian Splatting training unrelated to MonoGS
  SLAM workflows.
- The user needs a CPU-only visual odometry or SLAM stack.
- The user asks to edit or maintain a different repository rather than use
  MonoGS workflows.

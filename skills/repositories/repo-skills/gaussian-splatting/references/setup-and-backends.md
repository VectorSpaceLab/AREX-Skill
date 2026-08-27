# Shared Setup and Backend Notes

## Purpose

This root reference gives quick, cross-cutting setup facts for future agents before they choose a sub-skill.

## Core Requirements

- Python optimizer/render/metrics workflows require CUDA-capable PyTorch and custom CUDA extensions.
- The official environment file uses Conda, Python 3.7.13, PyTorch 1.12.1, and CUDA toolkit 11.6.
- The README notes that newer PyTorch/CUDA environments can work, but extension builds must match the installed PyTorch and compiler/toolkit.
- The optimizer targets CUDA-ready GPUs with compute capability 7.0+ and recommends 24 GB VRAM for paper-quality training.
- The project is licensed for non-commercial research/evaluation use; check `LICENSE.md` in the source distribution before commercial use.

## Required Python Extension Modules

| Module | Role | Workflow impact |
|---|---|---|
| `diff_gaussian_rasterization` | differentiable rasterization and rendering | required for train/render |
| `simple_knn._C` | CUDA KNN distance for Gaussian initialization | required for training/model initialization |
| `fused_ssim` | faster SSIM loss | optional fallback exists for training, but useful for accelerated workflows |

## Setup Decision Tree

1. If the question is about installation, imports, CUDA, compilers, or extension builds, use `sub-skills/setup-and-backends/`.
2. If the question is about raw images, COLMAP layouts, Blender transforms, or depth maps, use `sub-skills/data-preparation/`.
3. If the question is about optimizer flags or model output from `train.py`, use `sub-skills/training/`.
4. If the question is about `render.py`, `metrics.py`, or `full_eval.py`, use `sub-skills/rendering-evaluation/`.
5. If the question is about SIBR remote or real-time viewers, use `sub-skills/viewers/`.

## Safe Diagnostics

Use the bundled root checker for a broad preflight:

```bash
python scripts/check_3dgs_environment.py --repo-root <checkout> --require-cuda --require-extensions --check-tools
```

This checker only imports modules, allocates a tiny CUDA tensor, and reports optional tool availability. It does not train, render, run COLMAP, or start SIBR.

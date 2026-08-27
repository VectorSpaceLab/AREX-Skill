---
name: gaussian-splatting
description: "Routes official 3D Gaussian Splatting setup, data preparation,
  training, rendering, evaluation, and viewer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Gaussian Splatting Repo Skill

Use this repo skill when the user needs to operate or troubleshoot the official GraphDeco/Inria `gaussian-splatting` implementation for 3D Gaussian Splatting: CUDA setup, COLMAP/Blender scene preparation, optimizer training, offline rendering/metrics, paper-style evaluation, or SIBR viewers.

## Start Here

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.
- Read [references/setup-and-backends.md](references/setup-and-backends.md) for a cross-cutting summary of Python/CUDA/submodule requirements.
- Read [references/troubleshooting.md](references/troubleshooting.md) when you need to route an error to the nearest troubleshooting page.
- Use [scripts/check_3dgs_environment.py](scripts/check_3dgs_environment.py) for a safe broad preflight. It does not run training, rendering, COLMAP, or SIBR.

## Route Map

| User task | Read |
|---|---|
| Install the repo, initialize submodules, build CUDA extensions, check PyTorch/CUDA, debug imports | [sub-skills/setup-and-backends/SKILL.md](sub-skills/setup-and-backends/SKILL.md) |
| Prepare images, validate COLMAP/Blender scene layouts, run conversion, create depth regularization files | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| Build or debug `train.py` commands, choose feature flags, resume checkpoints, handle OOM/debug/viewer training issues | [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md) |
| Run or diagnose `render.py`, `metrics.py`, pretrained model evaluation, `full_eval.py`, output/result JSON layouts | [sub-skills/rendering-evaluation/SKILL.md](sub-skills/rendering-evaluation/SKILL.md) |
| Build/run SIBR remote or real-time viewers, connect to optimizer, use top view, debug OpenGL/CUDA interop | [sub-skills/viewers/SKILL.md](sub-skills/viewers/SKILL.md) |

## Minimal Preconditions

The core Python workflows require:

- a CUDA-capable NVIDIA GPU for real train/render/metrics execution,
- PyTorch with CUDA support,
- built/importable `diff_gaussian_rasterization` and `simple_knn` extensions,
- a prepared COLMAP or Blender/NeRF synthetic scene for training,
- a trained model directory for rendering/evaluation.

A CPU-only environment can run validators and command builders, but it does not verify the core optimizer or renderer.

## Safe Preflight

For an editable checkout or source tree, run:

```bash
python scripts/check_3dgs_environment.py --repo-root <checkout> --require-cuda --require-extensions --check-tools
```

If this fails on CUDA or extensions, route to setup/backends before training or rendering. Missing `colmap`, `magick`, or SIBR binaries matters only for conversion or viewer tasks.

## Common Workflow Chain

1. Setup/backend: prove CUDA and extensions.
2. Data preparation: validate `<scene>` and optional depth files.
3. Training: run `train.py -s <scene> -m <model> --eval --disable_viewer` or a tailored variant.
4. Rendering/evaluation: run `render.py -m <model>` and `metrics.py -m <model>`.
5. Viewer: run a SIBR real-time viewer with `-m <model>` or connect a remote viewer to an optimizer.

## Boundaries and Warnings

- Do not run full training, full evaluation, dataset downloads, pretrained model downloads, COLMAP conversion, or SIBR builds as implicit smoke checks; ask for explicit compute/time/network approval.
- Do not tell users that CPU validation proves CUDA training/rendering.
- Do not rely on original repository docs or scripts at runtime when a bundled reference/script covers the needed operation.
- Respect the repository's non-commercial research/evaluation license terms.

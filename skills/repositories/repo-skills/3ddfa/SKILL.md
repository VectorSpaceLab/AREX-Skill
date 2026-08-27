---
name: 3ddfa
description: "Guide 3DDFA Python inference, geometry rendering,
  training/evaluation, and optional C++ ONNX workflows for 3D dense face
  alignment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# 3DDFA Repo Skill

Use this repo skill when a task involves 3DDFA / 3D Dense Face Alignment: face alignment in full pose range, 68-point landmark prediction, dense 3D face vertices, pose boxes, PLY/OBJ export, depth/PNCC/PAF outputs, MobileNet-V1 checkpoints, 3DDFA training/evaluation, or the optional C++ OpenCV DNN port.

This skill is an operating guide for a 3DDFA checkout or adapted codebase. It is self-contained: use the references and bundled scripts here for routing, command construction, diagnostics, and troubleshooting instead of reopening the original repository documentation.

## First Checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a checkout.
2. Read [references/install-and-compatibility.md](references/install-and-compatibility.md) before installing dependencies or choosing CPU/CUDA/dlib/Cython paths.
3. Run [scripts/check_3ddfa_environment.py](scripts/check_3ddfa_environment.py) against the target checkout for a safe import/resource diagnostic.
4. If the task names a concrete workflow, route to the matching sub-skill below.

Minimal diagnostic from this skill root:

```bash
python scripts/check_3ddfa_environment.py --repo-root /path/to/3DDFA
```

The diagnostic checks resources and imports; it does not run native inference, training, downloads, CMake builds, or benchmarks.

## Route Map

| User task or signal | Read |
|---|---|
| Run still-image inference, no-dlib bbox inference, inspect `main.py` flags, diagnose dlib/Cython startup, verify MobileNet forward shape, understand output filenames | [sub-skills/python-inference/SKILL.md](sub-skills/python-inference/SKILL.md) |
| Decode 62-D parameters, ROI boxes, sparse/dense vertices, PLY/OBJ/`.mat`, pose matrices, depth/PNCC/PAF, Cython renderer, BFM/3DMM data artifacts, video-frame rendering | [sub-skills/geometry-rendering/SKILL.md](sub-skills/geometry-rendering/SKILL.md) |
| Adapt training commands, choose WPDC/VDC/PDC, validate filelists/param files/data roots, resume checkpoints, interpret AFLW/AFLW2000 metrics | [sub-skills/training-evaluation/SKILL.md](sub-skills/training-evaluation/SKILL.md) |
| Export MobileNet checkpoint to ONNX, place C++ weights, build/run OpenCV DNN demo, debug CMake/OpenCV/Yolo/ONNX issues | [sub-skills/cpp-onnx-port/SKILL.md](sub-skills/cpp-onnx-port/SKILL.md) |
| Cross-cutting install/import/runtime failure | [references/troubleshooting.md](references/troubleshooting.md) |

## Operating Boundaries

- Prefer CPU-safe diagnostics first. CUDA training/evaluation and GPU inference are optional capability paths and must be verified separately.
- The unmodified Python image CLI imports `dlib` and render utilities before argument parsing. Even bbox-only workflows can fail at startup if Python `dlib` or the Cython render extension is missing.
- Depth and PNCC require the compiled Cython mesh core; PLY/OBJ/landmarks can be planned separately, but the native CLI import path may still require the extension unless wrapped or patched.
- Full training, benchmark extraction, and the C++ demo depend on external datasets, optional weights, system packages, or GPUs. Treat these as explicit prerequisites, not default verification steps.
- Do not use this skill for 3DDFA_V2 unless the user explicitly asks to port concepts; this skill is based on the legacy 3DDFA repository snapshot in the provenance reference.

## Bundled Scripts

- [scripts/check_3ddfa_environment.py](scripts/check_3ddfa_environment.py) — shared checkout/resource/import diagnostic.
- [sub-skills/python-inference/scripts/inspect_3ddfa_inference.py](sub-skills/python-inference/scripts/inspect_3ddfa_inference.py) — image/video inference-specific diagnostic and command planner.
- [sub-skills/python-inference/scripts/smoke_mobilenet_forward.py](sub-skills/python-inference/scripts/smoke_mobilenet_forward.py) — safe MobileNet architecture forward smoke.
- [sub-skills/geometry-rendering/scripts/smoke_geometry.py](sub-skills/geometry-rendering/scripts/smoke_geometry.py) — safe 3DMM reconstruction shape smoke.
- [sub-skills/training-evaluation/scripts/validate_training_args.py](sub-skills/training-evaluation/scripts/validate_training_args.py) — training command/data-layout checker that does not launch training.
- [sub-skills/cpp-onnx-port/scripts/export_mobilenet_to_onnx.py](sub-skills/cpp-onnx-port/scripts/export_mobilenet_to_onnx.py) — explicit ONNX export helper for the optional C++ port.

## Verification Expectations

Safe verification usually includes:

- package/import/resource diagnostics;
- MobileNet CPU forward shape `(1, 62)`;
- geometry reconstruction shapes `(3, 68)` and dense `(3, 53215)`;
- script `--help` checks for bundled helpers;
- explicit skip notes for dlib predictor, Cython build, CUDA, external datasets, and OpenCV C++ demo when unavailable.

Do not claim native end-to-end inference, GPU training/evaluation, full benchmarks, or C++ runtime success unless those exact paths were run in the target environment.

---
name: face-evolve
description: "Use face.evoLVe for high-performance face recognition workflows
  across alignment, data preparation, PyTorch training, feature verification,
  and Paddle deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# face-evolve

Use this repo skill when the task involves face.evoLVe, a source-style face recognition library with PyTorch and PaddlePaddle workflows for face alignment, identity-folder data preparation, backbone/head/loss training, feature extraction, verification metrics, quantization, and deployment demos.

This skill is for operating or adapting face.evoLVe workflows. It is not a generic face-recognition tutorial and it is not a full replacement for trained checkpoints, public datasets, Paddle export artifacts, or accelerator runtimes.

## First read

- Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout or should be refreshed.
- Read `references/quickstart-and-environment.md` for install/import expectations, source-style checkout behavior, optional dependency groups, and safe smoke checks.
- Read `references/troubleshooting.md` when imports, source entrypoints, optional dependencies, data paths, or backend assumptions fail.
- Run `scripts/check_face_evolve_env.py` for a lightweight dependency and optional checkout sanity check before launching training, extraction, or Paddle workflows.

## Route by task

- Use `sub-skills/face-alignment/SKILL.md` for MTCNN detection, landmark localization, affine face crops, batch alignment, crop-size scaling, and resize-before-align preprocessing.
- Use `sub-skills/data-preparation/SKILL.md` for ImageFolder identity-folder validation, low-shot class pruning, hidden-file cleanup, validation `bcolz`/`_list.npy` layouts, and public data/model zoo constraints.
- Use `sub-skills/pytorch-training/SKILL.md` for PyTorch config editing, IR/IR-SE/ResNet backbone construction, ArcFace/CosFace/SphereFace/Am_softmax heads, Focal/Softmax losses, training/validation/checkpoints, and legacy source repair.
- Use `sub-skills/feature-extraction-verification/SKILL.md` for extracting embeddings from PyTorch checkpoints, v1/v2 preprocessing, horizontal-flip TTA, l2 normalization, ROC/threshold verification, and pair-array validation.
- Use `sub-skills/paddle-workflows/SKILL.md` for PaddlePaddle training, PaddleSlim quantization, Paddle Inference demos, Paddle Lite demos, and Paddle import-shadowing/deployment artifact checks.

## Operating defaults

- Treat face.evoLVe as a source checkout, not a normal pip-installable distribution: place the target checkout on `PYTHONPATH` only for the relevant framework path and prefer the bundled helper scripts when available.
- Prefer CPU-only smoke checks for planning and debugging. Full PyTorch/Paddle training and deployment require external datasets, trained/exported models, and often CUDA or edge runtimes.
- For PyTorch model work, start with README-supported combinations: `IR_50` or `IR_SE_50`, `ArcFace`, `Focal`, `INPUT_SIZE=[112,112]`, and 512-dimensional embeddings.
- For Paddle work, avoid putting the repository root on `PYTHONPATH` before importing PaddlePaddle because the repo has a top-level `paddle/` source directory.
- Validate identity-folder data before pruning, training, or extracting features; hidden files and empty/low-shot classes are common failure sources.

## Do not do by default

- Do not run full training, public dataset downloads, model-zoo downloads, quantization, Paddle Inference video demos, or Paddle Lite edge demos unless the user supplies the required artifacts and accepts runtime cost/hardware needs.
- Do not rely on the original construction checkout path. If a bundled script asks for `--repo-root`, pass the user's target face.evoLVe checkout explicitly.
- Do not claim CUDA, Paddle Inference, Paddle Lite, or quantization verification from a CPU import smoke.

---
name: pytorch-training
description: "Routes Distil-Whisper pseudo-labelling, student initialization,
  distillation, and evaluation workflows in the PyTorch stack."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Training

## Purpose

Use this sub-skill when the user wants to generate pseudo-labels, initialize a student Whisper model, run teacher-student distillation, or evaluate the PyTorch training scripts under `training/`.

## Include here

- Pseudo-labelling with `training/run_pseudo_labelling.py`.
- Student initialization with `training/create_student_model.py`.
- Distillation with `training/run_distillation.py`.
- Evaluation with `training/run_eval.py`.
- Dataset mixing, WER filtering, Hub pushes, and Accelerate-driven launch patterns.

## Exclude or route elsewhere

- Direct checkpoint inference belongs in `inference`.
- JAX/Flax reproduction belongs in `flax-reproduction`.
- TPU-specific conversion helpers belong in `flax-reproduction` unless the user explicitly wants the PyTorch stack only.

## Read next

- `references/workflows.md` for the full PyTorch training flow.
- `references/troubleshooting.md` for dataset, Hub, and training-config failures.
- `../../references/model-overview.md` for checkpoint choices that affect student initialization.
- `../../scripts/check-env.py` before importing the stack.
- `scripts/create_student_model.py` when the user wants a bundled initialization helper.

## How to route

- "Pseudo-label this dataset" -> start here.
- "Initialize a smaller Whisper student" -> start here.
- "Train the distilled model" -> start here.
- "Run evaluation / compute WER" -> start here.

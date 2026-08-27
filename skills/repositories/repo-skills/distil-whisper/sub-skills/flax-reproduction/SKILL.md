---
name: flax-reproduction
description: "Routes Distil-Whisper JAX/Flax reproduction, long-form evaluation,
  and conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Flax Reproduction

## Purpose

Use this sub-skill when the user wants the original JAX/Flax Distil-Whisper package, the Flax pipeline, long-form transcription, checkpoint conversion, or the TPU/GPU-oriented reproduction flow under `training/flax/`.

## Include here

- The `distil_whisper` package under `training/flax/distil_whisper`.
- Flax student initialization.
- Flax evaluation and long-form transcription.
- Checkpoint conversion from a Flax training state to Hugging Face weights.
- JAX/Flax workflow notes, including scan weights, TPU-oriented settings, and the Flax pipeline.

## Exclude or route elsewhere

- Direct Transformers inference belongs in `inference`.
- PyTorch pseudo-labelling, training, and evaluation belong in `pytorch-training`.
- Benchmark-only or hardcoded local debug scripts are not the default route unless the user explicitly asks about them.

## Read next

- `references/workflows.md` for Flax initialization, evaluation, long-form, and conversion recipes.
- `references/troubleshooting.md` for JAX, SciPy, NumPy, and distributed-init failures.
- `../../references/model-overview.md` for checkpoint selection context.
- `../../scripts/check-env.py` before importing the package or launching a script.
- `scripts/create_student_model.py` for a bundled initialization helper.
- `scripts/convert_train_state_to_hf.py` for the bundled conversion/export helper.

## How to route

- "How do I reproduce the original Flax workflow?" -> start here.
- "How do I use FlaxWhisperPipeline?" -> start here.
- "How do I convert a JAX training state to HF weights?" -> start here.
- "How do I run long-form transcription in the Flax stack?" -> start here.

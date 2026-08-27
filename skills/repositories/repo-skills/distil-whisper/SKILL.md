---
name: distil-whisper
description: "Routes Distil-Whisper inference, PyTorch distillation training,
  and Flax reproduction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Distil-Whisper

## Purpose

Use this skill when the user wants to transcribe audio with Distil-Whisper, choose or compare checkpoints, run the PyTorch distillation stack under `training/`, or reproduce the original JAX/Flax stack under `training/flax/`.

## First stop

- Read `references/model-overview.md` to choose a checkpoint and decode path.
- Run `scripts/check-env.py` to verify the CPU inspection stack before deeper work.
- Read `references/repo-provenance.md` when deciding whether this skill still matches the current checkout.

## Route map

- `sub-skills/inference/SKILL.md` for checkpoint usage, short-form transcription, long-form transcription, speculative decoding, and inference-speed trade-offs.
- `sub-skills/pytorch-training/SKILL.md` for pseudo-labelling, student initialization, distillation training, evaluation, and dataset mixing in the PyTorch stack.
- `sub-skills/flax-reproduction/SKILL.md` for the JAX/Flax package, conversion helpers, long-form transcription, and original reproduction workflows.

## Install notes

This repo has two practical dependency surfaces:

- The Flax package under `training/flax/`.
- The PyTorch training scripts under `training/`.

For a local checkout, install the Flax package in editable mode and then add the PyTorch training dependencies from the root `training/` metadata. The verified inspection environment used a single CPU prefix with Python 3.11, a CPU-only torch wheel, JAX 0.4.18, Flax 0.7.2, SciPy 1.11.4, and the core Hugging Face audio stack. See `references/repo-provenance.md` for the exact verified versions.

## Minimal smoke

1. `python scripts/check-env.py`
2. `python -m pip check`
3. Read the relevant sub-skill before running a workflow command.

## Runtime boundaries

- Do not tell future agents to open or run files from the original repository checkout when a bundled reference or script exists.
- Do not treat benchmark-only or TPU-host-specific helpers as default user workflows.
- Keep training-scale runs, model downloads, and Hub pushes in the route-specific references unless the user explicitly wants to perform them.

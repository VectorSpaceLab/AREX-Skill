---
name: finetuning-data-prep
description: "Prepare and validate MOSS-TTS fine-tuning JSONL data and launch
  supervised fine-tuning runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# finetuning-data-prep

Use this sub-skill when the task is about preparing training JSONL, codec preprocessing, supervised fine-tuning launch planning, or first checkpoint smoke checks for MOSS-TTS Delay, Local, Local Transformer v1.5, Realtime, TTSD, SoundEffect v1, or VoiceGenerator workflows.

## Use this for

- Choosing a raw JSONL schema for TTS, voice cloning, multi-speaker TTSD, SoundEffect v1, VoiceGenerator, or Realtime conversation fine-tuning.
- Validating raw or prepared JSONL before expensive codec preprocessing or `accelerate launch` training.
- Running or modifying the repository fine-tuning helpers: `prepare_data.py`, `sft.py`, `run_train.sh`, Accelerate DDP/FSDP/DeepSpeed configs, and sharded JSONL outputs.
- Planning batch size, gradient accumulation, mixed precision, loss weighting, `n_vq`, and single-node or multi-node launch shapes.
- Diagnosing data-preparation and training-launch failures before handing generation/inference work to an inference sub-skill.

## Route elsewhere

- SoundEffect v2 DiT fine-tuning, diffusion-specific manifests, or DiT checkpoint issues: `../soundeffect-v2/SKILL.md`.
- llama.cpp conversion, quantization, backend evaluation, or GGUF runtime checks: `../llama-cpp-backend/SKILL.md`.
- Full inference after training belongs to the owning inference sub-skill for the selected model family. This sub-skill only covers a quick post-finetune smoke check that verifies a checkpoint can generate a short WAV.
- Generic Hugging Face model-family selection and non-training prompts: `../hf-family-workflows/SKILL.md`.

## Operating sequence

1. Pick the task id and model family from `references/data-formats.md`.
2. Validate the raw or prepared JSONL with `scripts/validate_training_jsonl.py` before launching codec or model work.
3. Preprocess raw audio into `audio_codes` or conversation-turn codes using `references/preprocessing.md`.
4. Launch training with `references/training-launches.md`; use the bundled troubleshooting reference if ranks, shards, `n_vq`, memory, or reference-audio fields fail.
5. After a checkpoint is saved, perform only a short smoke inference with the matching inference workflow, then route any deeper generation/evaluation request to the owning inference sub-skill.

## Bundled references and tools

- JSONL schemas and task-specific required fields: `references/data-formats.md`.
- Codec preprocessing, reference-code handling, sharding, and validator usage: `references/preprocessing.md`.
- `accelerate`, FSDP, DeepSpeed, `run_train.sh`, and hyperparameter launch patterns: `references/training-launches.md`.
- Known failure modes and recovery actions: `references/troubleshooting.md`.
- No-model JSONL checker: `scripts/validate_training_jsonl.py`.

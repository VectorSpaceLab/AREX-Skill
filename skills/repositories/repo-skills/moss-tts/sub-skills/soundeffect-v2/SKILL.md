---
name: soundeffect-v2
description: "Operate MOSS-SoundEffect v2 DiT/DAC/Qwen3 inference, demo,
  fine-tuning metadata, and checkpoint export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# soundeffect-v2

Use this sub-skill for MOSS-SoundEffect v2.0 workflows: the separate text-to-audio diffusion package built from a DiT backbone, Flow Matching scheduler behavior, DAC VAE audio representation, and Qwen3 text encoder. It covers isolated environment setup, pipeline inference, audio saving, Gradio launch parameters, fine-tuning metadata validation, and export of fine-tuned DiT checkpoints into a loadable Hugging Face-style directory.

## Best-fit requests

- Generate environmental or sound-effect audio with `MossSoundEffectPipeline`.
- Choose `seconds`, diffusion steps, CFG scale, sigma shift, dtype, seed, device, and output path for SoundEffect v2 inference.
- Recover from TorchDynamo/Triton compile failures or first-call compilation issues in the v2 pipeline.
- Launch or adapt the SoundEffect v2 Gradio demo using `SOUNDEFFECT_MODEL_DIR` and device settings.
- Prepare JSONL metadata for SoundEffect v2 DiT fine-tuning with required `audio` and `prompt` fields.
- Validate SoundEffect v2 metadata without importing torch or loading a model.
- Fine-tune the v2 DiT from an existing Hugging Face model directory or repo id, then export the resulting checkpoint for pipeline loading.

## Route elsewhere

- MOSS-SoundEffect v1 or any Delay-family autoregressive sound-effect workflow: `../hf-family-workflows/SKILL.md`.
- Delay-family fine-tuning data preparation, `audio_codes`, or generic MOSS-TTS training data: `../finetuning-data-prep/SKILL.md`.
- Generic MOSS-TTS voice cloning, continuation, multilingual TTS, voice generation, or dialogue TTS: `../hf-family-workflows/SKILL.md`.

## Operating map

1. Start with `references/pipeline-and-finetune.md` for setup, inference, Gradio, fine-tuning, and export workflows.
2. Use `references/api-reference.md` for exact package pins, pipeline signatures, CLI-style variables, metadata schema, training/export arguments, and outputs.
3. Use `references/troubleshooting.md` when dependency conflicts, model cache/downloads, compile errors, CUDA memory, long runs, metadata errors, export failures, or Gradio launch issues appear.
4. Use `scripts/validate_soundeffect_metadata.py` before launching training. It is stdlib-only and checks JSONL structure plus optional audio-path existence.

## Quick safeguards

- Create a clean Python 3.12+ environment for this package. Do not reuse the top-level MOSS-TTS environment.
- Install PyTorch CUDA 12.8 wheels through the PyTorch index when using the `torch-cu128` extra.
- For inference, prefer CUDA with `torch.bfloat16`; CPU fallback exists but can be too slow for practical generation.
- Set `TORCHDYNAMO_DISABLE=1` before Python if TorchDynamo, Triton, or CUDA Graph compilation fails.
- Keep `seconds` within the model limit, normally 30 seconds, and keep `num_inference_steps` bounded for smoke tests.
- Validate fine-tuning metadata before launching `accelerate`; each JSONL row must include non-empty `audio` and `prompt` strings.
- During export, provide a valid `SOURCE_HF_DIR` containing the frozen `vae`, `text_encoder`, `tokenizer`, and `scheduler` subdirectories.

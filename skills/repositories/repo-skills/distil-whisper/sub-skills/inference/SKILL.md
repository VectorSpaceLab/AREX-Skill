---
name: inference
description: "Routes Distil-Whisper checkpoint usage, transcription, and
  inference-speed workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference

## Purpose

Use this sub-skill when the user wants to transcribe audio with a Distil-Whisper checkpoint, compare short-form versus long-form decoding, enable speculative decoding, or choose an inference-speed trade-off.

## Include here

- Transformers-based transcription with `AutoModelForSpeechSeq2Seq`, `AutoProcessor`, and `pipeline`.
- Short-form transcription for clips under 30 seconds.
- Sequential and chunked long-form transcription.
- Speculative decoding with an assistant model.
- Flash Attention 2 and SDPA guidance when the user wants a speed/memory tweak.
- Checkpoint selection guidance for `distil-large-v3`, `distil-small.en`, and the legacy checkpoints.

## Exclude or route elsewhere

- Pseudo-labelling, student initialization, distillation training, and evaluation belong in `pytorch-training`.
- JAX/Flax pipeline and conversion workflows belong in `flax-reproduction`.

## Read next

- `references/workflows.md` for copyable inference recipes.
- `references/troubleshooting.md` for model download, backend, and decode errors.
- `../../references/model-overview.md` when you need checkpoint selection context.
- `../../scripts/check-env.py` for a quick environment sanity check before loading a model.

## How to route

- "How do I transcribe this audio?" -> start here.
- "Should I use chunked or sequential long form?" -> start here.
- "Can Distil-Whisper act as Whisper's assistant model?" -> start here.
- "Which checkpoint should I use on a small device?" -> start here.

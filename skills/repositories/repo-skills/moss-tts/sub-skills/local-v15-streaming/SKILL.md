---
name: local-v15-streaming
description: "Operate MOSS-TTS Local Transformer v1.5 batch and realtime
  streaming decode workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# local-v15-streaming

Use this sub-skill when the task is about **MOSS-TTS-Local-Transformer-v1.5** local batch inference, realtime streaming decode, browser streaming app operation, 48 kHz stereo codec-v2 audio, device/dtype split, token or duration estimates, continuation prompts, or voice-clone prompts.

## Route elsewhere

- MOSS-TTS-Realtime voice-agent model, realtime conversation, or live voice-agent serving: `../realtime-voice-agent/SKILL.md`.
- Generic Hugging Face family prompts, non-v1.5 model-family usage, or router-level model choice: `../hf-family-workflows/SKILL.md`.
- Fine-tuning, dataset preparation, manifests, or training local v1.5: `../finetuning-data-prep/SKILL.md`.
- SoundEffect v2 generation or diffusion sound-effect workflows: `../soundeffect-v2/SKILL.md`.

## Minimum operating facts

- Checkpoint: `OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5`.
- Codec/tokenizer: `OpenMOSS-Team/MOSS-Audio-Tokenizer-v2`.
- Audio format: 48 kHz stereo; decoded tensors are normally `[2, samples]`.
- Frame topology: 12.5 frames/sec, 12 RVQ layers, time-synchronous local-transformer frames.
- Backbone: Qwen3-4B-derived local transformer release.
- Default audio sampling for the app: temperature `1.7`, top-p `0.8`, top-k `25`, repetition penalty `1.0`.

## Use the bundled references

- Batch inference, web streaming launch, mode semantics, and prompt patterns: `references/batch-and-streaming.md`.
- Python/CLI/app API fields and event contracts: `references/api-reference.md`.
- Failure modes and fixes: `references/troubleshooting.md`.
- Safe no-model estimate helper: `scripts/estimate_local_v15_tokens.py`.

Before claiming a v1.5 workflow is correct, verify that the runtime reports the expected sample rate (`48000`), RVQ depth (`12`), and stereo channel count, and that final output includes a WAV, audio-token dump, and metadata JSON in the configured output location.

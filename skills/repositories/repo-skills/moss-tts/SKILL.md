---
name: moss-tts
description: "Route MOSS-TTS family speech, voice-agent, sound-effect,
  llama.cpp, streaming, and fine-tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MOSS-TTS

Use this repo skill when a task names **MOSS-TTS**, **OpenMOSS/MOSS-TTS**, **MOSS-TTS-v1.5**, **MOSS-TTSD**, **MOSS-VoiceGenerator**, **MOSS-TTS-Realtime**, **MOSS-TTS-Local-Transformer-v1.5**, **MOSS-SoundEffect**, `MossTTSDelay`, `MossTTSLocal`, `moss-tts-llama-cpp`, GGUF/ONNX/TensorRT audio-tokenizer inference, or MOSS-TTS fine-tuning JSONL.

This skill teaches how to operate the model-family workflows. It does not execute long model downloads, generation, training, service startup, benchmark runs, TensorRT builds, or GPU performance checks by default.

## First route by task

| User intent | Read next |
|---|---|
| Hugging Face `AutoProcessor`/`AutoModel` generation, voice cloning, duration control, language tags, Pinyin/IPA, MOSS-TTSD, MOSS-VoiceGenerator, SoundEffect v1, or Gradio-style model-family demos | `sub-skills/hf-family-workflows/SKILL.md` |
| Torch-free, low-memory, GGUF, ONNX, TensorRT, `moss-tts-llama-cpp`, config YAML, bridge build, weight conversion, or batch eval | `sub-skills/llama-cpp-backend/SKILL.md` |
| MOSS-TTS-Local-Transformer-v1.5 batch or realtime streaming decode, 48 kHz stereo, codec v2, browser streaming app, or token/frame estimates | `sub-skills/local-v15-streaming/SKILL.md` |
| MOSS-TTS-Realtime voice-agent sessions, streaming text deltas, FastAPI service, client payloads, KV-cache reuse, or prompt-audio context | `sub-skills/realtime-voice-agent/SKILL.md` |
| Fine-tuning manifests, JSONL schema, `audio_codes`, preprocessing, `accelerate`, FSDP, ZeRO-3, sharded outputs, or post-training smoke plans | `sub-skills/finetuning-data-prep/SKILL.md` |
| MOSS-SoundEffect v2 DiT/DAC/Qwen3 pipeline, separate environment, `MossSoundEffectPipeline`, sound-effect fine-tuning metadata, or export to HF format | `sub-skills/soundeffect-v2/SKILL.md` |

If the user only says “generate speech with MOSS-TTS,” start with `hf-family-workflows`. If the user says “no PyTorch,” “GGUF,” “low memory,” or “llama.cpp,” route to `llama-cpp-backend`. If the user says “Realtime” with voice-agent turns, route to `realtime-voice-agent`, not Local v1.5 streaming.

## Read root references when needed

- `references/model-family-overview.md` — model/checkpoint/architecture map, audio-format differences, and scenario boundaries.
- `references/installation-profiles.md` — dependency profiles, extras, Python/CUDA/FFmpeg notes, and the package exposure caveat.
- `references/troubleshooting.md` — cross-cutting install/import, backend, model download, audio, and packaging failures before routing deeper.
- `references/repo-provenance.md` — source snapshot and refresh baseline.
- `references/repo-routing-metadata.json` — structured router metadata used by managed repo-skill importers.
- `scripts/check_moss_tts_environment.py` — safe diagnostic helper for metadata/import/optional dependency checks; run it before blaming model code.

## Installation triage

Use a clean Python 3.12 environment for most MOSS-TTS workflows. Choose the smallest profile that matches the task:

- **HF generation / Gradio demos**: install the top-level package with `torch-runtime`; choose a PyTorch wheel index matching the host backend. FFmpeg is required by `torchcodec` audio I/O.
- **FlashAttention**: add `flash-attn` only when CUDA, GPU architecture, dtype, and build memory support it. Otherwise use SDPA on CUDA or eager on CPU.
- **llama.cpp backend**: use `llama-cpp` profiles instead of the full torch runtime; add ONNX, TensorRT, or Torch heads only when that backend is selected.
- **Fine-tuning**: add `finetune`; add `finetune-deepspeed` only for ZeRO-3.
- **SoundEffect v2**: use its separate package/environment; it pins a different NumPy/Transformers/Diffusers/Torch stack and should not be mixed with the root MOSS-TTS runtime.

Minimal diagnostic command from this root skill directory:

```bash
python scripts/check_moss_tts_environment.py --json
```

If metadata is installed but imports such as `moss_tts_delay` fail, read `references/installation-profiles.md` and `sub-skills/hf-family-workflows/references/model-packaging.md`; the current package metadata may require running from a source checkout, adding the checkout to `PYTHONPATH`, or using a packaging layout that explicitly exposes source packages.

## Safety and verification boundaries

- Do not treat a CPU import as proof that CUDA generation, FlashAttention, TensorRT, or training works.
- Do not run long generation, model downloads, service listeners, training jobs, or benchmark batches unless the user explicitly authorizes time, network, disk, and hardware use.
- Prefer bundled validators and config inspectors for cheap checks before expensive runtime work.
- Keep model family and code family aligned: Delay, Local 1.0, Local v1.5, TTSD, VoiceGenerator, SoundEffect v1, Realtime, and SoundEffect v2 have different prompt/code/tokenizer assumptions.
- For any current repository checkout whose commit or public APIs differ from `references/repo-provenance.md`, run `refresh-repo-skill` before relying on this skill for exact flags or compatibility rules.

---
name: hf-family-workflows
description: "Operate Hugging Face remote-code and Gradio-style workflows for
  MOSS-TTS family models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# hf-family-workflows

Use this sub-skill when the task is to run, adapt, or debug the Hugging Face `AutoProcessor`/`AutoModel` remote-code workflows or the Gradio-style UI parameters for the MOSS-TTS family.

## Best-fit requests

- MOSS-TTS-v1.5 or MOSS-TTS 1.0 direct TTS, voice cloning, continuation, duration control, language tags, Pinyin, IPA, or `[pause X.Ys]` prompt control.
- MOSS-TTSD-v1.0 multi-speaker dialogue generation with `[S1]`...`[S5]` tags and per-speaker reference audio.
- MOSS-VoiceGenerator text + natural-language voice-instruction prompts.
- MOSS-SoundEffect v1 text-to-sound prompts through the Delay-family Hugging Face API.
- Choosing between Delay and Local architectures for non-streaming Hugging Face generation.
- Selecting `attn_implementation`, dtype/device, model ID, codec path, sampling parameters, or Gradio launch flags.
- Normalizing prompt text before sending it to `build_user_message`.
- Diagnosing import, package exposure, model download/cache, remote-code, reference-audio, or mixed checkpoint/code failures.

## Route elsewhere

- Torch-free / low-memory llama.cpp, GGUF, ONNX, or TensorRT backend: `../llama-cpp-backend/SKILL.md`.
- MOSS-TTS-Local-Transformer-v1.5 realtime streaming app or streaming decode internals: `../local-v15-streaming/SKILL.md`.
- MOSS-TTS-Realtime voice-agent, FastAPI, SSE, or multi-turn streaming sessions: `../realtime-voice-agent/SKILL.md`.
- Fine-tuning, data JSONL construction, `audio_codes`, training launchers, or post-finetune checks: `../finetuning-data-prep/SKILL.md`.
- MOSS-SoundEffect-v2.0 DiT/Flow-Matching pipeline: `../soundeffect-v2/SKILL.md`.

## Operating map

1. Start with `references/hf-generation-workflows.md` for concrete generation recipes, model IDs, Gradio-style flags, and prompt patterns.
2. Use `references/api-reference.md` when you need exact `build_user_message`, conversation shape, processor modes, audio-code, and hyperparameter contracts.
3. Use `references/model-packaging.md` before changing model/code/codec packaging, using fused checkpoint layouts, or diagnosing package exposure.
4. Use `references/troubleshooting.md` for known failure signatures and fixes.
5. Use `scripts/normalize_tts_text.py` for safe stdlib-only prompt cleanup; it can run from any current working directory.

## Quick safeguards

- Always pass `trust_remote_code=True` for Hugging Face `AutoProcessor` and `AutoModel` loads.
- Prefer CUDA + `bfloat16` for 8B models. CPU can load only in very constrained smoke tests and is usually impractical for generation.
- Keep model code, config, `n_vq`, tokenizer, and audio codec matched. Mixed Delay/Local/TTSD/VoiceGenerator code and checkpoints often produce shape errors or gibberish.
- For v1.5 multilingual prompts, set the language field when known; for continuation, prepend the reference transcript to the text.
- Do not use this skill as proof that model download or full generation succeeded in the target runtime; those are runtime prerequisites to verify where the model will actually run.

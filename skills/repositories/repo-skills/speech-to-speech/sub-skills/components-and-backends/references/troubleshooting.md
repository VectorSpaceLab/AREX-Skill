# Component and backend troubleshooting

## Optional dependency import errors

Registry-backed optional dependencies raise actionable messages such as:

```text
Backend 'faster-whisper' (stt) requires optional dependencies. Install them with `pip install "speech-to-speech[faster-whisper]"`.
```

Install only the named extra for the selected backend. If an optional native
library fails with a `RuntimeError` during import, treat it like a missing native
dependency and inspect the platform wheel, Python version, and accelerator
runtime.

## Qwen3-TTS Linux CUDA/GGML failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import/load error mentioning `qwentts-cpp-python` or CUDA shared libraries | Wheel does not match the CUDA runtime | Install the matching `qwentts-cpp-python` wheel variant (`cu124`, `cu128`, `cu130`, or `cpu`) before reinstalling/starting `speech-to-speech`. |
| GGUF local load fails | Talker and codec paths are not both provided or model family mismatches files | Provide both `--qwen3_tts_gguf_talker_path` and `--qwen3_tts_gguf_codec_path`, and align `--qwen3_tts_model_name` with Base, CustomVoice, or VoiceDesign. |
| Voice clone ignores cached reference | Raw reference and cached `.spk`/`.rvq` options conflict | Use either raw `--qwen3_tts_ref_audio` or precomputed references. `.rvq` requires `.spk` and reference text. |
| Very long utterances truncate | Token cap too low for text length | Increase `--qwen3_tts_max_new_tokens` cautiously or shorten responses via prompt instructions. |

## Apple Silicon/MLX issues

- Use `--mac-optimal-settings` for defaults, but remember explicit flags win.
- MLX quantization suffixes are `bf16`, `4bit`, `6bit`, and `8bit`.
- Linux cannot verify Apple Silicon MPS recipes; record them as reference-only
  unless running on a Mac.
- If llama.cpp native audio reports `unknown projector type: gemma4uv`, upgrade
  llama.cpp before changing the speech pipeline.

## Direct audio-input failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--stt none` rejected with `responses-api` | Direct audio bypass requires audio-input LLM backend | Use `--llm_backend chat-completions`. |
| Provider rejects audio payload | Wrong `responses_api_audio_content_type` or non-audio model | Pick an explicitly audio-capable `--model_name` and test `input_audio` versus `audio_url` according to provider support. |
| Audio history grows too large | Completed audio turns remain in chat history | Lower `--responses_api_audio_history_turns`; old turns become role-preserving placeholders. |

## Language and voice problems

- Wrong response language: set a fixed STT language when possible, or enable
  `--enable_lang_prompt` so the LLM receives a language instruction.
- Wrong TTS language: verify Qwen3 alias normalization and that the selected TTS
  supports the detected language. MMS and Kokoro have their own language/voice
  mappings.
- Unsupported language fallback: Whisper-family handlers keep the last known
  supported language if detection yields an unsupported code; avoid relying on
  unsupported language auto-detection for production.

## Model downloads and offline mode

- First runs may download Silero VAD, STT, LLM, TTS, Smart Turn, NLTK, or Qwen
  reference assets.
- Warm exact model selections online before setting offline flags.
- The default remote Responses API profile is not offline.
- If a Smart Turn checkpoint is missing, provide a local path or disable Smart
  Turn for the target run.

## DeepFilterNet and dependency conflicts

DeepFilterNet is optional for audio enhancement and may require `numpy<2`, while
Pocket TTS requires newer NumPy. Do not combine them in one environment unless
you have resolved the dependency constraints. Keep audio enhancement optional
when Pocket TTS is selected.

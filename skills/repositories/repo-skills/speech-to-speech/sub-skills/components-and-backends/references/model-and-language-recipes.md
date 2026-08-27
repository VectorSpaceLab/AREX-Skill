# Model and language recipes

## Default hosted LLM plus local STT/TTS

The shortest supported startup is:

```bash
export OPENAI_API_KEY="..."
speech-to-speech serve
```

This keeps STT and TTS local while sending the LLM request through the default
Responses API profile. Override `--model_name`, `--responses_api_base_url`, and
`--responses_api_api_key` for another OpenAI-compatible provider.

## Local OpenAI-compatible LLM server

Run a provider-compatible server such as llama.cpp or vLLM separately, then aim
`responses-api` or `chat-completions` at it:

```bash
speech-to-speech serve   --llm_backend responses-api   --model_name "ggml-org/gemma-4-E4B-it-GGUF"   --responses_api_base_url "http://127.0.0.1:8080/v1"   --responses_api_api_key ""
```

Use `chat-completions` when the upstream lacks Responses API support, when its
Chat Completions streaming/tool path is more compatible, or when using the
package's direct audio-input bypass.

## Direct audio-input LLM path

Use this when the LLM itself consumes user audio and no STT transcript is
wanted:

```bash
speech-to-speech serve   --stt none   --llm_backend chat-completions   --model_name "YOUR_AUDIO_CAPABLE_MODEL"   --responses_api_audio_content_type input_audio
```

Rules:

- `--stt none` bypasses transcription and sends completed VAD audio to the LLM.
- The LLM backend must be `chat-completions`; the default `responses-api`
  backend is rejected for this path.
- The default `gpt-5.4-mini` is not an audio-input model. Pick an explicit
  provider/model that accepts the selected audio payload shape.
- `--responses_api_audio_content_type input_audio` embeds WAV base64 directly;
  `audio_url` sends a base64 data URL. Some llama.cpp-style endpoints accept
  only one of these shapes.
- `--responses_api_audio_history_turns` controls how many recent audio turns
  remain in chat history before older audio is replaced by role-preserving text.

## Apple Silicon local profile

`--mac-optimal-settings` supplies defaults suitable for macOS/MPS:

- Parakeet TDT for STT.
- MLX LM for the LLM backend.
- Qwen3-TTS for TTS through MLX Audio.
- MPS-capable component devices where applicable.

It does not choose `serve` versus `local`, and explicit flags win:

```bash
speech-to-speech local   --mac-optimal-settings   --model_name mlx-community/Qwen3-4B-Instruct-2507-bf16
```

For a native-audio Gemma recipe on Apple Silicon, the important shape is a
separate llama.cpp server plus:

```bash
speech-to-speech serve   --stt none   --llm_backend chat-completions   --tts qwen3   --responses_api_base_url "http://127.0.0.1:8080/v1"   --responses_api_api_key ""   --responses_api_audio_content_type input_audio   --qwen3_tts_mlx_quantization 6bit   --min_silence_ms 300
```

This is reference-only on non-macOS hosts. Full validation needs Apple Silicon,
a current llama.cpp with Gemma multimodal support, enough unified memory, and
cached model assets.

## Qwen3-TTS recipes

Default Qwen3-TTS settings:

| Option | Default |
| --- | --- |
| `--qwen3_tts_model_name` | `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` |
| `--qwen3_tts_speaker` | `Aiden` |
| `--qwen3_tts_language` | `auto` |
| `--qwen3_tts_backend` | `ggml` on non-macOS |
| `--qwen3_tts_ggml_quantization` | `BF16` |
| `--qwen3_tts_non_streaming_mode` | true on faster-qwen3-tts |
| `--qwen3_tts_mlx_quantization` | `6bit` on Apple Silicon |

### Linux GGML and torch modes

Use GGML for the default low-latency path:

```bash
speech-to-speech serve   --tts qwen3   --qwen3_tts_backend ggml   --qwen3_tts_ggml_quantization Q4_K_M
```

Use `--qwen3_tts_backend torch` to switch to the older CUDA-graphs path. On
Linux, resolve the `qwentts-cpp-python` wheel against the local CUDA runtime
before trying to load the model. Available wheelhouse variants documented by
the project include `cu124`, `cu128`, `cu130`, and `cpu`.

### Local GGUF pair

When using local GGUF files, provide both talker and codec paths and keep the
model type aligned with the files:

```bash
speech-to-speech serve   --tts qwen3   --qwen3_tts_backend ggml   --qwen3_tts_model_name Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign   --qwen3_tts_gguf_talker_path /models/qwen-talker.gguf   --qwen3_tts_gguf_codec_path /models/qwen-codec.gguf   --qwen3_tts_instruct "Warm, confident narrator"
```

Talker without codec, codec without talker, or local files paired with the wrong
model family are configuration errors.

### Voice cloning and cached references

- CustomVoice models can use preset speakers such as `Aiden` without reference
  audio.
- Base/voice-clone flows may use `--qwen3_tts_ref_audio` and
  `--qwen3_tts_ref_text`.
- GGML can cache raw references into `.spk` and `.rvq` files; reuse them with
  `--qwen3_tts_ref_spk` and optional `--qwen3_tts_ref_rvq`.
- Raw reference audio and precomputed `.spk`/`.rvq` are mutually exclusive.
- `.rvq` requires a matching `.spk` and reference text.

## Language behavior

STT backends emit language codes or accept fixed language flags. Qwen3-TTS
normalizes common aliases such as `en`, `zh-cn`, `ja`, `ko`, `de`, `fr`, `ru`,
`pt-br`, `es`, and `it` to full language names. `auto` keeps language selection
from the pipeline when available.

`--enable_lang_prompt` is opt-in for LLM handlers. When STT produces a language
code, the handler can prepend a short instruction such as "Please reply to my
message in <language>." Use it for multilingual conversations when model
responses drift into the wrong language; leave it off when explicit user/system
instructions should dominate.

## Offline and cache planning

Offline use is not a single flag. Warm the exact selected assets while online:
Silero VAD, STT model, local LLM, TTS model, Qwen references, NLTK/Smart Turn
resources, and any external server weights. Then set offline environment flags
appropriate for the model libraries and use local model paths or cached Hub
assets. The default remote Responses API profile is never offline.

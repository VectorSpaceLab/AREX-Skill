# Install and runtime reference

## Package identity

| Field | Value |
| --- | --- |
| Distribution | `speech-to-speech` |
| Import root | `speech_to_speech` |
| Console script | `speech-to-speech` |
| Python | `>=3.10` |
| Distilled version | `0.2.12` |

Install from PyPI:

```bash
pip install speech-to-speech
```

Minimal smoke:

```bash
python - <<'PY'
import speech_to_speech
print(speech_to_speech.__version__)
PY
speech-to-speech --help
speech-to-speech serve --help
speech-to-speech talk --help
speech-to-speech local --help
```

## Default runtime shape

The package runs a low-latency voice-agent cascade:

```text
microphone/client audio -> VAD -> STT or direct-audio LLM -> LLM -> TTS -> client audio
```

The server exposes an OpenAI Realtime-compatible API over:

- WebSocket: `GET /v1/realtime` upgraded to WebSocket.
- WebRTC: `POST /v1/realtime/calls` with SDP, when the `webrtc` extra is
  installed.

The default command profile is:

```bash
export OPENAI_API_KEY="..."
speech-to-speech serve
```

Default components are Parakeet TDT STT, `responses-api` LLM with
`gpt-5.4-mini`, Qwen3-TTS, 16 kHz pipeline audio, Smart Turn enabled, live
transcription enabled, and one pipeline/session slot.

## Optional extras

Install optional groups only for selected workflows:

```bash
pip install "speech-to-speech[webrtc]"          # WebRTC transport
pip install "speech-to-speech[faster-whisper]"  # Faster-Whisper STT
pip install "speech-to-speech[paraformer]"      # FunASR/ModelScope STT
pip install "speech-to-speech[kokoro]"          # Kokoro TTS on non-macOS
pip install "speech-to-speech[pocket]"          # Pocket TTS
pip install "speech-to-speech[chattts]"         # ChatTTS
pip install "speech-to-speech[whisper-mlx]"     # Apple Silicon Lightning Whisper MLX
pip install "speech-to-speech[mlx-lm]"          # Apple Silicon MLX LLM/VLM support
```

Apple Silicon packages are platform-marked. Linux import checks do not verify
MPS/MLX runtime capability.

## CUDA and Qwen3-TTS install note

On Linux, the default Qwen3-TTS GGML backend uses `faster-qwen3-tts[ggml]` and
`qwentts-cpp-python`. If the default PyPI wheel does not match the machine's
CUDA runtime, install a matching wheelhouse build before installing or
reinstalling `speech-to-speech`. Project-documented variants include CUDA 12.4,
CUDA 12.8, CUDA 13.0, and CPU fallback wheel directories.

Do not treat a successful `import torch` or tiny CUDA allocation as proof that
Qwen3-TTS model inference is ready; actual model load verifies that separately.

## Docker and compose profile

Containerized serving is useful when exposing the server or pairing with a
local OpenAI-compatible LLM service. A typical concept is:

```bash
speech-to-speech serve \
  --host 0.0.0.0 \
  --port 8765 \
  --llm_backend responses-api \
  --responses_api_base_url "http://llama:8080/v1" \
  --responses_api_api_key ""
```

`0.0.0.0` is needed for a published container port but exposes the API to every
reachable interface of that network mapping. Put public deployments behind a
gateway that owns TLS, authentication, quotas, and logging. GPU compose profiles
need the NVIDIA container runtime and are not CPU-only smokes.

## Offline operation

Offline use requires warming every selected asset while online: Silero VAD,
selected STT, selected local LLM or external local server, selected TTS, Qwen
voice references, Smart Turn/NLTK resources, and any browser demo static/runtime
assets. Then use local paths or cache-only flags for the model libraries. The
default remote Responses API profile still needs network access.

## Refresh signals

Refresh this skill when any of these change:

- CLI commands or flag validation for `serve`, `talk`, or `local`.
- Backend registry names, optional extras, defaults, or dataclass options.
- Realtime event names/order, session update schema, WebRTC behavior, or LLM
  proxy routes.
- Qwen3-TTS backend/wheel/model naming, language aliases, or voice reference
  rules.
- Browser demo env vars, connection modes, tools, limits, or UI design rules.

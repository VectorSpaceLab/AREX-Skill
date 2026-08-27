# Backend catalog

`speech-to-speech` builds a queue-backed pipeline with VAD, STT or direct audio
input, LLM, output processing, and TTS. Each selectable STT/LLM/TTS backend is
registered by name and has its own dataclass-backed CLI options.

## Default component profile

The default `serve` profile is:

```bash
speech-to-speech serve   --stt parakeet-tdt   --llm_backend responses-api   --tts qwen3
```

Important default values verified from the installed package:

| Area | Default |
| --- | --- |
| STT | `parakeet-tdt` with live transcription enabled |
| LLM | `responses-api`, `model_name=gpt-5.4-mini`, streaming enabled |
| TTS | `qwen3`, CustomVoice model, speaker `Aiden`, language `auto`, GGML backend on non-macOS |
| VAD | Silero VAD, threshold `0.6`, 16 kHz, Smart Turn enabled |
| Pool | `num_pipelines=1` |
| LLM proxy | disabled |

## STT backends

| `--stt` value | Install status | Typical platform | Notes |
| --- | --- | --- | --- |
| `none` | base package | any | Bypasses STT and sends the completed VAD audio turn to an audio-input LLM. Requires `chat-completions` and an audio-capable model. |
| `parakeet-tdt` | base package | CUDA/CPU via nano-parakeet; Apple Silicon via MLX path | Default STT. Supports optional language and live partial transcription. |
| `whisper` | base package | CPU/CUDA through Transformers | Uses shared `--language` with fixed language or `auto`; handler retains last supported language when detection is outside its supported list. |
| `mlx-audio-whisper` | base package on macOS path | Apple Silicon | Uses MLX Audio Whisper; practical use is Apple Silicon/MPS. |
| `whisper-mlx` | `speech-to-speech[whisper-mlx]` | Apple Silicon | Lightning Whisper MLX optional backend. |
| `faster-whisper` | `speech-to-speech[faster-whisper]` | CPU/CUDA | Faster-Whisper optional backend; effective language support follows selected Whisper checkpoint. |
| `paraformer` | `speech-to-speech[paraformer]` | CPU/CUDA | FunASR/ModelScope optional backend; default model is Chinese-oriented. |

## LLM backends

| `--llm_backend` value | Install status | Typical platform | Capabilities |
| --- | --- | --- | --- |
| `responses-api` | base package | hosted provider or self-hosted OpenAI-compatible `/v1/responses` | Default, streaming, structured tools, LLM proxy support. Not the direct-audio bypass backend. |
| `chat-completions` | base package | hosted provider, llama.cpp, vLLM, or OpenAI-compatible `/v1/chat/completions` | Supports direct audio-input path with `--stt none`, shares `--responses_api_*` flags, supports LLM proxy. |
| `transformers` | base package | CPU/CUDA local model | In-process local text/VLM generation. Tool calls are prompt-rendered and parsed from generated text. |
| `mlx-lm` | `speech-to-speech[mlx-lm]` on macOS | Apple Silicon | MLX local model path; selected by `--mac-optimal-settings` unless overridden. |

Connection flags with the `responses_api_` prefix are intentionally shared by
`responses-api` and `chat-completions`: base URL, API key, streaming,
provider-thinking controls, audio-input payload shape, and recent-audio history.

## TTS backends

| `--tts` value | Install status | Typical platform | Notes |
| --- | --- | --- | --- |
| `qwen3` | base package | GGML/torch on non-macOS; MLX Audio on Apple Silicon | Default. Supports CustomVoice speakers, VoiceDesign instruct prompts, voice cloning references, GGUF local files, GGML quantization, and MLX quantization mapping. |
| `facebookMMS` | base package | CPU/CUDA | MMS TTS through Transformers; maps `--tts_language`/detected STT language to MMS model suffixes and can reload on language change. |
| `kokoro` | base Darwin path; `speech-to-speech[kokoro]` on non-macOS | CPU/CUDA or Apple Silicon | Kokoro-82M; can auto-switch voice/language for mapped languages. |
| `pocket` | `speech-to-speech[pocket]` | CPU/CUDA | Pocket TTS; preset voices include `alba`, `marius`, `javert`, `jean`, `fantine`, `cosette`, `eponine`, `azelma`. |
| `chatTTS` | `speech-to-speech[chattts]` | CPU/CUDA | ChatTTS optional backend with `--chat_tts_*` options. |

Deprecated TTS and STT implementations are intentionally not part of the CLI
surface. Treat old archive-era backends as historical, not selectable runtime
choices.

## Optional dependency groups

Install one extra at a time for the selected backend:

```bash
pip install "speech-to-speech[faster-whisper]"
pip install "speech-to-speech[paraformer]"
pip install "speech-to-speech[webrtc]"
pip install "speech-to-speech[kokoro]"
pip install "speech-to-speech[pocket]"
pip install "speech-to-speech[chattts]"
```

Apple Silicon extras such as `mlx-lm` and `whisper-mlx` are platform-marked for
Darwin. On Linux, installing those extras should not be treated as proof that
MLX workflows are available.

## VAD and Smart Turn surface

The VAD stage is always present unless a future implementation changes the
pipeline shape. It uses 16 kHz audio and feeds either STT or the direct-audio
LLM bypass. The command-level VAD knobs include threshold, minimum speech,
minimum silence, continuation windows, live transcription silence, and Smart
Turn thresholds/delays. Tune VAD and Smart Turn together when turns end too
early or too late; route command-level flag selection to `cli-and-server`.

# CLI reference and operating profiles

This reference distills the public command surface. Use `speech-to-speech
<command> --help` for the installed version's generated option list; do not
assume that an option belonging to one command is accepted by another.

## Command family

| Command | Owns | Connection behavior |
| --- | --- | --- |
| `serve` | Realtime server, pipeline selectors, host/port, VAD, session pool, proxy | Serves the OpenAI Realtime-compatible API over WebSocket and WebRTC. Default bind is `127.0.0.1:8765`. |
| `talk` | Packaged microphone/speaker client | Connects to one existing full endpoint supplied with `--url`; it does not build a pipeline. |
| `local` | Server plus packaged audio client | Builds the same pipeline as `serve`, forces the server to loopback, and connects the packaged client to `ws://127.0.0.1:<port>/v1/realtime`. |

The console entry point is `speech-to-speech`. A server/client split is useful
when an application, browser client, or another machine owns the Realtime
connection. `local` is the shortest path for a single machine with a sound
card.

### Legacy migration

The supported migration aliases are top-level forms such as:

```bash
speech-to-speech --mode realtime --port 8765
speech-to-speech --mode local --local_audio_input_device 2
```

They map to `serve` and `local`, respectively, and print a deprecation warning.
The `--mode=value` spelling is also accepted. Modes such as `socket`,
`raw-websocket`, and `websocket` are removed and fail with guidance to use
`serve` or `local`. Prefer the explicit command because the aliases are
scheduled to stop working.

## `talk`: packaged audio client

`talk` requires a **full** endpoint ending in `/realtime`, not only a host or
base path:

```bash
speech-to-speech talk --url ws://127.0.0.1:8765/v1/realtime
speech-to-speech talk --url wss://voice.example/v1/realtime --api-key "$OPENAI_API_KEY"
```

The URL must be absolute and use `ws`, `wss`, `http`, or `https`; query strings
and fragments are rejected. HTTP(S) is normalized to the corresponding
WebSocket(S) connection. The default URL is
`ws://127.0.0.1:8765/v1/realtime`.

Useful client options:

| Option | Default | Use |
| --- | --- | --- |
| `--model` | `local` | Model label sent when opening the Realtime session. The server profile controls the actual configured LLM. |
| `--api-key` | unset | Explicit key for the endpoint. For loopback, the client supplies a harmless local placeholder when no key is given; for non-loopback URLs, an omitted key lets the OpenAI client use its environment configuration. |
| `--send-rate`, `--recv-rate` | `16000` | PCM microphone and speaker rates. `16000` is the package-native default; `24000` is the other supported explicit PCM schema rate. |
| `--chunk-size` | `1024` | Microphone/speaker callback block size in samples. |
| `--input-device`, `--output-device` | unset | Sound-device indexes. Leave unset to use the system default. |
| `--instructions` | unset | Optional session instructions sent by the packaged client. |
| `--voice` | unset | Optional output voice field for the session update. |
| `--print-json` | false | Print raw received Realtime events while retaining the friendly renderer. |
| `--block-mic-during-playback` | false | Stop capture while audio is playing. The default keeps capture enabled for barge-in. |
| `--connection-retry-timeout` | `30.0` seconds | Time to retry a not-yet-ready endpoint before surfacing the connection error. |

`talk` does not accept `--host`, `--port`, `--base-url`,
`--websocket-base-url`, `--stt`, or other pipeline/server flags. Pass the
endpoint in `--url` and configure the server separately.

## `serve`: server and pipeline flags

Minimal remote-provider profile:

```bash
export OPENAI_API_KEY="..."
speech-to-speech serve
```

The server listens at `ws://127.0.0.1:8765/v1/realtime` by default. The
important command-level selectors are:

| Option | Default / behavior |
| --- | --- |
| `--host` | `127.0.0.1`. Use `0.0.0.0` only when an explicit network exposure is intended and an access-control boundary exists. |
| `--port` | `8765`. |
| `--stt` | `parakeet-tdt`. |
| `--llm_backend` | `responses-api`, targeting the provider's `/v1/responses` path. |
| `--tts` | `qwen3`. |
| `--model_name` | `gpt-5.4-mini` for the default Responses API profile. |
| `--responses_api_base_url` | unset, which selects the default OpenAI-compatible endpoint. |
| `--responses_api_api_key` | unset. Use `OPENAI_API_KEY` for the default OpenAI profile or set this explicitly for another provider. An explicit empty value is useful for an unauthenticated local OpenAI-compatible server. |
| `--responses_api_stream` | enabled by default. |
| `--enable_live_transcription` | enabled by default; the live STT path is intended for Parakeet TDT. |
| `--num_pipelines` | `1`; each slot has isolated VAD/STT/LLM/TTS state and admits one concurrent session. |
| `--enable_llm_proxy` | disabled by default; only remote `responses-api` and `chat-completions` backends support it. |
| `--llm_proxy_connect_timeout_s` | `10.0` seconds for connecting to the upstream proxy target. |
| `--mac-optimal-settings` | On macOS, changes defaults to Parakeet TDT, MLX LM, Qwen3-TTS, and MPS-capable devices. It does not select a command. |

The default component profile also includes VAD threshold `0.6`, 16 kHz audio,
`min_silence_ms=64`, `min_speech_ms=384`,
`min_speech_continuation_ms=192`, Smart Turn enabled, and live transcription
updates every `0.5` seconds. The default Qwen3-TTS configuration uses the
CustomVoice model, speaker `Aiden`, language `auto`, GGML on non-macOS, and
non-streaming prefill enabled. Backend-specific installation, device, model,
voice, and language details belong to
[components-and-backends](../../components-and-backends/SKILL.md).

### OpenAI key and base URL behavior

- For the default remote profile, export `OPENAI_API_KEY` and leave the base
  URL unset.
- For a provider or self-hosted OpenAI-compatible server, set
  `--responses_api_base_url` and select `--model_name` for that server. Pass
  `--responses_api_api_key` when the upstream needs a key.
- The same `--responses_api_*` connection flags are shared by
  `--llm_backend responses-api` and `--llm_backend chat-completions`; the latter
  sends requests to `/v1/chat/completions` instead of `/v1/responses`.
- A local upstream such as llama.cpp can be used with an empty API key. A
  remote upstream still needs its own credential even when the speech server
  itself is bound only to loopback.

### Local/self-hosted LLM profiles

**Separate local server, remote-style client.** Start a compatible llama.cpp or
vLLM endpoint separately, then point the speech pipeline at it:

```bash
speech-to-speech serve \
  --llm_backend responses-api \
  --model_name "ggml-org/gemma-4-E4B-it-GGUF" \
  --responses_api_base_url "http://127.0.0.1:8080/v1" \
  --responses_api_api_key ""
```

Use `--llm_backend chat-completions` when the upstream exposes only Chat
Completions or when its Responses streaming/tool path is unsuitable. The
backend-specific reasoning and audio rules are owned by
[components-and-backends](../../components-and-backends/SKILL.md).

**In-process local model.** Use `--llm_backend transformers` on CPU/CUDA or
`--llm_backend mlx-lm` on Apple Silicon, with an appropriate `--model_name`.
`--mac-optimal-settings` selects the MLX-oriented defaults on macOS, but an
explicit `--llm_backend`, `--model_name`, `--stt`, `--tts`, `--device`, or
component-device option wins over the preset.

**Direct audio input caveat.** The command-level shape is:

```bash
speech-to-speech serve \
  --stt none \
  --llm_backend chat-completions \
  --model_name "YOUR_AUDIO_CAPABLE_MODEL"
```

`--stt none` sends VAD-completed audio directly to the LLM. It is rejected with
`responses-api`; the default `gpt-5.4-mini` is not an audio-input model. Use an
explicit audio-capable model and verify the provider's Chat Completions audio
format. Route model selection, `input_audio` versus `audio_url`, history, and
provider compatibility to
[components-and-backends](../../components-and-backends/SKILL.md).

## `local`: loopback server plus audio

```bash
speech-to-speech local
speech-to-speech local --port 9876 --local_audio_input_device 2 \
  --local_audio_output_device 4 --local_audio_print_json
```

`local` accepts the pipeline and VAD options used by `serve`, plus:

| Option | Default / behavior |
| --- | --- |
| `--port` | `8765`; the loopback server and packaged client use this port. |
| `--local_audio_input_device` | unset; optional input sound-device index. |
| `--local_audio_output_device` | unset; optional output sound-device index. |
| `--local_audio_chunk_size` | `1024` samples. |
| `--local_audio_block_mic_during_playback` | false; leave false for barge-in. |
| `--local_audio_print_json` | false; print raw events from the packaged local client when enabled. |

`local` rejects `--host`; it does not honor a network bind override. Its server
is built with `127.0.0.1`, and its client uses the loopback WebSocket URL even
if a caller tries to alter the parsed server host.

`serve` rejects `--local_audio_*` flags, and both `serve` and `local` reject the
client's `--url`. Use `talk` when the audio client must target a separately
started service.

## Docker/Compose profile

A GPU compose profile can run a llama.cpp service on port `8080` and the speech
pipeline on port `8765`. The pipeline service is configured conceptually as:

```bash
speech-to-speech serve \
  --host 0.0.0.0 \
  --port 8765 \
  --llm_backend responses-api \
  --model_name "ggml-org/gemma-4-E4B-it-GGUF" \
  --responses_api_base_url "http://llama:8080/v1" \
  --responses_api_api_key ""
```

Inside a container, `0.0.0.0` is needed for the published port, but it exposes
the API to every reachable interface of that container/host mapping. Put the
published service behind a gateway or restrict the network. The compose profile
uses a CUDA llama image and GPU reservations; it is not a CPU-only smoke path.

## Offline command profile

Offline operation is a cache contract, not a parser switch. Warm the exact
selected STT, LLM, TTS, Silero VAD, NLTK, and Smart Turn assets once while
online. Then a local LLM endpoint or an in-process local backend must be used,
and every selected model must be available from the local cache or a local
model path. `HF_HUB_OFFLINE=1` prevents Hub requests; a missing Smart Turn
checkpoint must be supplied with `--smart_turn_model_path` or Smart Turn must
be disabled. The default remote Responses API is not offline merely because the
speech server is local.

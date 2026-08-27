# CLI and server troubleshooting

## Parser and command selection

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `unknown command` or `a command is required` | No explicit command was selected. | Use exactly one of `serve`, `talk`, or `local`. |
| `--mode` prints a warning | A legacy alias is being used. | Replace `--mode realtime` with `serve` or `--mode local` with `local`; aliases are temporary. |
| A legacy mode says only `realtime` and `local` remain | A removed mode such as `socket` or `websocket` was used. | Migrate to `serve`; clients connect through the Realtime endpoint with `talk` or another compatible client. |
| `talk` rejects `--host`, `--port`, `--stt`, `--base-url`, or `--websocket-base-url` | Server/pipeline flags were given to the client command. | Put those options on `serve`; give `talk` a full `--url` and client audio flags. |
| `serve` rejects `--local_audio_*` | Local audio flags were given to the server-only command. | Use `local` for the packaged microphone/speaker client, or use `talk` separately. |
| `local` rejects `--host` | `local` is deliberately loopback-only. | Use `serve --host ...` for a network service and connect with `talk`. |
| `serve` or `local` rejects `--url` | `--url` belongs only to `talk`. | Remove it and use the command's own port, or start a separate server and use `talk`. |

## URL and audio client issues

- `--url` must be an absolute endpoint ending in `/realtime`, for example
  `ws://127.0.0.1:8765/v1/realtime`. Do not pass only `http://host:port`, a
  base `/v1` URL, a query string, or a fragment.
- A non-loopback `talk` connection with no explicit `--api-key` relies on the
  OpenAI client's environment configuration. Set the needed credential or pass
  `--api-key` explicitly.
- `local`'s `--local_audio_input_device` and
  `--local_audio_output_device` are sound-device indexes, not network ports.
  Start with both unset, then inspect the host's available audio devices using
  its normal audio tooling.
- If local playback prevents interruption, leave
  `--local_audio_block_mic_during_playback` disabled. Enable it only when
  feedback/echo is more important than barge-in.
- If a sound-device callback fails, first try the system default devices and a
  conservative `--local_audio_chunk_size 1024`; the CLI does not install or
  select an audio driver for you.

## Authentication, provider, and profile failures

- A default `responses-api` run with no explicit base URL expects a usable
  OpenAI credential, normally `OPENAI_API_KEY`.
- A self-hosted OpenAI-compatible service usually needs a base URL ending in
  `/v1` and often accepts an empty API key. Use the service's model identifier
  in `--model_name`; the speech server does not discover it for you.
- `--responses_api_base_url` and `--responses_api_api_key` apply to both
  `responses-api` and `chat-completions`. The backend chooses `/v1/responses`
  versus `/v1/chat/completions`.
- `--stt none` is rejected with `responses-api`. Select
  `--llm_backend chat-completions` and an explicitly audio-capable model. Do
  not assume the default `gpt-5.4-mini` accepts audio; route content type and
  model/provider checks to
  [components-and-backends](../../components-and-backends/SKILL.md).
- `--enable_llm_proxy` fails before startup for `transformers` or `mlx-lm`.
  Use `responses-api` or `chat-completions`. The proxy also requires a trusted
  network or an authenticated gateway because the stock server has no auth or
  rate limiting.

## Host, port, and capacity

- `Address already in use` means another process owns the selected port. Stop
  it or choose a different `--port`; `local` uses the same port for its forced
  loopback server.
- A client can reach the server on the host but not from another machine when
  `serve` is left at `127.0.0.1`; that bind is local-only by design. If remote
  access is intentional, use an explicit host bind plus a gateway/firewall.
- `session_limit_reached` means every pipeline slot is active, draining, or
  stuck. Disconnect idle clients, inspect `GET /v1/pool`, and wait for a clean
  release before concluding that the server is dead. Increase
  `--num_pipelines` only after accounting for the extra handler/model memory.
- A pool value below one is invalid and fails before server construction.
- If a pool larger than one on Apple Silicon logs that live transcription was
  disabled, this is an expected MLX contention safeguard. Final STT remains
  enabled; use a single pipeline when live progressive updates are required.

## Turn-taking and transcription

- **Premature turn ends:** increase `--min_silence_ms` or use a less aggressive
  VAD threshold; if Smart Turn calls a pause incomplete, increase
  `--smart_turn_max_wait_ms` cautiously.
- **Long response latency after a pause:** lower an overly large Smart Turn
  grace or `--smart_turn_incomplete_delay_ms`; avoid reducing
  `min_speech_ms` until noise rejection is understood.
- **Cut-off short continuation:** retain the recommended
  `--min_speech_ms 384 --min_speech_continuation_ms 192` pairing and consider a
  modest `--short_segment_merge_ms` for fragmentary audio.
- **No live transcript:** live updates are intended for Parakeet TDT and are
  distinct from the final transcript. Check the selected `--stt`, the update
  interval, and whether a multi-pipeline Apple Silicon run disabled them.
- **Smart Turn download/offline error:** cache the supported checkpoint while
  online, pass `--smart_turn_model_path` to a local ONNX file, or use
  `--no_smart_turn`. `HF_HUB_OFFLINE=1` cannot supply a missing checkpoint.
- **NLTK resource error or first-run network access:** warm `punkt_tab` and
  `averaged_perceptron_tagger_eng` before going offline. The pipeline imports
  NLTK resources at startup.
- **DeepFilterNet installation conflict:** it is optional and requires
  `numpy<2`, while Pocket TTS requires `numpy>=2`. Use separate environments or
  omit audio enhancement from the Pocket TTS profile.

## Proxy and Docker warnings

- A proxy request returning `501` usually means the proxy is disabled, the
  request used the non-selected endpoint, or a local LLM backend was selected.
  Check `--enable_llm_proxy` and the backend/path pair.
- A proxy `502` means the speech server could not reach its configured upstream;
  check the base URL from the server's network namespace and upstream health.
- Proxy client API keys do not create authentication on the stock server. Put a
  gateway in front of it before binding to `0.0.0.0`.
- In a container profile, `127.0.0.1` names the pipeline container itself. Use
  the compose service name for the LLM upstream, and bind the published speech
  service to `0.0.0.0` only behind the intended network boundary.
- A GPU compose profile assumes the CUDA runtime and GPU reservation are
  available. Treat missing GPU/container runtime errors as deployment issues,
  not CLI parser failures.

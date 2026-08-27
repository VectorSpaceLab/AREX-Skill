# Server runtime, endpointing, capacity, and proxy

## Binding and transport

`serve` starts one FastAPI/uvicorn server and exposes the OpenAI
Realtime-compatible WebSocket endpoint at `/v1/realtime`. WebRTC is also
available when the package's `webrtc` extra is installed. The default CLI bind
is `127.0.0.1:8765`; this is intentionally safer than the lower-level server
class default.

Use an explicit public bind only when the network boundary is understood:

```bash
speech-to-speech serve --host 0.0.0.0 --port 8765
```

The Realtime API does not add authentication merely because the host is
non-loopback. Do not expose this command directly to an untrusted LAN,
container network, or Internet-facing interface. Put an authenticated gateway,
firewall, or private network in front of it. This warning is especially
important when `--enable_llm_proxy` is enabled.

`local` is different: its pipeline builder forces `127.0.0.1` and constructs the
packaged audio client against
`ws://127.0.0.1:<port>/v1/realtime`. It cannot be turned into a network server
with `--host`.

## Pipeline pool and session capacity

`--num_pipelines N` creates N isolated pipeline units. Each unit owns its VAD,
STT, LLM, TTS, queues, cancellation state, and conversation state. One server
routes each new connection to the first free unit. The maximum number of
simultaneous WebSocket or WebRTC sessions is therefore N, not an unlimited
number of clients sharing one conversation.

`N` must be at least `1`; a zero or negative value fails before the pipeline is
started. When all units are occupied:

- WebSocket clients receive an error event with type
  `session_limit_reached`, then a policy-close (`1008`).
- WebRTC offers receive the same error type in a `503` response.
- The remedy is to disconnect a client, wait for its session to drain, or start
  another process/service with a larger pool. Increasing N increases model and
  handler memory/compute requirements.

For operational inspection, the server exposes `GET /v1/pool`. Its response
shows the pool `size`, `in_use`, and per-unit `idle`, `active`, `draining`, or
`stuck` state. A unit that remains draining/stuck may indicate a handler that
failed to finish shutdown; treat it as capacity still in use rather than
assuming a new client can claim it.

On Apple Silicon, a pool larger than one automatically disables live
transcription when it would contend on the global MLX lock. Final STT still
runs; the change is a readability/contention safeguard, not a session failure.

## LLM proxy gateway contract

Enable the proxy only for a remote OpenAI-compatible LLM backend:

```bash
speech-to-speech serve \
  --llm_backend responses-api \
  --enable_llm_proxy
```

The selected backend determines the one active path:

- `responses-api` -> `POST /v1/responses`
- `chat-completions` -> `POST /v1/chat/completions`

The other known path returns `501` with a reason. Local `transformers` and
`mlx-lm` backends are rejected before pipeline construction because they do not
provide proxy support. The proxy is disabled by default.

The proxy is a passthrough with no authentication and no throttling of its own.
It holds the configured upstream key server-side, overwrites each request's
`model` with the server's `--model_name`, and treats each request as stateless
(the caller sends the complete message/input list). Proxy requests bypass
pipeline queues and are concurrent with the voice session; new speech does not
cancel them. The proxy's connect timeout is controlled by
`--llm_proxy_connect_timeout_s` (default `10.0` seconds); generation reads have
no short fixed timeout because a provider may stream for minutes.

Use an authenticated gateway when the proxy is reachable by more than a
trusted operator. Supplying an API key to a client SDK does not secure this
stock server: the server itself does not validate that key. `GET /v1/usage`
includes an additive `llm_proxy` counter section for requests, status buckets,
and observed token totals.

## VAD and Smart Turn tuning

The pipeline endpointing path combines Silero VAD with optional Smart Turn.
Start from these defaults:

| Flag | Default | Meaning and tuning direction |
| --- | ---: | --- |
| `--thresh` | `0.6` | VAD speech confidence. Higher values require stronger speech evidence and can miss quiet speech; lower values are more permissive and can admit noise. |
| `--sample_rate` | `16000` | Pipeline audio rate in Hz. |
| `--min_silence_ms` | `64` | Silence needed to segment a turn. Increasing it avoids splits in brief pauses but delays turn end; very low values can fragment speech. |
| `--min_speech_ms` | `384` | Minimum new-turn speech duration. Increase to reject short noise; decrease only when short utterances matter. |
| `--min_speech_continuation_ms` | `192` | Hysteresis threshold for speech continuing a reopenable turn. The recommended pairing is `192` with `min_speech_ms=384`. |
| `--speech_pad_ms` | `500` | Audio retained before detected speech is emitted. |
| `--max_speech_ms` | unlimited | Optional forced split for very long continuous speech. |
| `--short_segment_merge_ms` | `0` | Hold and stitch adjacent short fragments before discarding them; useful with very small silence windows. |
| `--speculative_reopen_ms` | `800` | Grace after a soft end during which resumed speech can reopen the same turn. |
| `--unanswered_reopen_ms` | `7000` | Upper sanity cap for an unanswered soft-ended turn; Smart Turn can clamp it to preserve its own grace. |

Smart Turn is enabled by default for both `serve` and `local`. It uses a
quantized CPU ONNX runtime and a supported v3.2 checkpoint. Its controls are:

| Flag | Default | Meaning |
| --- | ---: | --- |
| `--smart_turn_threshold` | `0.5` | Completion probability cutoff. A higher threshold waits more readily on ambiguous pauses. |
| `--smart_turn_max_wait_ms` | `2000` | Maximum speculative grace for an incomplete turn. |
| `--smart_turn_incomplete_delay_ms` | `600` | Delay before STT/LLM work starts when the turn looks incomplete; resumed speech can invalidate that revision. |
| `--smart_turn_cpu_count` | `1` | ONNX Runtime threads per inference. |
| `--smart_turn_model_path` | unset | Local v3.x CPU ONNX checkpoint. Without it, the supported checkpoint is obtained from the model cache/Hub on first use. |
| `--no_smart_turn` | n/a | Disable Smart Turn when its checkpoint is unavailable or its speculative behavior is not wanted. |

When speech resumes during the incomplete delay or speculative grace, the
pipeline emits a newer turn revision and discards stale work before it reaches
the user. If responses are consistently late, reducing speculative waits may
help; if words are cut off at natural pauses, first increase Smart Turn grace or
VAD silence rather than disabling VAD entirely.

## Live transcription

Live transcription is enabled by default and uses progressive Parakeet TDT
updates when that STT backend is selected. `--live_transcription_update_interval`
defaults to `0.5` seconds. It is display/progress feedback; final transcription
still follows the normal turn path. If live updates are noisy or expensive,
select a compatible backend and adjust the interval, or disable the feature with
the boolean option shown by `speech-to-speech serve --help`.

Live transcription is not a generic capability of every STT backend. For
backend selection, language behavior, and optional dependencies, route to
[components-and-backends](../../components-and-backends/SKILL.md).

## First-run and optional notices

- **NLTK resources:** importing the pipeline ensures `punkt_tab` and
  `averaged_perceptron_tagger_eng` are present and may download them when they
  are missing. Warm them while online before using an offline profile.
- **Smart Turn checkpoint:** the CPU runtime is included, but the checkpoint is
  separate. Cache it before offline use, supply `--smart_turn_model_path`, or
  use `--no_smart_turn`.
- **DeepFilterNet:** audio enhancement is optional, not part of the default
  profile. Its dependency requires `numpy<2` and conflicts with Pocket TTS's
  `numpy>=2` requirement. Install it only for a profile that actually enables
  audio enhancement and does not use Pocket TTS in the same environment.
- **WebRTC:** the WebRTC transport requires the `webrtc` extra. The WebSocket
  path does not require starting a WebRTC client.

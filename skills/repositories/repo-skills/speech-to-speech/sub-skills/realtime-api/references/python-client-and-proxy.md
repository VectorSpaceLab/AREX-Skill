# Python client and LLM proxy reference

This reference covers the package's client-facing helper behavior and the
optional HTTP proxy that re-exposes a selected remote LLM backend.

## Packaged audio client behavior

The `speech-to-speech talk` command wraps `RealtimeAudioClientConfig` and the
OpenAI Realtime client. Use it when a future task needs a quick microphone and
speaker client instead of a custom WebSocket implementation.

Important client defaults:

| Field | Default | Notes |
| --- | --- | --- |
| `url` | `ws://127.0.0.1:8765/v1/realtime` | Must normalize to a full Realtime endpoint. |
| `model` | `local` | Label sent in the session request; the server's configured LLM still decides the actual model. |
| `send_rate` / `recv_rate` | `16000` / `16000` | PCM client rates. The internal server pipeline is 16 kHz. |
| `chunk_size` | `1024` | Sound-device callback block size. |
| `input_device` / `output_device` | unset | Optional device indexes. |
| `block_mic_during_playback` | false | Leave false to preserve barge-in unless echo feedback is the priority. |
| `connection_retry_timeout` | `30.0` seconds | Lets `talk` wait for a server that is still starting. |

URL normalization accepts `ws`, `wss`, `http`, and `https` schemes and converts
HTTP(S) to the corresponding WebSocket base. Query strings and fragments are
rejected so credentials do not get embedded in the socket URL by accident. A
client should supply a full endpoint ending in `/v1/realtime`.

Examples:

```bash
speech-to-speech talk --url ws://127.0.0.1:8765/v1/realtime
speech-to-speech talk --url https://voice.example/v1/realtime --api-key "$OPENAI_API_KEY"
```

For loopback, the packaged client can use a harmless placeholder credential.
For non-loopback endpoints, rely on the target server's credential policy and
avoid printing tokens in logs.

## Custom Python Realtime clients

A custom client should follow the same sequence as the bundled audio client:

1. Open a WebSocket to the normalized Realtime endpoint.
2. Read `session.created` before assuming server readiness.
3. Send a `session.update` containing instructions, optional voice, and tool
   declarations.
4. Stream `input_audio_buffer.append` base64 PCM16 chunks for WebSocket audio,
   or send `conversation.item.create` text/tool-result items.
5. Wait for server VAD or send `response.create` explicitly.
6. Treat `response.done` as the point at which the next response may be safely
   created.

If using the OpenAI Python SDK's Realtime helpers, keep the WebSocket base URL
consistent with the endpoint the `talk` command would derive. The server is
OpenAI Realtime-compatible at the protocol level, but model behavior still
comes from the configured `speech-to-speech` pipeline.

## LLM proxy

`serve --enable_llm_proxy` exposes OpenAI-compatible HTTP paths on the same
FastAPI app:

- `POST /v1/chat/completions`
- `POST /v1/responses`
- provider-compatible model listing where supported by the selected backend

The proxy is available only when the selected LLM backend advertises proxy
support. In this package, that means the remote-style backends:

- `responses-api`
- `chat-completions`

In-process `transformers` and `mlx-lm` backends do not provide the HTTP proxy.

### Proxy routing rules

- The proxy forwards to the same upstream connection configured by
  `--responses_api_base_url`, `--responses_api_api_key`, and related
  `responses_api_*` options.
- When the incoming request has a `model`, that request model can override the
  command-level `--model_name` for the proxied side task.
- `--llm_proxy_connect_timeout_s` controls upstream connection timeout. Reads
  may intentionally run for minutes during generation.
- The speech server does not add its own authentication, quotas, or tenant
  isolation around proxy requests.

### Safe proxy exposure

Keep the proxy on loopback during development:

```bash
speech-to-speech serve \
  --enable_llm_proxy \
  --llm_backend responses-api \
  --responses_api_base_url "http://127.0.0.1:8080/v1" \
  --responses_api_api_key ""
```

If exposing `--host 0.0.0.0`, put the server behind a gateway that owns TLS,
authentication, rate limits, and audit logging. Treat an enabled LLM proxy as a
provider credential boundary, not just a local debug convenience.

## Minimal validation checklist

- `speech-to-speech talk --url <endpoint>` receives `session.created`.
- Custom WebSocket clients do not put API keys in query strings.
- A second `response.create` waits for `response.done` from the first.
- Tool results use `conversation.item.create` and trigger follow-up generation
  only when a spoken or textual follow-up is desired.
- The LLM proxy is enabled only for `responses-api` or `chat-completions` and
  only behind the intended network boundary.

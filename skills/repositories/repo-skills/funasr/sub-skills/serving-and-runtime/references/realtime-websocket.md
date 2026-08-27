# Realtime WebSocket server

This reference covers the packaged realtime CLI, session control messages, chunk sizing, and the hotword / endpoint-mode controls that matter when you are debugging streaming output.

## Best entry point

Use `funasr-realtime-server` for the packaged realtime service.

```bash
funasr-realtime-server --help
funasr-realtime-server --endpoint-mode server --device cuda:0
funasr-realtime-server --endpoint-mode client --device cpu
```

## CLI flags that matter

| Flag | Default | Why it matters |
|---|---|---|
| `--port` | `10095` | WebSocket port for clients. |
| `--model` | `FunAudioLLM/Fun-ASR-Nano-2512` | Default Nano-family model id. |
| `--hub` | `ms` | Chooses the remote hub for the model id. |
| `--device` | `cuda:0` | Runtime device for the loaded model. |
| `--endpoint-mode` | `server` | `server` uses VAD-driven endpoints; `client` expects explicit `START` / `COMMIT` control. |
| `--partial-window-sec` | `15.0` | Caps repeated partial re-decode of a long utterance. Lower it for high concurrency. |
| `--enable-spk` | off | Turns on streaming speaker diarization. |
| `--spk-model` | `iic/speech_eres2netv2_sv_zh-cn_16k-common` | Speaker model for `--enable-spk`. |
| `--hotword-file` | unset | Model-decoding hotwords, one per line. |
| `--postprocess-hotword-file` | unset | Deterministic text-level corrections applied after decoding. |
| `--language` | unset | Optional language hint passed into the session. |
| `--dtype` | `bf16` | `bf16`, `fp16`, or `fp32` / `float32`. |
| `--ws-ping-interval` / `--ws-ping-timeout` | `20.0` / `20.0` | Keepalive tuning for flaky networks. |
| `--ws-close-timeout` | `10.0` | Graceful close timeout. |
| `--ws-max-size` | `10 MiB` | Maximum incoming WebSocket message size. |
| `--log-session-stats-interval` | `0.0` | Optional session-state logging cadence. |

## Session control messages

The realtime server understands a small set of textual control messages in addition to binary audio chunks:

| Message | Meaning |
|---|---|
| `START` | Reset the session and mark it active. |
| `STOP` | Finalize the current session and send the last result. |
| `COMMIT` | Finalize the current utterance while keeping the session open; only valid in client endpoint mode. |
| `HOTWORDS:foo,bar` | Replace the current decoding hotwords with a comma-separated list. |
| `POSTPROCESS_HOTWORDS:wrong=>right` | Install deterministic text-level corrections for final output. |
| `LANGUAGE:en` | Update the session language hint. |

Binary messages are PCM audio bytes. The packaged server expects the session to send audio in the format the runtime can decode reliably; 16 kHz mono PCM is the safest choice.

## Output shape

The server returns JSON objects with fields such as:

- `sentences`
- `partial`
- `partial_start_ms`
- `duration_ms`
- `is_final`

Each completed sentence can include `text`, `start`, `end`, and optional `spk` speaker ids.

## Chunk sizing guidance

The legacy streaming client documents chunk tuples such as `5,10,5` as roughly 600 ms. Use that idea as a starting point when you tune latency versus stability.

- Smaller chunks reduce latency but increase the number of partial decodes.
- Larger chunks reduce decoder churn but can delay the first visible transcript.
- `--partial-window-sec` bounds how much audio is re-decoded while a long utterance is still open.

## Common session patterns

### Server VAD mode

1. Open the WebSocket connection.
2. Send `START`.
3. Stream binary PCM chunks.
4. Send `STOP` when the audio ends.

This is the default mode when you want the server to detect utterance endpoints.

### Client endpoint mode

1. Open the WebSocket connection.
2. Send `START`.
3. Stream binary PCM chunks.
4. Send `COMMIT` whenever the client decides the utterance ended.
5. Keep streaming or send `STOP` at the end of the session.

This mode is useful when the client already knows the utterance boundaries and wants to avoid server-side VAD.

## When output looks empty or delayed

- Check whether you forgot `START`, `STOP`, or `COMMIT`.
- Confirm that the client and server agree on `server` versus `client` endpoint mode.
- Use 16 kHz mono PCM unless the client stack explicitly documents something else.
- Increase the chunk size a little if the server is decoding too often.
- Lower `--partial-window-sec` if a long utterance is forcing too much re-encoding.
- Verify that your keepalive settings are not causing the connection to close before the final result arrives.

## Boundary notes

- This reference owns the streaming transport and session-control behavior, not model-family selection.
- If the issue is `fun-asr-nano` applicability, dtype choice, or GPU backend warnings, route to `llm-asr-and-vllm`.
- If the issue is a batch transcription or subtitle flow, route to `python-asr-pipelines`.

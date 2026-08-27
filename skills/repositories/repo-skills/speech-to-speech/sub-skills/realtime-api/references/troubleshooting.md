# Realtime API troubleshooting

## Connection and endpoint errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| WebSocket closes before any useful event | URL is not the full Realtime endpoint or uses an unsupported scheme | Use a full `ws://.../v1/realtime` or `wss://.../v1/realtime` URL. HTTP(S) URLs are acceptable only when a helper normalizes them to WebSocket form. |
| No `session.created` after connect | Client is not actually connected to the Realtime route, or server startup is still in progress | Probe the exact endpoint, then confirm the server process is bound on the intended host/port. |
| `session_limit_reached` | Every pipeline unit is already claimed | Increase `--num_pipelines`, reduce concurrent sessions, or make clients disconnect cleanly so units can drain `SESSION_END` and release. |
| `unknown_or_invalid_event` | Event name or JSON shape does not match the supported Realtime subset | Compare the event to `realtime-protocol.md`; do not send arbitrary OpenAI beta fields unless the package has implemented them. |
| `invalid_session_type` | `session.update` uses a schema shape the runtime cannot merge | Send only supported GA session fields: instructions, audio input/output, output modalities, tools, and turn detection. |

## Response lifecycle problems

### `conversation_already_has_active_response`

The service serializes responses. A second `response.create` while one response
is active or pending is rejected. Wait for `response.done` before sending the
next create, or implement a client-side queue.

### Response never speaks after a tool result

A tool result is only conversation state. After sending
`conversation.item.create` with `type: function_call_output`, send
`response.create` when the result should be summarized or spoken. Do not send a
follow-up create for fire-and-forget robot/action tools unless the tool result
contains user-facing information.

### Barge-in does not stop the assistant

Check these in order:

1. The session turn-detection config has not disabled interruption.
2. The client is clearing its playback buffer when `input_audio_buffer.speech_started`
   or a cancelled `response.done` arrives.
3. The response was active or pending at the time of speech start; spurious
   cancel requests when nothing is active intentionally do not set the discard
   guard.
4. If using WebRTC, remember audio buffer clearing is server-side; inspect
   `output_audio_buffer.clear` and remote audio track handling.

## Audio and transcription issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Live transcript deltas are absent | Live transcription disabled or backend does not support the expected partial path | Enable live transcription and prefer `parakeet-tdt` for live partials. Final transcription may still appear. |
| User speech is cut into too many turns | Silence threshold too short for the speaker or language | Tune VAD/Smart Turn flags in `cli-and-server`; do not change Realtime event handling first. |
| WebSocket user audio accepted but no speech detected | Bad PCM format, very small chunks, or missing trailing speech/silence pattern | Send PCM16 mono chunks, keep the package-native 16 kHz target when possible, and include enough trailing silence for VAD to close the turn. |
| WebRTC client sends `input_audio_buffer.append` error | WebRTC carries audio as RTP | Remove JSON audio append and attach an audio track to the peer connection. |

## Session update surprises

`session.update` deep-merges explicit fields. If a voice change unexpectedly
preserves old tools or turn detection, that is expected. Send a replacement
`tools` list to replace tools, or explicit `null` for a field that should be
cleared. Avoid resending a broad stale session object from client state unless
all fields are intended.

## LLM proxy failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Proxy route unavailable | `--enable_llm_proxy` is off or selected LLM backend does not support proxying | Enable the flag and use `responses-api` or `chat-completions`. |
| Upstream auth error | The proxy forwards to the configured upstream and does not invent credentials | Set `--responses_api_api_key` or the upstream's expected environment variable. |
| Proxy works locally but is unsafe on LAN | The package proxy has no authentication or rate limiting | Bind to loopback or place it behind a gateway with TLS/auth/rate limits. |
| Request hangs during generation | Read timeout is intentionally unbounded for long generations | Use smaller upstream model prompts, provider-side limits, or client request timeouts. |

## Safe probe usage

Use `scripts/realtime_endpoint_probe.py --url <endpoint>` to confirm that an
endpoint accepts a WebSocket and emits `session.created`. Add
`--send-session-update` to verify the session update acknowledgement. The probe
prints event types only and never prints credentials or audio payloads.

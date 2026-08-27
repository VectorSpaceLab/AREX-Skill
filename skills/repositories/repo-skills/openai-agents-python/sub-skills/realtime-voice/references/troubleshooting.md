# Realtime and Voice Troubleshooting

Use this matrix to diagnose realtime session, telephony, and voice pipeline issues without relying on original repo examples or credentialed demos.

## Quick Triage

1. Decide whether the app is using `agents.realtime` or `agents.voice`.
2. For realtime, validate static config with [../scripts/check_realtime_config.py](../scripts/check_realtime_config.py) before opening a websocket.
3. For voice pipeline imports, check whether `pip install 'openai-agents[voice]'` was used.
4. For telephony, confirm format, chunking, credential/webhook setup, and playback tracking separately.
5. For interruption problems, verify both server-side settings and local playback flushing.

## Missing Voice Extra or `numpy`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` from `agents.voice` mentioning `numpy` and `websockets` | Optional voice dependencies are not installed. | Install `pip install 'openai-agents[voice]'` in the app environment. |
| `agents.realtime` imports but `agents.voice` does not | Base package includes realtime but not voice pipeline extras. | Install only the `voice` extra if the task needs `VoicePipeline`; do not install unrelated extras. |
| Voice code fails in a minimal container with no audio devices | Import may work, but examples using `sounddevice` need host audio libraries/devices. | Keep tests on `AudioInput` with numpy buffers or fake STT/TTS models; do not require microphone/speaker hardware. |

Use the bundled checker:

```bash
python skills/openai-agents-python/sub-skills/realtime-voice/scripts/check_realtime_config.py --check-voice --json
```

The checker imports `agents.voice` and returns a clean install hint instead of a traceback when the optional extra is missing.

## Websocket, Network, and Authentication Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Connection fails before session events arrive | Missing API key, wrong endpoint URL, blocked network, or unsupported model. | Confirm `OPENAI_API_KEY` or `model_config["api_key"]`; verify model access and endpoint reachability outside the skill. |
| Azure realtime connection fails | Wrong endpoint shape or missing explicit headers. | Use a GA realtime WebSocket URL and pass Azure auth headers explicitly. Avoid legacy beta realtime paths. |
| Authorization missing when `headers` is set | The SDK does not inject `Authorization` when custom headers are supplied. | Add `authorization` or `api-key` in `model_config["headers"]` yourself. |
| Custom listener sees raw errors but high-level loop continues unexpectedly | The session emits `raw_model_event` plus transformed `error` events. | Handle both `raw_model_event` for diagnostics and `error` for user-visible failures. |

Static config validation cannot prove network reachability or credentials. Do not make the skill helper call OpenAI.

## Audio Format Mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Audio sounds garbled or too fast/slow | Format/sample-rate mismatch between app audio and session settings. | For local PCM use `pcm16` with 24 kHz mono int16 bytes. For Twilio-style media streams use `g711_ulaw` at 8 kHz. |
| Telephony media stream produces silence or noise | Sending decoded PCM while session expects µ-law, or vice versa. | Keep incoming Twilio µ-law bytes as µ-law when using `g711_ulaw`; configure both input and output formats consistently. |
| Interruption truncation seems wrong | Playback tracker format was not set or playback bytes do not match output format. | Pass `RealtimePlaybackTracker` through `model_config`; call `on_play_bytes` or `on_play_ms` only for audio actually heard. |
| Voice pipeline rejects input buffer | `AudioInput.buffer` is not `np.int16` or `np.float32`. | Convert arrays to supported dtype before constructing `AudioInput`. |

The realtime SDK normalizes `pcm16`, `g711_ulaw`, `g711_alaw`, and mapping forms like `{"type": "audio/pcm", "rate": 24000}`. Unknown custom strings may pass through to lower layers but should be treated as advanced provider-specific usage.

## Turn Detection and Manual Response Control

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Audio is sent but the model does not respond | Turn detection is disabled or `create_response` is false. | Commit audio and send a raw `response.create`, or enable server/semantic VAD with `create_response: True`. |
| Model responds before the user finishes speaking | VAD settings are too eager. | Tune `turn_detection` fields such as `eagerness`, `threshold`, `silence_duration_ms`, or use manual response control. |
| App needs to inspect/gate audio before a response | High-level `send_message()` starts responses for text, while audio buffering may need explicit flow. | Send raw `input_audio_buffer.commit` and `response.create` through `session.model.send_event(...)` after app checks pass. |
| SIP caller hears no greeting | Attach flow waits for user input. | After session attach, send a raw `response.create` with greeting instructions. |

Manual response control pattern:

```python
from agents.realtime.model_inputs import RealtimeModelSendRawMessage

await session.model.send_event(
    RealtimeModelSendRawMessage(message={"type": "input_audio_buffer.commit"})
)
await session.model.send_event(
    RealtimeModelSendRawMessage(message={"type": "response.create"})
)
```

Use raw events only when the high-level helpers do not cover the flow.

## Interruption and Truncation Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Assistant keeps playing after the user barges in | App did not stop local playback on `audio_interrupted`. | Flush output queues, stop/fade playback, and reset jitter buffers when `audio_interrupted` arrives. |
| Server history includes audio the user never heard | No custom playback tracker in remote/delayed playback. | Pass `RealtimePlaybackTracker` and update it from real playback acknowledgements. |
| Truncation is skipped | Tracker reports no current audio, or elapsed time exceeds completed audio length while no response is ongoing. | Verify `on_play_bytes`/`on_play_ms` calls include the correct `item_id` and `content_index`. |
| Local playback clicks on interruption | Audio output is cut abruptly. | Fade the current chunk briefly, then flush queued chunks. |

For telephony, update playback progress from provider mark/ack events instead of assuming bytes were heard immediately.

## Telephony Credentials and Server Concerns

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Twilio/SIP examples cannot run locally | They require OpenAI credentials, Twilio credentials, public webhook URLs, and network access. | Distill the pattern into app code; do not require original examples as runnable prerequisites. |
| SIP attach raises `UserError` | `OpenAIRealtimeSIPModel` requires `model_config["call_id"]`. | Pass the realtime call id from the incoming call webhook after accepting the call. |
| Duplicate incoming webhooks spawn multiple observers | Provider retry behavior or webhook duplication. | Track active call tasks by `call_id` and ignore duplicates while one is running. |
| Webhook security concerns | Unsigned or unverified incoming webhooks. | Verify webhook signatures in application code before accepting calls or starting observers. |
| Phone call audio lags or starts clipped | Startup buffering/chunking not tuned. | Buffer a small number of 40–50 ms chunks before forwarding; flush stale buffers periodically. |

Do not store phone numbers, stream IDs, call IDs, webhook secrets, or API keys in reusable skill files.

## Unsupported Structured Outputs in `RealtimeAgent`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Code attempts `RealtimeAgent(output_type=...)` or expects Pydantic final output | `RealtimeAgent` does not support structured outputs. | Use a normal `Agent` with `Runner` for structured output, or make a realtime tool return structured JSON as a tool result. |
| Developer expects per-agent model settings | Realtime model settings are session-level. | Put model name, audio, modalities, and tool choice in `RealtimeRunner(config={"model_settings": ...})` or `runner.run(model_config={"initial_model_settings": ...})`. |
| Handoff input filters are expected | Realtime handoffs set `input_filter=None`. | Use `on_handoff`, `input_type`, and `is_enabled`; design history filtering outside realtime handoff input filters. |

Route normal structured-output agent design to ../core-runtime/SKILL.md and general handoff design to ../tools-handoffs-guardrails/SKILL.md.

## Tool Approval or Guardrail Surprises

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tool requiring approval never runs | App does not handle `tool_approval_required`. | Call `approve_tool_call(call_id)` or `reject_tool_call(call_id)` from the session loop. |
| Tool input guardrail failure appears after approval prompt | Default guardrail timing runs immediately before execution after approval. | Set `tool_execution.pre_approval_tool_input_guardrails=True` if the app must check before prompting. |
| Output guardrail trips after some audio already played | Realtime guardrails run on debounced transcript text. | Handle `guardrail_tripped` and always stop local playback on `audio_interrupted`. |
| Tool rejection message is generic | No custom `tool_error_formatter` or rejection message. | Pass `rejection_message` to `reject_tool_call(...)` or configure `tool_error_formatter`. |

## Voice Pipeline Runtime Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Streamed voice app does not interrupt in-progress TTS | `VoicePipeline` does not provide built-in interruption handling. | Implement app-level microphone/speaker gating around lifecycle events or use realtime sessions for interruption-heavy apps. |
| Pipeline trace includes sensitive audio/transcripts | Defaults include sensitive data and audio. | Set `trace_include_sensitive_data=False` and `trace_include_sensitive_audio_data=False`, or disable tracing. |
| Pipeline test calls real STT/TTS services | Default provider is being used in tests. | Inject fake `STTModel` and `TTSModel` implementations. |
| Output chunks are too small/large | `TTSModelSettings.buffer_size` or `text_splitter` is not tuned. | Adjust `buffer_size`, `text_splitter`, or `transform_data`. |

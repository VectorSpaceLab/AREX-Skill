# Realtime API Reference

This reference distills the realtime docs, source, examples, and tests into self-contained guidance for future agents building server-side realtime sessions with `openai-agents`.

## What Realtime Is For

Realtime agents keep a live transport open so the model can receive text/audio incrementally, stream audio back, call tools, hand off between specialists, and recover from interruptions without starting a fresh HTTP request for every turn.

The Python SDK realtime path is server-side:

- Default transport: `OpenAIRealtimeWebSocketModel` over WebSocket.
- Telephony attach transport: `OpenAIRealtimeSIPModel` with an existing realtime `call_id`.
- Browser WebRTC transport: outside this SDK; use platform WebRTC docs and use Python only for server-side orchestration if needed.

## Main Classes

| Class or function | Import | Purpose |
| --- | --- | --- |
| `RealtimeAgent` | `from agents.realtime import RealtimeAgent` | Realtime-specialized agent with instructions, tools, handoffs, hooks, and output guardrails. |
| `RealtimeRunner` | `from agents.realtime import RealtimeRunner` | Session factory that binds a starting realtime agent, optional realtime model, and run config. |
| `RealtimeSession` | `from agents.realtime import RealtimeSession` | Live async session for sending input, receiving events, approving tools, rejecting tools, interrupting, and updating the active agent. |
| `RealtimePlaybackTracker` | `from agents.realtime import RealtimePlaybackTracker` | Application-owned playback progress tracker used for accurate interruption truncation. |
| `OpenAIRealtimeWebSocketModel` | `from agents.realtime import OpenAIRealtimeWebSocketModel` | Default OpenAI realtime WebSocket transport. |
| `OpenAIRealtimeSIPModel` | `from agents.realtime import OpenAIRealtimeSIPModel` | Attach transport for existing realtime calls, used by SIP flows. |
| `realtime_handoff` | `from agents.realtime import realtime_handoff` | Creates a realtime handoff with realtime-compatible limitations and validation. |
| `RealtimeModelSendRawMessage` | `from agents.realtime.model_inputs import RealtimeModelSendRawMessage` | Sends raw Realtime API client events through `session.model.send_event(...)`. |

## `RealtimeAgent` Shape and Limits

`RealtimeAgent` intentionally supports fewer knobs than normal `Agent` because the session owns one realtime model connection.

Supported directly on the agent:

- `name`
- `handoff_description`
- `instructions` as a string or callable
- `prompt`
- `tools`
- `handoffs`
- `output_guardrails`
- `hooks`
- `clone(**kwargs)` for shallow copies

Important limitations:

- Model choice is session-level, not per-agent.
- Normal `model_settings` are not agent-level for realtime.
- Structured outputs are not supported by `RealtimeAgent`.
- Normal `tool_use_behavior` is not part of realtime agent behavior.
- Voice can be configured, but changing voice after a session has already spoken is not a safe design assumption.

Use a normal `Agent` and route to ../core-runtime/SKILL.md when a task primarily needs structured outputs, text-only HTTP/SSE streaming, or normal `Runner` behavior.

## Session Lifecycle

A standard realtime session follows this sequence:

1. Define one or more `RealtimeAgent` instances.
2. Create `RealtimeRunner(starting_agent=agent, config=run_config)`.
3. Call `session = await runner.run(context=..., model_config=...)`.
4. Enter the session with `async with session:` or `await session.enter()`.
5. Send text, structured messages, or audio with `send_message()` / `send_audio()`.
6. Consume `async for event in session:` until the application decides to close.
7. Let the context manager call `close()`, or call `await session.close()` when using `enter()` manually.

Minimal pattern:

```python
from agents.realtime import RealtimeAgent, RealtimeRunner

agent = RealtimeAgent(
    name="Assistant",
    instructions="You are a concise voice assistant.",
)

runner = RealtimeRunner(
    starting_agent=agent,
    config={
        "model_settings": {
            "model_name": "gpt-realtime-2",
            "audio": {
                "input": {
                    "format": "pcm16",
                    "transcription": {"model": "gpt-4o-mini-transcribe"},
                    "turn_detection": {"type": "semantic_vad", "interrupt_response": True},
                },
                "output": {"format": "pcm16", "voice": "ash"},
            },
        }
    },
)

async with await runner.run() as session:
    await session.send_message("Say hello in one short sentence.")
    async for event in session:
        if event.type == "audio":
            play_bytes(event.audio.data)
        elif event.type == "agent_end":
            break
        elif event.type == "error":
            raise RuntimeError(event.error)
```

## Config Surfaces

### `RealtimeRunner(config=...)` / `RealtimeRunConfig`

Use runner config for SDK-side and session-default behavior:

| Key | Purpose |
| --- | --- |
| `model_settings` | Session model settings, including model name, audio settings, modalities, prompt, tools, handoffs, tracing. |
| `output_guardrails` | Extra output guardrails for realtime responses. |
| `guardrails_settings.debounce_text_length` | Transcript size threshold before realtime output guardrails run. |
| `tracing_disabled` | Disable realtime tracing for this run. |
| `async_tool_calls` | Whether local function calls run asynchronously; defaults to true. |
| `tool_execution.pre_approval_tool_input_guardrails` | Runs tool input guardrails before emitting tool approval events, then runs them again before execution. |
| `tool_error_formatter` | Formats local tool execution or approval-rejection errors returned to the model. |

### `runner.run(model_config=...)` / `RealtimeModelConfig`

Use model config for transport connection options and run-time overrides:

| Key | Purpose |
| --- | --- |
| `api_key` | API key string or callback; if absent, OpenAI transport uses `OPENAI_API_KEY`. |
| `url` | Custom WebSocket endpoint, including Azure GA realtime endpoints. |
| `headers` | Explicit transport headers; when supplied, authorization is not injected automatically. |
| `initial_model_settings` | Model settings merged at connection time and overriding runner defaults where keys overlap. |
| `playback_tracker` | `RealtimePlaybackTracker` instance for accurate interruption truncation. |
| `call_id` | Attach to an existing realtime call; this repo's shipped example uses SIP. |

### `RealtimeSessionModelSettings`

Prefer the nested `audio` shape for new code:

```python
{
    "model_name": "gpt-realtime-2",
    "audio": {
        "input": {
            "format": "pcm16",
            "transcription": {"model": "gpt-4o-mini-transcribe"},
            "noise_reduction": {"type": "near_field"},
            "turn_detection": {
                "type": "semantic_vad",
                "interrupt_response": True,
                "create_response": True,
            },
        },
        "output": {"format": "pcm16", "voice": "ash", "speed": 1.0},
    },
    "output_modalities": ["audio"],
    "tool_choice": "auto",
}
```

Other useful model settings include:

- `instructions`
- `prompt`
- `modalities`
- `output_modalities`
- `voice`
- `speed`
- `max_output_tokens`
- legacy flat aliases: `input_audio_format`, `output_audio_format`, `input_audio_transcription`, `input_audio_noise_reduction`, `turn_detection`
- `tool_choice`
- `parallel_tool_calls`
- `reasoning`
- `tools`
- `handoffs`
- `tracing`

Supported audio format names in source helpers include `pcm16`, `g711_ulaw`, and `g711_alaw`; mapping forms such as `{"type": "audio/pcm", "rate": 24000}` are also accepted.

## Inputs

### Text Input

Use `session.send_message("...")` for simple user text. The high-level path creates user input and starts a response for typical text turns.

### Structured Text and Image Input

Use `RealtimeUserInputMessage`-style dictionaries for multimodal user messages:

```python
await session.send_message(
    {
        "type": "message",
        "role": "user",
        "content": [
            {"type": "input_image", "image_url": image_data_url, "detail": "high"},
            {"type": "input_text", "text": "Describe this image."},
        ],
    }
)
```

The web-app example uses this shape to forward image data URLs. Keep image payload handling in the application; the SDK accepts the structured message.

### Audio Input

Use `await session.send_audio(audio_bytes)` for raw audio chunks. For manual turn boundaries, pass `commit=True` or send lower-level raw events.

Common input assumptions:

- `pcm16`: raw 16-bit PCM at 24 kHz in the SDK examples and length calculations.
- `g711_ulaw`: telephony-friendly µ-law format at 8 kHz, used by the Twilio Media Streams pattern.
- `g711_alaw`: A-law variant where required by telephony infrastructure.

## Manual Turn and Response Control

Server-side turn detection can create responses automatically. If turn detection is disabled or you need explicit gating, use raw client events through the model transport.

Pattern for raw response creation:

```python
from agents.realtime.model_inputs import RealtimeModelSendRawMessage

await session.model.send_event(
    RealtimeModelSendRawMessage(
        message={"type": "response.create"}
    )
)
```

Use raw `session.update`, `input_audio_buffer.commit`, and `response.create` when:

- `turn_detection` is disabled.
- The app needs to inspect or gate audio before triggering a response.
- A SIP/telephony call needs an immediate greeting after attachment.
- A custom out-of-band response prompt is required.

## Session Events

Consume `RealtimeSessionEvent` values with `async for event in session:`. Useful event types:

| Event type | Meaning | Common handler |
| --- | --- | --- |
| `agent_start` | A realtime turn started for the current agent. | Update UI state. |
| `agent_end` | Current assistant turn ended. | Stop turn spinner or break a one-turn demo loop. |
| `audio` | Assistant audio bytes are ready. | Enqueue for playback with `event.item_id` and `event.content_index`. |
| `audio_end` | Assistant audio item completed. | Flush playback state for the item. |
| `audio_interrupted` | Assistant audio was interrupted. | Stop local playback and clear queued audio. |
| `tool_start` | Local tool execution started. | Show tool progress. |
| `tool_end` | Local tool execution completed. | Log output or update UI. |
| `tool_approval_required` | A tool is paused for human approval. | Call `approve_tool_call()` or `reject_tool_call()`. |
| `handoff` | Active realtime agent changed. | Update specialist label. |
| `history_added` | A new local history item was appended. | Render incremental transcript or tool item. |
| `history_updated` | Local history changed. | Re-render full conversation state. |
| `guardrail_tripped` | Output guardrail interrupted the response. | Stop playback, show replacement-flow notice. |
| `input_audio_timeout_triggered` | Server detected inactivity timeout. | Prompt user or trigger fallback. |
| `error` | SDK/model error event. | Surface and close/retry according to app policy. |
| `raw_model_event` | Forwarded low-level transport event. | Debug, custom telemetry, or feature-specific handling. |

For UI history, prefer `history_added`/`history_updated` over parsing raw events. Strip binary audio payloads before sending history over browser/websocket UI channels.

## Interruption and Playback Tracking

Realtime interruption has two sides:

1. Send an interrupt or rely on server-side `turn_detection.interrupt_response`.
2. Stop local playback immediately and tell the transport how much audio the user actually heard.

For local low-latency playback, the default tracker can be sufficient. For remote playback, telephony, buffering, fade-outs, or jitter buffers, create a tracker:

```python
from agents.realtime import RealtimePlaybackTracker

playback_tracker = RealtimePlaybackTracker()
session = await runner.run(model_config={"playback_tracker": playback_tracker})
```

When audio is actually played, call one of:

```python
playback_tracker.on_play_bytes(event.item_id, event.content_index, played_bytes)
playback_tracker.on_play_ms(event.item_id, event.content_index, elapsed_ms)
```

On `audio_interrupted`, stop local playback and clear queued chunks. The tracker resets when the model processes interruption. Tests verify that custom playback progress is used to build `conversation.item.truncate`, and that no truncation is sent when no audio is playing.

Telephony mark/ack pattern:

- Send outgoing audio to the telephony provider.
- Send a mark after each audio chunk.
- Store mark id → `(item_id, content_index, byte_count)`.
- When the provider acknowledges the mark, call `playback_tracker.on_play_bytes(...)` or `on_play_ms(...)`.
- On `audio_interrupted`, send a clear/flush command to the telephony provider.

## Tools and Approvals

Realtime agents support normal `function_tool` tools. Tool behavior is live-session oriented:

- Tool calls arrive as realtime model events and become `tool_start` / `tool_end` events.
- Structured tool outputs are serialized to JSON when possible before being sent back to the model.
- `async_tool_calls` defaults to true so multiple tool calls can run without blocking event consumption.

Approval pattern:

```python
async for event in session:
    if event.type == "tool_approval_required":
        if user_allows(event.tool.name, event.arguments):
            await session.approve_tool_call(event.call_id)
        else:
            await session.reject_tool_call(event.call_id, rejection_message="Denied by user.")
```

`approve_tool_call(call_id, always=False)` and `reject_tool_call(call_id, always=False, rejection_message=None)` are no-ops if the pending call id is unknown. Use `always=True` only when the application intentionally wants to remember that approval or rejection decision through the session context.

To run tool input guardrails before the approval event is emitted:

```python
runner = RealtimeRunner(
    agent,
    config={"tool_execution": {"pre_approval_tool_input_guardrails": True}},
)
```

Those guardrails still run again immediately before execution after approval.

## Handoffs

Realtime handoffs can be direct `RealtimeAgent` entries or explicit `realtime_handoff(...)` wrappers:

```python
from agents.realtime import RealtimeAgent, realtime_handoff

billing = RealtimeAgent(name="Billing", instructions="Handle billing issues.")
triage = RealtimeAgent(
    name="Triage",
    instructions="Route callers to the right specialist.",
    handoffs=[realtime_handoff(billing, tool_name_override="transfer_to_billing")],
)
```

Realtime handoff notes:

- Bare `RealtimeAgent` handoffs are auto-wrapped.
- `realtime_handoff` supports tool name/description overrides, `on_handoff`, `input_type`, and `is_enabled`.
- Realtime handoffs deliberately set `input_filter=None`; normal handoff input filters are not supported.
- `input_type` requires `on_handoff` and strict JSON schema validation.
- `is_enabled` can be a boolean, sync callable, or async callable.

## Output Guardrails

Realtime output guardrails run against accumulated transcript text, not every partial token. The key runtime details are:

- `guardrails_settings.debounce_text_length` controls how much transcript text accumulates before a guardrail run.
- A trip emits `guardrail_tripped` instead of raising out of the session loop.
- The session interrupts the active response, forces `response.cancel`, and sends a follow-up user message naming the triggered guardrail so the model can produce a replacement.
- The audio player must still handle `audio_interrupted`, because guardrails run after transcript accumulation and some audio may already be buffered.

## SIP and Telephony

Use `OpenAIRealtimeSIPModel` when OpenAI sends a realtime call webhook and your app has an existing `call_id` to attach to.

Attach pattern:

```python
from agents.realtime import RealtimeRunner
from agents.realtime.openai_realtime import OpenAIRealtimeSIPModel

runner = RealtimeRunner(starting_agent=agent, model=OpenAIRealtimeSIPModel())

async with await runner.run(model_config={"call_id": call_id}) as session:
    async for event in session:
        ...
```

Source tests verify that SIP connect requires `call_id` and uses a URL shaped like `wss://api.openai.com/v1/realtime?call_id=...`.

If accepting an incoming call separately, align the accept payload with the agent-derived session settings. `OpenAIRealtimeSIPModel.build_initial_session_payload(...)` can build a session payload from a realtime agent, context, model config, run config, and overrides.

For Twilio-style media streams:

- Use `input_audio_format="g711_ulaw"` and `output_audio_format="g711_ulaw"` or equivalent nested audio format settings.
- Buffer incoming µ-law bytes into predictable 40–50 ms chunks before `send_audio()`.
- Send outgoing assistant audio as provider media payloads.
- Use provider mark/clear events to update playback tracking and handle interruption.
- Keep credential checks and webhook signature verification in application code, not in reusable skill content.

## Low-Level Transport Hooks

`session.model` exposes the `RealtimeModel` implementation. Use it sparingly for:

- `add_listener(...)` / `remove_listener(...)` custom transport listeners.
- Raw client events through `send_event(RealtimeModelSendRawMessage(...))`.
- Manual `session.update`, `response.create`, and `input_audio_buffer.commit` control.
- Custom WebSocket endpoint, headers, API key callbacks, and `call_id` attach through `model_config`.

If custom headers are supplied, add authorization explicitly. The SDK does not inject `Authorization` when `headers` is provided.

## Safe Static Validation

Use [../scripts/check_realtime_config.py](../scripts/check_realtime_config.py) to catch common config mistakes before opening a websocket. It imports realtime classes, validates audio formats and common setting shapes, and optionally detects whether the `voice` extra is installed. It does not prove credentials, endpoint reachability, device availability, or model access.

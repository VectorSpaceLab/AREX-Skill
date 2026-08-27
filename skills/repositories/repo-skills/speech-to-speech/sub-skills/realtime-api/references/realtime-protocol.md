# Realtime protocol reference

`speech-to-speech serve` exposes an OpenAI Realtime-compatible endpoint at
`/v1/realtime`. The implementation accepts JSON client events, translates them
into the queue-backed VAD → STT/audio-input → LLM → output-processor → TTS
pipeline, and emits protocol events back to the client.

## WebSocket connection lifecycle

1. Open `ws://<host>:<port>/v1/realtime`.
2. Server immediately sends `session.created` with the current session.
3. Client usually sends `session.update` to set instructions, voice, tools,
   output modalities, and turn-detection preferences.
4. Server replies with `session.updated` after a valid update.
5. Client streams audio or text/tool items, then either lets server VAD trigger
   implicit responses or sends `response.create` explicitly.
6. Server emits speech, transcription, assistant text/audio, tool-call, and
   terminal response events.

A pool unit is claimed for the session. If all units are busy, a connection
receives an `error` event whose error type is `session_limit_reached`.

## Client event families

| Event | Use |
| --- | --- |
| `input_audio_buffer.append` | WebSocket-only base64 PCM audio. The service decodes, resamples to 16 kHz if needed, chunks into 512-sample frames, and enqueues for VAD. |
| `input_audio_buffer.commit` | Commit a buffered audio turn when manually controlling audio. Empty commits are rejected. |
| `session.update` | Deep-merge session configuration. Lists such as tools are replaced wholesale; nested audio fields preserve siblings not explicitly set. |
| `conversation.item.create` | Add user text/image/audio or function-call output items without necessarily triggering generation. |
| `response.create` | Ask the LLM for a response. Per-response instructions, tool choice, and output modalities override the session for that response. |
| `response.cancel` | Cancel the active or queued response and re-enable listening. |
| `output_audio_buffer.clear` | WebRTC-only request to flush server-side buffered output audio. |

## Server event families

| Event | Signal |
| --- | --- |
| `session.created`, `session.updated` | Session state lifecycle. |
| `error` | Protocol, validation, capacity, unsupported transport, or response-state error. |
| `input_audio_buffer.speech_started`, `input_audio_buffer.speech_stopped` | VAD turn boundaries. Speech start can also signal barge-in cancellation. |
| `conversation.item.created` | A user text item or function-call output was accepted into conversation state. |
| `conversation.item.input_audio_transcription.delta` | Live partial transcript, when enabled by the selected STT/VAD path. |
| `conversation.item.input_audio_transcription.completed` | Final user transcript plus duration bookkeeping. |
| `response.created` | A response became active. |
| `response.output_audio_transcript.delta`, `.done` | Assistant transcript deltas and final transcript. Concatenate deltas for live display; treat `.done` as finalization. |
| `response.output_audio.delta`, `.done` | WebSocket audio chunks and output item audio completion. WebRTC does not send audio delta events; RTP carries audio. |
| `response.function_call_arguments.done` | A completed function call with `call_id`, `name`, and JSON `arguments`. |
| `response.done` | Response terminal status: `completed`, `cancelled`, or `failed`. |

## Session update merge rules

`RuntimeConfig.apply_session_update` applies only fields explicitly present in
the update. Nested Pydantic models recurse instead of replacing whole siblings.
Practical effects:

- Updating `audio.output.voice` preserves `audio.input.turn_detection`.
- Sending `audio.input.turn_detection: null` intentionally clears turn
  detection.
- Sending a new `tools` list replaces the entire tool list.
- Sequential updates accumulate instructions, voice, and tool choice unless a
  later update touches the same field.

This behavior matters for clients that change voice or tool configuration at
runtime: send only the fields being changed.

## Response and turn ordering

The backend allows one active response at a time. If a client sends a second
`response.create` before the first response has produced `response.done`, the
client should expect a state error such as
`conversation_already_has_active_response`. Serialize creates in the client or
queue the next create until the prior response finishes.

Assistant text and tool calls preserve model order. The LLM output processor
puts each assistant output event and any matching TTS input onto one ordered
queue, so text before a tool call reaches the protocol before the tool event,
and text after a tool call remains after it.

## Tool call round trip

1. Client declares function tools in `session.update`.
2. The LLM emits `response.function_call_arguments.done` with a `call_id` and
   argument JSON.
3. Client executes the tool.
4. Client sends:

```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_...",
    "output": "tool result text or JSON"
  }
}
```

5. If the tool result should be spoken or summarized, client sends
   `response.create`. For fire-and-forget physical/expression tools, the model
   should have spoken the lead-in before the call, and no follow-up response is
   required unless the result has user-facing information.

## Barge-in and cancellation

When user speech starts during an active or pending response and
`turn_detection.interrupt_response` is true:

- `input_audio_buffer.speech_started` is delivered after closing any active
  response audio/transcript item.
- The cancel scope generation increments; stale LLM/TTS output is dropped.
- Pending response keys are closed so late output cannot leak into a later
  session or response.
- WebSocket clients must clear their client-side playback buffer when they see
  `speech_started` or a cancelled `response.done`.
- WebRTC clears unplayed audio on the server-side `PipelineAudioTrack`.

If interruption is disabled in session config, user speech is still processed
but does not cancel the assistant response.

## Audio chunking and sample rates

- The internal pipeline sample rate is 16 kHz PCM16.
- WebSocket `input_audio_buffer.append` may deliver larger base64 payloads; the
  service splits them into 512-sample chunks and keeps remainder bytes for the
  next append.
- The packaged audio client omits explicit PCM format for 16 kHz; if a client
  sets a format, only the supported Realtime PCM shape should be used.
- WebRTC sends browser audio as RTP/Opus at 48 kHz; the server downmixes and
  resamples to 16 kHz before queueing it.

## Pool release and stuck-session safety

Each accepted session owns one `PipelineUnit`. On disconnect, the route handler
sends a `SESSION_END` control message through the handler chain. The unit is not
released until that sentinel drains back to the output queue, preventing stale
transcripts or audio from leaking into the next client. If handlers wedge, the
unit is quarantined and can be surfaced as stuck rather than reused unsafely.

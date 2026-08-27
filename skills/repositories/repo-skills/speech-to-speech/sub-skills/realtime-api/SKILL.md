---
name: realtime-api
description: "Use and debug speech-to-speech's OpenAI Realtime-compatible
  WebSocket/WebRTC API, session lifecycle, tool calls, cancellation, and LLM
  proxy endpoints."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Realtime API

Use this sub-skill when the task involves a client, service, gateway, or test
that speaks to `speech-to-speech` over its OpenAI Realtime-compatible API.

## Route by surface

- **WebSocket clients:** read [Realtime protocol](references/realtime-protocol.md)
  for `/v1/realtime`, event ordering, PCM chunking, and turn lifecycle.
- **Python/OpenAI SDK clients or the packaged audio client:** read
  [Python client and proxy](references/python-client-and-proxy.md).
- **WebRTC clients:** read [WebRTC transport](references/webrtc-transport.md)
  before using `/v1/realtime/calls`, RTP audio, or TURN/ICE settings.
- **LLM side-task proxy:** read
  [Python client and proxy](references/python-client-and-proxy.md#llm-proxy)
  before enabling `/v1/chat/completions` or `/v1/responses` on the speech
  server.
- **Command selection, server host/port, `serve`/`local`/`talk`:** route to
  [cli-and-server](../cli-and-server/SKILL.md).
- **STT/LLM/TTS models, direct audio-input model compatibility, voices, and
  optional extras:** route to
  [components-and-backends](../components-and-backends/SKILL.md).
- **Browser demo connection modes and web tools:** route to
  [browser-demo](../browser-demo/SKILL.md).

## Operating sequence

1. Confirm the server endpoint. WebSocket clients use a full URL ending in
   `/v1/realtime`; WebRTC clients POST SDP to `/v1/realtime/calls`.
2. Send or inspect `session.update` before response generation. Session updates
   deep-merge explicit fields: changing output voice does not reset input turn
   detection or tools unless those fields are explicitly replaced or cleared.
3. Stream microphone PCM over WebSocket with `input_audio_buffer.append`, or use
   RTP media over WebRTC. Do not send `input_audio_buffer.append` on the WebRTC
   data channel.
4. Observe response serialization: only one `response.create` may be active at
   a time; wait for `response.done` or implement a client-side response queue.
5. For barge-in/cancel bugs, track both protocol events and server-side
   generation/response-key behavior. See [troubleshooting](references/troubleshooting.md).
6. Use the bundled probe when only endpoint readiness is needed:
   [`scripts/realtime_endpoint_probe.py`](scripts/realtime_endpoint_probe.py).

## Key invariants

- Pipeline audio is 16 kHz PCM16 internally; WebSocket sends base64 PCM chunks
  as JSON events, while WebRTC uses RTP/Opus on the media track.
- `session.created` is the first event after a WebSocket connection or data
  channel open. Successful `session.update` receives `session.updated`.
- Assistant output may interleave text and tool calls. Tool results are sent as
  `conversation.item.create` with `type: function_call_output`; send
  `response.create` afterward only when the tool result needs a spoken/text
  follow-up.
- Barge-in is cooperative: VAD emits speech events, the send loop cancels the
  active generation, stale LLM/TTS output is discarded, and clients clear
  unplayed audio.
- The LLM proxy is unauthenticated by this package. Enable it only on loopback,
  a trusted network, or behind a gateway that owns access control.

Detailed event schemas, client patterns, transport differences, and recovery
steps are bundled in the linked references above.

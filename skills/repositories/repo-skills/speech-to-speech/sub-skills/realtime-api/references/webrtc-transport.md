# WebRTC transport reference

The WebRTC transport exposes the same OpenAI Realtime session model as the
WebSocket endpoint, but moves microphone and assistant audio onto RTP media
tracks. JSON control events flow over a data channel named `oai-events`.

## Endpoint and handshake

WebRTC clients use the OpenAI GA calls endpoint:

```http
POST /v1/realtime/calls
Content-Type: application/sdp
```

The request body is the browser/client SDP offer. A successful response returns
status `201`, an SDP answer body, and a `Location` header ending in the created
call id. The server claims one pipeline unit from the same pool used by
WebSocket sessions; if no unit is available, the client receives the same
capacity class of error.

The transport requires the `webrtc` extra. Without `aiortc` and its media
dependencies, the endpoint answers with a clear not-implemented response rather
than silently falling back to WebSocket.

## Event channel

The browser or client creates a data channel named `oai-events`. When the data
channel opens, the server sends `session.created`. After that, JSON events use
the same event names and session/update semantics as WebSocket mode, except for
audio-buffer restrictions.

Allowed WebRTC data-channel events include:

- `session.update`
- `conversation.item.create`
- `response.create`
- `response.cancel`
- `output_audio_buffer.clear`

Rejected over WebRTC:

- `input_audio_buffer.append` — microphone audio must be the RTP audio track,
  not JSON/base64.

## Audio behavior

- Browser/client input audio is sent as an RTP audio track, usually Opus at the
  WebRTC media rate.
- The server downmixes/resamples inbound media to the 16 kHz PCM pipeline rate.
- Assistant TTS PCM is paced back as RTP audio frames. WebRTC clients should not
  expect `response.output_audio.delta`; that event is WebSocket-only because the
  voice arrives on the remote media track.
- The output track emits silence when the pipeline is idle so the peer
  connection remains stable.

## Barge-in and buffer clearing

WebRTC owns unplayed assistant audio on the server side. The service supports
`output_audio_buffer.clear` for WebRTC to drop queued output. The server also
clears output audio automatically on `response.cancel` and on VAD-driven
interruption when the session allows barge-in.

Client-side UI should still clear local transcript/playback indicators when it
receives terminal cancellation events:

1. `response.output_audio.done` and transcript finalization when applicable.
2. `response.done` with `status=cancelled` and reason such as `turn_detected`.
3. `input_audio_buffer.speech_started` for the new user turn.

## ICE and TURN configuration

The backend reads `SPEECH_TO_SPEECH_ICE_SERVERS` as a JSON list of RTCIceServer
entries. Use this when browsers and the backend cannot reach each other with
host candidates alone:

```bash
export SPEECH_TO_SPEECH_ICE_SERVERS='[
  {"urls": "stun:stun.example.com:3478"},
  {"urls": "turn:turn.example.com:3478", "username": "user", "credential": "secret"}
]'
```

For the browser demo, also set the demo-side `RTC_ICE_SERVERS` so the browser
receives matching STUN/TURN hints from `/api/config`. The backend setting and
the demo setting serve different peers; configure both for internet deployments.

## WebRTC versus WebSocket routing

Use WebRTC when browser media-track behavior, lower browser-side audio-copying
cost, or same-origin SDP proxying is the desired integration. Use WebSocket
when:

- You need explicit base64 PCM chunks for test fixtures or recording replay.
- You are debugging raw protocol ordering with a simple JSON client.
- You are in load-balancer demo mode, which is WebSocket-only in this repo.
- The `webrtc` extra cannot be installed in the target environment.

## Troubleshooting checklist

- `POST /v1/realtime/calls` returns 501 or not implemented: install
  `speech-to-speech[webrtc]` in the backend environment.
- Data channel opens but no `session.created`: confirm the data channel is named
  exactly `oai-events` and that the SDP answer was applied.
- JSON audio append fails: remove `input_audio_buffer.append`; WebRTC sends mic
  audio as RTP.
- Silent assistant audio while events work: inspect remote audio track wiring,
  autoplay policy, server output queue cancellation, and ICE selected pair.
- Works on LAN but not over the internet: configure TURN, expose UDP media
  paths, and make sure both browser and backend have compatible ICE server
  settings.

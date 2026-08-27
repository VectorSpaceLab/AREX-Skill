# Browser client behavior

The browser demo has two realtime clients with the same visual UI: a WebSocket
client and a WebRTC client. Both speak the OpenAI Realtime GA event model, but
they differ in who opens the connection and where audio flows.

## WebSocket mode

WebSocket is the default and the only transport available for user-entered URLs
and load-balancer mode.

Flow:

1. Browser opens the configured `ws(s)://.../v1/realtime` URL.
2. Server sends `session.created`.
3. Browser sends `session.update` using GA-style fields such as
   `session.audio.input`, `session.audio.output`, `session.output_modalities`,
   instructions, and tools.
4. The microphone AudioWorklet converts browser Float32 audio to 16 kHz PCM16
   and posts approximately 40 ms chunks.
5. Browser sends each chunk as `input_audio_buffer.append`.
6. Server returns transcript, tool-call, response transcript, and
   `response.output_audio.delta` events.
7. The playback worklet converts assistant PCM to the browser audio context and
   drives the orb's assistant-audio visual state.

WebSocket mode keeps a bounded in-memory copy of sent microphone frames. When
server VAD marks a user turn, the demo can wrap those frames into a replayable
WAV for conversation history. This replay feature is WebSocket-only because
WebRTC microphone audio rides a media track instead of JSON chunks.

## WebRTC mode

WebRTC is shown only when `SPEECH_TO_SPEECH_URL` pins the backend. It is hidden
for user-entered URLs and load-balancer mode.

Flow:

1. Browser creates an `RTCPeerConnection`, adds the microphone track, and opens
   a data channel named `oai-events`.
2. Browser POSTs its SDP offer to same-origin `/api/calls`.
3. Demo server forwards the SDP to the pinned backend's
   `POST /v1/realtime/calls` endpoint.
4. Browser applies the SDP answer and receives assistant audio as a remote audio
   track.
5. JSON events travel over `oai-events`; microphone audio never uses
   `input_audio_buffer.append`.

WebRTC requires the backend `webrtc` extra. Without it, the calls endpoint
returns a clear not-implemented response and the browser should remain on
WebSocket.

## Browser security rules

- Microphone and camera require HTTPS or localhost. Plain HTTP on a LAN IP such
  as `http://192.168.x.y` is rejected by browsers even when the backend is
  reachable.
- `localhost` and `127.0.0.1` are safe local origins for development.
- Chrome/Edge can switch output devices using `AudioContext.setSinkId`; other
  browsers may keep the system default speaker.
- Autoplay policies can block output until the user clicks/taps the orb.

## Settings and local storage

Important settings are stored locally in the browser, not on the speech server.
Known namespaces:

| Key/prefix | Purpose |
| --- | --- |
| `s2s.transport` | `websocket` or `webrtc` transport pick when available. |
| `s2s.ws.*` | WebSocket URL, voice, instructions, and related client settings. |
| `s2s.audio.inputId` | Preferred microphone device id. |
| `s2s.audio.outputId` | Preferred speaker/output device id. |

Settings -> Restart reconnects with the current URL, voice, instructions, and
transport choice. Device changes usually apply on the next conversation or
restart.

## Audio worklet behavior

Input worklet:

- consumes `getUserMedia` with echo cancellation, noise suppression, and auto
  gain control;
- resamples browser-rate Float32 audio to 16 kHz Int16 PCM;
- sends roughly 40 ms frames in WebSocket mode;
- applies the demo's noise gate in WebSocket capture mode.

Output worklet:

- consumes assistant PCM chunks;
- resamples/plays through the browser audio context;
- fades and buffers to reduce clicks;
- updates the orb's assistant-audio visual variables.

The WebSocket noise gate is hidden in WebRTC mode because the browser sends its
raw media track with browser-level audio processing instead.

## Docker and namespace behavior

A browser WebSocket is opened by the browser, so a host browser needs a host
reachable name such as `localhost:8765`. A WebRTC SDP handshake in the demo goes
through the demo server, so when that server is inside Docker it may need
`host.docker.internal:8765` to reach a backend on the host. If one URL makes
only one transport work, this namespace split is the first thing to check.

## Client-side validation checklist

- Confirm `/api/config` reports the expected mode and pinned URL/LB state.
- Confirm the selected transport is allowed for that mode.
- For WebSocket, inspect whether the browser opened the exact
  `/v1/realtime` URL and received `session.created`.
- For WebRTC, inspect `/api/calls`, the SDP answer, the `oai-events` data
  channel, ICE selected pair, and remote audio track.
- Confirm microphone permission and secure origin before debugging backend VAD.
- If user-audio replay is required, use WebSocket mode.

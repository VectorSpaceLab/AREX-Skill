# Browser demo troubleshooting

## Browser cannot use microphone or camera

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Permission prompt never appears | Page is not HTTPS or localhost | Use `http://localhost:7860` for local work or deploy behind HTTPS. LAN HTTP origins are not secure browser origins. |
| Permission was denied earlier | Browser/site permission persisted the denial | Reset microphone/camera permission in browser site settings, then reload. |
| No output device switch | Browser lacks `AudioContext.setSinkId` | Use system default output or a Chromium-based browser for live speaker switching. |
| Assistant hears itself | Speaker audio feeds the microphone | Use headphones, browser echo cancellation, or headless `talk --block-mic-during-playback` when barge-in is not being tested. |

## Demo cannot connect to backend

1. Confirm the backend is already listening at a full Realtime endpoint.
2. Confirm `/api/config` reports the intended mode: pinned, user-direct, or load
   balancer.
3. In pinned/user-direct mode, confirm the browser can open the WebSocket URL.
4. In Docker, check whether the URL is being dialed by the browser or by the
   containerized demo server.
5. In LB mode, inspect `/api/session`, queue status, and whether `SPACE_ID` is
   enabling metering.

Common fixes:

- Use `ws://localhost:8765/v1/realtime` for host-browser WebSocket testing.
- Use `host.docker.internal` only for traffic initiated from inside a Docker
  container.
- Do not expect WebRTC in user-entered URL or LB mode.
- Increase backend `--num_pipelines` when multiple browser sessions cause
  `session_limit_reached`.

## WebRTC-specific failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Transport selector lacks WebRTC | Backend URL is not env-pinned or mode is LB/user-entered | Set `SPEECH_TO_SPEECH_URL`; WebRTC is intentionally locked to pinned mode. |
| `/api/calls` fails with 501-like backend message | Backend lacks `speech-to-speech[webrtc]` | Install the backend extra and restart the backend process. |
| Handshake succeeds but no media | ICE cannot connect or browser blocked playback | Configure `RTC_ICE_SERVERS` and backend `SPEECH_TO_SPEECH_ICE_SERVERS`; check remote audio track and autoplay gesture. |
| WebSocket works but WebRTC does not in Docker | SDP proxy and browser socket use different network namespaces | Use a URL reachable from the demo container for WebRTC or run the demo without Docker. |

## Web search unavailable

- If `SERPER_API_KEY` is set server-side, the Tools panel should show search as
  ready and keep the key hidden from the browser.
- If no server key exists, the user must paste a Serper key in the Tools panel.
- If the tool is disabled, verify the active session received a new
  `session.update` after toggling tools.
- Search provider errors should appear as tool/search errors; do not expose the
  server-side key in logs or UI.

## Camera tool returns weak or irrelevant answers

- Confirm the tool is enabled and camera permission is granted.
- Confirm the upstream LLM is vision-capable; the tool can provide an image, but
  a text-only model cannot reason over it.
- On WebRTC, remember the snapshot may be re-encoded smaller to fit a data
  channel message budget.
- Ensure the client sends exactly one follow-up `response.create` after the tool
  output batch completes.

## Startup greeting surprises

- Greeting speaks before the user's first turn: set `STARTUP_GREETING` to an
  empty value.
- Greeting repeats on reconnect: expected per connection, but it should not
  repeat within one connection.
- Greeting seems to hide first-turn latency: disable it for benchmarking or
  native-audio tests.

## Usage limits and queue confusion

- Metering is active only when both `LOAD_BALANCER_URL` and `SPACE_ID` are set.
- Queue waiting time should not count as conversation usage; metering starts
  when a session is claimed.
- Local runs are unmetered even when a load-balancer URL is present without
  Space identity.
- At capacity means the queue itself is full; busy means every compute is in
  use but queueing may still be possible.

## UI regression checklist

Before shipping a UI change:

- No saturated color outside the orb or small role echoes.
- Keyboard focus remains visible on every interactive element.
- The layout works at 360 px width.
- `prefers-reduced-motion` is respected.
- Tap targets are at least 44 px.
- Mono is used only for machine/status identifiers, not explanatory prose.

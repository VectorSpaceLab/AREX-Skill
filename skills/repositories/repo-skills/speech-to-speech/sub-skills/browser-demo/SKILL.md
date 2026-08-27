---
name: browser-demo
description: "Run, deploy, and modify the speech-to-speech browser demo,
  including WebSocket/WebRTC client modes, tools, search/camera flows, Hugging
  Face Space limits, and UI behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Browser demo

Use this sub-skill when the task is to run the browser voice UI, connect it to a
`speech-to-speech` backend, deploy it as a Space/container, debug browser audio
or transport selection, change demo tools/search/camera behavior, or preserve
UI design rules while editing the demo.

## Route by task

- **Start or deploy the demo server:** read
  [Demo deployment](references/demo-deployment.md).
- **Debug WebSocket/WebRTC browser connection, microphone, audio worklets,
  localStorage, or Docker hostnames:** read
  [Browser client behavior](references/browser-client-behavior.md).
- **Modify web search, camera snapshot, startup greeting, account/limits, or UI
  design:** read [Demo UI and tools](references/demo-ui-and-tools.md).
- **Diagnose user-facing demo failures:** read
  [Troubleshooting](references/troubleshooting.md).
- **Choose backend STT/LLM/TTS models for the server behind the demo:** route to
  [components-and-backends](../components-and-backends/SKILL.md).
- **Start the backend CLI or size `--num_pipelines`:** route to
  [cli-and-server](../cli-and-server/SKILL.md).
- **Debug raw Realtime events or WebRTC `/v1/realtime/calls`:** route to
  [realtime-api](../realtime-api/SKILL.md).

## Minimal local sequence

1. Start a backend first, normally at `ws://localhost:8765/v1/realtime`.
2. Install the bundled demo server requirements in the environment that will
   run the web app.
3. From this sub-skill directory, set the backend URL and optional demo env vars:

```bash
python -m pip install -r assets/demo/requirements.txt
export SPEECH_TO_SPEECH_URL=ws://localhost:8765/v1/realtime
export SERPER_API_KEY=...      # optional, enables server-side web search
export STARTUP_GREETING=...    # optional; empty disables automatic greeting
uvicorn --app-dir assets/demo server:app --port 7860
```

4. Open `http://localhost:7860/`, click the orb, allow the microphone, and talk.
   Browsers require HTTPS or localhost for microphone/camera access.

## High-signal demo rules

- `SPEECH_TO_SPEECH_URL` is the highest-priority mode: the browser connects
  directly to the pinned Realtime URL, the settings URL is locked, load-balancer
  metering is off, and WebRTC can be offered.
- User-entered direct URLs are WebSocket-only. WebRTC is disabled because the
  same-origin `/api/calls` proxy forwards only to an env-pinned URL.
- `LOAD_BALANCER_URL` mode is WebSocket-only and hides the backend URL from the
  browser. When also running on a Hugging Face Space with `SPACE_ID`, OAuth
  identity and daily time limits are active.
- In Docker, WebSocket and WebRTC may require different backend hostnames:
  WebSocket is dialed by the browser; WebRTC SDP is proxied by the demo server.
- The UI color thesis is strict: saturated color belongs to the orb and tiny
  role echoes only. Do not add colored buttons, fills, or borders outside that
  system.

The detailed references above are self-contained so future agents can handle
normal operation and edits without relying on the source demo files being
present.

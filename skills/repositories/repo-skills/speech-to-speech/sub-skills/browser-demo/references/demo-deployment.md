# Demo deployment reference

The browser demo is a FastAPI/uvicorn web app that serves the voice UI and, in
selected modes, same-origin proxy routes for load balancing, search, and WebRTC
SDP calls. The speech backend is still the separate `speech-to-speech serve`
process.

## Local quickstart

Start the backend first:

```bash
export OPENAI_API_KEY="..."
speech-to-speech serve
```

Then start the bundled demo app from this sub-skill directory with a pinned
backend URL:

```bash
python -m pip install -r assets/demo/requirements.txt
export SPEECH_TO_SPEECH_URL=ws://localhost:8765/v1/realtime
export SERPER_API_KEY=...      # optional; web search disabled without a key
export STARTUP_GREETING=...    # optional; empty string disables greeting
uvicorn --app-dir assets/demo server:app --port 7860
```

Open `http://localhost:7860/`, click the orb, allow microphone access, and talk.
Use `localhost` or HTTPS for browser microphone/camera permissions.

## Connection modes

The demo reports mode through `/api/config`, then the browser chooses the
matching client path.

| Env shape | Browser connection | URL field | Transport | Metering |
| --- | --- | --- | --- | --- |
| `SPEECH_TO_SPEECH_URL` set | Browser connects directly to the pinned URL | visible and locked | WebSocket or WebRTC | off |
| Neither URL env set | User pastes a direct URL in Settings | editable | WebSocket only | off |
| `LOAD_BALANCER_URL` set | Browser asks demo `/api/session`; server contacts LB and returns per-session URL | hidden | WebSocket only | on only when `SPACE_ID` is also set |

`SPEECH_TO_SPEECH_URL` wins over `LOAD_BALANCER_URL`. The pinned URL is not a
secret; it is intentionally visible to the browser. The load-balancer URL stays
server-side.

## WebRTC deployment

WebRTC is available only with an env-pinned backend URL. The browser POSTs its
SDP offer to the demo's same-origin `/api/calls` route; the demo forwards the
handshake to the pinned backend's `POST /v1/realtime/calls`. After the handshake,
media and data channel flow between browser and backend.

Backend requirements:

```bash
pip install "speech-to-speech[webrtc]"
export SPEECH_TO_SPEECH_ICE_SERVERS='[{"urls":"stun:stun.example.com:3478"}]'  # optional
```

Demo-side ICE hints:

```bash
export RTC_ICE_SERVERS='[{"urls":"stun:stun.example.com:3478"}]'
```

Across the internet, use TURN and expose the UDP/media path. Host-only ICE is
usually fine only for localhost or a simple LAN.

## Docker hostnames

When the demo runs in Docker and the backend runs on the host, one
`SPEECH_TO_SPEECH_URL` may not satisfy both transports:

- WebSocket is dialed by the browser on the host. It usually needs
  `ws://localhost:8765/v1/realtime`.
- WebRTC SDP forwarding is initiated by the demo server inside the container.
  It may need `ws://host.docker.internal:8765/v1/realtime` so the container can
  reach the host backend.

If both transports must be tested without swapping env vars, run the demo
without Docker so browser and demo server share the host namespace.

## Hugging Face Space and load balancer mode

For a multi-compute deployment, set `LOAD_BALANCER_URL`. If the app runs as a
Space, `SPACE_ID` is injected by the runtime and enables OAuth-aware metering.
The server forwards a signed-in user's HF token to the load balancer using a
server-side header so the browser never sees that credential. Anonymous users
have no credential forwarded.

Limit-related env vars:

| Env | Default behavior |
| --- | --- |
| `LIMIT_ANON_SEC` | Daily seconds for anonymous visitors, default 300. |
| `LIMIT_FREE_SEC` | Daily seconds for signed-in non-PRO users, default 600. |
| `UNLIMITED_ORGS` | Additional HF org names whose members are treated as unlimited. |
| `USAGE_HASH_SECRET` | HMAC secret for identity hashes and anonymous cookie signing. |

Metering activates only when both `LOAD_BALANCER_URL` and `SPACE_ID` are
present. Local runs remain unmetered even if `LOAD_BALANCER_URL` is set without
Space identity.

## Startup greeting

By default, each new connection injects one hidden user item asking for a brief
greeting and immediately requests a response. This also warms the prompt prefix.
Set `STARTUP_GREETING` to customize it, or set it to an empty value to disable
automatic greeting. Both WebSocket and WebRTC clients guard against sending the
greeting more than once per connection.

## Environment variable summary

| Env | Purpose |
| --- | --- |
| `SPEECH_TO_SPEECH_URL` | Highest-priority direct backend URL; accepts full `ws(s)://.../v1/realtime` or a bare host that the app expands. |
| `LOAD_BALANCER_URL` | Server-side LB address for multi-compute sessions. |
| `SERPER_API_KEY` | Server-side Serper key; enables web search without exposing the key to the browser. |
| `STARTUP_GREETING` | Hidden first-turn prompt; empty disables. |
| `RTC_ICE_SERVERS` | STUN/TURN config served to the browser. |
| `SPACE_ID` | Space runtime signal enabling OAuth/limits with LB mode. |
| `LIMIT_ANON_SEC`, `LIMIT_FREE_SEC`, `UNLIMITED_ORGS`, `USAGE_HASH_SECRET` | Usage-limit policy. |

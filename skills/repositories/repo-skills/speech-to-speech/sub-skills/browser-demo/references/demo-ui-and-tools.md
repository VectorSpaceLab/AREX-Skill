# Demo UI and tools reference

This reference distills the browser demo's user-facing tools, startup greeting,
account/limit behavior, and UI design rules.

## Tool declarations

The demo can declare two Realtime function tools in `session.update`:

| Tool | Purpose | Availability |
| --- | --- | --- |
| `web_search` | Run a Google/Serper search and return concise results to the model. | Enabled when a server `SERPER_API_KEY` exists or the user pastes a key in the Tools panel. |
| `camera_snapshot` | Capture one current webcam frame and return it to a vision-capable model. | User toggle plus browser camera permission. |

Both tools default to enabled in stored settings, but `web_search` is usable
only when a key is available. The tool set can be pushed to a live session so
turning tools on/off updates the next model call.

## Web search flow

- Server-side key: `SERPER_API_KEY` enables search without exposing the key to
  the browser.
- User key: if no server key exists, the Tools panel can accept a user-provided
  Serper key stored in local browser storage.
- Request path: browser calls same-origin `/api/search`; the demo server calls
  Serper and returns a compact result/answer payload.
- Failure mode: without either key, the search toggle is disabled and the model
  should not receive the web-search tool.

Use server-side keys for shared deployments. Treat user-provided keys as local
browser state for individual testing, not as a managed credential store.

## Camera snapshot flow

When enabled, the demo asks for camera permission and shows a live self-view.
When the model calls `camera_snapshot`, the client captures a single frame and
sends an image payload back as the function-call output. WebRTC snapshots are
re-encoded to fit a single data-channel message budget, so a WebRTC snapshot may
be lower fidelity than a WebSocket snapshot.

Browser requirements:

- HTTPS or localhost origin for camera access.
- User permission; if denied, reset permission in browser/site settings.
- A vision-capable upstream model if the snapshot is expected to affect the
  answer.

## ToolCallBatcher behavior

Multiple tool calls can appear in one assistant response. The demo batches tool
executions by originating response so it sends one follow-up `response.create`
after:

1. the response has reached a successful terminal state, and
2. every tool output for that response has been returned.

This prevents stale or partial follow-ups and preserves call order. Failed or
cancelled responses discard their tool batch rather than triggering a follow-up
from stale tool outputs.

## Startup greeting

`STARTUP_GREETING` controls a hidden first user item. Non-empty values ask the
model to produce a brief greeting after the connection opens. Empty value
disables it. Both WebSocket and WebRTC clients send it at most once per
connection.

Use an empty greeting for latency or native-audio tests where the first spoken
turn should be the user's actual utterance.

## Account and limits UI

Account/limit behavior is meaningful only in Hugging Face Space load-balancer
mode:

- `LOAD_BALANCER_URL` activates LB session/queue flow.
- `SPACE_ID` marks the app as a Space and enables OAuth-aware metering.
- Signed-in HF users can receive higher limits or unlimited status depending on
  PRO/team/org policy.
- Anonymous users are metered by an anonymous cookie and server-side day bucket.

Outside LB+Space mode, the account chip and limits should not be treated as
production enforcement.

## Settings and copy voice

Settings users can control:

- transport (`WebSocket`/`WebRTC` when selectable),
- direct backend URL where mode permits,
- microphone and speaker devices,
- voice name,
- instructions/system prompt,
- WebSocket noise gate threshold,
- enabled tools and optional user search key.

Copy should use sentence case and plain verbs. Errors should say what happened
and how to recover. Mono labels are for machine identifiers such as `YOU`,
`ASSISTANT`, `TOOL CALL`, and transport/status tags; human prose stays in the
body font.

## Design editing rules

When changing UI HTML, CSS, or DOM-building JavaScript, preserve these rules:

1. Saturated color belongs to the orb and tiny role echoes only. Do not add
   colored button fills, colored panel borders, or tinted surfaces.
2. Use existing CSS tokens rather than raw hex colors.
3. Keep Inter for body/UI prose and Geist Mono for machine/status identifiers.
4. Use hairlines and spacing, not heavy boxes, for separation.
5. The orb remains the center of gravity and primary animation.
6. Honor `prefers-reduced-motion` and keep new motion quieter than the orb.
7. Support 360 px mobile width, visible keyboard focus, and tap targets at least
   44 px.
8. Remove decorative accessories that do not clarify user state or action.

A good demo edit should feel like a precise extension of the voice orb, not a
separate dashboard theme.

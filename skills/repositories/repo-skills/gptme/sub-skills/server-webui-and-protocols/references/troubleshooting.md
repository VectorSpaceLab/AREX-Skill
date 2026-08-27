# Troubleshooting

This reference collects the failure modes that show up most often across the server, Web UI, ACP, TUI, and deployment surfaces.

## Connection and auth problems

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| Browser says the server may not allow requests from this origin | `--cors-origin` does not match the page origin, or Chrome Local Network Access has not been allowed yet | Match the origin exactly and allow the browser prompt when a hosted page reaches a local server. |
| UI loads but API requests get `401` | Missing or stale bearer token | Confirm the server token, the frontend connection settings, and whether the UI can use the auth cookie. |
| SSE connects in same-origin mode but fails cross-origin | SameSite cookie not sent cross-origin | Use the auth header or the query-token fallback that the frontend client already supports. |
| Requests are rejected with a Host-header error | Host validation is enabled and the proxy host is not allow-listed | Add the legitimate proxy hostname with `--allowed-hosts`, or keep bearer auth enabled instead of disabling it. |

### Hosted Web UI to local server

For the common `chat.gptme.org` → local `gptme-server` setup, remember that three layers must line up:

1. the server must allow the UI origin via `--cors-origin`
2. the browser may still need an explicit *Local Network Access* permission
3. the UI still needs the bearer token for capability-bearing routes

If any of those layers is missing, the browser can fail in different ways that look similar at first glance.

## Server startup and dependency problems

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `gptme-server` import fails with `flask_compress` or similar | Server extras are missing | Install the `server` extra and retry. |
| `gptme-tui` import fails with `textual` or `json_repair` | TUI or base runtime dependency is missing | Install the `tui` extra and confirm the base package dependencies are present. |
| ACP launch exits early with an `agent-client-protocol` message | ACP dependency is missing | Install the `acp` extra or the `gptme-acp` shim package. |
| The process starts but never answers the browser/editor | The UI/editor is reaching the process, but the process is waiting on missing config, a blocked model call, or a protocol handshake that never begins | Check stderr, not stdout, and confirm the expected token/model/config are present. |

## SSE metadata mismatches

If the Web UI shows the wrong model label, cost badge, or tool state, the usual cause is metadata drift between the backend REST path and the SSE completion path.

Check these points first:

- `msg2dict(...)` is what turns backend messages into REST/SSE payloads
- both `message_added` and `generation_complete` should carry the same message metadata
- the UI reads `model`, `resolved_model`, `cost`, `usage`, `tool`, and `panel_hints`
- `usage` should be a nested object with token counts, not a flattened bag of numbers

Use [../scripts/check_webui_message_metadata.py](../scripts/check_webui_message_metadata.py) to compare a representative REST message sample with the SSE completion sample before digging into the frontend.

## Web UI rendering problems

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| A change appears in one markdown view but not the other | One of the two rendering paths was updated and the other was not | Audit both renderers before assuming the bug is in the backend. |
| Nested code fences render incorrectly | The nested-fence convention was changed without adjusting the preprocessing step | Verify the code-block widening logic before changing the parser. |
| A conversation label or cost badge disappears after streaming ends | The SSE completion event and the final REST log entry disagree | Compare the REST message and the SSE `generation_complete` payload. |
| Panel tabs never appear | `metadata.panel_hints` is absent, malformed, or filtered out | Check the message metadata and the server-side panel validation path. |

## Deployment problems

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| SSE tokens arrive only at the end of the response | Reverse proxy buffering is still on | Disable buffering for the upstream location and keep a long read timeout. |
| The service restarts but client configs stop working | The server token is regenerated on each boot | Set a stable `GPTME_SERVER_TOKEN`. |
| The server is reachable on the host but not from a sidecar or desktop shell | Parent-death watching is not enabled | Use `--exit-on-parent-death` or `--watch-pid` for the wrapper process. |
| A custom UI build is ignored | The custom UI directory is missing or invalid | Confirm the configured build directory exists; otherwise the server falls back to the bundled or legacy UI. |

## ACP-specific problems

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| The editor sees garbled JSON-RPC | Something wrote to stdout before or during the ACP loop | Keep normal logs on stderr only and avoid shell wrappers that print banners. |
| The ACP process looks idle | It is waiting for the editor to speak ACP | Confirm the editor is launching the shim/module that speaks ACP, not the plain interactive CLI. |
| Tool approval keeps timing out | Permission requests are not reaching the client or the client is denying them | Check the protocol logs and the editor's ACP permission UI. |

## TUI-specific problems

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `/edit` or another external-terminal command fails in the TUI | The TUI does not yet support that external-program workflow | Resume the conversation in the plain CLI for the command that needs an external terminal. |
| Inline mode does not behave like the alternate screen UI | Inline mode intentionally trades features for terminal scrollback | Use the normal TUI mode when you need in-place tool-output expansion. |

## Version-skew gap

The frontend source in this checkout contains conversation-metadata helpers, but the backend evidence used for this skill does not expose a matching server route. If that feature is important in a particular checkout, treat it as a version-skew issue instead of assuming the UI is wrong.

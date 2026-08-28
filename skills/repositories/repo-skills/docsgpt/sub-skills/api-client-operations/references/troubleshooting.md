# API and Client Troubleshooting

| Symptom/status | Likely cause | Recovery |
|---|---|---|
| 401 | missing/invalid API key/JWT, wrong auth mode | inspect `/api/config`; send key in correct payload/header; rotate if exposed |
| 403 | authenticated but lacks agent/source/team/tool permission | verify owner/team grants and requested resource |
| `/mcp` or reconnect 404 | Flask-only server or proxy mismatch | run full ASGI target and forward exact path |
| 409 with idempotency | first request still in flight or key reused incorrectly | wait/query state; use unique key per logical request |
| 429 on events | connection/replay budget exceeded | close duplicate streams, back off, resume with cursor |
| stream JSON parse errors | client parses TCP chunks instead of complete SSE lines/frames | buffer bytes, split complete frames, preserve partial tail |
| missing final id/end | disconnect or server error | use message id/reconnect route; inspect error/journal before retrying generation |
| duplicate answers/tool calls | retry without supported idempotency or continuation history duplicated | check persisted conversation/run; do not blindly replay state-changing request |
| attachment remains pending | worker/Redis/queue/parser failure | poll with deadline, inspect task result, route to ingestion/service diagnosis |
| attachment denied/not found | upload and answer use different user context | use same API-key owner/JWT user |
| `/v1` ignores `model` | expected behavior: key-bound agent selects model | change agent model or key, not request field |
| system message ignored | agent prompt override disabled | enable only if intended; understand whole-template replacement |
| sources absent in strict OpenAI client | DocsGPT metadata is on top-level extension chunks | inspect `docsgpt` extension frames or use native API |
| SSE works locally but stalls through proxy | buffering/compression/timeout | apply streaming proxy settings and keepalive |

Record method/path, status, sanitized response, request id/idempotency key hash, conversation/message/task id, final event type and client library version. Never log raw keys, JWTs, attachment bytes, or sensitive prompt/tool payloads.

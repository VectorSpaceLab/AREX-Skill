# Memory API Troubleshooting

## Validation returns 422

Common causes:
- Missing `messages` on `/add`.
- `messages[].timestamp` absent or non-positive.
- `sender_id`, `app_id`, or `project_id` contains path-unsafe characters.
- `/search` or `/get` includes both `user_id` and `agent_id`, or neither.
- `top_k` is 0, less than -1, or greater than 100.
- `/get memory_type` does not match owner type.

Fix the request body; do not retry unchanged.

## Search returns empty after flush

The write path can return before LanceDB has indexed the new Markdown. Retry with short backoff, inspect `/health` cascade readiness, or run `everos cascade sync` on the same root for deterministic local projection.

## Provider errors

`PROVIDER_NOT_CONFIGURED` means the requested method or feature needs a provider that is absent or malformed. Examples:
- LLM missing: extraction and LLM rerank paths fail.
- Embedding missing: vector/hybrid/agentic paths fail.
- Rerank missing: agentic or knowledge-related rerank paths fail.
- Multimodal LLM missing: non-text parsing fails.

Use `keyword` only as an intentional degraded mode.

## Multimodal failures

- Non-text content with only `text` returns unsupported format because there is no asset to parse.
- Base64 without an extension may fail modality inference.
- Office document parsing requires LibreOffice.
- Large base64 payloads can bloat the SQLite buffer until flush; prefer `uri` for large assets.

## Session confusion

`session_id` groups unprocessed buffer state. If two clients write concurrently to the same session, EverOS serializes per session, but long LLM calls can hold the session lock until `session_lock_timeout_seconds`.

## Scope confusion

Search never crosses `app_id` and `project_id`. If a memory exists but search misses, check that add/flush/search/get all use the same scope.

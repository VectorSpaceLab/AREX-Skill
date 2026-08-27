# Proxy API and CLI Reference

Read this for concrete request fields, routes, response behavior, and CLI/env settings.

## HTTP routes

| Route | Method | Purpose | Notes |
| --- | --- | --- | --- |
| `/v1/chat/completions` | `POST` | OpenAI-compatible chat completions endpoint | Applies approach/plugin dispatch before wrapping response. |
| `/v1/models` | `GET` | Model listing | Delegates to upstream provider when configured; local inference returns a synthetic current model entry. |
| `/health` | `GET` | Healthcheck | Returns `{"status": "ok"}` and bypasses server API-key auth. |

## Chat request handling

The server extracts these fields specially:

- `messages`: OpenAI-style chat messages.
- `model`: model name, possibly prefixed with approach/plugin slug(s).
- `stream`: if true, output is SSE-style chunks.
- `n`: number of final responses or repeated operation executions.
- `response_format`: preserved in request config for plugins such as JSON.
- `max_completion_tokens` and `max_tokens`: normalized so approach code can read `max_tokens`.

All other fields are copied into `request_config` and passed through to approaches/plugins where supported.

## Conversation parsing

`parse_conversation(messages)` separates a system prompt from a joined transcript of user/assistant turns. List-format content is normalized by concatenating text items. Prompt tags of the form `<optillm_approach>slug</optillm_approach>` are removed and returned as the selected approach.

## Response wrapping

- `none` direct proxy returns the upstream response dict when possible.
- Single approach text is wrapped into `choices[0].message.content`.
- Parallel approach output becomes multiple list items/choices.
- Reasoning tokens are counted from `<think>...</think>` content and exposed at `usage.completion_tokens_details.reasoning_tokens`.
- Streaming yields `chat.completion.chunk` objects and a final `data: [DONE]`.

## CLI defaults that matter

The source-level `server_config` starts with `approach: none`, but CLI parsing defaults `--approach` to `auto`, so normal command-line server startup allows model-prefix and request-level approach selection.

High-impact flags:

```bash
optillm \
  --approach auto \
  --model gpt-4o-mini \
  --base-url http://localhost:8080/v1 \
  --host 127.0.0.1 \
  --port 8000 \
  --log info
```

Security and TLS:

```bash
optillm --optillm-api-key server-secret
optillm --ssl-cert-path /path/to/ca-bundle.pem
optillm --no-ssl-verify  # development/debug only
```

Batching:

```bash
OPTILLM_BATCH_MODE=true OPTILLM_BATCH_SIZE=4 OPTILLM_BATCH_WAIT_MS=50 optillm
```

Conversation logging:

```bash
optillm --log-conversations --conversation-log-dir /secure/log/dir
```

## Batch compatibility rules

Batch mode rejects or fails when requests differ in stream mode, approach list, operation type, or model. Streaming requests cannot be batched. Treat batch logs as sensitive because request prompts and responses may be captured when conversation logging is also enabled.

## Field pass-through cautions

- `n` is preserved for `none` so upstream providers can return multiple choices.
- Approach wrappers may interpret `request_config` fields differently from upstream providers.
- Some providers reject system messages; the proxy plugin has fallback formatting, but the core server does not rewrite every provider limitation.
- If a provider uses `max_completion_tokens` but an approach only reads `max_tokens`, OptiLLM mirrors the preferred field into `max_tokens` for compatibility.

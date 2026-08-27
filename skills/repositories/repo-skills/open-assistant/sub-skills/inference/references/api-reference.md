# Inference server, worker, and chat protocol reference

This reference covers the OpenAssistant inference stack routes and protocols at an operating level. It is designed for debugging and local setup without reopening source files.

## Service roles

| Component | Role | Default local signal |
| --- | --- | --- |
| Inference server | FastAPI service for chat CRUD, debug/oauth auth, model-config listing, worker websocket coordination, plugin hosting, and SSE message events | HTTP `:8000` in compose/dev examples |
| Inference worker | Long-running process that connects to the server over websocket, advertises a model config and hardware info, receives work, and streams token/generated-text responses | `BACKEND_URL=ws://...`, `API_KEY`, `MODEL_CONFIG_NAME` |
| Text client | Debug REPL that logs in, creates a chat, posts prompter/assistant messages, and consumes SSE events | `python __main__.py --model-config-name=_lorem` |
| Safety server | Optional FastAPI Blade2Blade safety model service | HTTP `:8002`; used only when worker safety is enabled |
| Text generation inference server | Optional external generation backend for non-`_lorem` workers | Worker waits for it before serving real models |

## Inference server startup behavior

On startup the server:

1. Adds CORS and session middleware.
2. Exposes Prometheus metrics at `/metrics`.
3. Logs `INFERENCE_PROTOCOL_VERSION` from shared schemas.
4. Runs Alembic upgrades unless disabled by settings.
5. Initializes Redis-backed rate limiting unless disabled.
6. Adds debug worker API keys from settings when configured.
7. Mounts built-in plugin sub-apps under the configured plugin prefix.

If the server imports successfully, route categories include:

```text
/account/
/auth/check, /auth/providers, /auth/login/<provider>, /auth/callback/<provider>, /auth/trusted
/admin/workers, /admin/users, /admin/refresh_tokens
/chats, /chats/{chat_id}, /chats/{chat_id}/messages/...
/workers/work
/configs/model_configs
```

## Debug auth and text-client request flow

The debug text client follows this sequence:

1. `GET /auth/callback/debug?code=<username>` returns a bearer token when debug auth is enabled.
2. `POST /chats` creates a chat with authorization header `Bearer <token>`.
3. `GET /configs/model_configs` lists server-visible model config names.
4. `POST /chats/{chat_id}/prompter_message` creates a user message with `parent_id` and `content`.
5. `POST /chats/{chat_id}/assistant_message` requests an assistant message with `parent_id`, `model_config_name`, and `sampling_parameters`.
6. `GET /chats/{chat_id}/messages/{message_id}/events` streams SSE events until the assistant message is complete, or returns the full message when no stream is available.

The text client validates that `model_config_name` exists before submitting generation. Use `_lorem` for service and SSE plumbing without model downloads.

## Worker websocket lifecycle

The worker:

1. Reads settings such as `BACKEND_URL`, `API_KEY`, `MODEL_CONFIG_NAME`, `INFERENCE_SERVER_URL`, optional bearer/basic auth, `MAX_PARALLEL_REQUESTS`, safety level, and retry behavior.
2. Looks up `MODEL_CONFIG_NAME` in the shared model registry. Unknown names exit with status code 2.
3. Loads a tokenizer unless the selected model config is `_lorem`.
4. Waits for the inference HTTP backend when the config is not `_lorem`.
5. Connects to `BACKEND_URL + /workers/work` with headers:
   ```text
   X-API-Key: <worker-api-key>
   X-Protocol-Version: <shared inference protocol version>
   ```
6. Sends `WorkerInfo(config=WorkerConfig(...), hardware_info=WorkerHardwareInfo())`.
7. Handles incoming `WorkerRequest` objects in a thread pool up to `max_parallel_requests`.

Incoming worker request types:

| Request | Meaning | Worker action |
| --- | --- | --- |
| `work` | Generate for a chat thread | Format prompt, optionally run plugins/safety, stream tokens/generated text. |
| `ping` | Health/metrics request | Send `PongResponse`. |
| `wrong_api_key` | Server rejected key | Log explicit key error and stop/retry depending on settings. |
| `upgrade_protocol` | Worker/server schema mismatch | Exit with status 2 so orchestration can upgrade. |
| `terminate` | Controlled shutdown | Exit cleanly. |
| `error` | Server-side error | Raise runtime error with server message. |

Worker response types include `token`, `generated_text`, `error`, `general_error`, `pong`, `safe_prompt`, `plugin_intermediate`, and internal finish/error responses.

## Prompt formatting and generation

For the selected OpenAssistant protocol version `v2`:

- Prompter messages are prefixed with `<|prompter|>`.
- Assistant messages are prefixed with `<|assistant|>`.
- Optional system/custom-instruction material is prefixed with `<|system|>` and appended before the conversation.
- The final prompt appends `<|assistant|>` to signal the generation turn.
- If stop sequences are enabled, the worker stops at prompter, assistant, system, and EOS tokens.

If plugins are enabled in work parameters:

- The worker can prepare plugin OpenAPI endpoints, compose LangChain tools, perform intermediate tool calls, and then produce a final prompt/generation.
- Tool descriptions may be omitted from final prompt to save context.
- Plugin intermediate responses can be sent to the server.

If safety is enabled and safety level is nonzero:

- The worker sends `SafetyRequest(inputs=<prompt>, parameters=SafetyParameters(level=...))`.
- Safety output is parsed into a label and rule-of-thumb text.
- Caution/intervention labels can trigger a safe prompt replacement depending on severity and configured level.

## SSE event semantics

The text client handles server-sent events from assistant-message events:

| Event payload type | Meaning | Client behavior |
| --- | --- | --- |
| `token` | Next generated token text | Yield text fragment to caller/UI. |
| `message` | Final full message content | Stop streaming loop; full content can be ignored if tokens were already consumed. |
| `error` | Generation or server error | Raise an exception with the provided error. |
| `pending` | Work not yet completed | Log/ignore while waiting. |
| SSE event `ping` | Keepalive | Ignore. |

For website-side line buffering and browser rendering, use the `website` sub-skill; this reference covers server/client protocol meaning.

## Plugin OpenAPI parsing

The worker can fetch a plugin configuration URL, resolve the plugin's API URL, fetch JSON or YAML OpenAPI, resolve local `#/...` schema references, and build endpoint descriptors with method, summary, operation id, URL, parameters, and JSON payload schema. Network failures, invalid JSON/YAML, unsupported content types, and missing `$ref` components are treated as plugin-preparation failures, not as model failures.

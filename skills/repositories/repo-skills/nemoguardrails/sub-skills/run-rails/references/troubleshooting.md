# Troubleshooting

## Fast triage

1. Decide whether the failure is about the Python API, the CLI/server, or LangChain integration.
2. Check whether the config is trying to use `IORails` or the full `LLMRails` runtime.
3. For server issues, confirm the request shape before chasing the model provider.
4. For local smoke checks, use the bundled deterministic scripts first so you can rule out live-provider problems.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Guardrails` falls back to `LLMRails` | The config is not compatible with `IORails`, or an `llm` was passed. | Accept the fallback, set `use_iorails=False` to make it explicit, or set `require_iorails=True` if fallback is not allowed. |
| Wrapper behavior looks unexpected | `NEMO_GUARDRAILS_IORAILS_ENGINE` is enabled. | Unset the compatibility env var or import the direct runtime class you intended. |
| `StreamingNotSupportedError` from `stream_async` | Output rails are configured but output-rail streaming is disabled. | Enable `rails.output.streaming.enabled` or switch to `generate_async`. |
| `HTTP 422` for `config_id` / `config_ids` | Both fields were provided. | Send exactly one of them. |
| `HTTP 422` for `state` | The request used Colang 2.0 state over HTTP, or the dict shape is wrong. | For Colang 1.0 use `{"events": [...]}`; for Colang 2.0 use in-process `process_events_async` instead. |
| `HTTP 422` for `thread_id` | Threads are Colang 1.0 only, non-streaming only, and require a datastore. | Remove `thread_id`, disable streaming, or use a 1.0 config with datastore support. |
| `HTTP 422` for `tools` / `tool_choice` / `parallel_tool_calls` | The request is streaming or the config is not passthrough. | Use a non-streaming request and a config with `passthrough: true`. |
| `ValueError` about Colang 2.0 dict state | A public dict state was passed to the full runtime. | Use `process_events_async` with a live `State` object or keep the config on Colang 1.0. |
| `RuntimeError` about calling a sync API in async code | `generate`, `check`, or `stream` was called from a running event loop. | Switch to the async API. |
| `RunnableBinding` / tool-binding errors | A tool-bound model was wrapped at the wrong layer. | Bind tools on the model, keep `passthrough=True`, or wrap the whole agent/chain instead of the bound sub-node. |
| Empty or broken server model list | The upstream model provider is unreachable or lacks the expected base URL. | Check `MAIN_MODEL_ENGINE`, `MAIN_MODEL_BASE_URL`, and the request `Authorization` header. |
| Smoke script tries to download FastEmbed or Hugging Face assets | The embedding provider was not patched or replaced with a deterministic local implementation. | Run `scripts/deterministic_chat_smoke.py` or copy its deterministic embedding helper. |

## Chat and server specifics

- `chat --streaming` only works when the config supports output streaming.
- `server --disable-chat-ui` is the safest production default.
- `/v1/health` is shallow; a green health check does not prove that the upstream model provider works.
- `/v1/checks` is validation-only and does not replace a generation smoke.

## When the failure is in LangChain

- Use `RunnableRails` for chain wrapping and `GuardrailsMiddleware` for `create_agent` hooks.
- If a tool-call flow fails, check whether the failure is really about `passthrough=False` or tool-call metadata being dropped.
- If LangGraph buffers token streaming, test the same runnable directly before changing the graph logic.

## When to stop and reroute

- If the issue is config design, move to `../configure-rails/SKILL.md`.
- If the issue is evaluation or telemetry, move to `../evaluate-and-observe/SKILL.md`.
- If the issue requires changing repository code, move to `../repo-development/SKILL.md`.

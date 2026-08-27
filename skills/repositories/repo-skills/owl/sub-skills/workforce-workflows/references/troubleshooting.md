# Workforce Troubleshooting

## CAMEL or MCP import fails

**Symptom:** `ImportError` mentions `FastMCP`, `mcp.server`, or a CAMEL
submodule. **Cause:** dependency metadata can accept a newer MCP release whose
runtime exports differ from the pinned CAMEL release. Verify `camel-ai==0.2.84`
and inspect the installed MCP compatibility before changing packages. In the
verified inspection environment, `mcp<2` was required for CAMEL imports.
Reinstall only in an isolated environment, then run `pip check` and an import
probe; never mutate a user environment without approval.

## Missing or rejected provider key

**Symptom:** `ValueError: Missing or empty required API keys` during
`ModelFactory.create`. **Recovery:** run `validate_provider_config.py`, check
that the selected provider's variable is exported or loaded from a protected
file, and confirm the exact model-platform expectation. Do not print the value
or add a placeholder to source. For Gemini, resolve the repository's
`GOOGLE_API_KEY` versus `GEMINI_API_KEY` naming discrepancy against the
installed CAMEL provider documentation.

## Tool or multimodal failure

**Symptom:** a worker ignores tools, returns malformed calls, or cannot inspect
an image. **Cause:** model capability or provider-specific tool schema support,
not necessarily OWL orchestration. Start with a tool-capable text task; use a
vision-capable model for images; reduce the tool list; and inspect serialized
`tool_calls` in `chat_history`.

## Browser failure

**Symptom:** Playwright executable, display, or browser launch error. **Recovery:**
prepare browser binaries and system libraries separately, use headless mode on
headless hosts, or route the task to search/document tools when browser work is
not essential. Do not install browsers or start a browser as an import check.

## VLLM/OpenAI-compatible endpoint failure

**Symptom:** connection refused, 404, model-not-found, or authentication error.
**Recovery:** validate `VLLM_API_URL`, confirm the server is already listening,
query its advertised model name through an approved health check, and set
`VLLM_MODEL_NAME` to an exact served id. `ModelFactory` does not start VLLM.

## Task never completes

**Symptom:** the society reaches the round limit without `TASK_DONE`. Inspect
chat history and tool-call errors, lower task scope, ensure the user-side and
assistant-side prompts preserve their roles, and verify the final artifact
instead of increasing the limit blindly. For token counts, treat missing usage
metadata as an observability limitation.

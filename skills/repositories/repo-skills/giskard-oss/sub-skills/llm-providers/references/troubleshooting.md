# Troubleshooting

## `ProviderNotAvailableError`

**Symptoms:** Instantiating a provider fails immediately and the error message
suggests an extra such as `giskard-llm[openai]`.

**Cause:** The SDK for that provider is not installed in the active Python
environment.

**Fix:** Install the matching extra for the provider family you want to use.
For Azure OpenAI and Azure AI Foundry, the OpenAI extra is sufficient because
both providers use the OpenAI SDK.

## Missing authentication or endpoint variables

**Symptoms:** A provider instantiates but requests fail with authentication or
connection errors.

**Cause:** The relevant API key, endpoint, or version variable is unset or the
wrong alias is configured.

**Fix:**

- OpenAI: set `OPENAI_API_KEY`
- Google Gemini: set `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- Anthropic: set `ANTHROPIC_API_KEY`
- Classic Azure OpenAI: set `AZURE_API_KEY`, `AZURE_API_BASE`, and usually
  `AZURE_API_VERSION`
- Azure AI Foundry: set `AZURE_AI_API_KEY`, `AZURE_AI_ENDPOINT`, and optionally
  `AZURE_AI_API_VERSION`

If you use `os.environ/VAR_NAME` in `configure(...)`, the value is resolved when
that alias is first created. Reconfigure the alias or call `reset()` after
changing the environment.

## `UnsupportedOperationError`

**Symptoms:** The provider exists, but `aembedding(...)` or `aresponse(...)`
fails with a message saying the provider does not support that operation.

**Cause:** The provider implements only some of the `CompletionProvider`,
`EmbeddingProvider`, or `ResponseProvider` protocols.

**Fix:** Route the request to a capable provider:

- Use OpenAI, Google, or Azure OpenAI for embeddings.
- Use OpenAI or Google for Responses / Interactions.
- Use Anthropic for chat completions only.

## Invalid message roles or order

**Symptoms:** You get a `BadRequestError` before any SDK call starts.

**Cause:** The package validates message shapes and ordering first.

**Common fixes:**

- Ensure the message list is not empty.
- Ensure there is at least one non-system message.
- Give every tool message a `tool_call_id`.
- For Anthropic, alternate user/assistant turns and enable `merge_system=True`
  if you need multiple system or developer instructions.
- For Anthropic, do not send consecutive same-role conversation messages unless
  the sequence is intentionally folded through tool-result behavior.
- For Google and OpenAI, use canonical `system`, `developer`, `user`,
  `assistant`, and `tool` roles. Avoid ad hoc roles.

## Anthropic `merge_system`

**Symptoms:** Anthropic rejects multiple instruction messages.

**Fix:** Configure the alias with `merge_system=True` and keep the instructions
as separate system/developer messages. The provider will concatenate them into a
single top-level system payload.

## Bad request validation failures

**Symptoms:** `BadRequestError` mentions JSON/Pydantic validation, missing fields,
or unsupported response formats.

**Cause:** The public input shape does not match the provider's expected schema,
or a structured-output schema is not valid.

**Fix:**

- Use the public typed message/tool/result shapes from `giskard.llm.types`.
- For chat completion tools, use the nested `ToolDefParam` shape.
- For function outputs in `aresponse(...)`, include `name` when the provider or
  translator needs it.
- When requesting structured JSON, pass a Pydantic model class that can produce
  a valid JSON schema.

## Rate-limit, server, and timeout retry

**Symptoms:** Requests fail with 429, 5xx, or timeout-like errors.

**Fix:** Use `should_retry(error)` to decide whether the failure is transient.
The helper returns `True` for timeout, rate-limit, and server errors only.

If repeated failures happen immediately, reduce concurrency, add backoff, or
switch to a provider/model combination with a lower load profile.

## Google interactions or tool-result shape problems

**Symptoms:** Google completion or interaction calls fail when tool results are
fed back.

**Cause:** The provider needs the canonical Giskard tool-output shape and then
maps it to Gemini's wire format.

**Fix:** Use the shared function-call output type and keep the tool-call name
available when you build the continuation request.

## Azure Foundry confusion

**Symptoms:** A Foundry endpoint returns unexpected embedding or response
behavior, or a classic Azure config does not work with a Foundry URL.

**Cause:** The wrong Azure path is selected.

**Fix:**

- Use `provider="openai"` with an OpenAI-compatible Foundry v1 URL ending in
  `/openai/v1/`.
- Use `provider="azure"` for classic Azure OpenAI deployments.
- Use `provider="azure_ai"` for Azure AI Foundry resource endpoints on
  `*.services.ai.azure.com`.

## Custom transport ownership

**Symptoms:** A custom `http_client` behaves strangely or is closed too early.

**Cause:** The provider passes the caller-owned async client through to the SDK;
Giskard does not manage its lifecycle.

**Fix:** Close the custom HTTP client yourself after all provider calls finish.

## No-key inspection script fails

**Symptoms:** The bundled inspector cannot import the package or prints a missing
SDK warning.

**Cause:** The environment lacks the installed package or optional provider SDKs.

**Fix:** Verify the package is installed, then re-run the script. Missing optional
SDKs are expected and are reported as availability facts, not as live failures.

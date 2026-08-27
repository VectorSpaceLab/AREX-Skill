# SDK Troubleshooting

## Start With No-Network Checks

Run these before spending provider credits:

```bash
python sub-skills/sdk-core/scripts/sdk_smoke.py --checks import signature mock
```

Expected results:

- Import check proves `litellm` is installed and importable.
- Signature check proves the installed package exposes expected SDK parameters.
- Mock check proves `completion(..., mock_response=...)` returns the expected OpenAI-like response shape.

## Missing Provider Keys

Symptoms:

- `AuthenticationError`, provider auth errors, or messages asking for an API key.
- Works with `mock_response`, fails without it.

Fixes:

- Set the provider-specific environment variable, such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or the provider key expected by the selected model prefix.
- Pass `api_key=os.environ["PROVIDER_KEY"]` for per-call isolation.
- For Azure or OpenAI-compatible endpoints, verify `api_key`, `base_url` or `api_base`, `api_version`, and deployment name together.
- Never hard-code secrets in examples, generated skills, tests, or command lines.

## Unknown Provider or Model Prefix

Symptoms:

- Unknown provider/model errors.
- Bad-request errors that mention provider inference.
- A model works in a provider SDK but not through LiteLLM with the current model string.

Fixes:

- Use an explicit provider prefix in `model`, for example `openai/gpt-4o-mini`, `anthropic/claude-sonnet-4-20250514`, or `azure/my-deployment`.
- If using a custom endpoint or unusual model name, pass `custom_llm_provider` so LiteLLM does not infer the wrong provider.
- Check whether the task is actually provider endpoint catalog work; if so, route to providers-and-endpoints.
- Use `mock_response` to verify local code shape before making a live provider call.

## Unsupported or Dropped Parameters

Symptoms:

- Provider rejects `response_format`, `tools`, `tool_choice`, `parallel_tool_calls`, `thinking`, `web_search_options`, `stream_options`, or max-token fields.
- Response does not reflect an optional parameter.
- A parameter works for one provider but not another.

Fixes:

- Remove optional parameters until the minimal call succeeds, then add them back one at a time.
- Prefer OpenAI-format params first, but expect provider-specific support gaps.
- Use `max_completion_tokens` for reasoning-style models that reject `max_tokens`; use `max_tokens` for older text/chat models that do not know `max_completion_tokens`.
- For provider-native features, confirm whether LiteLLM expects the value in `**kwargs`, `extra_headers`, or an endpoint-specific parameter.
- Turn on debug/verbose logging only in safe local contexts and avoid logging secrets or message contents.

## Timeout, Network, and Provider Errors

Symptoms:

- `Timeout`, `APIConnectionError`, `APIError`, `RateLimitError`, or provider 5xx responses.
- Long hangs when no timeout is set.

Fixes:

- Set `timeout` explicitly on every production call.
- Catch `litellm.Timeout`, `litellm.RateLimitError`, and `litellm.APIError` separately when retry or fallback behavior differs.
- Use `mock_response` to separate application-code failures from provider/network failures.
- For retries and fallbacks across deployments, route to the routing sub-skill.
- For persistent 401/403/404 errors, re-check key, endpoint URL, API version, deployment/model name, and provider prefix.

## Streaming Iteration Mistakes

Symptoms:

- Code tries `response.choices[0].message.content` on a stream.
- Code prints nothing because it reads `message` instead of `delta`.
- Async code uses normal `for` on an async stream.

Fixes:

- For sync streaming, use `for chunk in stream:`.
- For async streaming, call `stream = await litellm.acompletion(..., stream=True)` and then `async for chunk in stream:`.
- Read partial text from `chunk.choices[0].delta.content` when present.
- Accumulate chunks into a string before JSON parsing or Pydantic validation.
- Treat usage-in-stream as provider-dependent even with `stream_options={"include_usage": True}`.

## Structured Output and Pydantic Issues

Symptoms:

- Provider rejects `response_format`.
- Pydantic schema is ignored or validation fails.
- Streaming JSON is incomplete until the stream ends.

Fixes:

- Confirm the provider supports JSON mode, JSON schema, or Pydantic response formats on the selected endpoint.
- Try `response_format={"type": "json_object"}` before a Pydantic class when isolating failures.
- Use `enable_json_schema_validation=True` when you want LiteLLM-side validation behavior and the provider path supports it.
- For streaming, accumulate all deltas first, then validate the complete text.
- If a schema is too complex, simplify nested unions/enums or post-validate with your own Pydantic model.

## Caching Optional Dependencies

Symptoms:

- Import errors for cache backends.
- Cache silently misses or behaves differently in tests.
- External cache connection failures.

Fixes:

- Use local/in-memory caching for simple SDK tests.
- Install optional extras required by the selected backend, such as disk cache or Redis clients.
- Configure external cache URLs, credentials, and namespaces outside code.
- Clear or replace `litellm.cache` between tests.
- Avoid caching user-sensitive prompts unless cache keys and retention are approved.

## Callback Import or Configuration Errors

Symptoms:

- Callback string names do not initialize.
- `CustomLogger` subclass hooks are not called.
- Async callbacks appear delayed.
- Sensitive message content appears in logs.

Fixes:

- Prefer `litellm.callbacks = [CustomLoggerSubclass(...)]` or a supported callback string.
- For async workloads, implement `async_log_success_event`, `async_log_failure_event`, or other async hooks.
- Wait for scheduled async callbacks in tests before asserting callback side effects.
- Use `turn_off_message_logging=True` or the global redaction setting for sensitive payloads.
- Reset global callback lists after tests: `callbacks`, `success_callback`, `failure_callback`, `_async_success_callback`, and `_async_failure_callback`.
- Some named integrations need their own environment variables; check callback-specific env var requirements before assuming a LiteLLM SDK bug.

## Cost or Token Count Looks Wrong

Symptoms:

- `completion_cost` raises for an unknown model.
- Token count differs from provider billing.
- Streaming response lacks usage.

Fixes:

- Pass `model` and response data explicitly when the response lacks provider/model metadata.
- Use custom pricing for private, newly released, or unlisted models.
- Treat token counts as estimates when providers use custom tokenizers or multimodal inputs.
- Use `use_default_image_token_count=True` for multimodal token estimates when image fetching is not allowed.

## Safe Exception Skeleton

```python
try:
    result = litellm.completion(model=model, messages=messages, timeout=30)
except litellm.AuthenticationError as exc:
    diagnostic = "provider authentication failed; check key and endpoint settings"
except litellm.Timeout as exc:
    diagnostic = "provider call timed out; reduce prompt size or increase timeout"
except litellm.RateLimitError as exc:
    diagnostic = "provider rate limit hit; retry later or use fallback routing"
except litellm.BadRequestError as exc:
    diagnostic = f"provider rejected request parameters: {exc}"
except litellm.APIError as exc:
    diagnostic = f"provider API failed: {exc}"
```

Do not swallow these exceptions silently. Return enough diagnostic context to identify the model prefix, endpoint family, and optional parameters, but never log API keys or sensitive messages.

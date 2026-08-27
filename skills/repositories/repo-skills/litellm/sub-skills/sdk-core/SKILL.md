---
name: sdk-core
description: "Use for direct LiteLLM Python SDK work: chat/text completions,
  async calls, streaming, embeddings, structured outputs, tools, token/cost
  checks, caching, callbacks, import/smoke validation, and shared SDK
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LiteLLM SDK Core

Use this sub-skill when the task is about calling LiteLLM as a Python library. LiteLLM exposes OpenAI-format SDK calls across providers, with safe local validation available through `mock_response` and the bundled smoke script.

## Route Elsewhere

- Use `../proxy-server/SKILL.md` for running or configuring the LiteLLM proxy server and CLI gateway.
- Use `../routing/SKILL.md` for `Router`, model groups, fallbacks, load balancing, and deployment selection.
- Use `../providers-and-endpoints/SKILL.md` for provider catalogs, endpoint-specific quirks, and pass-through APIs.
- Use `../agent-tools/SKILL.md` for MCP, A2A, and gateway-backed agent tool patterns.

## Start Here

1. For API signatures and parameter mapping, read `references/api-reference.md`.
2. For copy-ready SDK patterns, read `references/workflows.md`.
3. For failures and diagnostics, read `references/troubleshooting.md`.
4. For a safe local check, run:

```bash
python sub-skills/sdk-core/scripts/sdk_smoke.py --checks import signature mock
```

Run the command from the generated skill root, or pass the script path directly from any working directory. It imports the installed `litellm` package and does not contact providers unless `--provider-smoke` is combined with `--model` and `--api-key-env`.

## Core Mental Model

- `litellm.completion(...)` is the main synchronous chat-completion API; `litellm.acompletion(...)` is the async equivalent.
- `litellm.embedding(...)` and `litellm.aembedding(...)` handle embeddings with provider-specific credentials and optional caching.
- `litellm.text_completion(...)` supports legacy prompt-style text completions when a provider/model still exposes that shape.
- Most provider differences are expressed through `model` prefixes such as `openai/...`, `anthropic/...`, `azure/...`, `bedrock/...`, plus per-call `api_key`, `base_url` or `api_base`, `api_version`, and `extra_headers` when needed.
- Unknown or provider-specific parameters may be translated, forwarded, or dropped depending on provider support; validate behavior with `mock_response`, verbose logs, or a targeted live smoke call.

## Quick Patterns

```python
import litellm

response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    temperature=0.2,
    timeout=30,
)
print(response.choices[0].message.content)
```

```python
stream = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Count to three."}],
    stream=True,
    stream_options={"include_usage": True},
)
for chunk in stream:
    delta = chunk.choices[0].delta.content if chunk.choices else None
    if delta:
        print(delta, end="")
```

```python
response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Return JSON with a color field."}],
    response_format={"type": "json_object"},
    mock_response='{"color":"blue"}',
)
```

## Validation Checklist

- Import check: `python sub-skills/sdk-core/scripts/sdk_smoke.py --checks import`.
- Signature check: `python sub-skills/sdk-core/scripts/sdk_smoke.py --checks signature`.
- Mock SDK check: `python sub-skills/sdk-core/scripts/sdk_smoke.py --checks mock`.
- Optional live check: set the provider key in an environment variable, then run `python sub-skills/sdk-core/scripts/sdk_smoke.py --provider-smoke --model openai/gpt-4o-mini --api-key-env OPENAI_API_KEY`.

## Safety Defaults

- Prefer `mock_response` for tests and diagnostics that should not spend provider credits.
- Do not hard-code API keys; use provider environment variables or pass `api_key` from a secret manager.
- Keep `timeout` explicit on production calls.
- Reset global callbacks/cache in tests that mutate `litellm.callbacks`, `litellm.success_callback`, `litellm.failure_callback`, or `litellm.cache`.

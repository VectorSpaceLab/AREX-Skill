---
name: llm-and-output
description: "Select Browser Use LLM adapters and configure provider
  credentials, ChatBrowserUse defaults, structured output, extraction LLMs,
  fallback models, token/cost tracking, and model troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LLM and Output

Use this sub-skill when the user is choosing or debugging the model layer for Browser Use: `ChatBrowserUse`, OpenAI, Anthropic, Google/Gemini, Azure, Groq, Mistral, Ollama, OpenRouter, Vercel, OCI, AWS/Bedrock, structured Pydantic output, page extraction models, fallback LLMs, or token/cost accounting.

## Route Here

- The request mentions `llm=...`, `ChatBrowserUse`, `ChatOpenAI`, `ChatGoogle`, `ChatAnthropic`, `ChatMistral`, `ChatOllama`, `ChatOpenRouter`, `ChatVercel`, `ChatAzureOpenAI`, `ChatLiteLLM`, or `browser_use.llm.models`.
- The user asks which model to use, how to set provider API keys, how to pass `api_key`, `base_url`, retry, timeout, temperature, reasoning, or structured-output flags.
- The user needs `output_model_schema`, `history.structured_output`, `history.get_structured_output(...)`, Pydantic validation, JSON schema repair, or final-result parsing.
- The task uses `page_extraction_llm`, extraction schema, or a cheaper model for `extract` actions.
- The task uses `fallback_llm`, model failover, `agent.is_using_fallback_llm`, or `agent.current_llm_model`.
- The task asks for `calculate_cost`, `pricing_url`, token usage, usage summaries, or cost logs.

## Route Elsewhere

- General `Agent(...)`, task prompting, callbacks, history helpers, run-loop behavior, planning, flash mode, and timeouts belong in `../agent-programming/SKILL.md`.
- Browser/profile/CDP/session settings, cloud browser sessions, downloads, domains, screenshots, and low-level browser control belong in `../browser-control/SKILL.md`.
- Custom actions, default tools, file tools, sensitive data handling, and `ActionResult` belong in `../tools-and-actions/SKILL.md`.
- Terminal `browser-use` or `bu` CLI sessions belong in `../cli-and-sessions/SKILL.md`.
- `@sandbox`, Browser Use Cloud production deployment, MCP, skills, telemetry, and external integrations belong in `../production-integrations/SKILL.md`.

## Recommended Default

For new browser automation code, recommend `ChatBrowserUse()` first. It is the Browser Use maintained chat adapter for browser automation and defaults to the optimized `bu-2-0` model when `BROWSER_USE_API_KEY` is set.

```python
import asyncio
from browser_use import Agent, ChatBrowserUse

async def main():
    agent = Agent(
        task="Open https://example.com and report the page title.",
        llm=ChatBrowserUse(),
    )
    history = await agent.run(max_steps=10)
    print(history.final_result())

asyncio.run(main())
```

Do not replace model names in existing user code. Users may intentionally test new provider models that are unknown to this skill. If code already specifies a model, preserve it unless the user asks for a recommendation or the model is the direct cause of an error.

## Credential Rules

- Prefer environment variables loaded by the user's app or shell; do not print API keys.
- `ChatBrowserUse()` reads `BROWSER_USE_API_KEY`; it can also accept `api_key=...` and `base_url=...` explicitly.
- OpenAI-compatible adapters usually accept `api_key=...`, `base_url=...`, `timeout=...`, and `max_retries=...`.
- Provider adapters read their conventional env vars when not passed explicitly, such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `MISTRAL_API_KEY`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `OPENROUTER_API_KEY`, or `CEREBRAS_API_KEY` depending on the chosen adapter.
- Optional provider packages may be needed for less common adapters; if an import fails, install the documented extra or switch to a built-in adapter already available in the project environment.

See `references/models-and-credentials.md` for adapter snippets and credential checks.

## Model Adapter Patterns

Use top-level imports for common adapters:

```python
from browser_use import Agent, ChatBrowserUse, ChatOpenAI, ChatGoogle, ChatAnthropic
```

Use `browser_use.llm` for the full adapter surface and lazy imports:

```python
from browser_use.llm import ChatMistral, ChatOllama, ChatOpenRouter
```

Use `browser_use.llm.models.get_llm_by_name(...)` only when the user wants named aliases resolved from environment variables:

```python
from browser_use.llm.models import get_llm_by_name
llm = get_llm_by_name("bu_2_0")
```

Supported adapter families include Browser Use, OpenAI, Azure OpenAI, Google/Gemini, Anthropic, AWS/Bedrock, DeepSeek, Groq, Mistral, Cerebras, OCI raw, Ollama, OpenRouter, Vercel AI Gateway, and LiteLLM/LangChain compatibility paths.

## Structured Output

Use a Pydantic v2 model class with `output_model_schema=...` when the final answer must be machine-readable. Keep the model small and explicit.

```python
from pydantic import BaseModel
from browser_use import Agent, ChatBrowserUse

class Product(BaseModel):
    title: str
    price: str | None = None
    in_stock: bool

agent = Agent(
    task="Find the product title, price, and stock status. Return only the requested fields.",
    llm=ChatBrowserUse(),
    output_model_schema=Product,
)
history = await agent.run(max_steps=25)
product = history.structured_output or Product.model_validate_json(history.final_result())
```

Browser Use wires `output_model_schema` into the final `done` action and auto-bridges it to `extraction_schema` when no explicit extraction schema is provided. See `references/structured-output.md` for robust parsing, schema design, and validation repair.

## Page Extraction LLM

Use `page_extraction_llm` when normal planning needs a stronger model but page extraction should use a smaller, cheaper, or faster model.

```python
from browser_use import Agent, ChatBrowserUse, ChatOpenAI

agent = Agent(
    task="Find three pricing tiers and extract their names and monthly prices.",
    llm=ChatBrowserUse(),
    page_extraction_llm=ChatOpenAI(model="gpt-4.1-mini"),
)
```

This only changes extraction-style LLM calls used by tools such as `extract`; it does not replace the main planner. Custom tools that request `page_extraction_llm` are owned by `../tools-and-actions/SKILL.md`.

## Fallback Models

Use `fallback_llm` for resilience when the primary model fails with provider/rate-limit/server-style errors after the primary adapter's own retries are exhausted.

```python
from browser_use import Agent, ChatBrowserUse, ChatOpenAI

agent = Agent(
    task="Open https://example.com and summarize the page.",
    llm=ChatBrowserUse(),
    fallback_llm=ChatOpenAI(model="gpt-4.1-mini"),
)
history = await agent.run(max_steps=15)
if agent.is_using_fallback_llm:
    print(f"Switched to {agent.current_llm_model}")
```

See `references/cost-and-fallbacks.md` for failure classes, retry implications, and cost-aware patterns.

## Cost and Token Tracking

Set `calculate_cost=True` on `Agent` to populate `history.usage` and log usage summaries where adapter usage data is available. Browser Use token costing can use built-in pricing, OpenRouter pricing, custom mappings, and a configurable pricing URL.

```python
agent = Agent(task="...", llm=ChatBrowserUse(), calculate_cost=True)
history = await agent.run(max_steps=20)
if history.usage:
    print(history.usage.total_tokens, history.usage.total_cost)
```

Use `pricing_url=...` only when the user has a trusted model-pricing source. See `references/cost-and-fallbacks.md` for fields and caveats.

## Validation Checks

Run these lightweight checks before debugging a full web task:

```bash
python - <<'PY'
from browser_use import Agent, ChatBrowserUse, ChatOpenAI
from browser_use.llm import ChatGoogle, ChatAnthropic
print(Agent, ChatBrowserUse, ChatOpenAI, ChatGoogle, ChatAnthropic)
PY
```

Check credentials without revealing values:

```bash
python - <<'PY'
import os
for name in ["BROWSER_USE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
    print(name, "set" if os.getenv(name) else "missing")
PY
```

If `ChatBrowserUse()` raises `BROWSER_USE_API_KEY is not set`, either set the key or choose a different adapter with its own credentials.

## Troubleshooting First Steps

Start with `references/troubleshooting.md`, then narrow the failure:

- Import failure: verify package install, adapter import path, and optional extras for the provider.
- Authentication failure: confirm the right env var is set in the same shell or process running Python; do not log key contents.
- Structured-output failure: simplify the Pydantic model, cap steps, inspect `history.final_result()`, then validate with `model_validate_json`.
- Extraction failure: confirm `page_extraction_llm` is configured and the task tells the agent to use extraction where appropriate.
- Fallback not used: check whether the primary model is still retrying internally, or whether the error is not a model provider/rate-limit/server error.
- Cost missing: confirm `calculate_cost=True`, the adapter returns usage, and pricing data exists for the model.

## Hard Case Patterns

Support multi-skill requests by routing only the model/output portion here. Examples:

- Authenticated production extraction with `Browser(use_cloud=True)`, `ChatBrowserUse`, a custom 2FA tool, and structured Pydantic output: use this sub-skill for model/output schema and fallback; route cloud browser to `../browser-control/SKILL.md` or production deployment to `../production-integrations/SKILL.md`; route 2FA tool to `../tools-and-actions/SKILL.md`.
- Failure recovery where a user reports `ValidationError` after `history.final_result()`: use this sub-skill to repair schema/output parsing, then route run-loop or browser failures to the appropriate sibling only if model/output fixes do not explain the symptom.

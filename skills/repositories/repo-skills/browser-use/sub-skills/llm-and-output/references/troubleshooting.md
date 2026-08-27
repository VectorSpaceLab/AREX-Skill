# LLM and Output Troubleshooting

Use this guide for model/provider credentials, structured output, extraction models, fallback models, token/cost tracking, and LLM-adapter import failures. Route browser launch/session/CDP errors to `../../browser-control/SKILL.md`, custom tool/file/domain errors to `../../tools-and-actions/SKILL.md`, and run-loop/prompt/history issues to `../../agent-programming/SKILL.md`.

## Triage Checklist

1. Reproduce with the smallest script using `ChatBrowserUse()` or the exact user adapter.
2. Run an import smoke test.
3. Check key presence without printing secrets.
4. Confirm the failure class: import, authentication, provider response, structured validation, extraction, fallback, cost, or non-LLM.
5. Inspect `history.errors()`, `history.final_result()`, and `history.usage` only after the run returns a history object.

Import smoke test:

```bash
python - <<'PY'
from browser_use import Agent, ChatBrowserUse, ChatOpenAI, ChatGoogle, ChatAnthropic
from browser_use.llm import ChatMistral, ChatOllama, ChatOpenRouter
print("llm imports ok")
PY
```

Credential presence check:

```bash
python - <<'PY'
import os
for key in ["BROWSER_USE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
    print(key, "set" if os.getenv(key) else "missing")
PY
```

## Install and Import Failures

### Symptom: `ImportError: Failed to import Chat...`

Likely causes:

- `browser-use` is not installed in the active environment.
- Optional provider dependency is missing.
- The project is running a different Python interpreter than expected.
- The adapter name is misspelled or imported from the wrong module.

Fixes:

- Verify the active interpreter imports Browser Use:

  ```bash
  python - <<'PY'
  import browser_use
  from browser_use import Agent, ChatBrowserUse
  print(browser_use.__file__)
  print(Agent, ChatBrowserUse)
  PY
  ```

- Use top-level imports for common adapters and `browser_use.llm` for the wider adapter set.
- Install the provider extra or dependency requested by the import error.
- If OCI fails, use `ChatOCIRaw` only after installing OCI dependencies and configuring OCI credentials manually.

## Missing API Keys

### Symptom: `BROWSER_USE_API_KEY is not set`

`ChatBrowserUse()` requires `BROWSER_USE_API_KEY` unless `api_key=` is passed.

Fixes:

```bash
export BROWSER_USE_API_KEY="..."
```

or:

```python
import os
from browser_use import ChatBrowserUse

llm = ChatBrowserUse(api_key=os.getenv("BROWSER_USE_API_KEY"))
```

Do not paste real keys into prompts, logs, examples, or generated skill content.

### Symptom: provider says unauthorized, invalid key, or forbidden

Fixes:

- Confirm the env var for that adapter: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `MISTRAL_API_KEY`, Azure endpoint/key variables, or gateway-specific keys.
- Confirm the key is available to the same shell, container, sandbox, or process.
- Construct only the LLM first before creating an Agent.
- For Azure, confirm endpoint and deployment/model naming.

## Provider and Model Errors

### Symptom: invalid model name

For `ChatBrowserUse`, valid built-in aliases include `bu-2-0`, `bu-1-0`, and `bu-latest`, plus provider-prefixed ids containing `/` that the gateway can resolve.

Fixes:

- Preserve the user's requested model if they are testing a new model and the provider accepts it.
- If Browser Use rejects the model before any API call, use a valid alias or provider-prefixed id.
- If a provider rejects the model, check the provider account, region, gateway, and exact deployment name.

### Symptom: rate limit, timeout, 500-class errors

Fixes:

- Let the adapter's retry settings work first.
- Increase adapter `timeout` only when the provider is slow and the task is otherwise valid.
- Add a different-provider `fallback_llm` for resilience.
- Reduce max steps or use a smaller extraction model to lower request volume.

```python
agent = Agent(
    task="...",
    llm=ChatBrowserUse(max_retries=5, timeout=120),
    fallback_llm=ChatOpenAI(model="gpt-4.1-mini"),
)
```

## Structured Output Failures

### Symptom: Pydantic `ValidationError`

Likely causes:

- The agent returned prose instead of a structured final `done` payload.
- Required fields are missing from the page.
- Field types are too strict.
- The schema is too complex for the model/provider.

Fixes:

1. Confirm the Agent used `output_model_schema=MyModel`.
2. Inspect `history.final_result()`.
3. Parse explicitly with `MyModel.model_validate_json(...)`.
4. Make uncertain fields optional.
5. Add task instructions for exact count, null handling, and “finish with structured output only.”
6. Try `ChatBrowserUse()` or provider-specific structured-output compatibility flags.

### Symptom: `history.structured_output` is `None`

Fixes:

- Check `history.is_done()` and `history.is_successful()`.
- Use `history.get_structured_output(MyModel)` if available.
- Parse `history.final_result()` manually.
- Ensure the returned history is from the run that used `output_model_schema`.

## Extraction LLM Failures

### Symptom: extracted content is empty or malformed

Fixes:

- Add explicit task instructions to use extraction for the target fields.
- Configure `page_extraction_llm` with a model that handles the page language and schema.
- Simplify `extraction_schema` or rely on the auto-bridged schema from `output_model_schema`.
- Confirm the browser reached the page; navigation and DOM visibility issues belong in `../../browser-control/SKILL.md`.

### Symptom: custom action says `requires page_extraction_llm but none provided`

This is a custom tool injection issue. Ensure the Agent has an LLM and `page_extraction_llm` when the action needs it, then route custom action implementation details to `../../tools-and-actions/SKILL.md`.

## Fallback Failures

### Symptom: `fallback_llm` is configured but never used

Likely causes:

- The primary adapter is still retrying.
- The error is not a model provider/rate-limit/server error.
- The fallback adapter failed to construct due to missing credentials.

Fixes:

```python
print(agent.is_using_fallback_llm)
print(agent.current_llm_model)
print(history.errors())
```

If the first error mentions Chromium, CDP, profile, proxy, domain filtering, file access, or action validation, route to the relevant sibling sub-skill instead of changing models.

### Symptom: fallback activates but structured output breaks

Fixes:

- Choose a fallback with comparable structured-output support.
- Simplify the Pydantic schema.
- Use provider compatibility flags such as `supports_structured_output=False` for Google or OpenAI schema flags when appropriate.
- Keep final output instructions explicit.

## Cost and Usage Failures

### Symptom: `history.usage` is missing

Fixes:

- Confirm the run returned normally enough to finalize history.
- Confirm the adapter returns usage metadata.
- Use `calculate_cost=True` when cost fields are required.

### Symptom: token counts exist but cost is zero

Fixes:

- Set `calculate_cost=True` or `BROWSER_USE_CALCULATE_COST=true`.
- Confirm pricing data includes the model id.
- Use `pricing_url=...` only for a trusted pricing source.
- For gateway models, check whether their model ids map to pricing data.

## Browser or Session Failures That Are Not LLM Problems

If the error mentions any of these, route away from this sub-skill:

- Browser executable, Chromium install, Playwright, CDP URL, profile locks, downloads, proxies, domains, screenshots, or HAR: `../../browser-control/SKILL.md`.
- CLI session selection, `browser-use` command flags, persistent sessions, or terminal binary: `../../cli-and-sessions/SKILL.md`.
- Custom tools, `ActionResult`, tool parameter injection, sensitive data, file upload/download containment, or action schema validation: `../../tools-and-actions/SKILL.md`.
- Sandbox deployment, cloud profile sync, MCP, telemetry, or external integrations: `../../production-integrations/SKILL.md`.

## Minimal Reproduction Template

Use this when filing or debugging a model/output issue:

```python
import asyncio
from pydantic import BaseModel
from browser_use import Agent, ChatBrowserUse

class Result(BaseModel):
    title: str | None = None

async def main():
    agent = Agent(
        task="Open https://example.com and return the page title only.",
        llm=ChatBrowserUse(),
        output_model_schema=Result,
        calculate_cost=True,
    )
    history = await agent.run(max_steps=5)
    print("done", history.is_done())
    print("errors", history.errors())
    print("final", history.final_result())
    print("structured", history.structured_output)
    print("usage", history.usage)

asyncio.run(main())
```

If this minimal script works, reintroduce the user's custom browser settings, tools, schemas, and production wrappers one at a time, routing each failure to the owning sibling sub-skill.

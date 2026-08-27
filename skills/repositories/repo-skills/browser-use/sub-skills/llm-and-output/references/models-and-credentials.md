# Models and Credentials

Use this reference to select Browser Use LLM adapters, configure credentials, and run safe import/key checks. Preserve user-provided model names unless the user asks for a recommendation or the model choice is causing the failure.

## Safe Defaults

Prefer `ChatBrowserUse()` for new Browser Use automation because it is maintained for browser automation tasks and defaults to `bu-2-0`.

```python
from browser_use import Agent, ChatBrowserUse

agent = Agent(
    task="Open https://example.com and report the page title.",
    llm=ChatBrowserUse(),
)
```

`ChatBrowserUse(model="bu-latest")` normalizes to the current latest Browser Use model. It also accepts provider-prefixed gateway ids such as `openai/...`, `anthropic/...`, `google/...`, or `browser-use/...` when the Browser Use gateway supports them.

## Credential Checklist

- Load `.env` or shell variables before constructing the LLM.
- Check whether variables are present, never print their values.
- Prefer explicit `api_key=os.getenv("...")` when debugging environment propagation.
- Keep provider keys out of task prompts; if a site login needs secrets, route sensitive-data or custom-tool handling to `../../tools-and-actions/SKILL.md`.

Safe key-presence check:

```bash
python - <<'PY'
import os
for name in [
    "BROWSER_USE_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "MISTRAL_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "OPENROUTER_API_KEY",
    "CEREBRAS_API_KEY",
]:
    print(f"{name}: {'set' if os.getenv(name) else 'missing'}")
PY
```

## Common Top-Level Imports

The public package lazily exposes common chat adapters:

```python
from browser_use import (
    Agent,
    ChatBrowserUse,
    ChatOpenAI,
    ChatGoogle,
    ChatAnthropic,
    ChatMistral,
    ChatAzureOpenAI,
    ChatOllama,
    ChatVercel,
)
```

For the wider adapter set, import from `browser_use.llm`:

```python
from browser_use.llm import ChatGroq, ChatOpenRouter, ChatCerebras, ChatOCIRaw
```

## Adapter Recipes

### Browser Use

```python
from browser_use import ChatBrowserUse

llm = ChatBrowserUse()                         # requires BROWSER_USE_API_KEY
llm = ChatBrowserUse(model="bu-2-0")
llm = ChatBrowserUse(model="openai/gpt-5.5")   # gateway model id, if enabled for the account
```

Useful constructor knobs: `model`, `api_key`, `base_url`, `timeout`, `max_retries`, `retry_base_delay`, `retry_max_delay`.

If `BROWSER_USE_API_KEY` is missing, construction raises a `ValueError` telling the user to set the key.

### OpenAI

```python
from browser_use import ChatOpenAI

llm = ChatOpenAI(model="gpt-4.1-mini")
```

Useful knobs include `model`, `temperature`, `reasoning_effort`, `seed`, `top_p`, `api_key`, `base_url`, `timeout`, `max_retries`, `max_completion_tokens`, `add_schema_to_system_prompt`, `dont_force_structured_output`, `remove_min_items_from_schema`, and `remove_defaults_from_schema`.

Use `base_url` for OpenAI-compatible gateways:

```python
llm = ChatOpenAI(
    model="provider/model-id",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
```

### Google/Gemini

```python
from browser_use import ChatGoogle

llm = ChatGoogle(model="gemini-3-flash-preview")
```

Useful knobs include `api_key`, `vertexai`, `credentials`, `project`, `location`, `thinking_budget`, `thinking_level`, `max_output_tokens`, `supports_structured_output`, and retry settings. If structured output fails with a Gemini model, try `supports_structured_output=False` to use a prompt-based fallback.

### Anthropic

```python
from browser_use import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-0")
```

Useful knobs include `model`, `max_tokens`, `temperature`, `thinking`, `betas`, `fallbacks`, `api_key`, `auth_token`, `base_url`, `timeout`, and `max_retries`.

### Azure OpenAI

```python
from browser_use import ChatAzureOpenAI

llm = ChatAzureOpenAI(
    model="gpt-4.1-mini",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)
```

Azure failures are often endpoint/deployment-name mismatches rather than Browser Use issues. Verify the deployment name expected by the Azure resource.

### Mistral

```python
from browser_use.llm import ChatMistral

llm = ChatMistral(model="mistral-small-latest")
```

Mistral uses `MISTRAL_API_KEY` and optional `MISTRAL_BASE_URL`. Its structured-output path strips unsupported JSON schema keywords before sending schemas.

### Ollama

```python
from browser_use.llm import ChatOllama

llm = ChatOllama(model="llama3.1")
```

Use Ollama when the user explicitly wants a local model. Troubleshoot local server availability, model pulls, and vision/structured-output support before changing Browser Use code.

### OpenRouter and Vercel

```python
from browser_use.llm import ChatOpenRouter, ChatVercel

openrouter_llm = ChatOpenRouter(model="openai/gpt-4.1-mini")
vercel_llm = ChatVercel(model="openai/gpt-4.1-mini")
```

These adapters may return usage data that Browser Use can cost when pricing information is available.

### LiteLLM and LangChain Compatibility

Browser Use includes compatibility adapters, but they are best for advanced users who already have a working LiteLLM or LangChain setup. If a novice asks which path to use, prefer a native Browser Use adapter first.

## Named Model Factory

`browser_use.llm.models.get_llm_by_name(...)` resolves named aliases and reads the expected env var for the provider.

```python
from browser_use.llm.models import get_llm_by_name

llm = get_llm_by_name("bu_2_0")
llm = get_llm_by_name("openai_gpt_4_1_mini")
llm = get_llm_by_name("anthropic_claude_sonnet_4_0")
```

Factory behavior:

- Empty names raise `ValueError("Model name cannot be empty")`.
- Names generally use `provider_model_name` format.
- Provider names include `openai`, `azure`, `google`, `anthropic`, `mistral`, `cerebras`, and `bu`.
- OCI models require manual configuration with `ChatOCIRaw` and are not resolved by the simple factory.

## Import Smoke Test

Run this before diagnosing provider-specific failures:

```bash
python - <<'PY'
from browser_use import Agent, ChatBrowserUse, ChatOpenAI, ChatGoogle, ChatAnthropic
from browser_use.llm import ChatMistral, ChatOllama
from browser_use.llm.models import get_llm_by_name
print("imports ok")
print(get_llm_by_name)
PY
```

If this fails, fix installation/import issues before changing model configuration.

## Model Selection Guidance

- Use `ChatBrowserUse()` for most browser automation tasks.
- Use a provider model only when the user has a provider preference, a compliance requirement, local-model requirement, or a confirmed account/region setup.
- Use a smaller `page_extraction_llm` for extraction-heavy workflows to control cost.
- Use `fallback_llm` with a different provider when availability matters.
- Disable or lower vision only when the task can succeed from DOM/text and the model or provider struggles with image inputs.

Vision and screenshot behavior crosses into agent/browser configuration; route low-level screenshot/browser settings to `../../browser-control/SKILL.md` and agent `use_vision` behavior to `../../agent-programming/SKILL.md`.

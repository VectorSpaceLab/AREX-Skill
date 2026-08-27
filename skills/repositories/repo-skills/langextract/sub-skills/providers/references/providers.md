# Provider Configuration Reference

Use this reference when a task is about LangExtract provider selection, credentials, model routing, provider kwargs, or batch behavior. Prompt examples and schema design belong in `../extraction/SKILL.md`; custom third-party backend authoring belongs in `../provider-plugins/SKILL.md`.

## Effective factory APIs

Installed-package inspection confirmed these signatures:

```python
from langextract import factory

factory.ModelConfig(
    model_id: str | None = None,
    provider: str | None = None,
    provider_kwargs: dict | None = None,
)

factory.create_model(
    config,
    examples=None,
    use_schema_constraints=False,
    fence_output=None,
    return_fence_output=False,
    output_schema=None,
)

factory.create_model_from_id(
    model_id=None,
    provider=None,
    *,
    output_schema=None,
    **provider_kwargs,
)
```

`lx.extract()` accepts either simple provider arguments (`model_id`, `api_key`, `model_url`, `language_model_params`) or advanced provider objects through `config=` / `model=`. Use the high-level `lx.extract()` path unless you need explicit provider disambiguation, a custom provider, or a preconfigured model.

## Built-in provider routing

The built-in router registers these practical model-ID families:

| Provider | Model-ID signals | Notes |
| --- | --- | --- |
| Gemini | IDs beginning with `gemini` | Default provider path; supports schema constraints and user `output_schema`. |
| OpenAI | IDs beginning with `gpt-4`, `gpt4.`, `gpt-5`, or `gpt5.` | Requires the OpenAI optional dependency (`langextract[openai]`). Non-GPT OpenAI-compatible IDs need explicit provider selection. |
| Ollama | Local model IDs such as `gemma`, `llama`, `mistral`, `qwen`, `deepseek`, `gpt-oss`, and selected Hugging Face style IDs | Requires a local or proxied Ollama service and a pulled model. No API key is needed for native localhost Ollama. |

Inspect routing without credentials or network:

```bash
python scripts/check_provider_routes.py
python scripts/check_provider_routes.py gemini-3.5-flash gpt-4o gemma2:2b
python scripts/check_provider_routes.py --skip-plugins --json
```

Use explicit provider selection when model-ID auto-routing is ambiguous or insufficient:

```python
import langextract as lx

config = lx.factory.ModelConfig(
    model_id="my-openai-compatible-model",
    provider="openai",
    provider_kwargs={
        "api_key": "...",        # Prefer environment lookup in real code.
        "base_url": "https://openai-compatible.example/v1",
    },
)

result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    config=config,
)
```

Provider names may be broad (`"gemini"`, `"openai"`, `"ollama"`) or class-name-like (`"GeminiLanguageModel"`, `"OpenAILanguageModel"`, `"OllamaLanguageModel"`) when the router can resolve them.

## Credential and environment-variable behavior

Never embed secrets in skill-guided code. Prefer environment variables or caller-owned secret stores.

| Provider | Common variables | Behavior |
| --- | --- | --- |
| Gemini API key | `GEMINI_API_KEY`, then `LANGEXTRACT_API_KEY` | The factory adds `api_key` for Gemini-like model IDs when not explicitly supplied. |
| Vertex AI Gemini | `GOOGLE_CLOUD_PROJECT` or explicit `project`; Google application credentials | Set `vertexai=True`, `project`, and `location` in provider kwargs / `language_model_params`. API key is not required for Vertex mode. |
| OpenAI | `OPENAI_API_KEY`, then `LANGEXTRACT_API_KEY` for GPT-style IDs | Explicit `api_key` wins. Install the OpenAI extra first. |
| Ollama | `OLLAMA_BASE_URL` or explicit `model_url` / `base_url` | Defaults to `http://localhost:11434` for Ollama IDs. Native localhost Ollama does not require an API key. |

`api_key` and explicit `provider_kwargs` override environment defaults. If both API-key and Vertex AI settings are provided for Gemini, the API key path takes precedence for authentication and should be simplified unless that is intentional.

## Gemini and Vertex AI

Gemini provider construction accepts:

```python
from langextract.providers.gemini import GeminiLanguageModel

GeminiLanguageModel(
    model_id="gemini-3.5-flash",
    api_key=None,
    vertexai=False,
    credentials=None,
    project=None,
    location=None,
    http_options=None,
    format_type=lx.data.FormatType.JSON,
    temperature=0.0,
    max_workers=10,
    fence_output=False,
    max_retries=3,
    retry_delay=1.0,
    max_retry_delay=16.0,
    # plus selected Gemini API config keys
)
```

Use high-level `lx.extract()` for normal Gemini calls:

```python
result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-3.5-flash",
    language_model_params={
        "max_retries": 3,
        "retry_delay": 1.0,
        "max_output_tokens": 512,
    },
)
```

For Vertex AI:

```python
result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-3.5-flash",
    language_model_params={
        "vertexai": True,
        "project": "your-gcp-project",
        "location": "us-central1",
    },
)
```

Vertex AI mode requires both `project` and `location`. Batch mode for Gemini is Vertex-oriented and requires storage access.

## Gemini Batch API

Gemini batch settings live under `language_model_params={"batch": ...}`. The batch config fields are:

```python
{
    "enabled": True,
    "threshold": 50,
    "poll_interval": 30,
    "timeout": 3600,
    "max_prompts_per_job": 20000,
    "ignore_item_errors": False,
    "enable_caching": True,    # required explicitly when enabled
    "retention_days": 30,      # required explicitly; use None for permanent
}
```

Operational notes:

- Batch only triggers when the prompt count is at least `threshold`; otherwise realtime Gemini is used.
- `enable_caching` and `retention_days` must be explicit when batch is enabled.
- GCS input/output/cache objects are managed by the package; callers need suitable Vertex/GCS permissions.
- Batch jobs are non-latency-sensitive and may cost less than realtime calls, but failures are more operationally complex.

## OpenAI and OpenAI-compatible endpoints

OpenAI provider construction accepts:

```python
from langextract.providers.openai import OpenAILanguageModel

OpenAILanguageModel(
    model_id="gpt-4o-mini",
    api_key=None,
    base_url=None,
    organization=None,
    format_type=lx.data.FormatType.JSON,
    temperature=None,
    max_workers=10,
    batch=None,
)
```

Install the optional dependency before using it:

```bash
python -m pip install "langextract[openai]"
```

GPT-style `model_id`s auto-route to OpenAI. For non-GPT OpenAI-compatible endpoints, use `ModelConfig`:

```python
config = lx.factory.ModelConfig(
    model_id="my-json-chat-model",
    provider="openai",
    provider_kwargs={
        "base_url": "https://openai-compatible.example/v1",
        "api_key": "...",
    },
)
```

OpenAI JSON mode emits raw JSON by default (`requires_fence_output=False` for JSON). Leave `fence_output` unset unless you deliberately need a low-level fenced flow. OpenAI supports user `output_schema` through its structured-output schema path when the chosen model/endpoint supports it.

## OpenAI Batch API

OpenAI batch settings are passed as the provider kwarg `batch`, usually inside `ModelConfig.provider_kwargs` or through `language_model_params` when using `lx.extract()` provider construction.

```python
language_model_params={
    "batch": {
        "enabled": True,
        "threshold": 50,
        "completion_window": "24h",
        "poll_interval": 10,
        "timeout": 24 * 60 * 60 + 300,
        "max_requests_per_job": 50000,
        "metadata": {"workflow": "nightly-extraction"},
    }
}
```

Operational notes:

- OpenAI batch only triggers when the prompt count meets `threshold`.
- The helper uses the OpenAI Files and Batch APIs; output download failures can be permission-related.
- Per-item errors are not silently accepted. Treat batch as a production-style asynchronous path, not a debugging shortcut.

## Ollama local models

Ollama provider construction accepts:

```python
from langextract.providers.ollama import OllamaLanguageModel

OllamaLanguageModel(
    model_id="gemma2:2b",
    model_url="http://localhost:11434",
    base_url=None,
    format_type=None,
    timeout=None,
    # plus options such as seed, top_k, top_p, num_ctx, num_threads,
)
```

A simple high-level call:

```python
result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemma2:2b",
    model_url="http://localhost:11434",
    use_schema_constraints=False,
    fence_output=False,
)
```

Preflight before calling inference:

```bash
python scripts/ollama_demo.py --model gemma2:2b --preflight-only
```

Ollama facts:

- Native localhost Ollama does not need an API key.
- A proxied Ollama-compatible service may need `api_key`, `auth_scheme`, or `auth_header` kwargs.
- JSON is the default format mode. YAML is possible at lower levels but most extraction recipes should prefer JSON.
- LangExtract defaults `think=False` so reasoning-model traces are not mistaken for final JSON.
- GPT-OSS Ollama JSON calls use a chat adapter with a strict JSON system instruction.

## Schema/fence interactions across providers

Provider schemas decide whether raw JSON or fenced JSON is expected.

- Gemini schema constraints and explicit `output_schema` produce raw JSON.
- OpenAI JSON/structured outputs produce raw JSON.
- Ollama `FormatModeSchema` can enforce JSON syntax, but does not support user-provided `output_schema`.
- `output_schema` cannot be combined with `fence_output=True`, non-JSON `format_type`, or provider-native schema kwargs such as `response_format`, `response_schema`, or `response_json_schema`.
- If a caller passes a preconfigured `model=...`, `use_schema_constraints` is ignored unless the model is already configured or an `output_schema` is applied.

When the user's issue is about extraction schema shape, class names, attributes, or prompt examples, route to `../extraction/SKILL.md`.

## Live checks versus no-network inspection

This generated skill's provider guidance can be checked without credentials by inspecting router patterns and constructor signatures. Treat these as separate from live service validation:

- Safe/no-network: import package, inspect signatures, load built-ins/plugins, resolve provider classes, run mocked batch helper tests, run `scripts/check_provider_routes.py`.
- Credentialed/network: Gemini API calls, Vertex AI batch jobs, OpenAI realtime or batch calls.
- Local service: Ollama daemon/model availability and local inference.

Do not report optional live API or Ollama checks as verified unless they were actually run in the caller's environment.

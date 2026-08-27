# API Models

API model configs use OpenCompass wrappers around remote model services. They should be credential-safe, rate-limited, and configured with local resource requirements that match client-side work rather than server-side inference.

## OpenAI-Compatible Config

Use `OpenAI` or `OpenAISDK` for OpenAI and OpenAI-compatible services. `OpenAISDK` is the preferred route for modern OpenAI-compatible servers and deployed accelerator services.

```python
from opencompass.models import OpenAISDK

models = [
    dict(
        type=OpenAISDK,
        abbr='gpt-4o-api',
        path='gpt-4o',
        key='ENV',
        openai_api_base='https://api.openai.com/v1/',
        tokenizer_path='gpt-4',
        max_seq_len=8192,
        max_out_len=512,
        query_per_second=1,
        retry=3,
        rpm_verbose=True,
        batch_size=1,
        run_cfg=dict(num_gpus=0),
    )
]
```

Important fields:

- `key='ENV'`: reads `OPENAI_API_KEY`; do not put real keys into reusable configs.
- `openai_api_base`: API base URL. `OpenAI` supports an `ENV` mode for `OPENAI_BASE_URL` in code paths that use its default constants; explicit values are clearer for reusable configs.
- `openai_proxy_url='ENV'`: reads `OPENAI_PROXY_URL` when a proxy is needed.
- `path`: model name sent to the provider or compatible server.
- `tokenizer_path`: used for token length estimation; if omitted, OpenAI wrappers may fall back to `path` or `gpt-4` tokenization behavior.
- `query_per_second`: client-side rate limit.
- `retry`: retry count for provider/server failures.
- `rpm_verbose`: prints request-rate information.
- `max_workers`: controls OpenAI SDK client concurrency when supported by the wrapper.
- `extra_body`: provider/server-specific request fields for OpenAI-compatible endpoints.
- `run_cfg=dict(num_gpus=0)`: remote APIs usually need no local GPU.

## Credential Patterns

Prefer one of these patterns:

```python
# Public/shared config: requires runtime environment variable.
key='ENV'

# Local-only config: placeholder that must be replaced outside version control.
key='YOUR_API_KEY'

# OpenAI-compatible local server that ignores keys.
key='EMPTY'
```

Common environment variables:

- `OPENAI_API_KEY`: read by OpenAI-compatible wrappers when `key='ENV'`.
- `OPENAI_BASE_URL`: useful for OpenAI-compatible base URL defaults in OpenAI code paths.
- `OPENAI_PROXY_URL`: read when `openai_proxy_url='ENV'`.
- Provider-specific wrappers may require names such as API key, secret, app id, organization, or base URL fields directly in config; keep real values outside shared files.

## Rate and Batch Configuration

API failures often come from resource mismatch rather than prompt/dataset bugs.

- Set `batch_size=1` first for strict providers; increase only when the wrapper/provider supports concurrent requests safely.
- Use `query_per_second` to stay below provider rate limits.
- Use `retry` for transient failures, but do not mask permanent auth or quota errors with very high retry counts.
- Use `max_seq_len` and `max_out_len` that fit the provider model; token overflows may look like generic bad-request failures.
- For hosted inference services, `run_cfg.num_gpus` should usually be `0`; the server owns GPU allocation.

## OpenAI-Compatible Accelerator Service

LMDeploy and vLLM can expose OpenAI-compatible services. In that route, OpenCompass only sends API requests and performs token accounting.

```python
from opencompass.models import OpenAISDK

models = [
    dict(
        type=OpenAISDK,
        abbr='local-accelerated-api',
        key='EMPTY',
        openai_api_base='http://127.0.0.1:23333/v1',
        path='served-model-name',
        tokenizer_path='model-or-tokenizer-name',
        query_per_second=1,
        retry=3,
        max_seq_len=4096,
        max_out_len=512,
        batch_size=8,
        run_cfg=dict(num_gpus=0),
    )
]
```

Use `tokenizer_path` when the served model name is not a valid tokenizer id or when the default tokenizer estimate would be wrong.

## Native TurboMind API Wrapper

Use this for LMDeploy's native API service when examples or local conventions use `TurboMindAPIModel`.

```python
from opencompass.models.turbomind_api import TurboMindAPIModel

models = [
    dict(
        type=TurboMindAPIModel,
        abbr='internlm-turbomind-api',
        api_addr='http://127.0.0.1:23333',
        api_key=None,
        max_seq_len=2048,
        max_out_len=100,
        batch_size=8,
        run_cfg=dict(num_gpus=0, num_procs=1),
    )
]
```

## Dry-Run Config Check

Use the bundled script to inspect API model configs without constructing models or making network calls:

```bash
python scripts/check_api_model_config.py path/to/eval_config.py
```

The script checks:

- Whether `models = [...]` exists and is a list-like config value.
- Which model entries look API-backed by type name or API-specific fields.
- Missing or placeholder credentials for `key`, `api_key`, `api_secret`, `openai_api_base`, and `api_addr` fields.
- Suspicious `batch_size`, `query_per_second`, `retry`, and `run_cfg.num_gpus` settings.
- Whether `max_seq_len` and `max_out_len` are present.

It intentionally does not call `build_model_from_cfg()`, instantiate SDK clients, load tokenizers, or send test prompts.

## When to Write a New API Wrapper

Create a new `BaseAPIModel` subclass when provider behavior cannot be represented by existing wrappers.

Required behaviors:

- `is_api = True` for runner/resource handling.
- `generate(inputs, max_out_len, ...)` for generation tasks.
- `get_token_len(prompt)` for prompt truncation and length accounting.
- Provider auth, URL, retry, and rate-limit parameters exposed through constructor arguments.
- No hardcoded secrets.

Keep prompt-role mapping in `meta_template`/`APITemplateParser` conventions so dataset prompts remain reusable across providers.

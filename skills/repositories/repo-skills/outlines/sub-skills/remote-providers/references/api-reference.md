# Remote Provider API Reference

This reference summarizes the public Outlines API surface for server-based model
wrappers. Snippets use placeholders and are not meant to contact live services
inside this skill.

## Loader Selection

Import loaders from `outlines` or `outlines.models`:

```python
import outlines

# OpenAI / Azure / generic OpenAI-compatible endpoints
model = outlines.from_openai(openai_client, model_name="MODEL_NAME_OR_DEPLOYMENT")

# Provider-specific OpenAI-compatible servers
sglang_model = outlines.from_sglang(openai_client_for_sglang, model_name="MODEL_NAME")
vllm_model = outlines.from_vllm(openai_client_for_vllm, model_name="MODEL_NAME")

# Other server clients
anthropic_model = outlines.from_anthropic(anthropic_client, model_name="MODEL_NAME")
gemini_model = outlines.from_gemini(gemini_client, model_name="MODEL_NAME")
mistral_model = outlines.from_mistral(mistral_client, model_name="MODEL_NAME")
async_mistral_model = outlines.from_mistral(mistral_client, model_name="MODEL_NAME", async_client=True)
ollama_model = outlines.from_ollama(ollama_client, model_name="MODEL_NAME")
lmstudio_model = outlines.from_lmstudio(lmstudio_client, model_name="MODEL_NAME")
tgi_model = outlines.from_tgi(hf_inference_client)
dottxt_model = outlines.from_dottxt(dottxt_client, model="MODEL_ID")
```

### Exact verified signatures

- `from_anthropic(client, model_name=None)`
- `from_dottxt(client, model=None)`
- `from_gemini(client, model_name=None)`
- `from_lmstudio(client, model_name=None)`
- `from_mistral(client, model_name=None, async_client=False)`
- `from_ollama(client, model_name=None)`
- `from_openai(client, model_name=None)`
- `from_sglang(client, model_name=None)`
- `from_tgi(client)`
- `from_vllm(client, model_name=None)`

## Safe Client Construction Patterns

Use placeholders in examples and load real values only in downstream runtime code
that is allowed to use credentials. Do not print secret values.

```python
import os
import openai

# OpenAI
openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
model = outlines.from_openai(openai_client, "MODEL_NAME")

# Azure OpenAI through the OpenAI SDK family
azure_client = openai.AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)
model = outlines.from_openai(azure_client, "DEPLOYMENT_OR_MODEL_NAME")

# Generic OpenAI-compatible endpoint: this is still the OpenAI wrapper.
compatible_client = openai.OpenAI(
    base_url=os.environ["OPENAI_COMPATIBLE_BASE_URL"],
    api_key=os.environ["OPENAI_COMPATIBLE_API_KEY"],
)
model = outlines.from_openai(compatible_client, "PROVIDER/MODEL")
```

```python
# SGLang and vLLM are OpenAI-compatible but need their specialized loaders for
# server-side grammar/structured-output request fields.
sglang_client = openai.OpenAI(
    base_url=os.environ["SGLANG_BASE_URL"],
    api_key=os.environ.get("SGLANG_API_KEY", "EMPTY_OR_SERVER_TOKEN"),
)
sglang_model = outlines.from_sglang(sglang_client, "MODEL_NAME")

vllm_client = openai.OpenAI(
    base_url=os.environ["VLLM_BASE_URL"],
    api_key=os.environ.get("VLLM_API_KEY", "EMPTY_OR_SERVER_TOKEN"),
)
vllm_model = outlines.from_vllm(vllm_client, "MODEL_NAME")
```

```python
# TGI uses huggingface_hub clients.
from huggingface_hub import InferenceClient, AsyncInferenceClient

tgi = outlines.from_tgi(InferenceClient(os.environ["TGI_SERVER_URL"]))
async_tgi = outlines.from_tgi(AsyncInferenceClient(os.environ["TGI_SERVER_URL"]))
```

```python
# Dottxt requires constrained JSON generation and a model id.
from dottxt import DotTxt, AsyncDotTxt

dottxt_model = outlines.from_dottxt(DotTxt(api_key=os.environ["DOTTXT_API_KEY"]), "MODEL_ID")
async_dottxt_model = outlines.from_dottxt(AsyncDotTxt(api_key=os.environ["DOTTXT_API_KEY"]), "MODEL_ID")
```

```python
# Local server/client SDKs. These examples do not assert that services are up.
import ollama, lmstudio

ollama_model = outlines.from_ollama(ollama.Client(host=os.environ.get("OLLAMA_HOST")), "MODEL_NAME")
lmstudio_model = outlines.from_lmstudio(lmstudio.Client(), "MODEL_NAME")
```

## Calls, Streaming, Async, and Batch

Outlines models inherit a common public shape: call the model directly, call
`stream(...)` for streaming if available, or call `batch(...)` only when the
wrapper implements it. In this server-provider route, **batch is not
implemented for every listed provider**.

```python
# Sync generate
text = model("Prompt", max_tokens=64)

# Sync stream, only for wrappers with streaming support
for chunk in model.stream("Prompt", max_tokens=64):
    handle(chunk)

# Async generate / stream, only for wrappers with async support
text = await async_model("Prompt", max_tokens=64)
async for chunk in async_model.stream("Prompt", max_tokens=64):
    handle(chunk)
```

Async support by source wrapper:

- Yes by async client class: OpenAI/Azure, Dottxt, LM Studio, Ollama, SGLang,
  TGI, vLLM.
- Yes by flag: Mistral (`async_client=True`).
- No async wrapper in source: Anthropic, Gemini.

Streaming support by source wrapper:

- Yes: OpenAI/Azure, Anthropic, Gemini, LM Studio, Mistral, Ollama, SGLang, TGI,
  vLLM.
- No: Dottxt.

## Input Types

All providers accept plain `str` prompts. Additional accepted inputs are
provider-specific:

- `str`, `list` prompt+`Image`, and `Chat`: OpenAI/Azure, Anthropic, Gemini,
  LM Studio, Mistral, Ollama, SGLang, vLLM.
- `str` only: Dottxt and TGI.

For chat and multimodal details, route to `../../prompt-workflows/SKILL.md`.

## Output-Type Compatibility

| Desired `output_type` | Providers that support it in this route | Providers that reject it |
|---|---|---|
| `None` / plain text | all except Dottxt requires an output type | Dottxt |
| JSON schema object (`BaseModel`, dataclass, `TypedDict`, `outlines.json_schema`) | OpenAI/Azure, Dottxt, Gemini subset, LM Studio, Mistral, Ollama, SGLang, TGI, vLLM | Anthropic |
| JSON mode via `dict` | OpenAI/Azure, Mistral | Dottxt, Gemini, LM Studio, Ollama, Anthropic, SGLang/TGI/vLLM convert `dict` through their term path rather than OpenAI JSON mode |
| Multiple choice / enum / `Literal` | Gemini, SGLang, TGI, vLLM | OpenAI/Azure, Anthropic, Dottxt, LM Studio, Mistral, Ollama |
| Regex | SGLang, TGI, vLLM | OpenAI/Azure, Anthropic, Dottxt, Gemini, LM Studio, Mistral, Ollama |
| CFG / grammar | vLLM server; SGLang only with SGLang-compatible EBNF | OpenAI/Azure, Anthropic, Dottxt, Gemini, LM Studio, Mistral, Ollama, TGI |

OpenAI and Mistral mutate JSON schema payloads through
`set_additional_properties_false_json_schema`, adding `additionalProperties:
false` to every object schema unless already set. OpenAI also sends
`strict=True` in `response_format.json_schema`; Mistral sends `strict=True` in
its `response_format` schema object.

## Provider-Specific Request Fields

- OpenAI/Azure: `response_format={"type":"json_schema", ...}` or
  `response_format={"type":"json_object"}`.
- Gemini: `config={"response_mime_type": ..., "response_schema": ...}` with
  system instructions folded into config.
- Mistral: `response_format={"type":"json_schema", ...}` or
  `response_format={"type":"json_object"}`.
- Ollama: `format=<json schema dict>`.
- LM Studio: `response_format=<json schema dict>`.
- Dottxt: `response_format=<json schema string>` and `model=<model id>`.
- TGI: `grammar={"type":"json"|"regex", "value": ...}`.
- SGLang: JSON schema uses OpenAI strict schema; regex/CFG use
  `extra_body={"regex": ...}` or `extra_body={"ebnf": ...}`.
- vLLM: structured outputs are merged into `extra_body` as
  `structured_outputs={"json"|"regex"|"grammar": ...}`; source warns vLLM
  servers before `0.12` can silently ignore the newer field.

## Normalized Exceptions

Catch provider errors through `outlines.exceptions.APIError` or subclasses:

```python
from outlines.exceptions import APIError, RateLimitError

try:
    result = model("Prompt", max_tokens=64)
except RateLimitError as exc:
    # retryable=True; preserve request ID in logs/support tickets
    schedule_backoff(provider=exc.provider, request_id=exc.request_id)
except APIError as exc:
    if exc.retryable:
        schedule_backoff(provider=exc.provider, status=exc.status_code)
    else:
        raise
```

Available attributes: `provider`, `original_exception`, `status_code`,
`request_id`, `retryable`, and `hint`.

Provider exception maps:

- OpenAI, SGLang, vLLM: OpenAI SDK map; response validation ->
  `ProviderResponseError`; length/content-filter finish reasons and wrapper
  refusals -> `GenerationError`.
- Anthropic: SDK errors plus service unavailable/overloaded -> `ServerError`;
  deadline/timeouts -> `APITimeoutError`.
- Mistral: `httpx` timeout/connect plus v2 SDK public errors when present;
  status-code fallback handles older SDKs.
- Gemini: Google GenAI server errors plus `httpx` timeout/connect; client error
  `.code` falls back to status mapping.
- Ollama: connection and request errors plus status-bearing response errors.
- TGI: Hugging Face inference timeout, overload, validation, generation,
  gated repo, repository not found, and status fallback.
- Dottxt: urllib3 connection/timeout errors and status fallback.
- LM Studio: source intentionally bypasses `normalize_provider_errors`; catch
  SDK/runtime exceptions directly.

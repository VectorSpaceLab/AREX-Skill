# Remote Provider Matrix

This matrix is distilled from the Outlines source modules, public documentation, and provider tests used during skill creation. It represents the server/black-box provider route only and is self-contained for runtime use.

Legend: **JSON schema** means Outlines can convert Pydantic/dataclass/TypedDict,
`outlines.json_schema(...)`, and supported schema builders through the provider
adapter. **JSON mode** means unconstrained JSON syntax from `dict` without a
schema. **Simple/choice/regex** means the adapter converts ordinary Python
output types through Outlines terms for the server backend.

## Loader and Capability Matrix

| Provider | Source module | Loader signature | Accepted client(s) | Sync / async | Stream | Batch | Inputs | Output types | Credentials / endpoint settings | Error normalization | Key caveats |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OpenAI / Azure OpenAI | `src/outlines/models/openai.py` | `from_openai(client, model_name=None)` | `openai.OpenAI`, `openai.AsyncOpenAI`; Azure clients are documented and typed as supported through the same SDK family | sync and async by client class | yes | no | `str`, `list` prompt+`Image`, `Chat` | JSON schema with `strict=True` and recursive `additionalProperties: false`; JSON mode via `dict`; no `Regex`, no `CFG`, no simple scalar or multiple-choice terms | `OPENAI_API_KEY`; for Azure use SDK/client settings such as `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, API version, and deployment/model name; custom OpenAI-compatible endpoints use `base_url` on the client | `openai`, `vllm`, and `sglang` share the OpenAI SDK exception map; refusals raise `GenerationError` | Do not retry an OpenAI `Regex`/`CFG` request. Route to SGLang, TGI, vLLM, or a local model that supports the constraint. |
| Anthropic | `src/outlines/models/anthropic.py` | `from_anthropic(client, model_name=None)` | `anthropic.Anthropic` | sync only | yes | no | `str`, `list` prompt+`Image`, `Chat` | none through `output_type`; any non-`None` output type raises `NotImplementedError` | `ANTHROPIC_API_KEY`; client can carry base URL/options | Anthropic SDK exceptions, including overload/service-unavailable/deadline, normalize to Outlines API errors | Anthropic usually requires `max_tokens` in inference kwargs; no async wrapper in this source. |
| Gemini | `src/outlines/models/gemini.py` | `from_gemini(client, model_name=None)` | `google.genai.Client` | sync only | yes | no | `str`, `list` prompt+`Image`, `Chat`; system chat messages are collected into `system_instruction` | JSON schema subset converted to dataclass/TypedDict/Pydantic; homogeneous `list[SchemaType]`; enum/`Literal`/`Choice`; no `Regex`, no `CFG` | `GEMINI_API_KEY` per docs; Vertex/project options live on the Google client, not Outlines | Google GenAI server errors plus `httpx` timeout/connect errors; `ClientError.code` falls back by status | Use built-in `list[...]` for list output. Regex/pattern constraints are unsupported. |
| Mistral | `src/outlines/models/mistral.py` | `from_mistral(client, model_name=None, async_client=False)` | `mistralai.Mistral` | sync by default; async only when `async_client=True` | yes | no | `str`, `list` prompt+`Image`, `Chat` | strict JSON schema with recursive `additionalProperties: false`; JSON mode via `dict`; no `Regex`, no `CFG` | `MISTRAL_API_KEY`; client controls endpoint/options | Mistral SDK v2 public errors when present, `httpx` timeout/connect, and status-code fallback | `async_client=True` selects the async wrapper even though the SDK client class is the same. |
| Ollama | `src/outlines/models/ollama.py` | `from_ollama(client, model_name=None)` | `ollama.Client`, `ollama.AsyncClient` | sync and async by client class | yes | no | `str`, `list` prompt+`Image`, `Chat` | JSON schema only; no `Regex`, no `CFG` | Local/server endpoint is configured on the Ollama client, commonly via host settings such as `OLLAMA_HOST`; no API key required by default | `ConnectionError`, `httpx` connect/timeout, `ollama.RequestError`, and status-bearing `ollama.ResponseError` normalize | Requires a running Ollama service and a pulled model for live use; the skill/prereq script does not check service liveness. |
| LM Studio | `src/outlines/models/lmstudio.py` | `from_lmstudio(client, model_name=None)` | `lmstudio.Client`, `lmstudio.AsyncClient` | sync and async by client class | yes | no | `str`, `list` prompt+`Image`, `Chat` | JSON schema only; no `Regex`, no `CFG` | LM Studio app/server and downloaded model; endpoint selection is configured through the LM Studio SDK/app rather than Outlines | Source intentionally does **not** use `normalize_provider_errors`; local SDK/runtime exceptions pass through | Async wrapper enters the SDK async context lazily and exposes `close()`; call it when finished. |
| SGLang server | `src/outlines/models/sglang.py` | `from_sglang(client, model_name=None)` | `openai.OpenAI`, `openai.AsyncOpenAI` pointing at SGLang `base_url` | sync and async by client class | yes | no | OpenAI-formatted `str`, `list`, `Chat` | JSON schema through OpenAI strict schema; regex/simple/choice via `extra_body.regex`; CFG via `extra_body.ebnf` with SGLang-compatible EBNF, not normal Outlines/Lark grammar | OpenAI SDK client with SGLang `base_url`; placeholder endpoint envs such as `SGLANG_BASE_URL`/`SGLANG_API_KEY` are application choices | OpenAI SDK exception map under provider name `sglang`; refusals raise `GenerationError` | Structured-output support depends on the SGLang server backend. The adapter copies caller `extra_body` before adding constraints to avoid leakage between calls. |
| TGI server | `src/outlines/models/tgi.py` | `from_tgi(client)` | `huggingface_hub.InferenceClient`, `huggingface_hub.AsyncInferenceClient` | sync and async by client class | yes | no | `str` only | JSON grammar (`grammar.type=json`), regex grammar (`grammar.type=regex`), simple/choice via regex conversion; no `CFG` | Endpoint URL passed to HF client; tests use `TGI_SERVER_URL`; token may be needed for protected endpoints (`HF_TOKEN`/client token) | Hugging Face inference errors and status-code fallback normalize | Test mock path supports JSON and Regex and rejects CFG. Live servers may vary by TGI version/backend. |
| vLLM server | `src/outlines/models/vllm.py` | `from_vllm(client, model_name=None)` | `openai.OpenAI`, `openai.AsyncOpenAI` pointing at vLLM `base_url` | sync and async by client class | yes | no | OpenAI-formatted `str`, `list`, `Chat` | all Outlines term families through `extra_body.structured_outputs`: JSON schema, regex/simple/choice, CFG grammar; server must support structured outputs | OpenAI SDK client with vLLM `base_url`; placeholder endpoint envs such as `VLLM_BASE_URL`/`VLLM_API_KEY`; docs warn structured output needs vLLM server `>=0.12` | OpenAI SDK exception map under provider name `vllm`; refusals raise `GenerationError` | Older vLLM servers may silently ignore structured-output arguments; validate constrained behavior with a mock or approved live fixture outside this no-network skill. |
| Dottxt | `src/outlines/models/dottxt.py` | `from_dottxt(client, model=None)` | `dottxt.DotTxt`, `dottxt.AsyncDotTxt` | sync and async by client class | no | no | `str` only | JSON schema only; `output_type` is required; no unconstrained generation, no `Regex`, no `CFG` | `DOTTXT_API_KEY`; model id required at loader time or per call (`model=`) | urllib3 connection/timeout errors normalize; status-code fallback still applies | The source and docs support async clients, even though the docs feature matrix may lag. The async error message says `from_dottxt_async()`, but the actual loader is `from_dottxt`. |

## Explicit Exclusions from This Route

| Provider/page | Why excluded here | Correct route |
|---|---|---|
| Transformers, llama.cpp, MLX-LM, and vLLM offline modules | Local/offline engines, not server/black-box integrations. Local errors intentionally pass through rather than using `normalize_provider_errors`. | Local models / structured-generation route. |
| Generic OpenAI-compatible documentation patterns | Documentation patterns, not separate source modules or loaders. | Use `from_openai` for generic OpenAI-compatible APIs unless the endpoint is specifically SGLang or vLLM and needs their request fields. |
| OpenRouter, OrcaRouter, Requesty-style examples | OpenAI-compatible examples with no dedicated source modules in this revision. | Use `from_openai(openai.OpenAI(base_url=...))` and expect OpenAI-style JSON support only if the upstream model supports it. |
| vLLM offline | Offline local engine, distinct from vLLM OpenAI-compatible server wrapper. | Local/offline route. |

## Retry Classification

All normalized provider errors are `outlines.exceptions.APIError` subclasses.
Transient/retryable classes are exactly:

- `RateLimitError` (`status_code=429`): back off, reduce concurrency or request rate, preserve `request_id`.
- `ServerError` (`5xx`, Anthropic overload): bounded retry after short wait.
- `APITimeoutError`: bounded retry or raise timeout/connectivity issue.
- `APIConnectionError`: retry only after checking endpoint/host/network assumptions.

Permanent or request-fix classes are not retryable: `AuthenticationError`,
`PermissionDeniedError`, `NotFoundError`, `BadRequestError`,
`ProviderResponseError`, and `GenerationError`.

# Backend API reference

Read this when selecting a backend, passing constructor arguments, or inspecting
an output. The signatures and mappings below are for Mellea `0.8.0.dev0` and
Python `>=3.11`.

## Selection and construction

`mellea.start_session(backend_name=..., model_id=..., ctx=..., context_type=..., model_options=..., **backend_kwargs)` returns a `MelleaSession`. The accepted backend names are `ollama`, `hf`, `openai`, `watsonx`, and `litellm`. `context_type` is `simple` or `chat` and cannot be supplied together with `ctx`. `mellea.stdlib.start_backend.start_backend(...)` has the same selection arguments but returns `(Context, Backend)`.

Direct constructors:

| Backend | Constructor-specific controls | Default model/endpoint behavior |
|---|---|---|
| `OllamaModelBackend` | `model_id`, `formatter`, `base_url`, `model_options`, `timeout` | Reads `OLLAMA_HOST` or uses the local Ollama endpoint; default timeout is 300 seconds. The constructor checks the service and pulls a missing model. |
| `OpenAIBackend` | `model_id`, `formatter`, `base_url`, `model_options`, `api_key`, `default_extra_body`, `load_embedded_adapters`, `adapter_source`, `default_to_constraint_checking_alora`, client `**kwargs` | Reads `OPENAI_API_KEY` and `OPENAI_BASE_URL`; absent `base_url` means the OpenAI SDK default. A non-empty key is still required for local compatible servers. |
| `LocalHFBackend` | `model_id`, `formatter`, `use_caches`, `cache`, `custom_config`, `default_to_constraint_checking_alora`, `model_options` | Uses a local Transformers model/checkpoint. Without `custom_config`, device preference is CUDA, then MPS, then CPU. |
| `LiteLLMBackend` | `model_id`, `formatter`, `base_url`, `model_options` | Uses the provider prefix in the LiteLLM model string. Leave `base_url` unset for provider inference; set it for a proxy or local service. |
| `WatsonxAIBackend` | `model_id`, `formatter`, `base_url`, `model_options`, `api_key`, `project_id`, SDK `**kwargs` | Reads `WATSONX_URL`, `WATSONX_API_KEY`, and `WATSONX_PROJECT_ID`. The native backend is deprecated; prefer LiteLLM or OpenAI-compatible WatsonX access. |
| `DummyBackend` | `responses: list[str] | None` | Returns queued responses, or `"dummy"` when `responses=None`; it does not perform constrained decoding. |

All concrete backends expose provider/model identity through the generation
metadata of returned `ModelOutputThunk` values. `Backend` is the abstract
contract: provider implementations override internal context and raw generation,
while public generation wrappers fire Mellea lifecycle hooks.

## Model options

Import `ModelOption` from `mellea.backends`. It is a constants class, not an
Enum. Common keys are:

| Key | Meaning and portability |
|---|---|
| `TEMPERATURE` | Sampling temperature; forwarded as `temperature`. |
| `MAX_NEW_TOKENS` | Generation limit; remapped to `num_predict` (Ollama), `max_completion_tokens` or `max_tokens` (OpenAI/LiteLLM/WatsonX depending on endpoint), and `max_new_tokens` (HF). |
| `SEED` | Reproducibility hint; provider support varies. |
| `SYSTEM_PROMPT` | Provider-independent system instruction. |
| `THINKING` | Provider/model-dependent reasoning control; `True`/`False` or an effort string may map to different provider fields. |
| `STREAM` / `STREAM_TIMEOUT` | Streaming switch and per-chunk timeout. The default timeout is 120 seconds when streaming and can be set to `None`. |
| `STOP_SEQUENCES` | A list of stop strings; each backend maps it to its native stop field. |
| `CONTEXT_WINDOW` | Backend-specific context-window override. |
| `TOOLS` / `TOOL_CHOICE` | Tool definitions and selection strategy; use the tools route for tool design. |
| `LOGITS` / `RAW_LOGITS` | Processed/raw per-token logits. Only the HF backend supports them; streaming does not expose them. |

Options can be placed in the backend constructor, passed per session call, or
managed temporarily with `MelleaSession.push_model_options()` and
`pop_model_options()`. Per-call options override persistent options. A
`ModelOption` key wins over a backend-native alias when both are present. Unknown
keys may be passed through, but provider support is not implied.

```python
from mellea import MelleaSession
from mellea.backends import ModelOption
from mellea.backends.ollama import OllamaModelBackend

session = MelleaSession(
    OllamaModelBackend(
        model_id="granite4.1:3b",
        model_options={ModelOption.SEED: 42},
    )
)
answer = session.instruct(
    "Return a short answer.",
    model_options={ModelOption.MAX_NEW_TOKENS: 64, ModelOption.TEMPERATURE: 0.2},
)
```

## ModelIdentifier

`ModelIdentifier` is a frozen record of provider-specific names plus optional
`context_length` and `hf_tokenizer_name`. `start_backend` resolves the relevant
field by backend. Important failure cases are intentional: an identifier with
no `openai_name`, `ollama_name`, or `watsonx_name` cannot be used directly for
that provider; use the provider's plain served model name instead.

`OpenAIBackend` requires a non-empty string or an identifier with
`openai_name`. For self-hosted vLLM/SGLang, the served name is usually the HF
repository ID or the explicit server alias, not a hosted catalog name. NVIDIA
hosted names in the catalog require the matching NVIDIA-compatible `base_url`.

## Structured output and metadata

Pass a Pydantic model class as `format=...` to `instruct()`, `chat()`, or
`act()`. The returned thunk's `.value` is JSON text; parse it with
`MyModel.model_validate_json(str(result))`. Do not assume every provider accepts
the same JSON-schema dialect. OpenAI platform requests have stricter schema
requirements, while non-OpenAI compatible servers are treated as less strict;
server errors remain possible.

Generation metadata uses an OpenAI-shaped `usage` dictionary where available,
with `prompt_tokens`, `completion_tokens`, and `total_tokens` as the core keys.
`model` is the requested model, `response_model` is what the provider reports,
`provider` identifies the backend, `response_id` is provider supplied,
`finish_reasons` reports completion status, and `streaming`/`ttfb_ms` describe
streaming. Provider-specific raw responses live under `mot.raw`; prefer the
portable fields unless provider-specific diagnostics are required.

## Source-backed verification boundary

The API facts here were checked against the package's public backend classes,
model catalog, session/start helpers, output metadata types, formatter exports,
unit/mocked backend tests, and the installed package. Live cloud calls, Ollama
service calls, checkpoint downloads, and full local model generation were not
used as acceptance evidence.

# ModelClient Protocol and Provider Notes

`ModelClient` is AdalFlow's provider boundary. `Generator`, `Embedder`, and some retriever/reranker components stay model-agnostic by sending rendered inputs and `model_kwargs` to a `ModelClient` that knows the provider SDK.

## Protocol every client must satisfy

A concrete client subclasses `adalflow.core.model_client.ModelClient` and implements:

| Method | Purpose |
|---|---|
| `init_sync_client()` | Create or return the synchronous SDK client. |
| `init_async_client()` | Create or return the asynchronous SDK client when supported. |
| `convert_inputs_to_api_kwargs(input=None, model_kwargs={}, model_type=ModelType.UNDEFINED)` | Translate AdalFlow input plus `model_kwargs` into provider `api_kwargs`. |
| `call(api_kwargs={}, model_type=ModelType.UNDEFINED)` | Make a synchronous provider call. |
| `acall(api_kwargs={}, model_type=ModelType.UNDEFINED)` | Make an asynchronous provider call when supported. |
| `parse_chat_completion(completion)` | Convert a provider LLM response into `GeneratorOutput`, usually with `raw_response` text or stream. |
| `parse_embedding_response(response)` | Convert a provider embedding response into `EmbedderOutput`. |
| `track_completion_usage(...)` | Return token/usage data when the provider exposes it. |
| `list_models()` | Optional provider model listing. |

`Generator` and `Embedder` depend on these methods. If `parse_chat_completion` returns a plain string instead of `GeneratorOutput`, downstream code can fail or lose error/usage fields.

## Lazy imports and optional extras

Provider classes exported from `adalflow.components.model_client` are lazy imports. They raise a targeted install message only when instantiated or accessed. This keeps base imports light, but the current package also imports OpenAI response event types in the generator module, so an environment that imports `Generator` may still need the `openai` SDK installed.

Do not subclass a lazy-import proxy. If extending a provider, import the concrete class from its module, for example:

```python
from adalflow.components.model_client.openai_client import OpenAIClient

class MyOpenAIClient(OpenAIClient):
    ...
```

Typical optional extras mirror SDK names:

```bash
pip install "adalflow[openai]"
pip install "adalflow[groq]"
pip install "adalflow[anthropic]"
pip install "adalflow[google-generativeai]"
pip install "adalflow[ollama]"
pip install "adalflow[together]"
pip install "adalflow[cohere]"
pip install "adalflow[azure]"
pip install "adalflow[bedrock]"
pip install "adalflow[fireworks-ai]"
pip install "adalflow[mistralai]"
```

Install only the provider extras needed by the task. Provider examples usually require network access and credentials; the bundled fake-client script does not.

## Provider selection table

| Provider/client | Typical import | Extra / SDK | Authentication / runtime | Model types and notes |
|---|---|---|---|---|
| OpenAI | `from adalflow.components.model_client import OpenAIClient` | `openai` | `OPENAI_API_KEY` or explicit runtime key; optional base URL/header args | Uses OpenAI Response API for `LLM` and `LLM_REASONING`; supports embeddings; supports multimodal content via `images` in `model_kwargs`; streaming uses Response API events. |
| OpenAI-compatible custom endpoint | `OpenAIClient(base_url=..., env_api_key_name=...)` | `openai` | Provider-specific key variable or explicit key | Best for endpoints that implement OpenAI-compatible Response API behavior. If the endpoint only supports legacy chat completions, verify compatibility before using. |
| DeepSeek | `DeepSeekClient` | `openai` | `DEEPSEEK_API_KEY` | Extends OpenAI-compatible behavior with a DeepSeek base URL and `messages` input style by default; useful for reasoner models. |
| XAI | `XAIClient` | `openai` | `XAI_API_KEY` | OpenAI-compatible subclass with XAI base URL. |
| SambaNova | `SambaNovaClient` | `openai` | `SAMBANOVA_API_KEY` | OpenAI-compatible subclass with SambaNova base URL. |
| Fireworks | `FireworksClient` | `fireworks-ai` plus OpenAI-compatible client surface | `FIREWORKS_API_KEY` | OpenAI-compatible subclass with Fireworks base URL; model names often include provider/account prefixes. |
| Mistral | `MistralClient` | `mistralai` plus OpenAI-compatible client surface | `MISTRAL_API_KEY` | OpenAI-compatible subclass with Mistral base URL; supports text/messages input style. |
| Groq | `GroqAPIClient` | `groq` | `GROQ_API_KEY` | Chat LLM client; documented note says Groq does not expose the same embedding method as OpenAI. |
| Anthropic | `AnthropicAPIClient` | `anthropic`/OpenAI SDK compatibility path | `ANTHROPIC_API_KEY` | Current client uses Anthropic's OpenAI SDK compatibility endpoint, handles `LLM` and `LLM_REASONING`, and converts ChatCompletion responses/streams into AdalFlow `GeneratorOutput`. Embeddings are not supported. |
| Google | `GoogleGenAIClient` | `google-generativeai` | `GOOGLE_API_KEY` | Supports LLM and embedding-style conversion paths in its client; verify model names and SDK behavior for the selected Google model. |
| Ollama | `OllamaClient` | `ollama` | Local Ollama server; optional `OLLAMA_HOST`, default local host if omitted | Supports local LLM and embedder calls; can use chat or generate API depending on `model_kwargs`; streaming returns chunks in `raw_response`. |
| Together | `TogetherClient` | `together` | `TOGETHER_API_KEY` | Wraps Together SDK while inheriting OpenAIClient-style integration; verify async key handling and model names when using. |
| Cohere | `CohereAPIClient` | `cohere` | `COHERE_API_KEY` | Current client primarily supports `ModelType.RERANKER`; it maps `top_k` to Cohere `top_n`. Do not use it as a drop-in text generator or embedder unless confirmed. |
| Azure OpenAI | `AzureAIClient` | `azure-core`, `azure-identity`, OpenAI Azure SDK support | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_VERSION`, or Azure credential | Supports LLM and embedding through Azure OpenAI; streaming usage tracking may be unavailable. |
| Bedrock | `BedrockAPIClient` | `boto3`/`botocore` | AWS profile/region or AWS access variables | Experimental client; uses Bedrock Converse/ConverseStream for `LLM`; async is not implemented. |
| Transformers/local | `TransformersClient`, `TransformerEmbedder`, `TransformerLLM`, `TransformerReranker` | `transformers`, often `torch` | Local model files/cache and hardware suitable for the model | Useful for local embeddings/reranking/LLMs; resource and model-download requirements are outside no-network smoke tests. |

## Direct client usage

Use a `ModelClient` directly only when writing a new AdalFlow component or debugging provider conversion. Otherwise prefer `Generator` or `Embedder`.

Direct LLM flow:

```python
from adalflow.core.types import ModelType
from adalflow.components.model_client import OpenAIClient

client = OpenAIClient()
api_kwargs = client.convert_inputs_to_api_kwargs(
    input="Summarize AdalFlow in one sentence.",
    model_kwargs={"model": "gpt-4o-mini", "temperature": 0},
    model_type=ModelType.LLM,
)
completion = client.call(api_kwargs=api_kwargs, model_type=ModelType.LLM)
output = client.parse_chat_completion(completion)
```

Direct embedding flow:

```python
from adalflow.core.types import ModelType
from adalflow.components.model_client import OpenAIClient

client = OpenAIClient()
api_kwargs = client.convert_inputs_to_api_kwargs(
    input=["first", "second"],
    model_kwargs={"model": "text-embedding-3-small"},
    model_type=ModelType.EMBEDDER,
)
response = client.call(api_kwargs=api_kwargs, model_type=ModelType.EMBEDDER)
embeddings = client.parse_embedding_response(response)
```

## Input and content formatting

Provider clients differ in how they represent prompts:

- OpenAI Response API text path sets `api_kwargs["input"]` to the rendered prompt.
- OpenAI multimodal path accepts `model_kwargs["images"]` and formats Response API content as `input_text` plus `input_image` entries.
- Some chat-completion-compatible clients convert prompt text into `messages=[{"role": "user" or "system", "content": ...}]`.
- Azure and older chat clients may parse special system/user markers when `input_type="messages"`.
- Bedrock Converse expects `messages=[{"role": "user", "content": [{"text": ...}]}]`.
- Ollama can choose generate vs chat mode from `model_kwargs`.

For OpenAI Response API image inputs, utilities in `adalflow.components.model_client.utils` validate or format content:

```python
from adalflow.components.model_client.utils import format_content_for_response_api

content = format_content_for_response_api(
    "Describe the image.",
    "https://example.invalid/image.png",
)
# content contains input_text plus input_image dictionaries
```

Local file paths in examples must be runtime-supplied. Do not hard-code machine-specific paths in reusable code.

## Provider switching checklist

1. Confirm whether the new provider supports the required `ModelType`.
2. Install only its optional extra/SDK.
3. Configure the provider's credential/environment outside source code.
4. Verify `model_kwargs` names, especially `model`, `stream`, `max_tokens`/output-token limits, `messages`, `images`, embedding dimensions, and provider-specific inference config.
5. Run a fake-client unit test for the surrounding pipeline before making a live call.
6. Make one minimal live call with `use_cache=False` and simple prompt.
7. Add output processors only after the raw provider response path is confirmed.

## Fake client as the preferred unit-test boundary

A fake `ModelClient` should emulate the AdalFlow protocol, not the entire provider SDK. Keep fake `api_kwargs` JSON-serializable so cache paths can be tested. Return realistic raw text to exercise parsers, and add an embedding branch when testing `Embedder` or `BatchEmbedder`.

Use `scripts/generator_fake_client_smoke.py` as the template for service-free tests.

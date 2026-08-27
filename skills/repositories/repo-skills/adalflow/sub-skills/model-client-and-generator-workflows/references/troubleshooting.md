# Troubleshooting Generator, ModelClient, Provider, and Embedder Workflows

Use this reference before retrying expensive provider calls. Most failures come from missing optional SDKs, missing credentials, mismatched `model_kwargs`/`ModelType`, parser errors, cache hits, or streaming shape assumptions.

## Quick triage

1. Reproduce with a fake `ModelClient` or `use_cache=False` before making another live call.
2. Render the prompt with `generator.get_prompt(...)` and inspect it.
3. Check `GeneratorOutput.error`. If set, inspect `raw_response` and parser configuration.
4. Confirm the provider SDK/extra is installed and the provider credential is available at runtime.
5. Confirm the selected `ModelType` is supported by the client.
6. For streaming, consume `raw_response` or `stream_events()` instead of expecting `data` to be populated immediately.
7. For embeddings, verify the provider supports embeddings and that the vector dimensions match downstream expectations.

## Common failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named openai` while importing generator-related code | Current generator import path requires OpenAI Response event types. | Install the OpenAI SDK or the OpenAI extra. If you only need a non-OpenAI fake test, the SDK may still be required for import. |
| Lazy provider class raises an install message | The optional SDK for that provider is missing. | Install only the selected provider extra/SDK, then re-run a minimal import/constructor check. |
| `Environment variable ... must be set` | The provider client was instantiated without a runtime key/endpoint. | Set the provider's documented environment variable or pass runtime credentials through the client constructor. Do not hard-code secrets in reusable scripts. |
| `model_type ... is not supported` | The client does not implement that `ModelType`, or the wrong component is being used. | Use `Generator` with `ModelType.LLM`/`LLM_REASONING`, `Embedder` for `EMBEDDER`, or a provider that supports the needed capability. |
| Provider validation error about missing `model`, `messages`, `input`, `modelId`, or `inferenceConfig` | `model_kwargs` are shaped for a different provider. | Check the provider table in `model-clients.md`; make one direct `convert_inputs_to_api_kwargs` call and inspect `api_kwargs`. |
| `GeneratorOutput.error` is set and `data` is `None` | The provider call failed or output processor raised an exception. | Inspect `error`, `raw_response`, and `api_response`; if `raw_response` contains usable text, fix the parser before retrying the provider. |
| Parser failure on valid-looking content | The model returned prose fences, extra text, invalid JSON/YAML, or fields that do not match the parser schema. | Add stronger prompt format instructions, use a parser designed for the expected shape, or add a repair/validation step outside live provider calls. |
| Output processor never sees complete text during streaming | Streaming chunks are not complete structured documents. | Disable streaming for structured parser workflows, or collect final text before parsing. |
| Repeated old answer after prompt/model changes | Cache hit or cache key did not change as expected. | Re-run with `use_cache=False`; clear the chosen cache if necessary; keep `api_kwargs` JSON-serializable. |
| Live provider was not called in a test | `Generator.use_cache` defaulted to true and returned a cached completion. | Pass `use_cache=False` in tests that assert model-client calls. |
| `TypeError: Object of type ... is not JSON serializable` before model call | Cache key creation JSON-serializes `api_kwargs`. | Disable cache for non-serializable runtime objects or convert model kwargs to plain JSON-compatible values. |
| `max_tokens` does not reach the provider as expected | Current `Generator._pre_call` treats `max_tokens` as a prompt-length guard and removes it before the provider call. | Verify the selected client/output-token limit behavior; use the provider-specific parameter path only after a minimal API-kwargs inspection. |
| `parse_chat_completion` fake returns string and `Generator` misbehaves | Fake client does not follow `ModelClient` protocol. | Return `GeneratorOutput(raw_response=...)` from `parse_chat_completion`; use the bundled fake-client script as a reference. |
| Streaming usage is missing or raises not implemented | Several providers cannot track usage for streaming iterators. | Treat usage as unavailable for streaming; run a non-streaming call if usage accounting is required. |
| Bedrock async call fails | Bedrock client async path is not implemented in this version. | Use synchronous `call` for Bedrock or choose a provider with async support. |
| Cohere text generation/embedding path fails | Current Cohere client is oriented around reranking. | Use Cohere only for the supported reranker path unless a live inspection confirms additional support. |
| Ollama connection fails | Local Ollama server is not running or host is wrong. | Start the local service and set the host only in runtime configuration. Confirm the model is pulled before calling. |
| Azure client complains about endpoint/version/key | Azure requires endpoint and API version in addition to authentication. | Set endpoint, API version, and either API key or Azure credential at runtime. |
| Bedrock auth or model errors | AWS profile/region/credentials/model access are missing or model id is wrong. | Check AWS runtime configuration and the model identifier outside reusable code; make a minimal Bedrock list/call only when authorized. |
| `EmbedderOutput.length` is zero with no obvious exception | Provider returned no embeddings or parser returned an error-bearing `EmbedderOutput`. | Inspect `EmbedderOutput.error`, `raw_response`, model name, input list, and provider embedding support. |
| Vector dimensions mismatch downstream | Embedding model or output processor changed vector size. | Check `EmbedderOutput.embedding_dim` before indexing or retrieval; rebuild dependent indexes when model/dim changes. |

## Optional SDK and credential notes

Provider environment variables commonly used by current clients:

| Client | Runtime credential/config |
|---|---|
| `OpenAIClient` | `OPENAI_API_KEY`, or custom key name via constructor. |
| `DeepSeekClient` | `DEEPSEEK_API_KEY`. |
| `XAIClient` | `XAI_API_KEY`. |
| `SambaNovaClient` | `SAMBANOVA_API_KEY`. |
| `FireworksClient` | `FIREWORKS_API_KEY`. |
| `MistralClient` | `MISTRAL_API_KEY`. |
| `GroqAPIClient` | `GROQ_API_KEY`. |
| `AnthropicAPIClient` | `ANTHROPIC_API_KEY`. |
| `GoogleGenAIClient` | `GOOGLE_API_KEY`. |
| `OllamaClient` | local service; optional `OLLAMA_HOST`. |
| `TogetherClient` | `TOGETHER_API_KEY`. |
| `CohereAPIClient` | `COHERE_API_KEY`. |
| `AzureAIClient` | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_VERSION`, or Azure credential. |
| `BedrockAPIClient` | AWS profile/region or AWS access/session variables. |

Never print secret values. It is safe to log which variable name is missing.

## Debugging `model_kwargs` safely

Before a live call, inspect provider conversion with a fake or authorized client:

```python
api_kwargs = client.convert_inputs_to_api_kwargs(
    input="hello",
    model_kwargs={"model": "provider-model", "temperature": 0},
    model_type=ModelType.LLM,
)
print(api_kwargs.keys())
```

Avoid printing full prompts or image payloads when they contain private data. Print keys, model name, stream flag, and content counts instead.

## Parser and structured-output recovery

When parsing fails:

1. Preserve the original `raw_response` for diagnosis.
2. Confirm that the parser matches the expected return shape: dict/list/scalar/dataclass.
3. Add parser format instructions to the prompt.
4. Test the parser on a fixed string without a model call.
5. Only then retry the provider.

For JSON, prefer a fake model response that contains representative invalid cases: extra Markdown fences, trailing prose, missing required fields, wrong types, and nested arrays/objects.

## Streaming recovery

Streaming providers can return several shapes:

- OpenAI Response API events, including text delta and completion events.
- ChatCompletion chunks.
- Bedrock stream chunk dictionaries.
- Ollama generator chunks.
- Async iterables converted by a provider adapter.

Recovery rules:

- Treat `raw_response` as the stream source.
- For async streams, use `async for event in output.stream_events()`.
- For OpenAI Response API events, use the utility functions in `adalflow.components.model_client.utils` to extract text deltas or complete text.
- Do not assume `usage` is available for streams.
- Disable cache for streaming.
- Do not run JSON/dataclass parsers on partial chunks; collect final text first.

## Content and image formatting

OpenAI Response API image/content helpers accept:

- image URL strings,
- local file paths supplied at runtime,
- data URI strings,
- dictionaries with `{"type": "input_image", "image_url": ...}`.

Typical failures:

| Symptom | Recovery |
|---|---|
| `FileNotFoundError` for image path | Use a runtime-valid path or a URL; do not bake machine-specific paths into reusable code. |
| `Image dict must have 'type' field` | Use `{"type": "input_image", "image_url": "..."}`. |
| Model rejects image input | Confirm the selected model supports vision/multimodal inputs. |
| `images` passed to a non-OpenAI-compatible client | Use the client's native content format or switch to a supported client. |
| Generated image data present but not saved | Check `GeneratorOutput.images`; call `save_images` with a caller-approved output directory. |

## Service-free sanity check

When unsure whether the problem is AdalFlow orchestration or the live provider, run:

```bash
python scripts/generator_fake_client_smoke.py
```

If the fake-client script passes, the `Generator`/`Embedder` orchestration, prompt rendering, and parser path are healthy. Focus next on provider extras, credentials, network access, and provider-specific kwargs.

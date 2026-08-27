# Context and retriever troubleshooting

Use this guide before spending provider tokens or launching a browser. The bundled probe should be the first command for local checks:

```bash
python sub-skills/contexts-and-retrievers/scripts/lavague_context_retriever_probe.py --context all --retriever all --check-env
```

## Missing optional context package

Symptoms:

- `ModuleNotFoundError: No module named 'lavague.contexts.anthropic'`
- `ModuleNotFoundError: No module named 'lavague.contexts.gemini'`
- `ModuleNotFoundError: No module named 'lavague.contexts.fireworks'`
- `ModuleNotFoundError: No module named 'lavague.contexts.cache'`

Fix:

```bash
pip install lavague-contexts-anthropic
pip install lavague-contexts-gemini
pip install lavague-contexts-fireworks
pip install lavague-contexts-cache
```

OpenAI and Azure contexts live in `lavague-contexts-openai`. If the root `lavague` bundle is not installed, install the specific context package needed by the task.

## Provider API key errors

LaVague context constructors validate key presence before returning a context. Do not print secret values; check only presence.

| Error or missing variable | Likely context | Fix |
| --- | --- | --- |
| `OPENAI_API_KEY is not set` | `OpenaiContext`, default context, Anthropic embedding, Fireworks multimodal, or omitted `ActionEngine`/`WorldModel` defaults | Export `OPENAI_API_KEY`, pass secure `api_key=`, or remove the OpenAI default by supplying custom model objects. |
| `ANTHROPIC_API_KEY is not set` | `AnthropicContext` | Export `ANTHROPIC_API_KEY` or pass secure `api_key=`. |
| `GOOGLE_API_KEY is not set` | `GeminiContext` | Export `GOOGLE_API_KEY` or pass secure `api_key=`. |
| `FIREWORKS_API_KEY is not set` | `FireworksContext` | Export `FIREWORKS_API_KEY` or pass secure `api_key=`. |
| Azure key/endpoint/deployment errors | `AzureOpenaiContext` | Export `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`; pass `embedding_deployment=` explicitly. |
| Cohere client/rerank errors | `CohereRetriever` | Install `lavague-retriever-cohere`, export `COHERE_API_KEY`, and allow provider/network calls before retrieval. |

## Azure deployment and endpoint confusion

`AzureOpenaiContext` has separate model names, deployment names, and endpoints.

- `endpoint`: base Azure OpenAI resource endpoint.
- `deployment`: Azure deployment for the text LLM.
- `mm_llm_deployment`: Azure deployment for the multimodal LLM; defaults to `deployment` if omitted.
- `embedding_deployment`: Azure deployment for the embedding model; required by the installed constructor.
- `embedding_endpoint`: only needed if embeddings use a different resource; otherwise it defaults to `endpoint`.
- `api_version`: defaults to `2023-07-01-preview` unless overridden or supplied through `AZURE_API_VERSION`.

Do not rely on the installed default `llm`/`mm_llm` strings; pass real model names explicitly.

## Default OpenAI embedding surprises

Non-OpenAI contexts may still need OpenAI:

- `AnthropicContext` uses Anthropic LLMs but OpenAI embeddings by default.
- `FireworksContext` uses Fireworks LLM/embedding but OpenAI `gpt-4o` for the multimodal WorldModel by default.
- `ActionEngine` without explicit `llm`, `embedding`, or `extraction_llm` loads the default OpenAI context.
- `WorldModel` without explicit `mm_llm` loads the default OpenAI context.
- The default retriever pipeline uses the selected embedding; if the embedding is OpenAI, retrieval can fail before action generation when `OPENAI_API_KEY` is absent.

Fix by passing a complete custom `Context`, using a provider context whose embedding matches available credentials, or choosing a syntaxic retriever pipeline that does not require embeddings.

## Cohere rerank key and safety

`CohereRetriever` imports from `lavague.retrievers.cohere` and reranks through the Cohere API. Safe checks should inspect its signature only. Do not instantiate and call retrieval unless:

1. `lavague-retriever-cohere` is installed.
2. `COHERE_API_KEY` is present or passed securely.
3. External API calls are explicitly approved.
4. The task budget can absorb rerank calls.

If Cohere is unavailable, use `SyntaxicRetriever` or the default semantic retriever instead.

## Cache prompt stores

`ContextCache` can be useful for deterministic dry runs, but it writes normal YAML files in the current working directory by default:

- `llm_prompts.yml` for text LLM prompts.
- `mm_llm_prompts.yml` for multimodal prompts keyed with image hashes.
- `embeddings.yml` for cached/reduced embeddings.

Common pitfalls:

- `ContextCache.default()` uses the default OpenAI context as fallback, so it needs `OPENAI_API_KEY`.
- `ContextCache.from_context(context)` may call the provider fallback on a cache miss.
- Bare `ContextCache()` returns placeholder/mocked values on cache misses; it is not a quality substitute for a real provider.
- Prompt stores can contain private page content, user data, or screenshots-derived hashes. Keep them task-local and out of reusable runtime files.

## `add_knowledge` and `user_data`

Use the right channel:

- `WorldModel.add_knowledge(file_path=...)` appends reusable examples to the WorldModel prompt. The file must exist locally for the run.
- `NavigationEngine.add_knowledge(knowledge)` appends short navigation prompt constraints.
- `agent.run(objective, user_data=...)` puts task-scoped data into short-term memory under user inputs.

Pitfalls:

- Do not put API keys, credentials, or private form data in reusable knowledge examples.
- `add_knowledge` is cached by file path at the method level; if you edit a file and call the same path again in the same process, restart or use a new path if the update is not reflected.
- `user_data` is run-scoped and should not be used as a permanent prompt-tuning mechanism.

## Custom LlamaIndex object mismatch

When supplying custom `llm`, `embedding`, or `mm_llm` objects:

- Ensure objects implement the LlamaIndex interfaces expected by LaVague.
- Use a multimodal object for `WorldModel(mm_llm=...)`, not a text-only LLM.
- Use an embedding object for `ActionEngine(..., embedding=...)`; retrievers call embedding methods during node retrieval.
- If one component is omitted, LaVague may silently load the default OpenAI context and require `OPENAI_API_KEY`.

## Import warnings and blocked downloads

Importing LaVague can trigger dependency warnings from LlamaIndex/NLTK. In the verified inspection environment, imports succeeded even when NLTK stopwords/punkt downloads were blocked by network safety policy. If imports fail because NLTK data is unavailable, pre-seed NLTK data in a trusted location or configure network access according to local security policy. Do not let a helper script download data by default.

LaVague also warns about telemetry unless `LAVAGUE_TELEMETRY=NONE` is set. The bundled probe sets this default in-process before importing LaVague modules.

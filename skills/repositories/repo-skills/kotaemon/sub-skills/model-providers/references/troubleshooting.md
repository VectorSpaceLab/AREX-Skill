# Model Provider Troubleshooting

Start with offline validation and configuration inspection. Only run UI connection tests, provider calls, model downloads, or graph indexing after the user approves network/service side effects.

## Fast decision tree

1. Identify the failing surface: `.env` seeding, Resources UI model entry, retrieval settings, web search, local model server, or GraphRAG index.
2. Run `python scripts/check_provider_env.py --env-file .env --select auto` and fix missing/placeholder credential pairs first.
3. If the app has already run, inspect the Resources UI entries; stale database-backed specs can remain even after `.env` changes.
4. Check endpoint shape: hosted OpenAI-compatible APIs and local OpenAI-compatible servers generally need `/v1`; Azure endpoints generally do not include deployment paths; native Ollama chat generally does not use `/v1`.
5. Check optional dependencies only for the selected provider. Do not install every optional integration into a working deployment.
6. For retrieval quality or RAG composition after provider calls work, switch to `../../rag-core/SKILL.md`.

## Symptom map

| Symptom | Likely cause | Safe check | Fix direction |
| --- | --- | --- | --- |
| OpenAI entry exists but calls fail immediately | `OPENAI_API_KEY` is a placeholder or wrong base URL | Validator reports placeholder and URL shape | Replace key; set `OPENAI_API_BASE=https://api.openai.com/v1` or correct compatible base |
| Azure chat works but embeddings fail, or reverse | Only one deployment variable is set or deployment name is wrong | Check `AZURE_OPENAI_CHAT_DEPLOYMENT` and `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` separately | Add the missing deployment or update the corresponding Resources entry |
| Azure URL errors mention malformed deployment URL | Endpoint includes `/openai/deployments/...` instead of resource endpoint | Inspect `AZURE_OPENAI_ENDPOINT` | Use resource endpoint such as `https://<resource>.openai.azure.com/` and put deployment in deployment key |
| Ollama works on host but not Docker Kotaemon | Container uses `localhost` for a host service | Run validator with `--docker` | Use `http://host.docker.internal:11434/v1/` or container networking that reaches Ollama |
| Ollama OpenAI-compatible provider returns 404 | Base URL missing `/v1/` or using native `/api` URL for `ChatOpenAI` | Inspect `KH_OLLAMA_URL` or UI `base_url` | Use `/v1/` for `ChatOpenAI` and `OpenAIEmbeddings` |
| Native `LCOllamaChat` fails with URL mismatch | Base URL includes `/v1/` where native Ollama wrapper expects host/API base | Inspect UI spec for `LCOllamaChat` | Use the non-`/v1/` Ollama base for native wrapper |
| Local GGUF model fails before generation | `llama-cpp-python` missing, path missing, or `chat_format` missing | Check package and spec fields; validator can check file path existence | Install optional package; set `model_path` and `chat_format`; choose smaller model if memory constrained |
| File indexing has no embeddings | Only LLM configured; embedding model missing/default invalid | Inspect Embedding Models UI and collection settings | Add/default an embedding provider; choose collection embedding model |
| Cohere reranking does nothing | `COHERE_API_KEY` empty or placeholder | Validator reports missing/placeholder key | Set key or disable reranking/choose another reranker |
| Voyage reranker construction fails | `VOYAGE_API_KEY` missing or `voyageai` package missing | Check key and package only if using Voyage | Install selected optional package and set key |
| Web search command fails | Selected backend key missing or package missing | Check `KH_WEB_SEARCH_BACKEND`, `TAVILY_API_KEY`, `JINA_API_KEY` | Set selected backend credentials/package; avoid real search during offline checks |
| MS GraphRAG raises `GRAPHRAG_API_KEY is not set` | Missing key | Validator with `--select graphrag` | Set `GRAPHRAG_API_KEY` or disable MS GraphRAG if using only Nano/LightRAG |
| GraphRAG local model fails before indexing | Custom YAML uses non-OpenAI-compatible base or missing embedding model | Check `settings.yaml.example` and `USE_CUSTOMIZED_GRAPHRAG_SETTING` | Use `/v1` API bases and valid chat/embedding model names |
| NanoGraphRAG/LightRAG ignores `GRAPHRAG_API_KEY` | These wrappers use default Resources LLM and embedding managers | Inspect default LLM/embedding in Resources UI | Set working defaults; reduce batch size for local models |
| Import error for a provider class | Optional package not installed | Read error message and provider type | Install only that provider's optional package in the active environment |

## Placeholder detection

Treat these as missing unless intentionally used for a local server that accepts dummy keys:

- Angle-bracket placeholders such as `<YOUR_OPENAI_KEY>` or `<COHERE_API_KEY>`.
- `your-key`, `placeholder`, `changeme`, `dummy`, `test`, `none`, and empty values.
- Commented variables in `.env` files are not active configuration.

The bundled validator redacts all key-like values in output. Do not paste real secrets into reports, issues, or generated skill content.

## Endpoint shape rules

| Provider type | Expected base or endpoint | Common mistake |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | Missing `/v1` or using Azure endpoint |
| Azure OpenAI | `https://<resource>.openai.azure.com/` | Including `/openai/deployments/<name>` in endpoint |
| Ollama as OpenAI-compatible | `http://localhost:11434/v1/` or Docker host equivalent | Using `http://localhost:11434/api` or omitting `/v1/` |
| Native `LCOllamaChat` | `http://localhost:11434/` or `http://localhost:11434` | Passing `/v1/` URL |
| text-generation-webui | `http://localhost:5000/v1/` | Starting server without API mode or embedding support |
| llama-cpp-python OpenAI server | `http://localhost:8000/v1/` | Confusing server mode with direct `LlamaCppChat` `model_path` mode |
| GraphRAG custom local OpenAI-compatible | `/v1` API base in YAML | Using native Ollama `/api` base |

## Optional package triage

Use the failing provider class to decide what to install. Examples from source error messages include:

- `Please install langchain-ollama` for native Ollama chat.
- `llama-cpp-python is not installed` for direct LlamaCpp wrappers.
- `Please install Cohere pip install cohere` for Cohere reranking.
- `Please install pip install tavily-python` for Tavily web search.
- GraphRAG import warnings recommending `graphrag future`, `nano-graphrag`, or LightRAG installation for graph pipelines.

Provider SDKs were not fully validated in the inspection environment, so avoid claiming that a backend works until a user-approved connection test succeeds.

## Safe validation commands

From the sub-skill directory or after copying the script:

```bash
python scripts/check_provider_env.py --env-file .env --select auto
python scripts/check_provider_env.py --env-file .env --select local --docker
python scripts/check_provider_env.py --env-file .env --select graphrag --settings-file settings.yaml.example
```

Expected results:

- Exit code `0`: selected provider groups have no missing required offline fields.
- Exit code `1`: missing/placeholder required pairs, incompatible URL suffixes, or missing local file paths need attention.
- Exit code `2`: CLI usage or unreadable input file problem.

The script does not read the app database. If `.env` looks correct but the app still fails, inspect Resources UI specs next.

# Provider Configuration

Kotaemon has two provider configuration paths:

1. `.env` plus `flowsettings.py` auto-populates initial provider dictionaries such as `KH_LLMS`, `KH_EMBEDDINGS`, `KH_RERANKINGS`, `KH_WEB_SEARCH_BACKEND`, and GraphRAG toggles.
2. The Gradio Resources UI stores LLM, embedding, and reranking specs in the app database through `ktem.llms.manager.LLMManager`, `ktem.embeddings.manager.EmbeddingManager`, and `ktem.rerankings.manager.RerankingManager`.

After a first run, do not assume changing `.env` automatically rewrites existing database-backed Resources entries. Inspect or update the UI model specs when behavior does not match the current `.env`.

## Configuration surfaces

| Surface | Use it for | Important behavior |
| --- | --- | --- |
| `.env` | First-run provider defaults, credentials, GraphRAG toggles, local model names, web-search keys | Read by `decouple.config`; placeholders may still create entries if non-empty |
| `flowsettings.py` | Source-level app defaults, model dictionaries, vendor class specs, graph index toggles, web-search backend | Seeds manager databases and app settings; safe to inspect, but editing changes runtime behavior |
| Resources UI `LLMs` | Add/update/delete/default chat models | Uses vendor classes from `LLMManager.vendors()` and persists specs |
| Resources UI `Embedding Models` | Add/update/delete/default embedding models | Uses vendor classes from `EmbeddingManager.vendors()` and persists specs |
| Resources UI `Rerankings` | Add/update/delete/default rerankers | Uses `RerankingManager`; UI connection checks can call providers |
| Retrieval settings | Select embedding per collection, reranker, reranking LLM, and LLM-scoring flags | Use local models carefully because reranking can create many parallel LLM calls |

## Environment keys

| Provider or feature | Required keys | Optional or default keys | Notes |
| --- | --- | --- | --- |
| OpenAI chat and embeddings | `OPENAI_API_KEY` | `OPENAI_API_BASE`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDINGS_MODEL` | Default base is `https://api.openai.com/v1`; placeholder `<YOUR_OPENAI_KEY>` is not usable |
| Azure OpenAI | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, one or both deployment names | `OPENAI_API_VERSION`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` | Endpoint is the resource endpoint, not a deployment URL; deployment names drive chat/embedding entries |
| Ollama/OpenAI-compatible local | `LOCAL_MODEL` for chat, `LOCAL_MODEL_EMBEDDINGS` for embeddings | `KH_OLLAMA_URL` | `flowsettings.py` defaults `KH_OLLAMA_URL` to `http://localhost:11434/v1/`; Docker often needs `host.docker.internal` |
| Cohere | `COHERE_API_KEY` for real Cohere chat/embedding/rerank calls | `CO_API_URL` for reranker base URL override | `flowsettings.py` includes Cohere entries; missing key can leave reranking ineffective |
| VoyageAI | `VOYAGE_API_KEY` | `VOYAGE_EMBEDDINGS_MODEL` | Adds Voyage embeddings and reranking only when key is present |
| Google | `GOOGLE_API_KEY` | none in `.env.example` | Default placeholder is `your-key`; Resources setup can update Google defaults |
| Mistral | `MISTRAL_API_KEY` | none | Uses OpenAI-compatible chat and Mistral embedding classes |
| Web search Tavily | `TAVILY_API_KEY` | `KH_WEB_SEARCH_BACKEND` defaults to Tavily class in `flowsettings.py` | Missing key raises at web-search runtime |
| Web search Jina | `JINA_API_KEY` | `JINA_URL` | To use Jina, change `KH_WEB_SEARCH_BACKEND` to the Jina web-search class |
| MS GraphRAG | `GRAPHRAG_API_KEY` | `GRAPHRAG_LLM_MODEL`, `GRAPHRAG_EMBEDDING_MODEL`, `USE_CUSTOMIZED_GRAPHRAG_SETTING` | Official MS GraphRAG indexing requires OpenAI-compatible or Ollama-compatible settings |
| Graph index toggles | none for visibility | `USE_MS_GRAPHRAG`, `USE_NANO_GRAPHRAG`, `USE_LIGHTRAG`, `USE_GLOBAL_GRAPHRAG` | Toggles control which GraphRAG index types appear |
| Multimodal Azure VLM | Azure endpoint/key/version/deployment if used | `USE_MULTIMODAL`, `OPENAI_VISION_DEPLOYMENT_NAME` | VLM endpoint is constructed from Azure settings in `flowsettings.py` |

Run `scripts/check_provider_env.py` for offline validation of these pairs. It never verifies actual connectivity.

## Auto-seeded provider specs

`flowsettings.py` seeds dictionaries with class paths and spec fields:

| Manager | Seeded name | Class type | Key spec fields |
| --- | --- | --- | --- |
| LLM | `openai` | `kotaemon.llms.ChatOpenAI` | `base_url`, `api_key`, `model`, `temperature`, `timeout` |
| Embedding | `openai` | `kotaemon.embeddings.OpenAIEmbeddings` | `base_url`, `api_key`, `model`, `timeout`, `context_length` |
| LLM | `azure` | `kotaemon.llms.AzureChatOpenAI` | `azure_endpoint`, `api_key`, `api_version`, `azure_deployment`, `timeout` |
| Embedding | `azure` | `kotaemon.embeddings.AzureOpenAIEmbeddings` | `azure_endpoint`, `api_key`, `api_version`, `azure_deployment`, `timeout` |
| LLM | `ollama` | `kotaemon.llms.ChatOpenAI` | `base_url`, `model`, `api_key: ollama` |
| LLM | `ollama-long-context` | `kotaemon.llms.LCOllamaChat` | non-`/v1/` `base_url`, `model`, `num_ctx` |
| Embedding | `ollama` | `kotaemon.embeddings.OpenAIEmbeddings` | `base_url`, `model`, `api_key: ollama` |
| Embedding | `fast_embed` | `kotaemon.embeddings.FastEmbedEmbeddings` | `model_name` |
| LLM | `claude` | `kotaemon.llms.chats.LCAnthropicChat` | `model_name`, `api_key` |
| LLM | `google` | `kotaemon.llms.chats.LCGeminiChat` | `model_name`, `api_key` |
| LLM | `groq` | `kotaemon.llms.ChatOpenAI` | OpenAI-compatible `base_url`, `model`, `api_key` |
| LLM | `cohere` | `kotaemon.llms.chats.LCCohereChat` | `model_name`, `api_key` |
| LLM | `mistral` | `kotaemon.llms.ChatOpenAI` | OpenAI-compatible `base_url`, `model`, `api_key` |
| Embedding | `cohere` | `kotaemon.embeddings.LCCohereEmbeddings` | `model`, `cohere_api_key`, `user_agent` |
| Embedding | `google` | `kotaemon.embeddings.LCGoogleEmbeddings` | `model`, `google_api_key` |
| Embedding | `mistral` | `kotaemon.embeddings.LCMistralEmbeddings` | `model`, `api_key` |
| Reranking | `cohere` | `kotaemon.rerankings.CohereReranking` | `model_name`, `cohere_api_key` |
| Reranking | `voyageai` | `kotaemon.rerankings.VoyageAIReranking` | `model_name`, `api_key` |

Some default entries contain placeholders such as `your-key`. They may appear in the UI but will fail real provider calls until replaced.

## Vendor classes available through the UI

LLM vendors exposed by `LLMManager` include `ChatOpenAI`, `AzureChatOpenAI`, `LCAnthropicChat`, `LCGeminiChat`, `LCCohereChat`, `LCOllamaChat`, and `LlamaCppChat`. `KH_LLM_EXTRA_VENDORS` can append custom dotted imports in `flowsettings.py`.

Embedding vendors include `AzureOpenAIEmbeddings`, `OpenAIEmbeddings`, `FastEmbedEmbeddings`, `LCCohereEmbeddings`, `LCHuggingFaceEmbeddings`, `LCGoogleEmbeddings`, `LCMistralEmbeddings`, `TeiEndpointEmbeddings`, and `VoyageAIEmbeddings`.

Reranking vendors include `TeiFastReranking`, `CohereReranking`, and `VoyageAIReranking`.

## Optional dependencies

Provider classes often import optional SDKs lazily. Missing packages surface only when a model is instantiated or called.

| Feature | Likely package requirement | Typical symptom |
| --- | --- | --- |
| OpenAI/Azure OpenAI wrappers | `openai`, LangChain OpenAI adapters for older completion wrappers | import error or API client creation error |
| Ollama native chat | `langchain-ollama` | `Please install langchain-ollama` |
| Cohere chat/embedding/reranking | `langchain-cohere`, `cohere` | import error or missing API key warning |
| Google/Gemini | Google LangChain integration packages | import error when UI connection test runs |
| HuggingFace embeddings | `sentence-transformers` and LangChain HuggingFace integration | import error or model download/cache issue |
| FastEmbed | `fastembed` | import error when embedding object is used |
| VoyageAI | `voyageai` | import error or API key error on object construction |
| TEI reranking/embeddings | TEI client-compatible dependencies and a running endpoint | connection or endpoint shape error |
| LlamaCpp chat/completion | `llama-cpp-python` and a valid GGUF path, or `repo_id` plus `filename` | import error, missing `model_path`, missing `chat_format`, memory/backend error |
| Tavily web search | `tavily-python` | `Please install pip install tavily-python` |
| Jina web search | `requests` plus `JINA_API_KEY` | missing key or HTTP error during runtime search |

## Web search backend

`KH_WEB_SEARCH_BACKEND` defaults to `kotaemon.indices.retrievers.tavily_web_search.WebSearch`. The chat page imports this dotted class when web search is enabled in a mention/command flow. Tavily requires `TAVILY_API_KEY` and the `tavily-python` package. Jina uses `kotaemon.indices.retrievers.jina_web_search.WebSearch` and requires `JINA_API_KEY`; it builds requests against the Jina search/reader API at runtime.

Do not test web search by sending real queries unless the user approves network calls. For offline diagnostics, validate only the selected backend class string, credential presence, and optional package availability.

## Reranking configuration

The default reranking entry is Cohere. If `COHERE_API_KEY` is absent, `CohereReranking` prints a warning and returns the original document order rather than adding scores. File index settings can enable or disable reranking, pick a reranking model, and select an LLM scorer. Setup code disables LLM reranking by default for Ollama because local models can struggle with many parallel scoring requests.

For retrieval composition and `LLMReranking` behavior, use `../../rag-core/SKILL.md`; for provider keys and reranker model entries, stay in this sub-skill.

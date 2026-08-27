# Configuration and secrets

Use this reference before any full STORM, VectorRM, or Co-STORM run. The bundled helpers support safe `--help`, `--dry-run`, and validation-only paths; full workflows still require model/search/embedding credentials and network access.

## Secrets loading pattern

Prefer environment variables. For local runs, the bundled helpers can also load a top-level TOML file with simple key/value pairs:

```toml
OPENAI_API_KEY = "..."
BING_SEARCH_API_KEY = "..."
ENCODER_API_TYPE = "openai"
QDRANT_API_KEY = "..."
```

Pass it as `--secrets-file ./secrets.toml`. Do not commit this file and do not store secrets in report/state artifacts. The Co-STORM helper redacts secret-looking fields before writing `instance_dump.json`.

## LiteLLM model configuration

New code should use `knowledge_storm.lm.LitellmModel`. The helper CLIs accept LiteLLM model strings and infer common credentials:

| Provider string pattern | Common env vars | Notes |
| --- | --- | --- |
| `openai/...` or `gpt-*` | `OPENAI_API_KEY` | Use `openai/gpt-4o`, `openai/gpt-4o-mini`, or a provider-compatible OpenAI endpoint. |
| `azure/...` | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` | Use Azure deployment names, for example `azure/my-gpt-4o-deployment`; helpers also expose `--api-base` and `--api-version`. |
| `anthropic/...` or `claude*` | `ANTHROPIC_API_KEY` | Works through LiteLLM if the dependency/provider supports the model. |
| `gemini/...` or `google/...` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Match LiteLLM provider naming. |
| `groq/...` | `GROQ_API_KEY` | Provider-specific rate limits can be tight. |
| `mistral/...` | `MISTRAL_API_KEY` | Use smaller max-token settings for smoke tests. |
| `deepseek/...` | `DEEPSEEK_API_KEY` | Check model context and output limits. |
| `together/...` or `together_ai/...` | `TOGETHER_API_KEY` | Useful for compatible hosted open models. |
| `ollama...` | usually none | Requires a local Ollama server/model, not a cloud key. |

If the key name cannot be inferred, use the helper's `--api-key-env NAME` and keep the model string explicit.

## STORM Wiki model components

`STORMWikiLMConfigs` has separate models for:

- conversation simulation and query splitting;
- question asking;
- outline generation;
- article generation;
- article polishing.

For cost control, use a cheaper model for conversation/question components and a stronger model for outline/article/polish. The bundled `sub-skills/storm-wiki/scripts/run_storm_wiki.py` exposes `--cheap-model`, `--strong-model`, and per-component overrides.

## Co-STORM model and embedding components

Co-STORM needs both chat-completion models and an embedding encoder. `CoStormRunner` constructs `Encoder()` during initialization, so embedding settings must be ready before runner construction.

Supported encoder environment patterns in this package version:

| Encoder type | Required env vars | Notes |
| --- | --- | --- |
| `ENCODER_API_TYPE=openai` | `OPENAI_API_KEY` | Uses `text-embedding-3-small`. |
| `ENCODER_API_TYPE=azure` | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` | Uses `azure/text-embedding-3-small`; ensure the deployment/provider supports it. |

The Co-STORM helper exposes `--encoder-api-type`, `--encoder-api-key-env`, `--encoder-api-base`, and `--encoder-api-version` to set the environment before constructing the runner.

## Internet retrievers

| Retriever | Required env/options | Sub-skills using it |
| --- | --- | --- |
| `bing` | `BING_SEARCH_API_KEY` | STORM Wiki, Co-STORM |
| `you` | `YDC_API_KEY` | STORM Wiki, Co-STORM |
| `brave` | `BRAVE_API_KEY` | STORM Wiki, Co-STORM |
| `serper` | `SERPER_API_KEY` | STORM Wiki, Co-STORM |
| `duckduckgo` | no API key, but package and public web access required | STORM Wiki, Co-STORM |
| `tavily` | `TAVILY_API_KEY` plus `tavily-python` optional dependency | STORM Wiki, Co-STORM |
| `searxng` | `SEARXNG_API_URL`; `SEARXNG_API_KEY` optional | STORM Wiki, Co-STORM |
| `azure_ai_search` | `AZURE_AI_SEARCH_API_KEY`, `AZURE_AI_SEARCH_URL`, `AZURE_AI_SEARCH_INDEX_NAME` | STORM Wiki helper only |

Lower `retrieve_top_k`, `search_top_k`, `max_search_queries`, `max_search_queries_per_turn`, and thread counts when providers rate-limit.

## VectorRM and Qdrant configuration

Use `sub-skills/vector-corpus/` when the task involves a user-owned corpus.

- CSV rows should include at least `content` and `url`; `title` and `description` are recommended.
- Offline Qdrant stores use a local directory and collection name. Keep directory paths stable across indexing and retrieval.
- Online Qdrant stores require a Qdrant URL and usually `QDRANT_API_KEY`.
- `VectorRM` uses Hugging Face embeddings through `langchain_huggingface`; choose `--device cpu` first, then `cuda` or `mps` only after verifying the backend.
- CUDA/MPS accelerates embedding generation but is not required for package functionality.

## Output directories

- STORM Wiki writes one topic-named subdirectory under the selected parent output directory.
- VectorRM helpers may write or update a Qdrant collection/directory plus STORM article outputs.
- Co-STORM writes directly under `--output-dir`: `report.md`, `report.txt`, `instance_dump.json`, and `log.json`.

Always inspect outputs before sharing because they may contain retrieved snippets, generated claims, and provider usage history.

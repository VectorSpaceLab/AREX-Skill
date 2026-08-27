# GraphRAG Provider Setup

Kotaemon exposes graph-based file index types through `flowsettings.py` toggles and GraphRAG pipeline classes under `ktem.index.file.graph`. Provider configuration differs by implementation.

## Implementation choices

| Implementation | Toggle | Index class added when enabled | Provider model source | Optional dependency |
| --- | --- | --- | --- | --- |
| MS GraphRAG | `USE_MS_GRAPHRAG` | `ktem.index.file.graph.GraphRAGIndex` | `GRAPHRAG_API_KEY`, `GRAPHRAG_LLM_MODEL`, `GRAPHRAG_EMBEDDING_MODEL`, optional `settings.yaml` | `graphrag<=0.3.6`, `future` |
| NanoGraphRAG | `USE_NANO_GRAPHRAG` | `ktem.index.file.graph.NanoGraphRAGIndex` | Default LLM and embedding managers from the Resources UI | `nano-graphrag` |
| LightRAG | `USE_LIGHTRAG` | `ktem.index.file.graph.LightRAGIndex` | Default LLM and embedding managers from the Resources UI | LightRAG package from its upstream repo |

Defaults in `flowsettings.py` are `USE_MS_GRAPHRAG=true`, `USE_NANO_GRAPHRAG=false`, `USE_LIGHTRAG=true`, and `USE_GLOBAL_GRAPHRAG=true`. Enabled graph index types are appended to `KH_INDEX_TYPES` and become GraphRAG collection options.

## MS GraphRAG

The MS GraphRAG indexing pipeline writes text documents to a graph-specific input directory, runs `python -m graphrag.index --root <graph-root> --reporter rich --init`, optionally copies `settings.yaml.example` to `settings.yaml`, and then runs indexing. Retrieval requires a previously built graph output directory and an embedding provider compatible with GraphRAG's OpenAI embedding adapter.

Required for real MS GraphRAG use:

```shell
GRAPHRAG_API_KEY=<real key or local-compatible value>
GRAPHRAG_LLM_MODEL=gpt-4o-mini
GRAPHRAG_EMBEDDING_MODEL=text-embedding-3-small
```

Failure behavior from source:

- If `GRAPHRAG_API_KEY` is empty, MS GraphRAG indexing/retrieval raises `GRAPHRAG_API_KEY is not set. Please set it to use the GraphRAG retriever pipeline.`
- If GraphRAG dependencies are missing, import-time warnings say to install `graphrag future`.
- Retrieval supports one file id at a time for the MS GraphRAG retriever.

## Custom MS GraphRAG settings

Set:

```shell
USE_CUSTOMIZED_GRAPHRAG_SETTING=true
```

Then edit the deployment's `settings.yaml.example` before indexing. Kotaemon copies it to the graph root as `settings.yaml` when building an MS GraphRAG index.

Important custom settings fields:

| YAML field | Purpose |
| --- | --- |
| `llm.api_key` | Usually `${GRAPHRAG_API_KEY}` |
| `llm.type` | `openai_chat` or `azure_openai_chat` |
| `llm.api_base` | OpenAI-compatible base URL, for example Ollama `http://127.0.0.1:11434/v1` |
| `llm.model` | Chat model name served by the selected API |
| `llm.model_supports_json` | Useful for models that support JSON responses |
| `embeddings.llm.api_base` | Embedding endpoint base URL |
| `embeddings.llm.api_key` | Usually `${GRAPHRAG_API_KEY}` |
| `embeddings.llm.model` | Embedding model name |
| `embeddings.llm.type` | Usually `openai_embedding` |

For local Ollama GraphRAG, both LLM and embedding API bases should use OpenAI-compatible `/v1` endpoints. The API key can be a local dummy value only if the local server accepts it; for hosted providers use a real key.

## NanoGraphRAG and LightRAG

NanoGraphRAG and LightRAG wrappers do not use `GRAPHRAG_API_KEY` directly. They build model functions from the app's default Resources entries:

- `ktem.llms.manager.llms.get_default()` supplies the async LLM function.
- `ktem.embeddings.manager.embedding_models_manager.get_default()` supplies embeddings and is called on sample text to infer embedding dimension.

This means a GraphRAG collection can fail even when `GRAPHRAG_API_KEY` is set if the default LLM or default embedding model in the Resources UI is missing, points to a placeholder key, or cannot be called. Use this sub-skill for provider setup, then use `../../rag-core/SKILL.md` when diagnosing retrieval/result formatting.

Both wrappers expose graph prompt and batch-size settings. If indexing hits rate limits or local-model overload, reduce index batch size and use a smaller local or hosted model.

## Global vs per-file graph behavior

`USE_GLOBAL_GRAPHRAG` affects NanoGraphRAG and LightRAG storage behavior. When true, graph mappings can reuse a collection-wide graph id; when false, they fall back to the base GraphRAG graph-id behavior. Keep this in mind when troubleshooting stale or unexpectedly shared graph context.

## Offline validation checklist

Run:

```bash
python scripts/check_provider_env.py --env-file .env --select graphrag
```

The script checks:

- Whether graph toggles parse as booleans.
- Whether at least one graph implementation is enabled when selected.
- Whether MS GraphRAG has `GRAPHRAG_API_KEY` when `USE_MS_GRAPHRAG=true`.
- Whether `USE_CUSTOMIZED_GRAPHRAG_SETTING=true` is paired with an existing settings YAML when provided via `--settings-file`.
- Whether local GraphRAG API bases look OpenAI-compatible when found in a settings YAML.

It does not import GraphRAG packages, run indexing, query a graph, or call model endpoints.

## Common GraphRAG remediation patterns

- Missing `GRAPHRAG_API_KEY` with MS GraphRAG: add a real key or a local-compatible dummy key only when using an OpenAI-compatible local endpoint that accepts it.
- Custom settings enabled but not copied/available: ensure the deployment has the intended `settings.yaml.example` before indexing; existing graph roots may already contain an older copied `settings.yaml`.
- Ollama URL without `/v1` in MS GraphRAG YAML: use the OpenAI-compatible `/v1` endpoint for both `llm.api_base` and `embeddings.llm.api_base`.
- NanoGraphRAG/LightRAG failure despite GraphRAG env vars: verify the default LLM and embedding Resources entries, because these implementations use manager defaults.
- Optional package conflict after installing graph packages: follow deployment-level dependency recovery in `../../app-deployment/SKILL.md`; do not keep reinstalling graph packages without checking the active environment.

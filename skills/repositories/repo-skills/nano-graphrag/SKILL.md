---
name: nano-graphrag
description: "Use nano-graphrag for lightweight GraphRAG indexing, querying,
  provider customization, storage backend selection, prompt/entity extraction
  tuning, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# nano-graphrag

Use this repo skill when a task involves the `nano-graphrag` Python package, lightweight GraphRAG/RAG indexing, graph-backed retrieval, local/global/naive query modes, custom LLM or embedding providers, storage backend swaps, entity-extraction troubleshooting, or GraphML knowledge graph inspection.

The root stays a router. Open the focused sub-skill for the workflow you need, then use its bundled references and scripts instead of reopening the source repository.

## Quick environment check

Install the package in the active project environment with one of:

```bash
pip install nano-graphrag
# or, for a checkout you are actively editing:
pip install -e .
```

Then verify importability:

```python
from nano_graphrag import GraphRAG, QueryParam
print(QueryParam(mode="global"))
```

If import fails with `ModuleNotFoundError: No module named 'transformers'`, install `transformers`; this repository version imports `transformers.AutoTokenizer` at module import time even though the package metadata may not list it explicitly.

Run [scripts/check_nano_graphrag_env.py](scripts/check_nano_graphrag_env.py) when you need a safe no-network import/API/storage sanity check before following deeper recipes.

## Route by task

| User task | Read first |
| --- | --- |
| Build a `GraphRAG`, insert text, query global/local/naive modes, use async methods, reuse a `working_dir`, or validate custom chunking. | [sub-skills/core-graphrag-workflows/SKILL.md](sub-skills/core-graphrag-workflows/SKILL.md) |
| Replace OpenAI with Azure OpenAI, Amazon Bedrock, DeepSeek/OpenAI-compatible APIs, Ollama, local embeddings, or debug provider kwargs/credentials. | [sub-skills/provider-and-model-integrations/SKILL.md](sub-skills/provider-and-model-integrations/SKILL.md) |
| Choose JSON/NanoVectorDB/HNSW/NetworkX/Neo4j storage, adapt FAISS/Milvus/Qdrant-style vector stores, or visualize GraphML. | [sub-skills/storage-backends/SKILL.md](sub-skills/storage-backends/SKILL.md) |
| Change prompts, repair malformed JSON, customize entity extraction/DSPy, or recover from zero entities / empty graph / Leiden failures. | [sub-skills/customization-and-troubleshooting/SKILL.md](sub-skills/customization-and-troubleshooting/SKILL.md) |

## Read these root references

- Read [references/package-overview.md](references/package-overview.md) for package purpose, public API surface, default components, install caveats, and how the sub-skills fit together.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, provider, storage, empty-graph, and optional dependency triage before choosing a deeper troubleshooting page.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout or whether `refresh-repo-skill` is needed.
- `references/repo-routing-metadata.json` is structured metadata consumed by the repo-skills router import process; do not edit it casually.

## High-confidence operating rules

1. Use a stable `working_dir` for persistent state. The default local stack writes JSON KV stores, NanoVectorDB JSON files, and NetworkX GraphML under that directory.
2. Do not run hosted-provider examples until credentials, network policy, model IDs, and rate limits are explicit. For no-network validation, use fake LLM/embedding helpers from the core sub-skill.
3. Enable `enable_naive_rag=True` before insertion if you will later query `QueryParam(mode="naive")`.
4. Treat Neo4j, Ollama, Bedrock, FAISS, Milvus, Qdrant, and downloaded local embedding models as optional integrations with their own services, packages, or credentials.
5. If insertion produces no entities/relations, debug provider output format and context length before replacing graph storage.
6. Keep any generated application scripts independent of this source checkout; copy or adapt needed patterns into the application or use the bundled scripts here.

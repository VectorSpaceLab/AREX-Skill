# Package Overview

## Purpose

`nano-graphrag` is a compact Python implementation of GraphRAG-style indexing and retrieval. It builds chunks from user text, extracts entities and relationships with LLM calls, clusters the knowledge graph, generates community reports, and supports global, local, and naive retrieval modes.

Use this reference to orient a task before choosing a sub-skill. Use the focused references for complete workflows.

## Public import surface

```python
from nano_graphrag import GraphRAG, QueryParam
```

There is no package console script in this version; the primary surface is Python API usage.

Key objects:

- `GraphRAG`: dataclass-style orchestrator for indexing, storage, model calls, and query execution.
- `QueryParam`: dataclass-style query configuration with `mode` values `"global"`, `"local"`, and `"naive"`.
- `nano_graphrag._storage`: built-in storage classes including `JsonKVStorage`, `NanoVectorDBStorage`, `HNSWVectorStorage`, `NetworkXStorage`, and `Neo4jStorage`.
- `nano_graphrag._utils.wrap_embedding_func_with_attrs`: wraps async embedding functions with `embedding_dim` and `max_token_size` attributes required by vector stores.
- `nano_graphrag.entity_extraction`: optional DSPy-based entity extraction helpers.

## Default components

A plain `GraphRAG()` uses:

- OpenAI chat functions for best/cheap model calls.
- OpenAI `text-embedding-3-small` embedding function.
- JSON file KV storage.
- NanoVectorDB local vector storage.
- NetworkX GraphML graph storage.
- Tiktoken tokenization with model name `gpt-4o`.
- Global query mode by default.

For real workloads, configure provider credentials or replace the LLM and embedding functions before inserting data. For no-network tests, use the fake functions in the core sub-skill smoke script.

## Working directory behavior

`GraphRAG(working_dir=...)` stores and reloads state under that directory. With default local components, common artifacts include:

- `kv_store_full_docs.json`
- `kv_store_text_chunks.json`
- `kv_store_llm_response_cache.json` when LLM cache is enabled
- `kv_store_community_reports.json`
- `vdb_entities.json`
- `vdb_chunks.json` when naive RAG is enabled
- `graph_chunk_entity_relation.graphml`

Use a new working directory when changing embedding dimension, vector backend type, or graph backend identity.

## Sub-skill map

- [Core GraphRAG workflows](../sub-skills/core-graphrag-workflows/SKILL.md): lifecycle, query modes, async, chunking, persistence, and no-network smoke checks.
- [Provider and model integrations](../sub-skills/provider-and-model-integrations/SKILL.md): default and custom LLM/embedding functions, hosted providers, Ollama, local embeddings, cache-aware wrappers, and provider-specific failures.
- [Storage backends](../sub-skills/storage-backends/SKILL.md): local storage classes, HNSW, Neo4j, adapter contracts, persistence artifacts, and GraphML visualization.
- [Customization and troubleshooting](../sub-skills/customization-and-troubleshooting/SKILL.md): prompts, JSON repair, entity extraction, DSPy, zero-entity failures, and empty-graph/Leiden recovery.

## Installation caveats

The source distribution declares Python `>=3.9`. This version imports `transformers.AutoTokenizer` during package import, so an environment may need:

```bash
pip install transformers
```

if the package was installed from metadata that did not pull it in.

Optional integrations may require additional packages or services:

- Ollama server and pulled local models for Ollama examples.
- Sentence Transformers or other model packages for local embeddings.
- Neo4j 5.x with the Graph Data Science plugin for `Neo4jStorage` clustering.
- FAISS, Milvus Lite, or Qdrant clients for custom vector-store adapters.
- Provider credentials and network access for hosted APIs.

## Minimal no-network sanity check

```python
import numpy as np
from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag._utils import wrap_embedding_func_with_attrs

@wrap_embedding_func_with_attrs(embedding_dim=8, max_token_size=128)
async def fake_embedding(texts: list[str]) -> np.ndarray:
    return np.zeros((len(texts), 8), dtype=float)

rag = GraphRAG(embedding_func=fake_embedding, enable_naive_rag=True)
assert QueryParam(mode="global").mode == "global"
```

This checks import and construction only. To exercise a deterministic insert/query flow without providers, use the bundled core smoke script.

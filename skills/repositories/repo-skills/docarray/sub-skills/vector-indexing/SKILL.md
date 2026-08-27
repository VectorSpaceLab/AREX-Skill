---
name: vector-indexing
description: "Build and troubleshoot DocArray Document Index workflows for local
  exact search, filters, hybrid queries, persistence, nested subindexes, and
  optional vector databases."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DocArray vector indexing

Use this sub-skill when a task needs to index typed documents, search embeddings, filter metadata, combine queries, persist a local index, or select an optional vector database backend.

## Route here for

- Defining a dimensioned vector field for `InMemoryExactNNIndex` or another `DocumentIndex`.
- Indexing `DocList` data and using `find()`, `find_batched()`, `filter()`, `filter_batched()`, ID access, deletion, or re-index updates.
- Building local hybrid queries with `build_query()` and `execute_query()`.
- Searching nested `DocList` fields with a subindex.
- Choosing HNSWLib, Qdrant, Weaviate, Elasticsearch, Redis, Milvus, MongoDB Atlas, or Epsilla integrations and diagnosing missing extras or services.

## Route elsewhere

- Base schemas, predefined documents, tensor typing, or `DocList`/`DocVec` modeling before indexing: use sibling [`document-modeling`](../document-modeling/).
- JSON/protobuf/bytes/CSV/DataFrame serialization or `file://`/S3 storage: use sibling [`serialization-storage`](../serialization-storage/).

## Read these bundled references

1. Start with [API reference](references/api-reference.md) for verified index signatures, schema requirements, and configuration fields.
2. Use [Index workflows](references/index-workflows.md) for local indexing, search, filters, query builders, persistence, and nested subindexes.
3. Use [Optional backends](references/optional-backends.md) before installing an external backend or starting a service.
4. Use [Troubleshooting](references/troubleshooting.md) for schema, dimension, query-builder, dependency, and service failures.

## Safe bundled helper

Run [inmemory_index_smoke.py](scripts/inmemory_index_smoke.py) for deterministic CPU-only local checks. It uses only NumPy and the in-memory index; it does not start a database, download data, or require credentials:

Run these commands from this sub-skill root (the directory containing this `SKILL.md`):

```bash
python scripts/inmemory_index_smoke.py --help
python scripts/inmemory_index_smoke.py
python scripts/inmemory_index_smoke.py --exercise-persist
```

The verified minimum scope is CPU with the in-memory backend. External services, HNSWLib, and accelerator-specific tensor paths remain optional and unverified until a task prepares their dependencies and service/hardware plan.

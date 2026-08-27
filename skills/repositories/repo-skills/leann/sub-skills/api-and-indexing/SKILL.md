---
name: api-and-indexing
description: "Build, update, search, filter, and safely manage LEANN indexes
  through the Python API, including precomputed embeddings and hybrid or grep
  retrieval."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LEANN API and Indexing

Use this sub-skill for the Python lifecycle around `LeannBuilder`,
`LeannSearcher`, passage metadata, precomputed vectors, low-level updates,
metadata filters, BM25/vector fusion, grep retrieval, and resource cleanup.

## Route by task

- Verify constructors, method signatures, defaults, result fields, and artifact
  names in [API reference](references/api-reference.md).
- Implement a new build, precomputed-vector build, update, staged replacement,
  or cleanup flow with [indexing and search workflows](references/indexing-and-search-workflows.md).
- Configure post-search metadata filters, pure BM25, hybrid retrieval, or grep
  with [metadata, hybrid, and grep](references/metadata-hybrid-and-grep.md).
- Diagnose bad base paths, missing artifacts, dimension or ID mismatches,
  update duplication, BM25/grep failures, and daemon cleanup with
  [troubleshooting](references/troubleshooting.md).
- Prove a local installation and HNSW backend without a model download by
  running the bundled [precomputed-index smoke](scripts/precomputed_index_smoke.py).

## Operating rules

1. Treat `index_path` as a **base path**, not as the `.meta.json`, `.index`, or
   passage file. Keep every sibling artifact together.
2. Use a new staging directory for builds and critical updates. Validate it,
   then publish the whole directory; never overwrite unrelated files or delete
   a parent directory in response to an error message.
3. Give every passage a unique string ID. For precomputed arrays, make the
   passage IDs and supplied vector IDs identical and order-aligned.
4. Set build and query embedding configuration consistently. A precomputed
   build avoids document embedding, but semantic search still needs a query
   embedding; pure BM25 and grep do not.
5. Configure recomputation on `LeannSearcher`; the per-call search override is
   deprecated. Disable warmup and daemon use for offline BM25-only checks.
6. Always call `cleanup()` or use `with LeannSearcher(...) as searcher:`.
7. Treat filters as post-retrieval filters. Missing or unsupported fields do
   not raise by default; they remove the affected result.
8. Choose update behavior from stored backend/index metadata. IVF supports
   remove-then-add; HNSW only supports low-level append on non-compact indexes.

## Boundaries

- For CLI build/search, daemon commands, filesystem watching, or idempotent
  document builds, use [CLI operations](../cli-operations/SKILL.md).
- For HNSW, IVF, DiskANN algorithms, storage modes, and backend tuning, use
  [backends and storage](../backends-and-storage/SKILL.md).
- For embedding modes, model/provider credentials, prompt templates, and chat
  providers, use [embeddings and chat](../embeddings-and-chat/SKILL.md).
- For document, email, browser, chat-history, or code ingestion applications,
  use [RAG applications](../rag-applications/SKILL.md).

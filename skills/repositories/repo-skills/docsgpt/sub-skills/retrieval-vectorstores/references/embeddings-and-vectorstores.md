# Embeddings and Vector Stores

## Embeddings

Default local behavior uses a sentence-transformer model identified by `EMBEDDINGS_NAME`. Remote embeddings are selected by `EMBEDDINGS_BASE_URL`, with optional `EMBEDDINGS_KEY` and `EMBEDDINGS_MAX_INPUT_TOKENS`.

Selection questions:

- Is data allowed to leave the deployment?
- Is the endpoint OpenAI-compatible and does it return a stable dimension?
- Can web and workers reach the same endpoint?
- Are long inputs truncated deliberately?
- Is local model RAM/GPU/download/cache available?

Changing model or dimension requires re-embedding/re-ingestion. Never mix vectors of different dimensions in one logical collection/index.

## Vector-store matrix

| Store | Typical mode | Important prerequisites/notes |
|---|---|---|
| `faiss` | local single-node files | simplest default; coordinate persistence/locking/backups; no meaningful score-threshold support |
| `pgvector` | Postgres extension | supports hybrid keyword path, score threshold and GraphRAG; separate connection setting may be used |
| `qdrant` | local/remote service | URL/location, ports, auth, collection, distance function; threshold warning semantics differ |
| `milvus` | Milvus Lite or server | URI/token/collection; verify client dependency and persistence mode |
| `elasticsearch` | Elastic service | endpoint/cloud id and credentials; validate mapping/dimension |
| `mongodb` | MongoDB Atlas vector search | optional legacy/vector backend; requires Mongo URI/client and Atlas index; not the default user-data store |

The active factory registry does not include LanceDB at this snapshot even though implementation/settings code exists. Treat it as unavailable until registry and native tests pass in the target version.

## pgvector notes

DocsGPT normalizes common Postgres URI forms. Keep the pgvector database schema and embedding dimension aligned.

For most source-filtered corpora, exact search is correct and often fast enough. An IVFFlat index chooses global candidates before a source filter can discard them, so a poorly sized index may return too few or no rows. Existing logic can increase probes and fall back, but this is not a substitute for sound index design.

- For small corpora (roughly below tens of thousands of vectors), prefer no approximate index.
- Build IVFFlat after loading representative data.
- Size lists to actual rows; monitor recall with source filters.
- Let probes derive from index lists or pin `PGVECTOR_IVFFLAT_PROBES` after measurement.
- Back up before dropping/rebuilding indexes.

## Migration procedure

1. inventory every source and current dimension;
2. provision target store/index with explicit dimension and distance metric;
3. freeze or version writes;
4. re-embed a tiny source and compare expected queries;
5. bulk re-ingest with progress/checkpoints;
6. compare row/chunk counts and retrieval recall;
7. switch reads;
8. retain rollback data until stable.

Legacy migration helpers are stateful and backend-specific. Do not run one solely because its filename appears relevant; verify source version, target schema, idempotency and backup first.

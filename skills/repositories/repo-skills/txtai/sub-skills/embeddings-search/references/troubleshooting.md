# Embeddings Search Troubleshooting

Use this when a txtai embeddings index builds, updates, searches, saves, or loads incorrectly. Start with result shape and configuration: most failures come from creating the `Embeddings` instance without the components the query later expects.

## Quick Triage

1. Print or inspect `embeddings.config` after construction and after `load`.
2. Check `embeddings.count()` after `index`, `upsert`, `delete`, and `load`.
3. Confirm whether `content=True` was set before indexing.
4. Identify query mode: natural-language string, SQL string, graph query, or in-memory `similarity`.
5. Confirm optional component availability: ANN backend, database backend, graph backend, sparse scoring, vector model, object encoder.
6. Run a tiny query without filters, then add SQL filters, graph clauses, hybrid weights, or subindex names one at a time.

## Tuple Results Instead Of Dictionaries

Signal:

```python
results = embeddings.search("query", 5)
# [(4, 0.31), ...]
results[0]["text"]  # TypeError
```

Cause: the index was built without content storage. txtai returns `(id, score)` tuples when content is disabled.

Fix:

```python
embeddings = Embeddings(content=True)
embeddings.index([(uid, {"text": text, "topic": topic}, None) for uid, text, topic in rows])
```

Important: setting `embeddings.config["content"] = True` after indexing is not enough. Rebuild with `index` from original rows or use `reindex` only if content storage already existed.

## SQL Query Fails Or Returns No Metadata

Signals:

- SQL query raises a parse/search error.
- `select text from txtai ...` returns missing columns.
- `similar(...)` query fails against a tuple-only index.

Checks:

- SQL requires `content=True` at indexing time.
- Dynamic fields require dictionary data rows or a configured text column.
- `similar(...)` is a txtai function, not standard SQL; run it through `embeddings.search`, not a raw database connection.
- Use bind parameters for user text: `similar(:q)` with `parameters={"q": "..."}`.
- Escape nested JSON/dictionary keys with bracket syntax, such as `[parent.child element]`.

Fix pattern:

```python
query = "select id, text, score from txtai where similar(:q, 50) and category = :category limit 5"
results = embeddings.search(query, parameters={"q": "climate", "category": "news"})
```

## Filters Drop Too Many `similar(...)` Results

Signal: a query without filters returns strong matches, but adding `where tenant = ...`, date filters, or permissions returns too few or no rows.

Cause: the similarity stage feeds candidate ids to the database stage. If the candidate set is too small, filters can remove all matches.

Fix: increase the candidate count in `similar` beyond the final `limit`.

```sql
select id, text, score
from txtai
where similar(:q, 100) and tenant = :tenant
limit 10
```

Rule of thumb: start with 10x the desired final limit when filters are selective, then tune for latency and recall.

## Bind Parameter Problems

Signals:

- User text containing quotes breaks SQL.
- The query searches for the literal `:q`.
- Batch search applies wrong parameters to queries.

Fixes:

- Pass `parameters={"q": value}` to `search`.
- Pass `parameters=[{"q": q1}, {"q": q2}]` to `batchsearch`.
- Bind both similar text and filters; do not interpolate user strings into SQL.
- Keep candidate count, index name, and weights literals when they are not user-controlled.

## Auto-Generated Id Pitfalls

Signals:

- `delete([id])` deletes nothing.
- `upsert` appends instead of replacing the intended record.
- The agent cannot map search results back to source records.

Causes and fixes:

- Raw string rows generate ids automatically; use explicit `(id, data, tags)` for mutable records.
- UUID autoid modes generate ids but the caller must store them if later updates/deletes are required.
- For existing tuple-only indexes, run a search first to discover ids, then delete/upsert explicit ids where possible.

Preferred mutable-row pattern:

```python
embeddings.index([("doc-1", "original", None)])
embeddings.upsert([("doc-1", "updated", None)])
embeddings.delete(["doc-1"])
```

## `index` Accidentally Replaced Data

Signal: a previously populated index now contains only the latest batch.

Cause: `index(rows)` builds a brand-new index and overwrites existing indexed state.

Fix: use `upsert(rows)` for incremental loads and reserve `index(rows)` for full rebuilds. If content storage is enabled and raw source rows are unavailable, use `reindex(...)` for configuration/model/backend rebuilds rather than `index`.

## Reindex Fails Or Cannot Recover Raw Data

Signals:

- `reindex` cannot rebuild from current state.
- After changing vector model/backend, rows are missing.

Causes:

- `reindex` depends on content storage; tuple-only indexes do not contain enough stored content.
- Object rows may need a preparation function when changing encoders/vectorizers.

Fix:

```python
embeddings = Embeddings(content=True)
embeddings.index(rows)
embeddings.reindex(path="new-local-or-hub-model", backend="hnsw")
```

If content was not enabled, rebuild with original source rows.

## Save/Load Path Issues

Signals:

- `load(path)` fails with missing configuration.
- A saved index loads but has zero results.
- Relative paths work in one process but fail in another.

Checks:

- Save to a directory or supported archive suffix such as `.tar.gz`.
- Confirm the saved directory contains txtai configuration and enabled component subdirectories.
- Use `Embeddings().exists(path)` before `load` when probing an index.
- After `load`, run `count()` and a known query.
- Avoid moving only one component subdirectory; move the whole saved index directory/archive.
- Cloud save/load requires matching cloud configuration and, for object storage providers, credentials available in the runtime environment.

## Missing ANN Backend Extras

Signals:

- Import errors for `faiss`, `hnswlib`, `annoy`, `sqlite_vec`, `torch`, `pgvector`, or another backend package.
- Backend-specific method errors during `upsert` or `delete`.

Fixes:

- Use the default backend only when its dependency is installed in the runtime.
- Select a simpler backend such as `backend="numpy"` for tiny/local checks when supported.
- Install focused optional dependencies for the chosen backend instead of broad all-extras.
- Confirm backend mutation semantics: some indexes are immutable or limited after creation.
- For Postgres/pgvector, verify the database service, URL, schema/table settings, and extension availability.

## Database Backend Problems

Signals:

- `content="duckdb"`, `content="client"`, or a database URL fails at construction/search/save.
- Dynamic columns or JSON filters behave differently across engines.

Fixes:

- Start with `content=True`/SQLite for local development.
- Install focused database extras for DuckDB or SQLAlchemy-backed engines.
- For client-server databases, verify the connection URL or `CLIENT_URL` where `content="client"` is used.
- Check JSON support for the selected database when using nested dictionary fields.
- Keep column names simple when possible; use bracket escaping for nested names and spaces.

## Object Storage Problems

Signals:

- `object` column is missing.
- Returned object is bytes/`BytesIO` instead of an image/list/custom object.
- Pickle object storage is blocked.

Fixes:

- Enable both `content=True` and `objects=True` or a specific object encoder before indexing.
- Store a `text` field alongside `object` if the object itself is not the vectorized input.
- Use `objects="image"` only when image dependencies are installed and image objects are expected.
- Treat `objects="pickle"` as trusted legacy behavior only; do not enable pickle for untrusted indexes or remote content.

## Model Download Or Offline Failures

Signals:

- Hugging Face or sentence-transformers download errors.
- SSL/proxy/offline/cache errors.
- A no-config `Embeddings()` call unexpectedly tries to download a default model.

Fixes:

- Use a local model path for production/offline environments.
- Pre-warm the model cache as a deployment step outside the skill content.
- Use `method="external"` with a local transform or precomputed vectors for smoke tests.
- Set `path` explicitly so agents know which model/backend is expected.
- Avoid running notebook/benchmark examples during validation unless network/GPU/model cache access is confirmed.

## CPU/GPU Backend Behavior

Signals:

- GPU is expected but `torch.cuda.is_available()` is false.
- Batch size causes memory errors.
- Quantization or Torch/GGML backend behavior differs from Faiss/Numpy.

Fixes:

- Treat CPU as the portable baseline unless the runtime explicitly verifies GPU availability.
- Tune `batch` and `encodebatch` downward for memory-constrained environments.
- Use `gpu=False` or CPU-compatible backend/model settings when needed.
- Document quantization precision and ANN backend together; quantization support varies by backend.
- Validate top-k results after backend changes; exact scores can vary.

## Hybrid Weight Issues

Signals:

- Keyword matches dominate semantic matches or vice versa.
- SQL hybrid query appears to ignore weights.
- Filtered hybrid results are sparse or empty.

Fixes:

- Confirm the index actually has both dense and sparse/scoring components (`hybrid=True`, `keyword=True`, or `sparse=...` as intended).
- For non-SQL search, pass `weights=` to `search`.
- For SQL search, pass weights in `similar(...)` after the candidate/index arguments.
- Increase candidate count before adjusting weights when SQL filters are present.
- Check scoring normalization settings when comparing BM25/TF-IDF/SPLADE with dense scores.

## Graph Backend And Query Problems

Signals:

- Graph attributes or graph queries fail.
- `search(..., graph=True)` returns normal rows/tuples.
- RDBMS graph backend cannot connect.

Fixes:

- Enable graph at construction with `graph=True` or `graph={...}` before indexing.
- Install graph dependencies for the selected backend; default graph behavior uses NetworkX.
- Use `content=True` when graph attributes need SQL selection or dynamic columns.
- Verify relationship ids match indexed ids; invalid manual relationships are ignored or replaced by semantic graph edges.
- For RDBMS graph backend, verify database URL, schema, service availability, and permissions.
- Save/load the parent embeddings index; graph data persists alongside it.

## Subindex Errors

Signals:

- Search raises index-not-found errors.
- SQL `similar(..., 'name')` selects the wrong component.
- `defaults=False` index has no searchable top-level index.

Fixes:

- Ensure `indexes={"name": {...}}` is configured before indexing.
- Use `search(query, index="name")` for non-SQL subindex selection.
- Use `similar(:q, candidates, 'name')` in SQL.
- Keep subindex names stable across save/load and deployment configs.
- If different fields are indexed, configure `columns={"text": "field"}` inside the relevant subindex.

## Custom SQL Function Or Expression Failures

Signals:

- SQL cannot resolve a function name.
- Expression column is missing or slow.
- Function works in Python but not through SQL.

Fixes:

- Register functions in the `Embeddings` configuration before indexing/querying when database setup occurs.
- Use resolvable callables or function dictionaries with explicit `name` and `function`.
- Add `expressions=[{"name": "...", "expression": "...", "index": True}]` for reusable computed fields.
- Keep heavyweight pipeline functions out of tight SQL loops unless latency is acceptable.

## Cleanup And Long-Running Processes

Signals:

- File locks or database connections remain open.
- Repeated indexing/search jobs grow memory.
- Tests interfere with each other through shared resources.

Fixes:

- Use `with Embeddings(...) as embeddings:` around short-lived jobs.
- Call `close()` in `finally` blocks for long-lived scripts.
- Do not run concurrent write operations against the same embeddings instance or path.
- Use separate save directories for test runs, staging, and production builds.

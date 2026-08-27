# Vector Search Troubleshooting

Use this checklist when `VectorIndex`, listener embeddings, or nearest-neighbor retrieval do not behave as expected.

## Dimension Mismatch

Symptoms:

- `VectorIndex.dimensions` is not the dimension expected by the model.
- Local search raises numpy shape or stacking errors.
- A service backend rejects inserts or queries because vector length is wrong.
- Exact-match retrieval returns poor scores even though records were indexed.

Likely causes:

- The model declares `datatype="vector[...:N]"` but returns a vector of length other than `N`.
- The compatible listener model returns a different length than the indexing listener model.
- A table field uses `Array`/`array[...]` with one shape while the model emits another shape.
- One code path returns lists and another returns arrays with different lengths.

Fixes:

1. Print or assert the length of every embedding returned by the indexing and compatible models.
2. Make the declared datatype shape match the actual model output length.
3. Recreate or reapply the listener/index after changing a model datatype, because the listener output table schema is part of index setup.
4. For plugin backends, recreate the backend collection/index if it was created with the old dimension.

## Missing Listener Outputs

Symptoms:

- `VectorIndex.setup()` cannot find a vector shape in the indexing listener output table schema.
- `copy_vectors()` logs that outputs were missing.
- `.like(...).select().execute()` returns no rows even though source records exist.
- The listener output table exists but rows lack the generated output field.

Likely causes:

- The indexing model was created without a vector datatype.
- `Listener.select` is `None` for the indexing listener.
- The source records were inserted but the listener run was not triggered.
- The query indexes an upstream listener output table, but the upstream listener has not produced rows yet.
- Records were added after index creation and CDC/listener work has not caught up.

Fixes:

1. Confirm the indexing listener has `select=db[table].select()` or an equivalent source query.
2. Confirm `listener.outputs` exists and contains rows with the generated output field and `_source`.
3. Apply the `VectorIndex` only after source data and upstream listener inputs exist, or re-run the listener/copy path for the new IDs.
4. For local recovery, reinitialize vector search so it can scan persisted `VectorIndex` components and copy missing listener outputs.

## Unsupported Measure

Symptoms:

- Construction fails with `KeyError` or `Unsupported measure`.
- A plugin backend creates an index but scoring semantics differ from local tests.

Likely causes:

- Local vector search implements `cosine`, `dot`, and `l2`; other measure names are not safe.
- Some plugin backends map measure names to backend-specific distance names and reject unknown values.
- The base enum contains a `css` value, but local search does not implement a `css` scoring function.

Fixes:

1. Use `measure="cosine"` unless there is a reason to choose another measure.
2. Use `"dot"` or `"l2"` only after validating the score interpretation for the selected backend.
3. Avoid `"css"` for local workflows.
4. If a plugin rejects a valid local measure, route to plugin-specific troubleshooting rather than changing the Superduper `VectorIndex` pattern.

## Empty Nearest-Neighbor Results

Symptoms:

- Local vector search logs that the vector database is empty.
- `.like(...).select().execute()` returns an empty list.
- `db.select_nearest(...)` returns `([], [])`.
- `describe()` reports size zero.

Likely causes:

- The vector backend has not received vectors yet.
- The listener output table is empty.
- `within_ids` restricts the search to IDs that are not present in the vector index.
- A local in-memory index was dropped or lost after restart and was not reinitialized.
- An optional vector DB plugin is unavailable or connected to the wrong collection/service.

Fixes:

1. Inspect listener output row count first; no outputs means there is nothing to copy.
2. Inspect backend size/list/describe when available.
3. Retry without a restrictive filter to rule out `within_ids` mismatches.
4. Reinitialize local vector search after restart.
5. For plugin backends, verify plugin package import and service health in the plugin-specific skill area.

## Zero Scores After Adding Data

A known practical case is querying a value that was not indexed yet: the query can return rows with scores that sum to zero because no matching embedding exists in the backend. After inserting new records, the new records become searchable only once their listener outputs are generated and copied to the vector backend.

Fixes:

1. Confirm the new source rows exist in the source table.
2. Confirm matching listener output rows exist for those source IDs.
3. Confirm the vector-search backend size increased.
4. If the Datalayer is local and the backend mapping was lost, reinitialize vector search.
5. If a service backend is used, check that add/upsert calls succeeded and were sent to the expected collection/index.

## Compatible Listener Not Used

Symptoms:

- A query like `{"y": ...}` fails even though the index works for `{"x": ...}`.
- The error says query keys do not match `VectorIndex` keys.
- Results look like they were embedded with the wrong model.

Likely causes:

- `VectorIndex` was built without `compatible_listener`.
- The compatible listener key does not match the key in the `like` document.
- The compatible model has a non-singleton signature but the listener key is a string.
- The compatible model output dimension differs from the indexing model dimension.
- The query document includes multiple listener keys and the selected model is ambiguous.

Fixes:

1. Define `compatible_listener=Listener(identifier="...", model=query_model, key="query_key", select=None)` on the `VectorIndex`.
2. Query with exactly that key: `.like({"query_key": value}, vector_index="...", n=k)`.
3. Keep compatible model output length and semantic embedding space identical to the indexing model.
4. Add an assertion-backed smoke query for both the indexing key and the compatible key.

## Optional Vector DB Plugin Missing Or Service Unavailable

Symptoms:

- Import errors for a plugin package.
- `load_plugin` cannot find a configured vector-search engine.
- Connection failures from Qdrant, ChromaDB, MongoDB Atlas, Snowflake, or another service backend.
- Backend-specific collection/index creation fails.

Likely causes:

- The optional plugin is not installed in the active runtime.
- The service is not running or is on a different host/port.
- Credentials or cloud permissions are missing.
- The configured `vector_search_engine` does not match the plugin implementation.
- The plugin has backend-specific constraints, such as ChromaDB expecting a localhost HTTP service.

Fixes:

1. Keep the `VectorIndex` and listener pattern unchanged while validating the plugin separately.
2. Route installation, credentials, service startup, and backend-specific index setup to `plugins-and-integrations`.
3. Once the plugin is healthy, verify only the shared contract here: add vectors, find nearest by array, delete vectors, and report size/list/describe if supported.

## Add/Delete/Copy Edge Cases

- `copy_vectors(ids=None)` skips records whose listener outputs are missing. Missing outputs are a listener/indexing problem, not a searcher problem.
- Local `delete(ids)` expects IDs already present in the lookup; deleting missing IDs can fail.
- Adding a vector with an existing ID replaces the older vector in the local searcher.
- `cleanup()` drops the backend component for the `VectorIndex`; use it only when tearing down the component.
- Service-backed searchers may batch inserts/upserts. A partial batch failure can leave backend size lower than listener output count.

## Safe First Aid Commands

Use the bundled smoke helper to verify constructor and local-search semantics without a database:

```bash
python scripts/superduper_vector_smoke.py
python scripts/superduper_vector_smoke.py --measure l2 --dimension 8
```

If the active environment has a suitable local/mock Datalayer backend installed, optionally run:

```bash
python scripts/superduper_vector_smoke.py --run-db
```

The optional database mode is deliberately small and should not require network, credentials, model downloads, or training.

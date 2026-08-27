# Embeddings API Reference

This reference summarizes the txtai embeddings APIs that future agents need for search/index lifecycle work. Use it with `SKILL.md` and `query-and-indexing.md` rather than reopening the source checkout.

## Imports And Construction

Primary imports:

```python
from txtai import Embeddings
# Equivalent focused import:
from txtai.embeddings import Embeddings
```

Verified constructor shape:

```python
Embeddings(config=None, models=None, **kwargs)
```

Configuration can be passed as a dictionary, keyword arguments, or both. Equivalent examples:

```python
Embeddings({"path": "sentence-transformers/all-MiniLM-L6-v2", "content": True})
Embeddings(path="sentence-transformers/all-MiniLM-L6-v2", content=True)
```

Important construction modes:

| Goal | Configuration |
| --- | --- |
| Default dense semantic search | `Embeddings()` |
| Specific vector model | `Embeddings(path="sentence-transformers/all-MiniLM-L6-v2")` |
| Metadata/SQL/dict result storage | `Embeddings(content=True)` |
| Sparse keyword only | `Embeddings(keyword=True)` |
| Sparse vector search | `Embeddings(sparse=True)` or `Embeddings(sparse="model-or-path")` |
| Dense + sparse hybrid | `Embeddings(hybrid=True)` |
| Graph index | `Embeddings(content=True, graph=True)` or `Embeddings(graph={...})` |
| External transform | `Embeddings(method="external", transform=my_function)` |
| Precomputed vectors | `Embeddings(method="external")` with vector rows |
| Subindexes | `Embeddings(defaults=False, indexes={"name": {...}})` |

`content=True` defaults to SQLite content storage. Other content backends include DuckDB and SQLAlchemy/client-server database URLs when optional dependencies and services are available.

## Row Formats

`index`, `upsert`, and `score` accept iterables. The iterable may be a list or a generator for large data.

| Row format | Meaning | Notes |
| --- | --- | --- |
| `"text"` | Single raw data value | txtai auto-generates ids. Use only when later update/delete by id is not needed. |
| `(id, data)` | Explicit id and data | Good for stable update/delete. |
| `(id, data, tags)` | Explicit id, data, optional tag string | Canonical internal/default row form. |
| `{"id": id, "text": text, ...}` | Dictionary row | Dict fields become dynamic SQL columns when `content=True`. |
| `(id, {"text": text, "object": bytes}, tags)` | Text plus object storage | Requires `content=True` and `objects=True` or an object encoder. |

Dictionary rules:

- The indexed text field is `text` unless `columns={"text": "other_field"}` remaps it.
- The binary/object field is `object` unless column configuration remaps it.
- `id` and `tags` keys are extracted when present.
- Nested dictionaries can be queried with bracket syntax such as `[parent.child element]`.
- If top-level indexing is disabled for subindexes and a configured text field is missing, txtai may fall back to string ids for searchable text.

## Core Methods

| Method | Purpose | Key arguments | Return |
| --- | --- | --- | --- |
| `index(documents, reindex=False, checkpoint=None)` | Build a new index and overwrite existing indexed content | row iterable, optional checkpoint directory | `None` |
| `upsert(documents, checkpoint=None)` | Insert or update records without full rebuild when possible | row iterable, optional checkpoint | `None` |
| `delete(ids)` | Delete records by external ids | list of ids | list of deleted ids |
| `reindex(config=None, function=None, **kwargs)` | Rebuild vectors/index components from stored content | config overrides, optional stream transform | `None` |
| `search(query, limit=None, weights=None, index=None, parameters=None, graph=False)` | Natural language, SQL, or graph search | query, limit, hybrid weights, subindex, bind parameters, graph flag | list of tuples, dicts, or graph results |
| `batchsearch(queries, limit=None, weights=None, index=None, parameters=None, graph=False)` | Search multiple queries | query list, optional list of parameter dicts | list of result lists |
| `similarity(query, data)` | Compare one query with an in-memory candidate list | query, list of candidates | sorted `(candidate_index, score)` tuples |
| `batchsimilarity(queries, data)` | Compare multiple queries with in-memory candidates | query list, list of candidates | one sorted tuple list per query |
| `score(documents)` | Build scoring index for word-vector models | row iterable | `None` |
| `terms(query)` | Extract keyword terms from a query/SQL query | query string | keyword string |
| `count()` | Count indexed records | none | integer |
| `exists(path=None, cloud=None, **kwargs)` | Check if a saved index exists | path/cloud config | boolean |
| `save(path, cloud=None, **kwargs)` | Persist index to directory or archive | directory/archive path, optional cloud config | `None` |
| `load(path=None, cloud=None, config=None, **kwargs)` | Load saved index | path/cloud config, config overrides | `Embeddings` instance |
| `close()` | Free ANN/database/scoring/graph/subindex/model resources | none | `None` |

`Embeddings` is a context manager:

```python
with Embeddings(content=True) as embeddings:
    embeddings.index(rows)
    embeddings.save("index")

with Embeddings().load("index") as embeddings:
    results = embeddings.search("query", 5)
```

## Search Result Shapes

| Configuration/query | Result shape |
| --- | --- |
| No content storage | `[(id, score), ...]` |
| `content=True`, natural language query | list of dictionaries with stored columns and score fields |
| `content=True`, SQL query | list of dictionaries with selected SQL columns |
| `similarity(query, data)` | `[(candidate_index, score), ...]` |
| `batchsearch([...])` | `[[result, ...], [result, ...], ...]` |
| `search(..., graph=True)` with graph enabled | graph-filtered result objects or graph-backed rows depending on query |

The most common surprise is tuple-only results. If the user expects `result["text"]` or SQL fields, rebuild the index with `content=True` before indexing.

## SQL Search Parameters

SQL runs through `Embeddings.search`:

```python
results = embeddings.search(
    "select id, text, score from txtai where similar(:q, 25) and topic = :topic limit 5",
    parameters={"q": "feel good story", "topic": "human-interest"},
)
```

- `parameters` is a dictionary for `search` and a list of dictionaries for `batchsearch`.
- Use named bind placeholders such as `:q` and `:topic` for user text.
- `similar(query, candidates, index, weights)` can control candidate count, subindex name, and hybrid weights in SQL.
- The `search(..., weights=...)` argument controls hybrid weights for non-SQL search.
- The `search(..., index=...)` argument selects a subindex for non-SQL search.

## Optional Components

| Component | Trigger | Notes |
| --- | --- | --- |
| Dense ANN | `path`, `dense`, or defaults | Default backend is Faiss. Other ANN backends may need optional packages. |
| Content database | `content=True`, `content="duckdb"`, `content="client"`, or URL | Required for SQL, metadata, object storage, and `reindex` from stored content. |
| Sparse scoring | `keyword=True`, `sparse=True`, `hybrid=True`, or `scoring=...` | BM25/TF-IDF/SPLADE and sparse ANN behavior depends on config and extras. |
| Graph | `graph=True` or `graph={...}` | Default graph backend is NetworkX; RDBMS backend needs database packages/service. |
| Subindexes | `indexes={...}` | Each subindex is an embeddings database with its own config. |
| Query translation | `query={"path": ...}` | Uses a model to translate natural language filters into SQL; may download model weights. |
| Object storage | `objects=True`, `objects="image"`, `objects="pickle"` | Requires content storage; pickle is legacy/trusted-only behavior. |

## Save/Load Format Expectations

A saved index directory stores a configuration plus enabled components:

- ANN vectors under an embeddings component path.
- Content database under documents storage when `content=True`.
- Sparse scoring data under scoring storage when enabled.
- Graph data under graph storage when enabled.
- Subindexes under indexes storage when enabled.
- Id mappings only when content storage is disabled.

`save(path)` accepts directories and archive paths such as `.tar.gz`; cloud-backed save/load is advanced and requires cloud configuration. Always test load with `Embeddings().load(path)` after writing an index for deployment or handoff.

## Resource Safety

Read searches are thread-safe, but writes must be synchronized by the application. Avoid concurrent `index`, `upsert`, `delete`, `reindex`, or `save` calls against the same embeddings instance/path. Prefer context managers in scripts and services to close database connections, graph resources, scoring indexes, ANN resources, subindexes, and vector models.

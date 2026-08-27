---
name: embeddings-search
description: "Build, query, maintain, and troubleshoot txtai embeddings
  databases for semantic, SQL, hybrid, graph, object, and subindex search."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Embeddings Search

Use this sub-skill when the task is to build, update, persist, query, or debug a txtai `Embeddings` database. txtai search combines dense vector indexes, optional sparse scoring, optional graph storage, and optional relational content storage behind the `Embeddings` API.

## Use This For

- Building an index from raw text, `(id, data)`, `(id, data, tags)`, or dictionary rows.
- Choosing between tuple-only vector results and `content=True` dictionary/SQL results.
- Running semantic search, `similarity`, `batchsearch`, SQL `similar(...)`, bind parameters, filters, and aggregations.
- Maintaining indexes with `index`, `upsert`, `delete`, `reindex`, `save`, `load`, `exists`, `count`, and `close`.
- Storing metadata, dynamic columns, nested JSON, binary objects, custom SQL functions, and expressions.
- Configuring hybrid sparse+dense search, graph search, subindexes, ANN backends, and database backends.

## Route Elsewhere

- For RAG answers, LLM prompting, `RAG`, `LLM`, or `Agent` orchestration, use [agents-and-llm-orchestration](../agents-and-llm-orchestration/SKILL.md).
- For document extraction, chunking, pipeline preprocessing, or deterministic `Workflow` task chains, use [pipelines-and-workflows](../pipelines-and-workflows/SKILL.md).
- For serving an index through `Application`, FastAPI, OpenAI-compatible routes, or deployment config, use [api-and-deployment](../api-and-deployment/SKILL.md).

## Start Here

1. Read [references/api-reference.md](references/api-reference.md) for constructor options, method signatures, row formats, result shapes, and lifecycle calls.
2. Read [references/query-and-indexing.md](references/query-and-indexing.md) for concrete semantic, SQL, hybrid, graph, object, subindex, and save/load recipes.
3. Read [references/troubleshooting.md](references/troubleshooting.md) before changing configuration, optional backends, persistence paths, or SQL queries.
4. Run `python scripts/semantic_search_smoke.py --help` to see a safe helper adapted from txtai's similarity demo.
5. Run `python scripts/semantic_search_smoke.py --run --sql` for a local deterministic dry-run that avoids model downloads by using an explicit external vector transform.

## Core Decisions

- Use `Embeddings()` or `Embeddings(path="...")` for default dense semantic search when model downloads are acceptable.
- Use `Embeddings(method="external", transform=...)` or `Embeddings({"method": "external"})` when vectors are supplied by local code or precomputed arrays.
- Set `content=True` before indexing when the task needs stored text, metadata fields, SQL queries, object retrieval, or `reindex` from stored content.
- Leave content disabled only when tuple results `(id, score)` are enough and metadata retrieval is unnecessary.
- Use explicit ids for records that will later be updated or deleted; auto-generated ids require a prior search to discover target ids.
- Use `upsert` for incremental insert/update and `index` only when replacing the whole index is intended.
- Use `reindex` only after content storage exists; it rebuilds vectors/indexes from stored content and avoids returning to raw source rows.
- Use a context manager or call `close()` when database, graph, scoring, or ANN resources should be released promptly.

## Minimal Patterns

```python
from txtai import Embeddings

rows = [
    ("a", {"text": "Maine man wins lottery ticket", "topic": "lucky"}, None),
    ("b", {"text": "Canada ice shelf collapsed", "topic": "climate"}, None),
]

with Embeddings(content=True) as embeddings:
    embeddings.index(rows)
    print(embeddings.search("feel good story", 3))
    print(embeddings.search(
        "select id, text, score from txtai where similar(:q, 10) and topic = :topic",
        parameters={"q": "lucky", "topic": "lucky"},
    ))
```

```python
# Tuple-only result mode: no SQL, no stored metadata.
embeddings = Embeddings()
embeddings.index(["Correct", "Not what we hoped"])
assert embeddings.search("positive", 1)[0][0] == 0
```

## Common Workflows

- **Quick semantic search**: create `Embeddings(path=...)`, call `index(rows)`, then `search(query, limit)` or `similarity(query, candidates)`.
- **Metadata filters**: create `Embeddings(content=True)`, index dictionaries with a `text` field plus metadata, and query with SQL filters.
- **SQL candidate tuning**: use `similar('query', candidates)` with a candidate count larger than the final `limit` when filters may discard matches.
- **Safe bind parameters**: pass `parameters={...}` for `similar(:q)` and field filters like `topic = :topic` instead of interpolating user text.
- **Object storage**: create `Embeddings(content=True, objects=True)` and index dictionaries with `text` plus `object` bytes or encoder-backed objects.
- **Hybrid search**: use `hybrid=True`, `keyword=True`, or `sparse=...` when sparse keyword/vector evidence should combine with dense search.
- **Graph search**: use `graph=True` or a graph config, then run graph-enabled searches or openCypher-style graph queries.
- **Subindexes**: use `defaults=False` and `indexes={...}` when different fields, models, or sparse/dense strategies need separate named indexes.
- **Persistence**: call `save(path)` after building and `Embeddings().load(path)` before querying; compressed and cloud-backed saves are advanced variants.

## Result Shapes

- Without content storage, `search` returns `[(id, score), ...]` and ids map to input ids or generated ids.
- With content storage, `search` returns dictionaries keyed by selected SQL/query columns, usually including `id`, `text`, `score`, and metadata.
- `similarity(query, data)` always compares a query against an in-memory candidate list and returns sorted `(candidate_index, score)` tuples.
- `batchsearch` returns one result list per query and accepts per-query parameter dictionaries.
- Graph searches may return graph objects or graph-backed query rows depending on query and `graph=True`.

## Validation Checklist

- Import check: `python - <<'PY'\nfrom txtai import Embeddings\nprint(Embeddings)\nPY`
- Script check: `python scripts/semantic_search_smoke.py --help`.
- No-download dry-run: `python scripts/semantic_search_smoke.py --run --sql`.
- For SQL tasks, assert the embeddings object was created with `content=True` before `index` or `upsert`.
- For save/load tasks, assert the saved path contains a txtai config and component directories or load via `Embeddings().exists(path)`.

## Troubleshooting First Questions

- Is `content=True` enabled before indexing, not after?
- Are ids stable and explicit for later `upsert` or `delete` calls?
- Is the query natural language, SQL, or graph syntax, and does the configured index support that mode?
- Are optional ANN, database, graph, sparse, or vector backend packages installed for the selected config?
- Is a model path local/available, or will the environment need network/cache access to download it?
- Are SQL `similar(...)` candidate counts high enough for downstream filters?
- Are hybrid weights and sparse/dense score normalization intentionally configured?
- Was `close()` called or a context manager used when long-lived resources are no longer needed?

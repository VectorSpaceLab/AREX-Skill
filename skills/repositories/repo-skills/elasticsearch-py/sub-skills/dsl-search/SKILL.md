---
name: dsl-search
description: "Guide elasticsearch.dsl query and search composition, mappings,
  typed Documents, aggregations, pagination, persistence, and sync/async DSL
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DSL and search

Use this route when a task asks for `Q`, `Search`, aggregations, filters,
mappings, `Document`, `Index`, `FacetedSearch`, or a high-level query that
should be rendered to the Elasticsearch request body. Use
[client-operations](../client-operations/SKILL.md) for client/auth setup and
[helpers-ingest](../helpers-ingest/SKILL.md) for bulk/scan/reindex.

## Fast route

1. Build a `Q` object for reusable query fragments, combining with `&` (AND),
   `|` (OR), and `~` (NOT). Use `.to_dict()` before sending when debugging.
2. Build an immutable-style `Search(index=...)` and chain `.query(...)`,
   `.filter(...)`, `.exclude(...)`, `.sort(...)`, `.source(...)`, `.extra(...)`,
   `.params(...)`, `.aggs.bucket(...)`, or `.execute()`.
3. Define `Document`/`InnerDoc` classes and `Field` objects when the mapping,
   validation, persistence, and typed result behavior are worth the extra
   structure. Create the index/mapping before saving documents.
4. Use async counterparts with `AsyncElasticsearch`; await execution and close
   the client. Render queries offline before any cluster call.

Read [api-reference.md](references/api-reference.md) for the public object model,
[workflows.md](references/workflows.md) for compositional recipes,
[data-and-mapping.md](references/data-and-mapping.md) for mappings and typed
documents, and [troubleshooting.md](references/troubleshooting.md) for
validation, response, and version failures. Run
[scripts/dsl_query_smoke.py](scripts/dsl_query_smoke.py) for an offline check.

## Offline-first example

```python
from elasticsearch.dsl import Q, Search

query = Q("bool", must=[Q("match", title="python")], filter=[Q("term", status="published")])
request = Search(index="books").query(query).sort("_score").source(["title"])
assert request.to_dict()["query"]["bool"]["must"][0] == {"match": {"title": "python"}}
# response = request.execute()  # requires a configured live cluster
```

The DSL is a request builder, not a server-side validator. A rendered request
can still fail because the index mapping, Elasticsearch version, privileges,
or query feature is incompatible.

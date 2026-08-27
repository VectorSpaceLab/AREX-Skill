---
name: esql-query-builder
description: "Guide the Elasticsearch Python ES|QL builder, safe parameterized
  queries, sync/async execution, functions, and tabular response conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ES|QL query builder

Use this route for ES|QL source/processing commands, Python expressions,
parameterized user input, `client.esql.query()`, or ES|QL table results. The
builder is technical preview at this source snapshot; check the target client
and server versions before relying on it.

## Fast route

1. Build a source with `ESQL.from_(...)`, `ESQL.row(...)`, `ESQL.show("INFO")`,
   `ESQL.ts(...)`, or `ESQL.branch()`.
2. Chain processing commands such as `.where(...)`, `.keep(...)`, `.eval(...)`,
   `.sort(...)`, `.stats(...)`, `.limit(...)`, `.metadata(...)`, and other
   methods on the returned `ESQLBase` object.
3. Render with `str(query)` or `query.render()` and review the result offline.
4. Pass the builder to `client.esql.query(query=query, params=[...])`; await the
   call for `AsyncElasticsearch`. Keep untrusted values in `params`, not in
   concatenated query strings.

Read [api-reference.md](references/api-reference.md) for sources, expressions,
and execution parameters; [workflows.md](references/workflows.md) for safe
recipes; [pandas-integration.md](references/pandas-integration.md) for tabular
conversion; and [troubleshooting.md](references/troubleshooting.md) for preview,
syntax, optional-dependency, and response issues. Run
[scripts/esql_query_smoke.py](scripts/esql_query_smoke.py) for offline checks.

## Offline example

```python
from elasticsearch.esql import E, ESQL

query = (
    ESQL.from_("employees")
    .keep("first_name", "last_name")
    .where(E("first_name") == E("?"))
    .limit(10)
)
print(query.render())
# client.esql.query(query=query, params=[name])  # requires a live cluster
```

Do not treat rendering as server validation. Check index names, privileges,
ES|QL feature availability, response columns/values, and server version when
executing.

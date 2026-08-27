# ES|QL builder API reference

`ESQL` is a static namespace, not an instance constructor. The verified source
methods include:

- `ESQL.from_(*indices)` → a `From` source.
- `ESQL.row(**params)` → a `Row` source.
- `ESQL.show(item)` → a `Show` source such as `"INFO"`.
- `ESQL.ts(*indices)` → a time-series source.
- `ESQL.branch()` → a branch for `FORK`.

Sources return `ESQLBase` objects. They can be printed or rendered with
`.render()`, and support processing commands including `.where()`, `.keep()`,
`.drop()`, `.eval()`, `.sort()`, `.limit()`, `.stats()`, `.inline_stats()`,
`.rename()`, `.mv_expand()`, `.enrich()`, `.grok()`, `.dissect()`, `.fork()`,
`.join()`, `.lookup_join()`, `.fuse()`, and additional methods exposed by the
installed class. Check `inspect.signature()` for a less common method before
using it.

Expressions can be strings or Python expression objects. Use `E("field")` from
`elasticsearch.esql` to create a field expression and use operators/functions
from `elasticsearch.esql.functions`. Wrap field names, expressions, and
placeholders with `E()` when they should not be treated as string literals.

Execution uses the generated API:

```python
response = client.esql.query(query=query, params=[untrusted_value])
response.body["columns"]
response.body["values"]
```

The async form is `await async_client.esql.query(...)`. Response bodies contain
column descriptors, row values, `is_partial`, and timing metadata when returned
by the server. Validate presence and types instead of assuming a fixed schema.

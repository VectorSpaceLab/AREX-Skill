# ES|QL troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `TypeError: ESQL() takes no arguments` | `ESQL` is a static namespace, not a query instance | Use `ESQL.from_(...)`, `ESQL.row(...)`, `ESQL.show(...)`, `ESQL.ts(...)`, or `ESQL.branch()`. |
| Query renders but server rejects it | Syntax/feature/version/mapping problem | Inspect `query.render()`, reduce to a minimal source, and compare with the target server's ES|QL support. |
| User value changes query structure | Untrusted value was interpolated into a string | Use `E("?")` and pass values in `params=[...]`; validate identifiers separately. |
| Field treated as a literal | A field/expression was passed as a normal string in a Python expression wrapper | Use `E("field")` or the appropriate `functions` wrapper. |
| Missing columns/values | Server returned a partial/error response or a command changed the schema | Inspect `response.body`, `columns`, `values`, and `is_partial` before conversion. |
| Async query is not awaited | Sync client or sync call used in async code | Use `AsyncElasticsearch` and `await client.esql.query(...)`; close the client. |
| DataFrame/Arrow conversion import fails | Optional `pyarrow` or Pandas dependency is absent | Install the selected optional dependency or return raw rows/list-of-records fallback. |
| `ValueError` for index/identifier | Invalid or unsafe identifier, wildcard, or reserved syntax | Use valid ES|QL identifiers and an allow-list; do not accept arbitrary user syntax. |
| Function output is wrong | Field was passed as a literal or function expects a typed expression | Wrap fields with `E()` and inspect the rendered function call. |

The builder is technical preview at this snapshot. Pin and test client/server
versions together for production use.

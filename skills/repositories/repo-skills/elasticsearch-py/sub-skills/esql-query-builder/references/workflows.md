# ES|QL workflows

## Build and review a query

```python
from elasticsearch.esql import E, ESQL, functions

query = (
    ESQL.from_("employees")
    .sort("emp_no")
    .keep("first_name", "last_name", "height")
    .eval(
        height_feet=E("height") * 3.281,
        height_cm=E("height") * 100,
    )
    .where(functions.length(E("first_name")) < 20)
    .limit(10)
)
print(query.render())
```

Review the rendered source/processing pipeline before execution. Use strings
when the expression is already trusted ES|QL syntax; use `E()` and function
wrappers when Python composition and correct literal/field distinction matter.

## Parameterize untrusted values

```python
query = (
    ESQL.from_("employees")
    .keep("first_name", "last_name")
    .where(E("first_name") == E("?"))
)
response = client.esql.query(query=query, params=[name_from_user])
```

Parameters are assigned in order to `?` placeholders. Do not interpolate
untrusted names or values into a query string. Validate index/field identifiers
against an allow-list as well; parameters are for values, not arbitrary query
syntax.

## Execute and inspect

For synchronous code call `client.esql.query(...)`; for async code await the
same endpoint. Inspect `response.body["columns"]` and
`response.body["values"]`, and handle `is_partial` explicitly. Convert rows to
records only after matching each value position to its column descriptor.

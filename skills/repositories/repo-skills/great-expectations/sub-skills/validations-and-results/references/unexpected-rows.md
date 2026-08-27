# Unexpected Rows

Unexpected-row workflows answer “which records failed?” They are useful for debugging and remediation, but they can be expensive or unsupported depending on expectation type and execution backend.

## Three different diagnostics

1. Partial unexpected samples in `evr.result`, controlled by result format and `partial_unexpected_count`.
2. Inline row payloads through `include_unexpected_rows`, supported for selected expectations/backends.
3. Full failing-row retrieval through `ValidationDefinition.get_unexpected_rows(...)`, supported only for `UnexpectedRowsExpectation`.

Do not treat these as interchangeable. Start with small samples, then escalate to full row retrieval only when the user needs it and the backend supports it.

## Partial unexpected samples

For many column expectations, `BASIC`, `SUMMARY`, and `COMPLETE` may include fields such as:

- `unexpected_count`
- `unexpected_percent`
- `partial_unexpected_list`
- `partial_unexpected_counts`
- `unexpected_list` in more verbose formats for some expectations

Example:

```python
result = validation_definition.run(
    result_format={"result_format": "SUMMARY", "partial_unexpected_count": 10}
)
for evr in result.results:
    if not evr.success:
        print(evr.result.get("partial_unexpected_list"))
```

A partial sample is not “all failures.” If the user asks for all failing rows, avoid answering from `partial_unexpected_list` alone.

## `include_unexpected_rows`

Some expectations can include failing rows directly in `evr.result["unexpected_rows"]`:

```python
result = validation_definition.run(
    result_format={"result_format": "BASIC", "include_unexpected_rows": True}
)
for evr in result.results:
    rows = evr.result.get("unexpected_rows")
    if rows is not None:
        print(rows)
```

Observed backend shapes differ:

- Pandas workflows may return a pandas `DataFrame` for `unexpected_rows`.
- SQL workflows may return a list-like row payload.
- Other backends or expectation types may not include the field even when requested.

Use this for small, local debugging. Do not enable it by default for production-sized data.

## Unexpected index query

`return_unexpected_index_query` asks GX for a backend-specific expression/query to identify failing rows:

```python
result = validation_definition.run(
    result_format={
        "result_format": "BASIC",
        "return_unexpected_index_query": True,
        "unexpected_index_column_names": ["id"],
        "partial_unexpected_count": 0,
    }
)
for evr in result.results:
    print(evr.result.get("unexpected_index_query"))
```

Examples of backend behavior:

- SQL engines can return a SQL query or where-clause-like query with compiled parameter values.
- Pandas can return an expression such as a dataframe filter over failing indexes.
- `BOOLEAN_ONLY` can still include an index query when explicitly requested, but otherwise returns minimal result details.
- `return_unexpected_index_query=False` suppresses the query when the expectation/backend would otherwise provide one.

Use `unexpected_index_column_names` to request stable identifiers instead of row positions when the backend supports it.

## Retrieve all unexpected rows for `UnexpectedRowsExpectation`

`ValidationDefinition.get_unexpected_rows()` is a separate API for `UnexpectedRowsExpectation`, not a generic API for every failed expectation.

```python
from great_expectations.expectations import UnexpectedRowsExpectation

result = validation_definition.run()
for evr in result.results:
    if not evr.success and isinstance(evr.expectation, UnexpectedRowsExpectation):
        rows = validation_definition.get_unexpected_rows(
            evr.expectation,
            batch_parameters=result.batch_parameters,
        )
        print(f"{len(rows)} unexpected rows found")
```

Important constraints:

- The expectation must be an `UnexpectedRowsExpectation`; other expectation types raise `ValueError`.
- The expectation must define an `unexpected_rows_query` string or a `$PARAMETER` reference resolving to a string.
- If the query uses suite parameters, pass matching `expectation_parameters` to `get_unexpected_rows()`.
- If the validation used partitioned batch parameters, pass `result.batch_parameters` or the same batch parameters to retrieve rows from the same batch.
- Metric computation failures can raise `RuntimeError` with the backend exception message.

## Suite-parameterized unexpected-row query

When an `UnexpectedRowsExpectation` stores its query as a suite parameter reference, pass the same expectation parameters during validation and retrieval:

```python
params = {"unexpected_query": "SELECT * FROM {batch} WHERE amount < 0"}
result = validation_definition.run(expectation_parameters=params)
rows = validation_definition.get_unexpected_rows(
    failing_evr.expectation,
    batch_parameters=result.batch_parameters,
    expectation_parameters=params,
)
```

If the parameter is missing or does not resolve to a string, GX raises an error rather than guessing.

## Caps and performance cautions

- Partial unexpected samples are capped by `partial_unexpected_count`; they are intentionally incomplete.
- Some docs and examples mention a default unexpected-row sample cap, commonly 200 rows, for row diagnostics. Use explicit retrieval/query workflows when the user needs all rows.
- `get_unexpected_rows(..., fetch_all=True)` behavior is internal to GX’s metric query path for `UnexpectedRowsExpectation`; the public method returns a list of dicts.
- `COMPLETE` may produce very large in-memory payloads. Prefer `return_unexpected_index_query` or a dedicated bounded query for large datasets.
- Always warn users before retrieving all failing rows from a remote warehouse or large table.

## Choosing a workflow

- Need only pass/fail: `BOOLEAN_ONLY`.
- Need failure counts and a sample: `SUMMARY` or `BASIC` with `partial_unexpected_count`.
- Need a reproducible pointer to failing rows: result-format dict with `return_unexpected_index_query=True` and stable index columns.
- Need all rows from a custom SQL-like unexpected condition: `UnexpectedRowsExpectation` plus `validation_definition.get_unexpected_rows(...)`.
- Need all rows for a built-in column expectation: prefer backend-specific index query or rerun a bounded source query; do not claim `get_unexpected_rows()` supports all built-ins.

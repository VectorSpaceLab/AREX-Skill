# Tabular conversion and optional dependencies

The ES|QL endpoint returns columns and row values. A stable conversion pattern is:

```python
body = response.body
names = [column["name"] for column in body["columns"]]
records = [dict(zip(names, row, strict=True)) for row in body["values"]]
```

Use the package's documented ES|QL/Pandas helpers when the application needs a
DataFrame or Arrow table, and install the corresponding optional extra only for
that workflow. `pyarrow` is an optional package extra; Pandas workflows may also
need `pandas` in the application environment. Keep an explicit list of columns
and preserve nulls/types rather than coercing every value to strings.

When `pyarrow`/Pandas is unavailable, return the raw `columns`/`values` body or
convert to a list of records. Report missing optional dependencies as an
installation choice, not as a query or cluster failure. Always check
`is_partial` before treating the table as complete.

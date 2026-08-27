# PandasAI Response Formats

## Purpose

Use this when validating generated code or handling `.chat()` results. PandasAI
expects generated code to assign a `result` dictionary. The parser turns that
dictionary into response objects.

## Required generated-code shape

Generated code should end with:

```python
result = {"type": "number", "value": 42}
```

The code path also expects data access through:

```python
df = execute_sql_query("SELECT ...")
```

A result without `execute_sql_query` is rejected by the code requirement
validator in this package version.

## Accepted result types

| `result["type"]` | Valid `value` shape | Response class | Notes |
| --- | --- | --- | --- |
| `number` | `int`, `float`, or NumPy integer | `NumberResponse` | Numeric formatting works through Python formatting. |
| `string` | `str` | `StringResponse` | Good for explanations and short textual answers. |
| `dataframe` | pandas DataFrame, Series, or dict | `DataFrameResponse` | Dict values are converted to pandas DataFrames. |
| `plot` | filesystem path string, base64 image URI, or chart dict | `ChartResponse` | The response object's public `type` is `chart`. |
| invalid/unknown | anything else | error during parse | Use troubleshooting guidance. |

`ErrorResponse` is returned by exception handling paths and exposes `type =
"error"`, a user-facing `value`, `last_code_executed`, and the raw `error` text
when available.

## Handling charts safely

```python
response = df.chat("Plot revenue by month")
if response.type == "chart":
    response.save("revenue_by_month.png")
```

Avoid relying on `print(response)` for charts because the chart response string
conversion calls image display behavior.

## Inspecting generated code

```python
response = df.chat("What is the average revenue?")
print(response.last_code_executed)
```

Use generated-code inspection when debugging wrong answers, unsafe table names,
wrong response types, or retry behavior. For local/semantic dataframes,
generated SQL table names should match the dataframe schema names.

## Output type hints

`Agent.chat` and `Agent.follow_up` accept `output_type`. Typical hints are
`number`, `dataframe`, `plot`, or `string`. A hint does not replace validation:
the generated code still must produce a compatible `result` value.

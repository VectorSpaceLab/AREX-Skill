# Result Formats and Outputs

GX validation results are Python objects that serialize to dictionaries. Use object attributes for normal control flow and `to_json_dict()` or `describe()` for JSON-like output.

## Result objects

`ValidationDefinition.run()` returns `ExpectationSuiteValidationResult` with these practical fields:

- `success`: `True` only when all evaluated expectations pass.
- `statistics`: aggregate counts such as `evaluated_expectations`, `successful_expectations`, `unsuccessful_expectations`, and `success_percent`.
- `results`: list of `ExpectationValidationResult` objects, one per evaluated expectation.
- `suite_name`: suite name used for the run.
- `suite_parameters`: suite parameters used to produce the result, when present.
- `meta`: validation metadata including GX version, batch metadata, `validation_id`, `checkpoint_id`, `run_id`, `validation_time`, and `batch_parameters`.
- `batch_id`: identifier for the active batch when available.
- `result_url`: Cloud or rendered result URL when a configured backend provides one.

Each `ExpectationValidationResult` contains:

- `success`: expectation-level pass/fail.
- `expectation_config`: expectation type and kwargs that were evaluated.
- `result`: diagnostic details controlled by result format and expectation type.
- `meta`: expectation-level metadata.
- `exception_info`: `raised_exception`, `exception_traceback`, and `exception_message`.
- `rendered_content`: populated only in contexts that render inline content, such as Cloud usage.

Useful methods:

```python
print(result.describe())
failed = result.get_failed_validation_results()
print(result.get_metric("statistics.unsuccessful_expectations"))
for evr in result.results:
    print(evr.describe_dict())
```

## Result format levels

GX exposes `gx.ResultFormat` with `BOOLEAN_ONLY`, `BASIC`, `SUMMARY`, and `COMPLETE`. Equivalent strings may also be accepted; enum values are less typo-prone.

| Format | Use when | Typical output |
| --- | --- | --- |
| `BOOLEAN_ONLY` | You only need pass/fail or are validating very large data. | Minimal `result`; by default no unexpected counts or samples. |
| `BASIC` | You need counts and simple diagnostics for failures. | Common fields such as `element_count`, `unexpected_count`, `unexpected_percent`, and a partial unexpected sample when supported. |
| `SUMMARY` | You need broader failure summaries without full row-level payloads. This is the default for validation definitions. | BASIC-like diagnostics plus summary lists/counts for many expectations. |
| `COMPLETE` | You need detailed diagnostics for debugging a small or bounded batch. | Most available diagnostic fields, including complete unexpected lists for many expectation types. |

Prefer the least verbose format that answers the task. `COMPLETE` can be expensive in memory, slow on remote engines, and noisy to serialize.

## Result format dictionaries

Use a dict when you need optional output controls:

```python
result_format = {
    "result_format": "BASIC",
    "partial_unexpected_count": 20,
    "include_unexpected_rows": False,
    "return_unexpected_index_query": True,
    "unexpected_index_column_names": ["id"],
}
result = validation_definition.run(result_format=result_format)
```

Common keys:

- `result_format`: one of `BOOLEAN_ONLY`, `BASIC`, `SUMMARY`, or `COMPLETE`.
- `partial_unexpected_count`: max number of unexpected values in partial samples. Use `0` to suppress partial samples when supported.
- `include_unexpected_rows`: asks GX to include failing rows for supported expectations/backends; avoid on large data.
- `return_unexpected_index_query`: asks GX to include an engine-specific query or expression for unexpected row indexes when supported.
- `unexpected_index_column_names`: columns to identify unexpected rows in SQL-style index queries when supported.

Support for optional keys is expectation- and backend-dependent. If a key is missing from `evr.result`, treat it as unavailable for that expectation/backend rather than assuming a validation failure.

## Interpreting aggregate results

Typical control flow:

```python
result = validation_definition.run(result_format=gx.ResultFormat.SUMMARY)
if result.success:
    print("validation passed")
else:
    print(result.statistics)
    for evr in result.results:
        if not evr.success:
            print(evr.expectation_config.type)
            print(evr.result)
            print(evr.exception_info)
```

`result.statistics` is the best quick summary for dashboards and branching. `result.results` is where expectation-specific details live.

A suite result can fail because expectations returned `success=False`, or because an expectation raised while `catch_exceptions=True` caused exception details to be captured. Check `evr.exception_info` on failures before assuming the data itself violated the rule.

## Exception information

Expectation classes have a `catch_exceptions` setting. When `catch_exceptions=True`, GX can return failed expectation results with `exception_info` populated instead of immediately raising the original error. When `catch_exceptions=False`, errors may propagate to the caller.

Diagnosis pattern:

```python
for evr in result.results:
    info = evr.exception_info or {}
    if info.get("raised_exception"):
        print(info.get("exception_message"))
```

Use exception info to distinguish invalid expectation configuration, unresolved suite parameters, missing columns, and backend metric failures from genuine data-quality failures.

## Serialization and logging

- Use `result.describe()` for a compact JSON string with success, statistics, expectation descriptions, and result URL.
- Use `result.to_json_dict()` for structured serialization.
- Avoid logging full `COMPLETE` results from production-sized batches.
- Redact or omit user data from row-level diagnostics before sharing outside the user’s environment.

## Performance guidance

- Default to `SUMMARY` for validation definitions unless the user asks for smaller or larger output.
- Use `BOOLEAN_ONLY` for high-volume routine checks where only pass/fail matters.
- Use `BASIC` for normal debugging and CI-style logs.
- Use `COMPLETE` only on small batches, bounded test fixtures, or after filtering to a narrow failing subset.
- Prefer `partial_unexpected_count` and index/query diagnostics over embedding all failing rows.

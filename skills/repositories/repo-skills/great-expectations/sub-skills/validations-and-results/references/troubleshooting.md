# Troubleshooting Validations and Results

Use this guide when validation execution fails, produces surprising output, or returns too much or too little diagnostic detail.

## Stale or missing validation references

Symptoms:

- `context.validation_definitions.get(name)` cannot find a validation.
- Running a validation reports missing suite, datasource, asset, or batch definition.
- A validation runs against an older suite or batch definition after resources were renamed or recreated.

Checks:

```python
validation = context.validation_definitions.get("my_validation")
print(validation.is_fresh())
print(validation.suite.name)
print(validation.batch_definition.name)
print(validation.asset.name)
print(validation.data_source.name)
```

Fixes:

- Re-retrieve the suite and batch definition from the current context.
- Recreate the `gx.ValidationDefinition` with current objects.
- Use `context.validation_definitions.add_or_update(validation)` intentionally when replacing the stored definition.
- If only the existing definition was modified in memory, call `validation.save()`.

## Missing batch parameters

Symptoms:

- Validation fails before expectations evaluate.
- Error mentions missing identifiers, no matching batch, or a batch request that cannot be built.
- A validation used to work but now fails after a path regex or partitioner changed.

Checks:

- Inspect how the batch definition was created: whole dataframe/table, path, yearly, monthly, daily, or custom regex.
- Ensure `batch_parameters` keys match the batch definition exactly.
- For regex partitioners, named capture groups determine expected keys.
- For dataframe assets, include `{"dataframe": dataframe}` unless the batch definition already fixes the data.

Examples:

```python
validation.run(batch_parameters={"year": "2026"})
validation.run(batch_parameters={"year": "2026", "month": "06"})
validation.run(batch_parameters={"dataframe": df})
```

If a filesystem asset regex changed from `(?P<year>\d{4})` to `(?P<year>\d{4})-(?P<month>\d{2})`, update validation calls to include `month` and consider recreating stale validation definitions.

## Unresolved suite parameters

Symptoms:

- Validation fails while processing expectation configs.
- Error references suite parameters, `$PARAMETER`, missing values, or invalid types.
- Expectation kwargs still contain unresolved dicts instead of concrete values.

Checks:

- Identify every `$PARAMETER` reference in the suite.
- Pass values through `expectation_parameters`, not `batch_parameters`.
- Use the expected runtime types, such as numbers for thresholds and strings for query text.

Example:

```python
validation.run(expectation_parameters={"min_amount": 0, "mostly_threshold": 0.98})
```

For `UnexpectedRowsExpectation.unexpected_rows_query` stored as a suite parameter, pass the same `expectation_parameters` to both `run()` and `get_unexpected_rows()`.

## Unexpected row cap confusion

Symptoms:

- User asks for all failing rows, but result only shows a sample.
- `partial_unexpected_list` has fewer entries than `unexpected_count`.
- `unexpected_rows` is absent despite requested result verbosity.

Checks and fixes:

- Treat `partial_unexpected_list` as a sample controlled by `partial_unexpected_count`.
- Use `include_unexpected_rows=True` only for supported expectations/backends and small data.
- Use `return_unexpected_index_query=True` to get an engine-specific pointer to failures.
- Use `ValidationDefinition.get_unexpected_rows()` only for `UnexpectedRowsExpectation`.
- Warn that backend support varies; missing fields can mean unsupported output, not success.

## Large `COMPLETE` results

Symptoms:

- Validation is slow, memory-heavy, or logs huge payloads.
- Serialized results are too large for CI, notebooks, or chat output.
- Output includes row-level data the user did not need.

Fixes:

- Use `gx.ResultFormat.BOOLEAN_ONLY` for pass/fail.
- Use `gx.ResultFormat.BASIC` or `SUMMARY` for normal debugging.
- Use `partial_unexpected_count` to cap samples.
- Prefer `return_unexpected_index_query` over embedding rows.
- Run `COMPLETE` only on small fixtures or filtered batches.

## `catch_exceptions` hides the original failure

Symptoms:

- Validation returns failed expectation results rather than raising.
- Data looks correct, but one result has `raised_exception=True`.
- Missing columns, bad metric config, or backend errors appear inside result payloads.

Checks:

```python
for evr in result.results:
    info = evr.exception_info or {}
    if info.get("raised_exception"):
        print(evr.expectation_config.type)
        print(info.get("exception_message"))
```

Fixes:

- Inspect `exception_info` before diagnosing the data.
- Check expectation constructor defaults; some expectations default `catch_exceptions=True`, while others may default to `False`.
- Set `catch_exceptions=False` while debugging if surfacing the original exception is more useful.

## Result format misuse

Symptoms:

- `BOOLEAN_ONLY` lacks `unexpected_count` or samples.
- `BASIC` lacks `unexpected_index_query`.
- Optional keys in a result-format dict appear ignored.
- Code assumes every `evr.result` has the same shape.

Fixes:

- Use `SUMMARY` or `BASIC` for counts and partial diagnostics.
- Explicitly request optional fields in a result-format dict.
- Check keys with `.get(...)` and handle missing fields gracefully.
- Remember that output fields depend on expectation type, result format, and backend.

## Validation succeeds but details look wrong

Checks:

- Confirm the validation uses the intended suite name and batch definition.
- Print `result.meta.get("batch_parameters")` to confirm the selected batch.
- Inspect `result.meta.get("active_batch_definition")` and `result.meta.get("batch_spec")` for backend selection metadata.
- Confirm suite parameters supplied to `run()` match the values expected by parameterized expectations.
- If a checkpoint ran the validation, route to `../checkpoints-actions-and-data-docs/SKILL.md` to inspect checkpoint-level result format and actions.

# Troubleshooting Expectations and Suites

## Unknown Expectation Names

Symptoms:

- `ExpectationNotFoundError` for a snake_case name.
- A suite fails to load after adding a custom expectation.
- `get_expectation_impl(...)` cannot resolve an expectation type.

Checks:

- Prefer class imports from `gx.expectations`, for example `gx.expectations.ExpectColumnValuesToBeInSet`.
- Confirm the serialized snake_case name matches the class, such as `ExpectColumnValuesToBeInSet` -> `expect_column_values_to_be_in_set`.
- Import the module that defines a custom expectation before loading or validating suites that reference it.
- Do not assume old gallery names or legacy method names still exist; inspect `dir(gx.expectations)` or use the registry in the active environment.

## Pydantic Validation Errors

Symptoms:

- Constructor raises a pydantic validation error.
- Error mentions a missing field such as `column`, `value_set`, `min_value`, or `max_value`.
- Error mentions `mostly`, enum values, or condition type.

Checks:

- Provide all required domain fields: column expectations need `column`; column-pair expectations need `column_A` and `column_B`; multicolumn expectations need `column_list`; table expectations have class-specific fields.
- Keep `mostly` in the inclusive range `[0, 1]`, unless it is a valid `$PARAMETER` dict resolved at validation time.
- Use `severity="critical"`, `"warning"`, or `"info"` only.
- Keep `meta` JSON-serializable.
- For result format dictionaries, include `result_format` when using options such as `include_unexpected_rows`.

## Missing Columns or Parameters

Symptoms:

- Validation fails because a column is missing from the batch.
- `SuiteParameterError` says no value was found for `$PARAMETER`.
- Validation succeeds in exploration but fails in checkpoint/production runs.

Checks:

- Validate the suite against a batch from the same asset/batch definition shape that production uses.
- Confirm exact column names and case sensitivity in the dataframe/table.
- Print or inspect `suite.suite_parameter_options` and supply every key in `expectation_parameters`.
- Use unique parameter keys per expectation, not generic keys that collide across fields.
- Route batch parameter selection and stale batch-definition issues to `../datasources-and-assets/SKILL.md` or `../validations-and-results/SKILL.md`.

## Invalid `mostly`

Symptoms:

- Constructor rejects `mostly=-0.5` or `mostly=1.5`.
- Fuzzy validation behaves differently than expected.

Checks:

- `mostly` is the minimum success ratio and must be between `0` and `1`; `0.95` means at least 95% of evaluated rows must pass.
- Missing values may be counted separately from unexpected values depending on the expectation; inspect the validation result for `missing_count`, `unexpected_count`, and percentages.
- If `mostly` is parameterized, the runtime value must still resolve to a number in range.

## Row Condition Parser Mismatch

Symptoms:

- Condition works on pandas but not Spark/SQL.
- Error mentions nested OR, OR inside AND, too many conditions, or invalid parameter type.
- String condition parser raises syntax errors.

Checks:

- Prefer object conditions with `Column("field")` and Python operators.
- Rewrite `A & (B | C)` as `(A & B) | (A & C)` because OR inside AND is rejected.
- Avoid nested OR groups; keep each OR branch as a single condition or an AND block.
- Use `Column("x").is_null()` or `.is_not_null()` instead of comparing to `None`.
- For `is_in` and `is_not_in`, pass a list/tuple/set, not a string; keep element types consistent.
- If maintaining legacy strings, match `condition_parser` to the string syntax: `"great_expectations"` for `col("x")` syntax, `"pandas"` for pandas query strings, and `"spark"` for Spark filters.

## Suite Persistence and Save Errors

Symptoms:

- `expectation.save()` fails or does not update the suite.
- Adding an expectation raises because it already belongs to a suite.
- Duplicate expectations are not added.

Checks:

- Call `context.suites.add(suite)` or `context.suites.add_or_update(suite)` before relying on `expectation.save()` callbacks.
- Use `suite.add_expectation(...)` with fresh expectation instances. If copying from another suite, use `copy.copy(expectation)` and clear `id` when necessary.
- GX treats suites as set-like; type and parameter-equivalent expectations are considered duplicates even when `meta` or `notes` differ.
- Use `context.suites.get(name=...)`, `context.suites.all()`, and `context.suites.delete(name=...)` for store CRUD rather than editing store files directly.

## Custom Expectation Registration and Serialization

Symptoms:

- Custom subclass validates in the notebook but fails in another process.
- Saved suite references a custom snake_case type that cannot be found.
- Serialization fails for custom defaults.

Checks:

- Define custom classes in importable Python modules and import them before suite loading/validation.
- Keep class defaults compatible with the parent expectation's pydantic fields.
- Avoid non-serializable defaults such as functions, open file handles, dataframes, or local objects.
- Test a fresh process that imports the custom class, loads the suite, and validates a tiny batch.
- If custom logic would require new metrics, add diagnostics and backend-specific tests; otherwise subclass a built-in expectation instead.

## Result Format Confusion

Symptoms:

- Validation returns too little detail for debugging.
- Validation returns very large result payloads.
- Unexpected rows are missing from a result.

Checks:

- Use `result_format="BASIC"` or `"SUMMARY"` while drafting suites.
- Use `"COMPLETE"` only for focused debugging and small batches.
- For full unexpected-row retrieval or backend-specific unexpected row queries, route to `../validations-and-results/SKILL.md`.

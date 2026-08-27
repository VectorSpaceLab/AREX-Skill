# Expectation API Patterns

GX Core in this checkout uses a class-first expectation API. Prefer importing classes from `great_expectations.expectations` through the top-level package alias:

```python
import great_expectations as gx

gxe = gx.expectations
expectation = gxe.ExpectColumnValuesToBeBetween(
    column="fare",
    min_value=0,
    max_value=500,
    mostly=0.98,
    severity="warning",
)
```

## Built-In Discovery

- Built-ins are exported from `gx.expectations`; representative classes include `ExpectColumnValuesToNotBeNull`, `ExpectColumnValuesToBeBetween`, `ExpectColumnValuesToBeInSet`, `ExpectColumnValuesToMatchRegex`, `ExpectColumnValuesToBeOfType`, `ExpectColumnDistinctValuesToBeInSet`, `ExpectColumnPairValuesAToBeGreaterThanB`, `ExpectCompoundColumnsToBeUnique`, `ExpectMulticolumnSumToEqual`, `ExpectTableRowCountToBeBetween`, `ExpectTableColumnsToMatchSet`, and `UnexpectedRowsExpectation`.
- Class names are CamelCase; serialized/registry expectation types are snake_case, such as `expect_column_values_to_be_between`.
- Current public class signatures include common optional fields such as `id`, `meta`, `notes`, `result_format`, `description`, `catch_exceptions`, `rendered_content`, `severity`, `windows`, and `batch_id`; required domain/success fields vary by class.
- If you must resolve a legacy name, `great_expectations.expectations.registry.get_expectation_impl("expect_column_values_to_be_in_set")` returns the registered class and raises `ExpectationNotFoundError` for unknown names.

## Representative Constructor Patterns

- **Column map:** `ExpectColumnValuesToNotBeNull(column="email", mostly=0.99)` evaluates row-by-row on one column; `mostly` defaults to `1` and must be between `0` and `1` unless supplied as a `$PARAMETER` dict.
- **Numeric bounds:** `ExpectColumnValuesToBeBetween(column="age", min_value=18, max_value=120, strict_min=False, strict_max=False)` accepts numeric/date/datetime bounds and optional strictness.
- **Regex validity:** `ExpectColumnValuesToMatchRegex(column="sku", regex=r"^[A-Z]{3}-\d{4}$")` validates string patterns.
- **Set membership:** `ExpectColumnValuesToBeInSet(column="status", value_set=["new", "active", "closed"])` checks an allowed set.
- **Schema/table checks:** `ExpectColumnToExist(column="id")`, `ExpectTableColumnsToMatchSet(column_set=["id", "email"], exact_match=False)`, and `ExpectTableRowCountToBeBetween(min_value=1, max_value=100000)` validate table-level properties.
- **Pair/multicolumn checks:** `ExpectColumnPairValuesAToBeGreaterThanB(column_A="end", column_B="start", or_equal=True)` and `ExpectCompoundColumnsToBeUnique(column_list=["account_id", "date"])` validate relationships.

## Suite Creation and CRUD

```python
context = gx.get_context(mode="ephemeral")
suite = gx.ExpectationSuite(name="orders_quality")
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"))
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeInSet(
        column="status",
        value_set=["new", "paid", "shipped", "cancelled"],
        severity="warning",
        meta={"owner": "data-quality"},
        notes="Business status vocabulary.",
    )
)
suite = context.suites.add(suite)
# Later:
suite = context.suites.get(name="orders_quality")
context.suites.add_or_update(suite)
all_suites = context.suites.all()
context.suites.delete(name="orders_quality")
```

Notes:

- `ExpectationSuite(name=...)` raises `ValueError` if the name is missing or not a string.
- `suite.add_expectation(expectation)` treats the suite as set-like: duplicate expectations are not appended when their type and non-metadata fields are equal.
- Adding an expectation with an existing `id` can raise because that instance already belongs to a suite; copy it and clear the id before moving it to a new suite.
- If a suite has been added to a context, modifying an expectation object and calling `expectation.save()` pushes changes back through the suite save callback.
- `suite.save()` persists through the active context's expectations store; use only when the suite already belongs to a context.

## Metadata, Notes, Severity, and Result Format

- `meta` stores JSON-serializable user metadata on an expectation or suite; use it for ownership, ticket links, or rationale, not secrets or local paths.
- `notes` accepts a string or list of strings for human-facing explanation.
- `description` overrides/augments rendered expectation wording; keep it consistent with actual default parameters.
- `severity` accepts `"critical"`, `"warning"`, or `"info"`; failed execution is still treated as critical regardless of configured severity.
- `result_format` accepts `"BOOLEAN_ONLY"`, `"BASIC"`, `"SUMMARY"`, `"COMPLETE"`, `gx.ResultFormat.*`, or a dict. Prefer `BASIC`/`SUMMARY` during suite drafting and reserve `COMPLETE` for targeted debugging because it can be large.
- `catch_exceptions` determines whether execution exceptions are captured in validation results; caught exceptions still indicate the data was not tested as intended.

## Testing Expectations Against a Batch

For exploratory work, get a small `Batch` using a sibling datasource helper, then validate either a single expectation or a whole suite:

```python
result = batch.validate(
    gx.expectations.ExpectColumnMaxToBeBetween(column="fare", min_value=0, max_value=500),
    result_format="BASIC",
)

suite_result = batch.validate(suite, result_format="SUMMARY")
```

Inspect `result.success`, `result.expectation_config`, `result.result`, and `result.exception_info`. Route result interpretation and unexpected-row workflows to `../validations-and-results/SKILL.md`.

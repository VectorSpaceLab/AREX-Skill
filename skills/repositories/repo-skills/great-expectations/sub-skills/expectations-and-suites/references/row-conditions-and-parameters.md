# Row Conditions and Parameters

Use this reference when an expectation should apply only to selected rows or when success thresholds must be provided at validation time.

## Runtime Expectation Parameters

GX supports parameterized expectation fields with dictionaries shaped like `{"$PARAMETER": "parameter_name"}`. During validation, provide matching values through `expectation_parameters`.

```python
expectation = gx.expectations.ExpectColumnMaxToBeBetween(
    column="fare",
    min_value={"$PARAMETER": "fare_min"},
    max_value={"$PARAMETER": "fare_max"},
)

runtime_parameters = {"fare_min": 0, "fare_max": 500}
result = batch.validate(expectation, expectation_parameters=runtime_parameters)
```

Patterns:

- Use unique, descriptive keys when a suite has multiple parameterized expectations, for example `passenger_count_max_upper` rather than `max_value`.
- `ExpectationSuite.suite_parameter_options` returns the sorted parameter keys referenced by all expectations in the suite.
- The same `expectation_parameters` dictionary is passed to `batch.validate(...)`, `ValidationDefinition.run(...)`, or checkpoint runs that validate parameterized expectations.
- Some parameter expressions can include simple arithmetic/functions; keep production suites simple unless the expression is covered by tests.
- If a parameterized field is not supplied at validation time, GX raises a `SuiteParameterError` or validation failure depending on the execution path.

## Suite Parameters on the Suite Object

`ExpectationSuite(name="...", suite_parameters={...})` can store default suite parameters with the suite. Use this for stable defaults that belong with the suite definition. Use validation-time `expectation_parameters` for values that change per run, batch, environment, or pipeline.

## Object-Based Row Conditions

Prefer the public object API from `great_expectations.expectations.row_conditions`:

```python
from great_expectations.expectations.row_conditions import Column

row_condition = (Column("country") != "US") & Column("country").is_not_null()
expectation = gx.expectations.ExpectColumnValuesToNotBeNull(
    column="country_of_origin",
    row_condition=row_condition,
)
```

Supported condition operators:

- Comparisons: `==`, `!=`, `>`, `<`, `>=`, `<=`.
- Set membership: `Column("status").is_in([...])`, `Column("status").is_not_in([...])`.
- Nullity: `Column("name").is_null()`, `Column("name").is_not_null()`.
- Composition: combine conditions with `&` for AND and `|` for OR.

## Row Condition Shape Limits

GX validates object-based conditions before execution:

- Up to 100 total condition statements are allowed.
- Nested AND blocks are flattened.
- OR conditions inside an AND block are rejected; rewrite `A & (B | C)` as `(A & B) | (A & C)`.
- Nested OR groups are rejected.
- `is_in` and `is_not_in` require a non-string iterable; elements must be strings or numeric values, with consistent element type except numeric `int`/`float` mixing.
- Comparing a column to `None` is invalid; use `is_null()` or `is_not_null()`.

## Legacy String Conditions and Parsers

Current expectation signatures still accept `row_condition` as a string and `condition_parser` as one of `"great_expectations"`, `"great_expectations__experimental__"`, `"pandas"`, or `"spark"`. Prefer object conditions for new code because they serialize as typed condition objects and avoid engine-specific parser strings.

Use legacy strings only when maintaining existing suites:

```python
expectation = gx.expectations.ExpectColumnValuesToBeBetween(
    column="bonus",
    min_value=5000,
    max_value=10000,
    row_condition='col("department") == "Sales"',
    condition_parser="great_expectations",
)
```

If you use `condition_parser="pandas"` or `"spark"`, the string is passed through to the execution engine's query/filter machinery. That makes syntax backend-specific and should be tested on the same backend used in production.

## Expectations That Do Not Accept Row Conditions

Do not add row conditions to expectation classes whose semantics are table-wide or query-wide. Known examples include `ExpectColumnToExist`, `ExpectQueryResultsToMatchComparison`, `ExpectTableColumnsToMatchOrderedList`, `ExpectTableColumnsToMatchSet`, `ExpectTableColumnCountToBeBetween`, `ExpectTableColumnCountToEqual`, and `UnexpectedRowsExpectation`.

## Combined Example

```python
from great_expectations.expectations.row_conditions import Column

suite = gx.ExpectationSuite(name="orders_parameterized")
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="discount_pct",
        min_value=0,
        max_value={"$PARAMETER": "max_discount_pct"},
        row_condition=Column("customer_tier").is_in(["gold", "platinum"]),
        severity="warning",
    )
)

required_parameters = {"max_discount_pct": 0.30}
result = batch.validate(suite, expectation_parameters=required_parameters)
```

Document the required parameter keys next to the suite or validation definition so future agents can supply them at runtime.

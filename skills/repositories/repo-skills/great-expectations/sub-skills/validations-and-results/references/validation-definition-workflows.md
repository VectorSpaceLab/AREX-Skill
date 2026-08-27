# Validation Definition Workflows

`gx.ValidationDefinition` binds one `BatchDefinition` to one `ExpectationSuite`. It is the direct API for running a suite against data without checkpoint actions.

## Prerequisites

Before creating a validation definition, obtain:

1. A `context` from `gx.get_context(...)`.
2. A `BatchDefinition` from a fluent data asset.
3. An `ExpectationSuite` persisted or managed through `context.suites`.

```python
import great_expectations as gx

context = gx.get_context(mode="ephemeral")
suite = context.suites.get(name="my_suite")
batch_definition = (
    context.data_sources.get("my_datasource")
    .get_asset("my_asset")
    .get_batch_definition("my_batch_definition")
)
```

If the task is about constructing the datasource, asset, or batch definition, route to `../datasources-and-assets/SKILL.md`. If the task is about expectation contents, route to `../expectations-and-suites/SKILL.md`.

## Create and save

Create a definition with public top-level `gx.ValidationDefinition` and add it through the context manager:

```python
validation_definition = gx.ValidationDefinition(
    name="daily_orders_validation",
    data=batch_definition,
    suite=suite,
)
validation_definition = context.validation_definitions.add(validation_definition)
```

Use `context.validation_definitions.add_or_update(validation_definition)` when replacing a previous definition with the same name is intended. Use `validation_definition.save()` after mutating an already-added definition.

A validation definition stores references to its suite and batch definition. If the backing suite, datasource, asset, or batch definition has been changed or recreated, rebuild or refresh the validation definition rather than assuming the old references still point to the desired objects.

## Retrieve and inspect

```python
validation_definition = context.validation_definitions.get("daily_orders_validation")
all_definitions = context.validation_definitions.all()
```

Useful properties:

- `validation_definition.name`: validation name.
- `validation_definition.batch_definition` or `.data`: the configured batch definition.
- `validation_definition.asset`: parent data asset.
- `validation_definition.data_source`: parent datasource.
- `validation_definition.suite`: expectation suite.
- `validation_definition.is_fresh()`: diagnostics for whether the validation and related resources are still present and in sync.

## Run a validation definition

`ValidationDefinition.run()` returns an `ExpectationSuiteValidationResult`.

```python
result = validation_definition.run(
    batch_parameters={"year": "2026", "month": "06"},
    expectation_parameters={"max_row_count": 10_000},
    result_format=gx.ResultFormat.SUMMARY,
)

print(result.success)
print(result.statistics)
```

Arguments:

- `batch_parameters`: selects the concrete batch for a partitioned or runtime batch definition. Keys are determined by the `BatchDefinition`, not by `ValidationDefinition`.
- `expectation_parameters`: resolves expectation suite `$PARAMETER` references for that validation run.
- `result_format`: controls result verbosity; see `result-formats-and-outputs.md`.
- `run_id`: optional `gx.RunIdentifier`; leave unset for normal runs so GX records a current run time.
- `checkpoint_id`: internal checkpoint integration field; leave unset outside checkpoint execution.

`run()` records metadata including `validation_id`, `checkpoint_id`, `run_id`, `validation_time`, and `batch_parameters` in `result.meta`. Dataframe objects passed as batch parameters are replaced in metadata instead of being embedded.

## Batch parameters

Batch-parameter keys come from how the batch definition was built:

- Whole table, whole dataframe, or fixed path definitions often require no batch parameters.
- Runtime dataframe batch definitions commonly use `{"dataframe": dataframe}`.
- Yearly definitions commonly use `{"year": "2026"}`.
- Monthly definitions commonly use `{"year": "2026", "month": "06"}`.
- Daily definitions commonly use `{"year": "2026", "month": "06", "day": "23"}`.
- Regex/path partitioners use the named capture groups or partitioner fields configured on the asset.

When a validation fails before evaluating expectations, first compare the supplied `batch_parameters` keys with the batch definition. If a filesystem regex changed from yearly to monthly, a previously working validation call may now be missing `month`.

## Suite parameters

Suite parameters are runtime values used inside expectation kwargs through `$PARAMETER` references. Pass them as `expectation_parameters`:

```python
result = validation_definition.run(
    expectation_parameters={"mostly_threshold": 0.95, "max_allowed": 100},
)
```

Use the same parameter names that the suite expects. Missing or wrong-typed values can raise during expectation processing before result statistics are produced.

## `batch.validate()` shortcut

Use `batch.validate()` for quick checks against one expectation on an already materialized batch:

```python
batch = batch_definition.get_batch(batch_parameters={"dataframe": dataframe})
expectation = gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id")
result = batch.validate(expectation, result_format=gx.ResultFormat.BASIC)
```

Choose this shortcut when:

- The task validates one expectation against a one-off batch.
- You do not need to persist a validation definition.
- You already have a `Batch` object.

Prefer `ValidationDefinition.run()` when:

- You need to validate a whole suite.
- The validation should be saved, retrieved, reused, or attached to checkpoints later.
- You need consistent `run_id`, validation metadata, and validation results storage.

## Minimal dataframe workflow

```python
import pandas as pd
import great_expectations as gx

df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", None]})
context = gx.get_context(mode="ephemeral")

batch_definition = (
    context.data_sources.pandas_default
    .add_dataframe_asset(name="orders")
    .add_batch_definition_whole_dataframe(name="orders_batch")
)

suite = gx.ExpectationSuite(name="orders_suite")
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="id"))
suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
suite = context.suites.add(suite)

validation = context.validation_definitions.add(
    gx.ValidationDefinition(name="orders_validation", data=batch_definition, suite=suite)
)

result = validation.run(batch_parameters={"dataframe": df})
assert result.statistics["evaluated_expectations"] == 2
```

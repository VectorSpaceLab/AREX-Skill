# Checkpoint API

A GX `Checkpoint` runs one or more saved `ValidationDefinition` objects and then runs post-validation actions. Use checkpoints when validation needs orchestration, Data Docs updates, notifications, or custom side effects; use `ValidationDefinition.run()` directly for simple validation-only tasks.

## Signature and imports

Use the public top-level class:

```python
import great_expectations as gx

checkpoint = gx.Checkpoint(
    name="daily_orders_checkpoint",
    validation_definitions=[validation_definition],
    actions=[],
    result_format=gx.ResultFormat.SUMMARY,
)
```

Verified constructor shape:

```text
gx.Checkpoint(
  *,
  name: str,
  validation_definitions: list[gx.ValidationDefinition],
  actions: list[ValidationAction] = None,
  result_format: gx.ResultFormat | dict | "BOOLEAN_ONLY" | "BASIC" | "SUMMARY" | "COMPLETE" = gx.ResultFormat.SUMMARY,
  id: str | None = None,
)
```

## Prerequisites

Before creating a checkpoint, create and save at least one validation definition:

```python
suite = context.suites.get("orders_suite")
batch_definition = (
    context.data_sources.get("orders_source")
    .get_asset("orders_asset")
    .get_batch_definition("daily_orders")
)
validation_definition = context.validation_definitions.add(
    gx.ValidationDefinition(
        name="daily_orders_validation",
        data=batch_definition,
        suite=suite,
    )
)
```

Route to `../datasources-and-assets/SKILL.md`, `../expectations-and-suites/SKILL.md`, or `../validations-and-results/SKILL.md` if those objects do not exist yet.

## Create, save, retrieve, update

```python
from great_expectations.checkpoint import UpdateDataDocsAction

checkpoint = gx.Checkpoint(
    name="daily_orders_checkpoint",
    validation_definitions=[validation_definition],
    actions=[UpdateDataDocsAction(name="update_local_docs", site_names=["local_site"])],
    result_format="SUMMARY",
)
checkpoint = context.checkpoints.add(checkpoint)
```

`context.checkpoints` is a manager with `add`, `add_or_update`, `get`, `all`, and `delete` methods. Use `add_or_update` when replacing a checkpoint with the same name is intended:

```python
checkpoint = context.checkpoints.add_or_update(checkpoint)
checkpoint = context.checkpoints.get("daily_orders_checkpoint")
known = context.checkpoints.all()
```

If you mutate a previously added checkpoint object, call `checkpoint.save()` before relying on the stored definition. If `checkpoint.run()` finds that the checkpoint is not fresh, GX can raise freshness errors unless all child resources are already added and only the checkpoint itself needs to be added.

## Run patterns

`Checkpoint.run()` accepts batch and suite parameters and returns a `CheckpointResult`:

```python
result = checkpoint.run(
    batch_parameters={"year": "2026", "month": "06"},
    expectation_parameters={"max_row_count": 10_000},
)

print(result.success)
print(result.describe_dict()["statistics"])
```

Arguments:

- `batch_parameters`: passed to every validation definition in the checkpoint. If definitions need different batch parameters, split the checkpoint or design batch definitions with shared keys.
- `expectation_parameters`: supplies suite `$PARAMETER` values for every validation definition in the checkpoint.
- `run_id`: optional `gx.RunIdentifier`; omit for normal runs so GX records the current run time.

A checkpoint with no validation definitions raises `CheckpointRunWithoutValidationDefinitionError` before actions run.

## Result format

Checkpoint `result_format` is applied to each underlying `ValidationDefinition.run()` call. Accepted values include `gx.ResultFormat.BOOLEAN_ONLY`, `BASIC`, `SUMMARY`, `COMPLETE`, strings with those names, or a result-format dict.

Use this default decision table:

| Need | Recommended format | Why |
| --- | --- | --- |
| Production pass/fail orchestration | `SUMMARY` | Includes statistics and compact unexpected summaries without row-level bloat. |
| Very small boolean gate | `BOOLEAN_ONLY` or `BASIC` | Minimizes stored and notification payload size. |
| Debug one bounded failure | `COMPLETE` or a dict with explicit unexpected options | Provides richer diagnostics but can be large. |
| Notifications with failed expectation snippets | `SUMMARY` plus Slack `show_failed_expectations=True` | Keeps alerts useful without leaking full data. |

Avoid `COMPLETE` on large production batches unless the user explicitly needs row-level diagnostics and accepts memory/storage cost. For unexpected rows and result-format dicts, route to `../validations-and-results/SKILL.md`.

## Inspect checkpoint results

Important `CheckpointResult` fields and methods:

- `result.name`: checkpoint name.
- `result.success`: `True` only when every validation result succeeded.
- `result.run_id`: run identifier used for all validations in this checkpoint run.
- `result.run_results`: mapping from `ValidationResultIdentifier` to each `ExpectationSuiteValidationResult`.
- `result.checkpoint_config`: the checkpoint object that produced the run.
- `result.describe_dict()`: compact JSON-serializable summary with evaluated validation count, success percent, and validation descriptions.
- `result.describe()`: JSON string form of `describe_dict()`.

Example summary extraction:

```python
summary = result.describe_dict()
failed = [
    validation_result
    for validation_result in result.run_results.values()
    if not validation_result.success
]
```

## Serialization and action dictionaries

Checkpoint serialization encodes validation definitions as identifiers. Action dictionaries must include a registered `type`, for example `{"type": "update_data_docs", "name": "update_docs", "site_names": []}`. Missing or unknown action types fail during deserialization. Prefer constructing action objects in Python unless the task specifically edits serialized checkpoint config.

Built-in action type values include:

- `update_data_docs` for `UpdateDataDocsAction`.
- `slack` for `SlackNotificationAction`.
- `email` for `EmailAction`.

Custom `ValidationAction` subclasses register their own `type` when the class is imported.

## Production shape

A typical production checkpoint keeps setup separate from orchestration:

1. Build and persist context, datasource, asset, batch definition, suite, and validation definition.
2. Configure local or hosted Data Docs sites on the context.
3. Create a checkpoint with one or more validation definitions.
4. Put `UpdateDataDocsAction` in `actions` if docs should update after each run.
5. Add notification actions with `notify_on="failure"` or severity-specific modes, never hardcoded secrets.
6. Run the checkpoint from the scheduler, passing only batch and suite parameters needed for that run.

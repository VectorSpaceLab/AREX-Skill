# API reference for automation

## Schedules

Use `@schedule` for a Python function that Dagster evaluates on a cron cadence:

```python
import dagster as dg

@dg.schedule(cron_schedule="0 6 * * *", job=my_job, execution_timezone="UTC")
def daily_schedule(context: dg.ScheduleEvaluationContext):
    if context.scheduled_execution_time.weekday() == 6:
        return dg.SkipReason("Skip Sunday loads")
    return dg.RunRequest(
        run_key=context.scheduled_execution_time.isoformat(),
        run_config={"ops": {"load": {"config": {"date": context.scheduled_execution_time.date().isoformat()}}}},
        tags={"automation": "daily_schedule"},
    )
```

Core schedule facts:

- `cron_schedule` accepts a five-field cron string or a sequence of cron strings; use `execution_timezone` for IANA time zone names such as `UTC` or `America/Los_Angeles`.
- The decorated function may return a run config dictionary, one `RunRequest`, a list of `RunRequest`s, a `SkipReason`, `None`, or yield `RunRequest`/`SkipReason` values.
- If a schedule returns more than one `RunRequest` on a tick, every request must include a non-empty `run_key`.
- Set exactly one target style: `job`, `job_name`, or `target`. `target` can point at asset selections, assets, jobs, or unresolved asset jobs.
- Use `default_status=dg.DefaultScheduleStatus.RUNNING` only when the schedule should start enabled in a newly loaded code location.

Use `ScheduleDefinition` when the schedule needs to be constructed programmatically:

```python
daily_schedule = dg.ScheduleDefinition(
    name="daily_schedule",
    cron_schedule="0 6 * * *",
    target=my_asset_job,
    run_config={"ops": {"load": {"config": {"mode": "daily"}}}},
)
```

## Sensors

Use `@sensor` for polling or external-event logic:

```python
import json
import dagster as dg

@dg.sensor(job=my_job, minimum_interval_seconds=60)
def file_sensor(context: dg.SensorEvaluationContext):
    cursor = json.loads(context.cursor) if context.cursor else {"seen": []}
    seen = set(cursor["seen"])
    new_files = [name for name in list_available_files() if name not in seen]

    if not new_files:
        return dg.SkipReason("No new files")

    for filename in sorted(new_files):
        yield dg.RunRequest(
            run_key=filename,
            run_config={"ops": {"ingest": {"config": {"filename": filename}}}},
        )

    context.update_cursor(json.dumps({"seen": sorted(seen.union(new_files))}))
```

Core sensor facts:

- A sensor may return or yield `RunRequest`, `SkipReason`, `SensorResult`, `None`, or a list of `RunRequest`s.
- A sensor with a `RunRequest` needs a target: `job`, `jobs`, `job_name`, `asset_selection`, or `target`.
- `RunRequest(run_key=...)` suppresses duplicate runs for the same key. Use `run_key=None` when a cursor reset should allow reprocessing.
- Do not set both `context.update_cursor(...)` and `SensorResult(cursor=...)` in the same evaluation.
- When returning a `SensorResult`, it must be the only returned object; put run requests, dynamic partition requests, asset events, and cursor on that `SensorResult`.
- If targeting multiple jobs, set `RunRequest(job_name="...")` for each request.

Use resources for dependency injection:

```python
class Poller(dg.ConfigurableResource):
    endpoint: str

    def pending_ids(self) -> list[str]: ...

@dg.sensor(job=my_job)
def external_sensor(context: dg.SensorEvaluationContext, poller: Poller):
    ids = poller.pending_ids()
    if not ids:
        return dg.SkipReason("No work")
    return [dg.RunRequest(run_key=item_id, run_config={"ops": {"load": {"config": {"id": item_id}}}}) for item_id in ids]
```

## Asset sensors

Use `@asset_sensor` when one upstream asset materialization should trigger custom logic:

```python
@dg.asset_sensor(asset_key=dg.AssetKey("raw_orders"), job=process_orders_job)
def raw_orders_sensor(context: dg.SensorEvaluationContext, asset_event: dg.EventLogEntry):
    materialization = asset_event.dagster_event.event_specific_data.materialization
    batch_id = materialization.metadata.get("batch_id")
    if batch_id is None:
        return dg.SkipReason("Materialization has no batch_id metadata")
    return dg.RunRequest(run_key=str(batch_id.value), run_config={"ops": {"process": {"config": {"batch_id": batch_id.value}}}})
```

Prefer `AutomationCondition.eager()` or `AutomationCondition.on_cron()` over asset sensors when the need is asset dependency propagation without arbitrary per-materialization run config. `@multi_asset_sensor` still exists but is deprecated in favor of declarative automation for most multi-asset dependency cases.

## Run status and failure sensors

Use run status sensors for reactions to completed, failed, or other run states:

```python
@dg.run_status_sensor(
    run_status=dg.DagsterRunStatus.SUCCESS,
    request_job=status_reporting_job,
)
def report_success(context: dg.RunStatusSensorContext):
    if context.dagster_run.job_name == status_reporting_job.name:
        return dg.SkipReason("Avoid reporting job loop")
    return dg.RunRequest(run_key=context.dagster_run.run_id)
```

Use `@run_failure_sensor` for failure-only handlers. In tests, build a context with `build_run_status_sensor_context(...)`; call `.for_run_failure()` when invoking a failure sensor function directly.

## Declarative automation

Use `AutomationCondition` on assets or asset checks when Dagster should infer runs from asset state:

```python
@dg.asset(automation_condition=dg.AutomationCondition.on_cron("0 2 * * *", cron_timezone="UTC"))
def daily_asset(): ...

@dg.asset(deps=[daily_asset], automation_condition=dg.AutomationCondition.eager())
def downstream_asset(): ...
```

Important condition constructors and operators:

- `AutomationCondition.on_cron(cron_schedule, cron_timezone="UTC")`: execute after a cron tick and after dependencies have updated since that tick.
- `AutomationCondition.eager()`: execute missing/newly stale targets when dependencies update, while avoiding missing/in-progress dependencies.
- `AutomationCondition.on_missing()`: fill missing targets after condition activation when dependencies are available.
- `AutomationCondition.missing()`, `newly_updated()`, `newly_requested()`, `code_version_changed()`, `data_version_changed()`, `cron_tick_passed()`, `in_latest_time_window()` for custom expressions.
- `AutomationCondition.any_deps_match(...)`, `all_deps_match(...)`, `any_deps_updated()`, `any_deps_missing()`, `all_deps_updated_since_cron(...)` for dependency-aware logic.
- `condition.with_label("meaningful_name")` improves UI/debuggability; `condition.replace("label_or_name", new_condition)` customizes built-in composites.
- `&`, `|`, and `~` compose conditions.

A default automation condition sensor is created for code locations containing assets with automation conditions. Add an explicit `AutomationConditionSensorDefinition` when you need custom selection, tags, or default status:

```python
defs = dg.Definitions(
    assets=[daily_asset, downstream_asset],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            name="core_asset_automation",
            target=dg.AssetSelection.groups("core"),
            default_status=dg.DefaultSensorStatus.RUNNING,
            run_tags={"source": "declarative_automation"},
        )
    ],
)
```

## Freshness and backfill policy

Freshness policy APIs define expectations for asset materialization timing. Pair them with freshness automation conditions or freshness checks when a task asks for health/freshness automation:

```python
@dg.asset(freshness_policy=dg.FreshnessPolicy.time_window(fail_window=dg.FreshnessTimeWindow(hours=24)))
def daily_export(): ...

@dg.asset(automation_condition=dg.AutomationCondition.freshness_failed().newly_true())
def freshness_repair(): ...
```

For partitioned asset backfills, attach `BackfillPolicy` to the asset definition:

```python
@dg.asset(partitions_def=daily_partitions, backfill_policy=dg.BackfillPolicy.multi_run(max_partitions_per_run=10))
def partitioned_asset(): ...
```

Use `BackfillPolicy.single_run()` only when one run can safely materialize the whole partition range. Use `BackfillPolicy.multi_run(max_partitions_per_run=N)` to bound per-run partition counts for larger or expensive backfills.

# Workflows for schedules, sensors, and automation conditions

## Choose the automation primitive

1. If the trigger is only wall-clock time, use `@schedule` or `ScheduleDefinition`.
2. If the trigger requires polling external state, inspecting files/messages/API state, or dynamic run config per event, use `@sensor`.
3. If the trigger is one asset materialization with custom event metadata logic, use `@asset_sensor`.
4. If the trigger is job success/failure, use `@run_status_sensor` or `@run_failure_sensor`.
5. If the trigger is asset dependency/freshness/backfill state, use `AutomationCondition`, freshness APIs, and `BackfillPolicy` before writing a custom sensor.

## Implement a schedule safely

- Define the target job or asset job first.
- Add `@schedule(cron_schedule=..., job=... or target=...)`.
- Return `SkipReason` for expected no-op ticks so the UI explains skips.
- Return `RunRequest` for dynamic config, tags, partition keys, or run keys.
- Use `context.scheduled_execution_time` instead of reading the current time directly; this makes tests deterministic.
- If returning multiple run requests, set a stable `run_key` on every request.

Unit test pattern:

```python
def test_daily_schedule_request():
    context = dg.build_schedule_context(scheduled_execution_time=datetime.datetime(2026, 1, 2, 6, 0))
    result = daily_schedule.evaluate_tick(context)
    assert result.skip_message is None
    assert len(result.run_requests) == 1
    assert result.run_requests[0].run_key == "2026-01-02T06:00:00"
```

If the schedule yields partitioned `RunRequest(partition_key=...)`, pass a repository or `Definitions` that can resolve the target job when building the test context.

## Implement a cursor-backed sensor

- Store only the minimum replay state in `context.cursor`; serialize it as a string such as JSON.
- Build run keys from source event IDs when duplicate suppression is desired.
- Update the cursor only after all run requests for the processed events are yielded or returned.
- Decide deliberately whether cursor reset should re-run events:
  - Use stable `run_key`s when reset should not launch duplicate runs.
  - Use `run_key=None` when reset is an intentional replay mechanism.
- Keep external polling behind a resource so tests can pass a fake resource to `build_sensor_context(resources={...})`.

Unit test pattern:

```python
def test_sensor_advances_cursor():
    context = dg.build_sensor_context(cursor='{"seen": []}', resources={"poller": FakePoller(["a", "b"])})
    result = file_sensor.evaluate_tick(context)
    assert [request.run_key for request in result.run_requests] == ["a", "b"]
    assert json.loads(result.cursor) == {"seen": ["a", "b"]}
```

If a resource is a context manager or generator resource, use `with dg.build_sensor_context(...) as context:` so the resource scope is active while evaluating the sensor.

## Use `SensorResult`

Use `SensorResult` when a sensor needs to return multiple payload types together, such as run requests plus dynamic partitions or asset events.

```python
return dg.SensorResult(
    run_requests=[dg.RunRequest(run_key=item_id, partition_key=item_id)],
    dynamic_partitions_requests=[partitions_def.build_add_request([item_id])],
    cursor=item_id,
)
```

Rules:

- Return a single `SensorResult`, not a list containing it and not a mix of `SensorResult` with `RunRequest`/`SkipReason`.
- Do not call `context.update_cursor(...)` in an evaluation that returns `SensorResult(cursor=...)`.
- For asset and run status sensors, some cursors are framework-managed; do not set a cursor where the framework owns it.

## Test run status sensors

1. Execute or construct a Dagster run and matching Dagster event in an ephemeral instance.
2. Build context with `build_run_status_sensor_context(sensor_name=..., dagster_instance=..., dagster_run=..., dagster_event=...)`.
3. Invoke the sensor function directly or call `.evaluate_tick(...)` as appropriate.
4. For failure sensors, convert the context with `.for_run_failure()` before direct invocation.

Guard against loops: when a status sensor requests a job, skip if `context.dagster_run.job_name` is the same reporting/remediation job that the sensor launches.

## Migrate custom sensors to declarative automation

Use this decision table:

| Existing pattern | Prefer | Keep a custom sensor when |
| --- | --- | --- |
| One upstream asset updates one downstream asset | `AutomationCondition.eager()` | Run config depends on materialization metadata |
| All dependencies should be ready by a cadence | `AutomationCondition.on_cron(...)` | The cadence depends on external service state |
| Fill missing partitions when parents exist | `AutomationCondition.on_missing()` | Non-asset side effects are required |
| Avoid old catch-up on reactivation | Customized `AutomationCondition` with `initial_evaluation()`, `newly_true()`, or labels | You need arbitrary Python polling |
| Multi-asset sensor coordinates asset dependencies | Declarative automation | You need custom event aggregation and custom run config |

## Customize automation conditions

Start from a built-in composite and replace labeled subconditions:

```python
condition = dg.AutomationCondition.eager().replace(
    "any_deps_missing",
    dg.AutomationCondition.any_deps_missing().allow(dg.AssetSelection.groups("required")),
)
```

Common customizations:

- Use `with_label(...)` for each business rule that future maintainers should recognize in the UI.
- Use `in_latest_time_window(datetime.timedelta(...))` when a partitioned asset should consider more than the latest partition.
- Use `all_deps_blocking_checks_passed()` when upstream blocking asset checks should gate automation.
- Use `any_new_update_has_run_tags(...)` or `all_new_updates_have_run_tags(...)` to include or exclude updates from particular run classes.
- Use `all_deps_updated_since_cron(...)` when dependencies should be fresh relative to a different boundary than the target cron.

## Preview and inspect CLI commands

Use the bundled helper to print safe CLI commands without starting daemon work:

```bash
python skills/dagster/sub-skills/automation-schedules-sensors/scripts/preview_sensor_schedule.py sensor --name my_sensor --module-name my_project.definitions
python skills/dagster/sub-skills/automation-schedules-sensors/scripts/preview_sensor_schedule.py schedule --module-name my_project.definitions
```

It prints commands such as `dagster sensor preview ...` and `dagster schedule preview ...`. It does not import user code or call Dagster.

## Native verification candidates

Useful native tests/examples to adapt during verification:

- Dynamic partitions examples that combine sensors with dynamic partition requests.
- CLI schedule/sensor command tests for `dagster sensor preview`, `dagster sensor cursor`, and `dagster schedule preview` behavior.
- Schedule tests covering cron, timezone, resources, and tick evaluation.
- Sensor invocation tests covering resources, cursor behavior, partitioned run requests, and `SensorResult` validation.
- Run status sensor docs/tests covering `build_run_status_sensor_context` and failure context conversion.

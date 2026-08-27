# Troubleshooting schedules, sensors, and declarative automation

## Import or installation errors

Symptoms:

- `ModuleNotFoundError: No module named dagster`.
- `dagster --help` fails.
- Definitions cannot load before any schedule/sensor code runs.

Fixes:

- Verify the active environment can import `dagster` and run `dagster --help`.
- Keep optional dependencies inside resources or user code that is easy to mock; schedule/sensor definitions should import without requiring production-only clients when possible.
- If a sensor polls an optional integration, catch missing optional dependency errors at resource construction time and return a clear `SkipReason` or test-friendly exception.

## Definition loading errors

Symptoms:

- `Attempted to provide more than one of 'job', 'job_name', and 'target'` for a schedule.
- `Attempted to provide more than one of 'job', 'jobs', 'job_name', and 'asset_selection'` for a sensor.
- A sensor returns `RunRequest` but has no target.

Fixes:

- Use exactly one targeting style on each definition.
- For schedules, choose one of `job`, `job_name`, or `target`.
- For sensors, choose one of `job`, `jobs`, `job_name`, `asset_selection`, or `target`.
- If a sensor targets multiple jobs, set `RunRequest(job_name="target_job")` on each request.

## Cron and timezone errors

Symptoms:

- Invalid cron schedule errors.
- A schedule fires at an unexpected local time.
- A cron interval appears to fire more often than expected.

Fixes:

- Use standard five-field cron expressions unless the API explicitly documents a preset such as `@daily` for the path you are using.
- Set `execution_timezone` on schedules or `cron_timezone` on `AutomationCondition.on_cron(...)`.
- Break unusual large cron intervals into a sequence of cron schedules when Dagster warns about out-of-range cron intervals.
- In tests, use `build_schedule_context(scheduled_execution_time=...)` instead of relying on the wall clock.

## Schedule evaluation failures

Symptoms:

- A schedule with multiple `RunRequest`s fails validation.
- A partitioned schedule test cannot resolve run config or tags.
- A schedule unexpectedly skips.

Fixes:

- Add a stable `run_key` to every request when returning multiple requests from one schedule tick.
- Pass repository/definitions context when testing partitioned requests so Dagster can resolve the target job.
- Inspect `ScheduleExecutionData.skip_message` after `.evaluate_tick(...)`.
- If using `should_execute`, remember a false result produces a skip instead of running the schedule body.

## Sensor duplicate runs

Symptoms:

- A sensor emits duplicate run requests after a cursor reset.
- A sensor keeps launching the same work every tick.
- Expected replay does not happen after resetting a cursor.

Fixes:

- Use stable `RunRequest(run_key=source_event_id)` to suppress duplicates across ticks and cursor resets.
- Use `run_key=None` when cursor reset should intentionally reprocess the same source records.
- Update `context.cursor` only after successfully identifying all events included in returned run requests.
- Store a high-water mark or processed IDs in the cursor; do not infer processed state from `last_run_key`, which is deprecated.
- Test two consecutive ticks with the previous tick's returned cursor to prove the second tick skips.

## Cursor and `SensorResult` conflicts

Symptoms:

- `SensorResult.cursor cannot be set if context.update_cursor() was called.`
- `When a SensorResult is returned from a sensor, it must be the only object returned.`
- Asset or run status sensor complains that the cursor is managed by the framework.

Fixes:

- Choose either `context.update_cursor(...)` or `return SensorResult(cursor=...)`, not both.
- Return exactly one `SensorResult`; put `run_requests`, `dynamic_partitions_requests`, `asset_events`, and `cursor` inside it.
- Do not set `SensorResult.cursor` from `@asset_sensor`, `@multi_asset_sensor`, or run status sensors when Dagster manages the cursor.

## Resource and optional dependency gaps

Symptoms:

- Sensor tests fail because a resource is unavailable.
- Accessing resources from a test context raises an error about context manager scope.
- Production polling libraries are unavailable locally.

Fixes:

- Inject polling clients as Dagster resources and pass fakes with `build_sensor_context(resources={...})` or `build_schedule_context(resources={...})`.
- Use `with build_sensor_context(...) as context:` when any resource is a generator or context manager.
- Keep expensive or optional imports inside resource initialization paths where they can be isolated and tested.

## Run status sensor loops

Symptoms:

- A run status sensor launches a reporting/remediation job, whose success triggers the same sensor repeatedly.
- A failure sensor fires for jobs outside the intended scope.

Fixes:

- In the sensor body, skip when `context.dagster_run.job_name` equals the job the sensor requests.
- Narrow `monitored_jobs` unless the sensor intentionally monitors all jobs or all code locations.
- For global monitoring, use `monitor_all_code_locations=True` deliberately and document the blast radius.

## Declarative automation does not run

Symptoms:

- Assets have `automation_condition=...` but no runs are launched.
- `AutomationCondition.on_cron(...)` appears late by one evaluation interval.
- Re-enabling automation launches too many catch-up partitions.

Fixes:

- Ensure an `AutomationConditionSensorDefinition` exists or the default automation condition sensor is present for the code location.
- Ensure that automation condition sensor is enabled in the deployment; daemon lifecycle and deployment operations belong outside this sub-skill.
- Remember conditions are evaluated on sensor ticks, not continuously; `cron_tick_passed()` becomes true on the first evaluation after the cron boundary.
- Use `initial_evaluation()`, `newly_true()`, `since_last_handled()`, or custom date filters to avoid unwanted catch-up on reactivation.
- For custom Python automation conditions, configure evaluation where user code can execute; otherwise use serializable built-in condition trees.

## Declarative automation picks the wrong partitions

Symptoms:

- Only the latest time partition is automated.
- Backfills or older partitions do not materialize as expected.
- Too many partitions are included in one run.

Fixes:

- Built-in `eager()`, `on_cron()`, and `on_missing()` include `in_latest_time_window()` by default; replace or customize that subcondition when older partitions should be considered.
- Attach `BackfillPolicy.multi_run(max_partitions_per_run=N)` to bound partition count per run.
- Use `BackfillPolicy.single_run()` only when one run can handle the full selected partition range.
- Check partition mappings and asset dependencies before blaming the automation condition.

## Freshness automation surprises

Symptoms:

- Freshness state is `UNKNOWN` or `NOT_APPLICABLE`.
- A freshness-based condition never becomes true.
- Freshness checks run but automation does not respond.

Fixes:

- Ensure the asset has a freshness policy or freshness check setup appropriate for the asset type.
- Materialize or observe the asset at least once when freshness state depends on event history.
- Use `AutomationCondition.freshness_failed()`, `freshness_warned()`, or `freshness_passed()` only for assets whose freshness state is computed.
- Distinguish health reporting from run launching: freshness checks report state, while automation conditions or sensors launch runs.

## CLI/API misuse

Symptoms:

- `dagster sensor preview` cannot find a sensor.
- `dagster schedule preview` shows planned state changes rather than evaluating one schedule tick.
- CLI commands fail because the code location is not specified.

Fixes:

- Provide the same code location selector flags that load the repository, such as `--module-name`, `--python-file`, `--attribute`, or workspace flags.
- Use `dagster sensor preview SENSOR_NAME ...` to evaluate one sensor without committing cursor changes.
- Use schedule unit tests with `build_schedule_context()` for one-tick schedule behavior; `dagster schedule preview` previews schedule state reconciliation.
- Use the bundled helper script to print command shapes before running them.

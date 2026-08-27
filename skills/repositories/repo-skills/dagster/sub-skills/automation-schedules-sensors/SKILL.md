---
name: automation-schedules-sensors
description: "Define, debug, and test Dagster schedules, sensors, asset sensors,
  run status sensors, declarative automation conditions, freshness automation,
  and backfill policies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Automation: schedules, sensors, and declarative conditions

Use this sub-skill when the task is about time-based or event-based automation in Dagster code:

- `ScheduleDefinition`, `@schedule`, cron schedules, time zones, schedule run config/tags, and schedule unit tests.
- `@sensor`, `RunRequest`, `SkipReason`, `SensorResult`, cursor handling, run keys, resource-backed sensors, and sensor unit tests.
- `@asset_sensor`, run status sensors, failure sensors, and tests using built Dagster context objects.
- `AutomationCondition`, `AutomationConditionSensorDefinition`, freshness-driven automation, and `BackfillPolicy` for partitioned assets.

Route elsewhere when the task is primarily about core asset modeling, deployment/daemon operations, or starting/stopping local CLI processes.

## Start here

- For implementation patterns and API choices, read [references/api-reference.md](references/api-reference.md).
- For end-to-end workflows and test commands, read [references/workflows.md](references/workflows.md).
- For common failures and fixes, read [references/troubleshooting.md](references/troubleshooting.md).
- To safely inspect what CLI preview commands would be used, run `python skills/dagster/sub-skills/automation-schedules-sensors/scripts/preview_sensor_schedule.py --help`.

## Quick routing

- Need a cron trigger for a job or asset job: use `@schedule` or `ScheduleDefinition`; test with `build_schedule_context()` and `.evaluate_tick()`.
- Need polling logic or external-event logic: use `@sensor`, stable `RunRequest(run_key=...)`, and `context.update_cursor(...)` or `SensorResult(cursor=...)`.
- Need to react to one asset materialization: use `@asset_sensor`; prefer declarative automation for asset dependency propagation when custom per-event run config is not required.
- Need to react to job success/failure: use `@run_status_sensor` or `@run_failure_sensor`; avoid triggering an infinite loop when the requested job can produce the same monitored status.
- Need asset-centric freshness, dependency, or backfill behavior: prefer `AutomationCondition.on_cron()`, `AutomationCondition.eager()`, `AutomationCondition.on_missing()`, freshness policies/checks, and `BackfillPolicy`.

## Definition checklist

- Put schedules and sensors in the repository or `Definitions(schedules=[...], sensors=[...])` that loads with the target jobs/assets.
- Use only one target style per schedule/sensor: `job`, `job_name`, `jobs`, `asset_selection`, or `target` as accepted by that definition.
- Give every multi-request schedule a non-empty `run_key` on each `RunRequest`; use stable sensor run keys only when duplicate suppression should survive cursor resets.
- Keep schedule/sensor evaluation pure enough for unit tests: move network/credentialed calls behind resources that can be stubbed in `build_*_context`.
- For declarative automation, ensure the automation condition sensor is present and enabled in the deployment; route daemon lifecycle and deployment checks to the deployment operations skill.

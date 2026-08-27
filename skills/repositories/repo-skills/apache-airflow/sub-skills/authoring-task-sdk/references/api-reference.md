<!-- SPDX-License-Identifier: Apache-2.0 -->

# Airflow 3 Authoring API Reference

## Public Interface Rules

- Prefer `airflow.sdk` for Dag authoring and task execution code. In Airflow 3, `airflow.sdk` is the public interface for Dag authors; imports from historical modules may still work as compatibility shims but are not the preferred target for new or migrated Dag files.
- Treat anything not exported by `airflow.sdk` or a provider's documented public module as unstable unless a bundled reference in this skill says otherwise.
- Dag files should avoid direct metadata database access. Use Task SDK context, XComs, Variables, Connections, assets, and provider hooks/operators instead of importing ORM models to query or mutate Airflow internals.
- Prefer verified live API signatures over examples copied from old Airflow 2 Dags.

## Core Imports

Use these imports for authoring code:

```python
from airflow.sdk import DAG, Asset, AssetAlias, Connection, Param, Variable
from airflow.sdk import dag, get_current_context, task, task_group
```

Also useful from `airflow.sdk` when needed: `BaseOperator`, `BaseSensorOperator`, `BaseHook`, `Context`, `TaskGroup`, `XComArg`, `chain`, `chain_linear`, `cross_downstream`, `literal`, `setup`, and `teardown`.

## Verified Signatures

These signatures were verified from installed Airflow package facts for the generated skill:

- `airflow.sdk.DAG(dag_id, *, description=None, default_args=NOTHING, start_date=NOTHING, end_date=None, schedule=None, template_searchpath=None, template_undefined=StrictUndefined, user_defined_macros=None, user_defined_filters=None, max_active_tasks=NOTHING, max_active_runs=NOTHING, max_consecutive_failed_dag_runs=NOTHING, dagrun_timeout=None, deadline=None, sla_miss_callback=None, catchup=NOTHING, on_success_callback=None, on_failure_callback=None, doc_md=None, params=None, access_control=None, is_paused_upon_creation=None, jinja_environment_kwargs=None, render_template_as_native_obj=False, tags=NOTHING, owner_links=NOTHING, auto_register=True, fail_fast=False, allowed_run_types=None, dag_display_name=NOTHING, task_group=NOTHING, disable_bundle_versioning=NOTHING, rerun_with_latest_version=None)`.
- `airflow.sdk.dag(dag_id_or_func=None, __DAG_class=DAG, __warnings_stacklevel_delta=2, **decorator_kwargs)`.
- `airflow.sdk.task(*args, **kwargs)`.
- `airflow.sdk.task_group(python_callable=None, **tg_kwargs)`.
- `airflow.sdk.Asset(name=None, uri=None, *, group=None, extra=None, watchers=None, access_control=None)`.
- `airflow.sdk.AssetAlias(name, *, group="asset")`.
- `airflow.sdk.Param(default=NOTSET, description=None, source=None, **kwargs)`.
- `airflow.sdk.Connection(*, conn_id, uri=None, **kwargs)`.
- `airflow.sdk.Variable(key, value=None, description=None)`.

## Dag Declaration Patterns

Context manager style:

```python
from datetime import datetime
from airflow.sdk import DAG, task

with DAG(
    dag_id="daily_orders",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["orders"],
) as dag:
    @task
    def extract() -> list[str]:
        return ["north", "south"]

    extract()
```

Decorator style:

```python
from datetime import datetime
from airflow.sdk import dag, task

@dag(start_date=datetime(2024, 1, 1), schedule="@daily", catchup=False)
def daily_orders():
    @task
    def extract() -> list[str]:
        return ["north", "south"]

    extract()

daily_orders()
```

Discovery rule: defining a decorated function is not enough. Call the decorated function at module top level so the Dag object exists when the file is parsed.

## TaskFlow and Task Groups

- `@task` wraps a Python callable as an Airflow task. Calling a decorated task in a Dag file creates a task object/XComArg; it does not run the Python function at parse time.
- `@task(multiple_outputs=True)` unrolls a returned dictionary into separate XCom values.
- `@task.branch` returns a downstream task id, task group id, list of ids, or `None` to skip all downstream branches.
- `@task.run_if(condition, skip_message=None)` and `@task.skip_if(condition, skip_message=None)` are available task decorators for conditional execution.
- `@task_group()` wraps a function into a `TaskGroup`; use `group_id` or the function name to keep ids stable.
- Dynamic task groups support `.partial(...).expand(...)` and `.expand_kwargs(...)` patterns, but mapped task groups must obey dynamic mapping constraints.

## Dependencies

Use operators or XComArg relationships rather than side-effecting functions at parse time:

```python
raw = extract()
clean = transform(raw)
raw >> clean
```

Common helpers from `airflow.sdk`:

- `chain(a, b, c)` for linear dependencies.
- `chain_linear(upstream_list, downstream_list)` for list-to-list relationships.
- `cross_downstream(upstream_list, downstream_list)` for all-to-all relationships.

Task ids must be unique within a Dag and also become part of nested task group paths, such as `group_id.task_id`.

## Dynamic Task Mapping

- Use `.expand(arg=[...])` for mapped arguments and `.partial(...)` for unmapped arguments.
- Only keyword arguments are accepted by `.expand()`.
- Task-generated mapping expects the upstream task to return a list or dictionary that can be stored in XCom.
- Avoid `TriggerRule.ALWAYS` on task-generated mapped tasks or mapped task groups; the expanded parameters do not exist at immediate execution time.
- A reduce task receives a lazy proxy for mapped outputs. Convert to `list(...)` only when the mapped size is bounded and the memory/performance trade-off is intentional.

## Params

- Define Dag-level Params with `params={"name": Param(default, type="string", ...)}` or plain JSON-serializable defaults.
- `Param` uses JSON Schema-style validation, so type/enum/minimum/maximum/items constraints are authoring-time and trigger-time contracts.
- Scheduled Dag runs use default Param values; manually triggered runs can override Params.
- Access runtime values from context (`get_current_context()["params"]`) or Jinja (`{{ params.name }}`), not from Python conditionals at parse time.
- Use `render_template_as_native_obj=True` on `DAG` when templated values should preserve native JSON types instead of strings.

## XCom and Context

- Use TaskFlow return values for most task-to-task data passing. The return value becomes an XComArg and automatically wires dependencies when passed to downstream TaskFlow tasks or templated operator fields.
- Use `get_current_context()` inside task execution to access `ti`, `dag_run`, `params`, logical dates, inlet/outlet events, and other runtime context.
- Use `context["ti"].xcom_push(...)` and `context["ti"].xcom_pull(...)` for explicit XComs.
- XCom values should be small and serializable; avoid using XCom for large dataframes, files, or high-volume payloads.
- XComs are cleared on task retry to keep retries idempotent; do not use them as durable retry state.

## Assets and Asset Scheduling

- Use `Asset(name=..., uri=...)` or `Asset(uri)` to declare data dependencies; `name` and `uri` identify the asset.
- Use `outlets=[asset]` or TaskFlow returns of `Asset`/`list[Asset]` for producer tasks.
- Use `inlets=[asset]` or `schedule=[asset]` / `schedule=asset` for consumer Dags.
- Use asset expressions (`asset_a & asset_b`, `asset_a | asset_b`) when a consumer needs boolean logic over asset events.
- Use `AssetAlias("alias-name")` when a producer creates the concrete asset URI at execution time. The alias schedule is unresolved until a producer emits an event that maps the alias to a concrete asset.
- Use inlet/outlet event context when attaching or reading per-event metadata; do not confuse asset `extra` metadata with event-specific metadata.
- Watchers belong to asset definitions and can react to asset events, but operational notification setup belongs outside this authoring sub-skill.

## Timetables and Schedules

Common `schedule` values:

- `None` for manually triggered Dags.
- Cron strings such as `"0 0 * * *"`.
- Presets such as `"@daily"`, `"@once"`, and `"@continuous"`.
- `datetime.timedelta(...)` for fixed intervals.
- Built-in timetable instances such as `CronTriggerTimetable`, `DeltaTriggerTimetable`, `MultipleCronTriggerTimetable`, `EventsTimetable`, or `AssetOrTimeSchedule`.
- Assets, asset lists, or asset expressions for asset-triggered Dags.

Avoid accessing Variables, Connections, remote services, or the metadata database while constructing timetables at parse time; timetable code is imported by parsing/scheduling components.

## Standard Provider Operators and Sensors

Verified standard provider import targets and signatures:

```python
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
from airflow.providers.standard.sensors.filesystem import FileSensor
```

- `PythonOperator(*, python_callable, op_args=None, op_kwargs=None, templates_dict=None, templates_exts=None, show_return_value_in_logs=True, **kwargs)`.
- `BranchPythonOperator(*, python_callable, op_args=None, op_kwargs=None, templates_dict=None, templates_exts=None, show_return_value_in_logs=True, **kwargs)`.
- `BashOperator(*, bash_command, env=None, append_env=False, output_encoding="utf-8", skip_on_exit_code=99, cwd=None, output_processor=lambda output: output, **kwargs)`.
- `FileSensor(*, filepath, fs_conn_id="fs_default", recursive=False, deferrable=False, start_from_trigger=False, trigger_kwargs=None, **kwargs)`.

Prefer `@task` over `PythonOperator` for plain Python logic unless the code specifically needs classic operator behavior such as templated fields, provider compatibility, or subclassing. Prefer `@task.branch` over direct `BranchPythonOperator` for new TaskFlow branching.

## Deferrable vs Async

- A deferrable operator or sensor releases the worker slot while waiting and resumes when a trigger event fires. Prefer this for long waits when a provider supplies a deferrable operator/sensor.
- Python-native async TaskFlow tasks use `async def` and `await` inside a worker slot for concurrent I/O. Use them when there is no suitable deferrable operator and the task uses async-compatible libraries.
- Do not call `defer()` from a `PythonOperator` callable or TaskFlow function. Deferral belongs to class-based operators.
- Avoid blocking calls in async code; blocking I/O inside `async def` defeats concurrency and can stall the event loop.

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Authoring Workflows

## Create a New Dag

1. Start from public imports: `from airflow.sdk import DAG, dag, task, task_group, Param, Asset` plus provider imports when needed.
2. Choose declaration style:
   - Use `with DAG(...) as dag:` when mixing TaskFlow with class-based operators/sensors.
   - Use `@dag(...)` when the Dag is mostly TaskFlow and benefits from function scoping.
3. Set explicit `dag_id`, `start_date`, `schedule`, and `catchup`. Use timezone-aware datetimes when the deployment requires a non-UTC timezone policy.
4. Keep top-level module code cheap and deterministic. Do not make network calls, read Airflow Variables, query the metadata DB, or scan large directories at parse time.
5. Ensure at least one Dag object is created at module top level. For `@dag`, call the decorated function at top level.
6. Validate the file with `scripts/validate_dag_file.py --list-dags` and optionally `--expect-dag-id`.

Minimal TaskFlow template:

```python
from datetime import datetime
from airflow.sdk import dag, task

@dag(dag_id="daily_orders", start_date=datetime(2024, 1, 1), schedule="@daily", catchup=False)
def daily_orders():
    @task
    def extract() -> list[str]:
        return ["north", "south"]

    @task
    def load(regions: list[str]) -> None:
        print(regions)

    load(extract())

daily_orders()
```

## Migrate Airflow 2 Dag Imports

Use this mapping as the first migration pass:

- `from airflow import DAG` or `from airflow.models import DAG` -> `from airflow.sdk import DAG`.
- `from airflow.decorators import dag, task, task_group` -> `from airflow.sdk import dag, task, task_group`.
- `from airflow.models import Variable` -> `from airflow.sdk import Variable`.
- `from airflow.models.param import Param` -> `from airflow.sdk import Param`.
- `from airflow.models.xcom_arg import XComArg` -> `from airflow.sdk import XComArg`.
- `from airflow.operators.python import PythonOperator, BranchPythonOperator` -> `from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator`.
- `from airflow.operators.bash import BashOperator` -> `from airflow.providers.standard.operators.bash import BashOperator`.
- `from airflow.sensors.filesystem import FileSensor` -> `from airflow.providers.standard.sensors.filesystem import FileSensor`.

Migration review checklist:

1. Replace legacy imports before changing behavior.
2. Keep existing `dag_id`, schedule, task ids, Params, and XCom keys stable unless the user requested a behavioral change.
3. Replace simple `PythonOperator` callables with `@task` only when templated fields or operator-specific behavior are not needed.
4. Replace branch callables with `@task.branch` when the branch target ids are directly downstream.
5. Validate that the migrated file imports and exposes the expected `dag_id`.

## Use TaskFlow with Standard Operators

TaskFlow outputs can feed standard operators through templated fields or XComArg-aware arguments. Use TaskFlow for Python data transformations and standard operators for shell commands, sensors, cross-Dag triggers, and provider-specific work.

```python
from datetime import datetime
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, task

with DAG("mixed_taskflow_standard", start_date=datetime(2024, 1, 1), schedule=None, catchup=False):
    @task
    def make_name() -> str:
        return "orders"

    BashOperator(task_id="echo_name", bash_command="echo {{ ti.xcom_pull(task_ids='make_name') }}")
```

Prefer direct TaskFlow arguments (`load(extract())`) where possible. Use Jinja/XCom pulls in classic operators only when the operator field is templated or the operator does not accept an XComArg directly.

## Define Dependencies and Task Groups

- Use `task_a >> task_b` and `task_b << task_a` for direct dependencies.
- Use `chain(...)` for readable linear chains.
- Use `@task_group(group_id="...")` to group related tasks without creating a subDag.
- Keep task group ids stable; changing a `group_id` changes fully qualified task ids and affects history.
- Avoid duplicate task ids inside a group; fully qualified ids still must be unique in the Dag.

Task group pattern:

```python
from airflow.sdk import task, task_group

@task_group(group_id="quality")
def quality_checks(records):
    @task
    def schema_check(rows): ...

    @task
    def range_check(rows): ...

    schema_check(records) >> range_check(records)
```

## Add Dynamic Task Mapping

Use dynamic mapping when the number of task instances is known only at runtime.

```python
from airflow.sdk import task

@task
def list_tables() -> list[str]:
    return ["customers", "orders"]

@task
def process_table(table: str) -> None:
    print(table)

process_table.expand(table=list_tables())
```

Mapping decisions:

- Use `.expand(x=[...])` for mapped values.
- Use `.partial(y=10)` for values shared by all mapped task instances.
- Use `.expand_kwargs(list_of_dicts)` when each mapped task instance needs a different argument set.
- Keep mapped payloads small enough for XCom and scheduler metadata.
- Add a reduce task only when downstream aggregation is required; remember mapped outputs are lazy proxies.

Common mapping review failures:

- Passing positional arguments to `.expand()`.
- Returning a non-list/non-dict value from the upstream producer.
- Using `TriggerRule.ALWAYS` with task-generated mapping.
- Eagerly converting a very large mapped output proxy to `list(...)`.

## Author Asset-Driven Dags

Producer pattern:

```python
from airflow.sdk import Asset, task

orders_asset = Asset(name="orders_daily", uri="s3://warehouse/orders/daily")

@task(outlets=[orders_asset])
def publish_orders() -> None:
    ...
```

Consumer schedule pattern:

```python
from datetime import datetime
from airflow.sdk import Asset, dag, task

orders_asset = Asset(name="orders_daily", uri="s3://warehouse/orders/daily")

@dag(dag_id="consume_orders", start_date=datetime(2024, 1, 1), schedule=[orders_asset], catchup=False)
def consume_orders():
    @task(inlets=[orders_asset])
    def read_orders() -> None:
        ...

    read_orders()

consume_orders()
```

Use `AssetAlias("name")` when the producer only knows the concrete asset URI at runtime. In the producer, emit an asset event that maps the alias to a concrete `Asset`; in the consumer, schedule on the same alias. If the UI shows an unresolved alias, first verify that a producer task with a matching outlet alias has run successfully and emitted the concrete asset event.

Use `AssetOrTimeSchedule` when a Dag must run both on time and on asset updates. Use `EventsTimetable` for a finite list of explicit datetimes. Keep asset identifiers stable; changing `name`, `uri`, or alias group can make old events stop matching new schedules.

## Choose a Timetable or Schedule

- Use `schedule=None` for manually triggered Dags.
- Use cron strings or presets for simple periodic Dags.
- Use `timedelta` for fixed intervals that do not need calendar semantics.
- Use trigger timetables for point-in-time schedules and data interval timetables when the Dag's data interval matters.
- Use asset schedules for event-driven Dags.
- Use mixed asset/time schedules only when both event and clock triggers are intentionally valid.

When reviewing a custom timetable, check serialization, timezone handling, no expensive parse-time I/O, and no direct metadata DB access from timetable construction.

## Use Params Safely

Param pattern:

```python
from datetime import datetime
from airflow.sdk import DAG, Param, get_current_context, task

with DAG(
    "parametrized_report",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    params={"region": Param("north", type="string", enum=["north", "south"])},
):
    @task
    def render_report() -> None:
        context = get_current_context()
        print(context["params"]["region"])

    render_report()
```

Review tips:

- Validate defaults against the schema; an invalid default can make the Dag fail parsing or triggering.
- Do not branch at parse time on `dag.params`; use runtime context inside tasks.
- Use `render_template_as_native_obj=True` when templated Params must remain integers, booleans, lists, or dictionaries.
- Keep Param values JSON-serializable and avoid custom Param subclasses in Dag files.

## Use XCom and Context

TaskFlow pattern:

```python
@task
def extract() -> dict[str, int]:
    return {"rows": 10}

@task
def report(metrics: dict[str, int]) -> None:
    print(metrics["rows"])

report(extract())
```

Explicit context pattern:

```python
from airflow.sdk import get_current_context, task

@task
def pull_previous() -> None:
    context = get_current_context()
    value = context["ti"].xcom_pull(task_ids="extract", key="return_value")
    print(value)
```

Use explicit XCom pulls when migrating old operator code or when a classic operator already pushes a specific key. Prefer TaskFlow return values for new Python task-to-task data flows.

## Use Variables and Connections

- Read Variables and Connections inside task execution or provider hooks, not at Dag parse time.
- `Variable.get(...)` and `Connection.get(...)` access runtime secret/config backends; treat failures as runtime configuration errors.
- Avoid using Variables for per-run inputs; Params are better for trigger-time user inputs.
- Avoid logging connection passwords, tokens, or raw URIs.

## Pick Deferrable, Sensor, or Async

- For waiting on files/events/external systems, prefer a provider sensor/operator with `deferrable=True` when available, such as `FileSensor(..., deferrable=True)`.
- Use `mode="reschedule"` sensors only when a deferrable version is unavailable and the provider supports reschedule mode.
- Use `async def` TaskFlow tasks for bounded concurrent I/O within one worker slot when no deferrable operator exists and the code uses async-compatible clients.
- Do not add `async` just for CPU-bound code or blocking libraries; it will not improve scheduler or worker efficiency.

## Validate a Dag File

Run the bundled helper:

```bash
python skills/apache-airflow/sub-skills/authoring-task-sdk/scripts/validate_dag_file.py dags/orders.py --list-dags
python skills/apache-airflow/sub-skills/authoring-task-sdk/scripts/validate_dag_file.py dags/orders.py --expect-dag-id daily_orders
```

What the helper checks:

- The file exists and can be imported by Airflow's Dag parser.
- DagBag import errors are reported with clear messages.
- At least one Dag is discovered.
- `--expect-dag-id` is present when supplied.
- `--list-dags` prints discovered Dag ids.

Use `--repo-root` only as a temporary import path when validating a Dag that imports project-local modules from a current checkout.

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Authoring Troubleshooting

## Dag File Is Not Discovered

Check these in order:

1. The file has a `.py` extension and is under the configured Dag folder.
2. The file is not excluded by `.airflowignore` patterns.
3. The file contains Airflow/Dag signals that pass safe discovery heuristics. If a file has no obvious `airflow` and `DAG`/`dag` strings, safe mode may skip it.
4. The Dag object exists at module top level. For `@dag`, call the decorated function at top level.
5. The file imports without raising exceptions in a clean parser process.
6. `dag_id` is unique across the Dag folder.

Use the bundled validator with `--list-dags` to distinguish “file imported but no Dag found” from “file import failed”.

## Import Errors After Migrating to Airflow 3

Common legacy imports and replacements:

- `from airflow import DAG`, `from airflow.models import DAG`, or `from airflow.models.dag import DAG` -> `from airflow.sdk import DAG`.
- `from airflow.decorators import dag, task, task_group` -> `from airflow.sdk import dag, task, task_group`.
- `from airflow.models import Variable` -> `from airflow.sdk import Variable`.
- `from airflow.models.param import Param` -> `from airflow.sdk import Param`.
- `from airflow.operators.python import PythonOperator, BranchPythonOperator` -> `from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator`.
- `from airflow.operators.bash import BashOperator` -> `from airflow.providers.standard.operators.bash import BashOperator`.
- `from airflow.sensors.filesystem import FileSensor` -> `from airflow.providers.standard.sensors.filesystem import FileSensor`.

If standard provider imports fail, confirm the standard provider package is installed in the target Airflow environment. The generated skill's verified package facts include `apache-airflow-providers-standard`.

## File Imports But No Dag Is Found

Likely causes:

- A decorated `@dag` function is defined but never called.
- The `DAG(...)` object is created inside a function, branch, or `if __name__ == "__main__"` block and not assigned to a top-level variable.
- `auto_register=False` is used unintentionally.
- A factory creates Dags but does not publish them into module globals.
- The validator is pointed at a helper module rather than the Dag file.

Fix by creating the Dag object at top level or explicitly assigning generated Dags into `globals()` when using a factory.

## Duplicate Task Ids

Symptoms include parse errors about duplicate task ids or missing tasks after refactoring. Check:

- Two operators or TaskFlow calls use the same `task_id`.
- A function decorated with `@task` is called multiple times without `override(task_id="...")` when distinct ids are needed.
- A task inside a `@task_group` collides with another task after group id prefixing.
- A migrated subDag pattern was flattened into a task group without updating ids.

Keep ids stable when migrating unless the user accepts historical run/task id changes.

## Invalid Params

Param failures usually come from JSON Schema mismatches:

- Default value does not match `type`, `enum`, `minimum`, `maximum`, or `items`.
- A scheduled Dag has no trigger-time override, so the default must be valid.
- A template uses `{{ params.count }}` as a string when the operator expects an integer.
- Parse-time code reads `dag.params` and expects runtime override values.

Fix by validating the default against the schema, reading runtime Params from `get_current_context()["params"]`, or enabling `render_template_as_native_obj=True` when native types are required in templated fields.

## Template and Search Path Mistakes

Common issues:

- `template_searchpath` points to a path that does not exist in the worker/parser environment.
- A templated file extension is missing from an operator's supported template extensions.
- A field is not listed in an operator's `template_fields`, so Jinja is never rendered.
- `BashOperator` treats a command ending with a templated extension as a template filename rather than inline shell text. Use `literal(...)` from `airflow.sdk` when you need to prevent templating.
- `render_template_as_native_obj` is missing when templates must render to lists, dicts, booleans, or numbers.

Keep paths deployment-relative or package-relative; do not hard-code local checkout paths into Dag files.

## Dynamic Mapping Shape Errors

Check these constraints:

- `.expand()` accepts keyword arguments only.
- Every mapped argument must be mappable: a list, dict, or upstream XComArg resolving to a list/dict.
- `.partial()` is for unmapped arguments shared by all mapped task instances.
- `expand_kwargs()` expects an iterable of dictionaries.
- Task-generated mapping cannot use `TriggerRule.ALWAYS`.
- Large mapped payloads increase scheduler and XCom pressure; pass references to external data instead of large records.

If a reduce task receives a lazy mapped-output proxy, iterate over it carefully and only cast to `list(...)` when the mapped cardinality is bounded.

## Asset-Scheduled Dag Does Not Trigger

Diagnose in this order:

1. Confirm the producer task declares the exact `Asset` in `outlets` or returns the `Asset` from a TaskFlow task.
2. Confirm the consumer Dag uses the same asset identity in `schedule` or an equivalent asset expression.
3. For `AssetAlias`, confirm a producer task with the matching `AssetAlias` outlet has actually emitted a concrete `Asset` event. Until then, the alias can appear unresolved.
4. Check `group` on `Asset` and `AssetAlias`; mismatched groups can prevent matching.
5. Distinguish asset definition metadata (`extra`) from event metadata in inlet/outlet event accessors.
6. If combining assets with time schedules, confirm whether the Dag uses asset-only scheduling, boolean asset expressions, or `AssetOrTimeSchedule`.
7. Verify the producing task succeeded; failed or skipped producer tasks may not emit the expected event.

Asset schedules are event-driven. They do not behave like cron catchup unless combined with an appropriate timetable.

## Direct Metadata DB Access Fails or Is Unsafe

Dag authoring and task code should not import ORM models such as task instances, Dag runs, or XCom rows to query or mutate the metadata database directly. In Airflow 3's Task SDK model, task execution communicates through public runtime APIs and the Execution API rather than direct DB sessions.

Use these alternatives:

- `get_current_context()` for runtime context.
- `ti.xcom_push()` / `ti.xcom_pull()` for small task-to-task messages.
- `Variable` and `Connection` public APIs for configuration/secrets.
- Provider hooks/operators for external systems.
- Assets and asset events for data-aware scheduling.

If a user needs operational metadata, route to the operations/API sub-skill rather than embedding metadata DB reads in Dag code.

## Deferrable vs Async Confusion

- Deferrable operators/sensors are for long waits and release the worker slot. Use provider support such as `deferrable=True` when available.
- Async TaskFlow tasks keep the worker slot but can multiplex concurrent I/O with `asyncio`.
- You cannot defer from inside a plain `PythonOperator` callable or `@task` function; deferral belongs to class-based operators.
- Blocking libraries inside `async def` still block; use async-compatible clients and `await` every I/O operation.
- Trigger code for custom deferrable operators must be asynchronous and serializable, but writing custom providers/operators is outside this sub-skill's boundary.

## Graphviz Optional Dependency

Graph rendering and visualization helpers can require the optional Graphviz Python/system dependencies. If visualization fails but the Dag parses, separate the optional visualization dependency from the Dag authoring issue:

- Validate parse/discovery with the bundled script first.
- Avoid adding Graphviz imports to top-level Dag code unless the deployment image includes them.
- Route deployment image/package installation questions to the deployment sub-skill.

## Provider Operator Missing or Behavior Changed

- Confirm the provider package is installed in the target environment.
- Use provider-specific import paths, not old core operator paths.
- Check whether a provider operator supports `deferrable`, templated fields, or XCom pushing before assuming behavior from a different operator.
- For broad provider implementation or packaging work, route to the provider/extension sub-skill.

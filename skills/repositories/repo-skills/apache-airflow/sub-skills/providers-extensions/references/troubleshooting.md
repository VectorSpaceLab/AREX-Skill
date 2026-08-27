<!-- SPDX-License-Identifier: Apache-2.0 -->

# Providers And Extensions Troubleshooting

Use this when provider imports, custom extensions, provider metadata, or generated provider files fail.

## Provider Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'airflow.providers.standard'`
- `ModuleNotFoundError` for a specific provider package
- A Dag parses locally but fails in scheduler/worker deployment

Likely causes and fixes:

- The provider package is not installed in every Airflow component that parses or executes the Dag. Install the explicit package, such as `apache-airflow-providers-standard`, in scheduler, Dag processor, workers, triggerer, and any image used to parse Dags.
- An Airflow extra was expected to install the provider but was not used in this environment. Prefer explicit provider package requirements for Dags that import provider code.
- The import path is stale. Airflow 3 Dag authoring should use `airflow.sdk` for public SDK imports and `airflow.providers.<provider>...` for provider classes.
- A provider’s optional dependency is missing. Install the provider extra or dependency required by the operator/hook feature, not only the base provider package.

## `BashOperator` Or `FileSensor` Missing

In the verified package set, `BashOperator` and `FileSensor` are part of the standard provider, not just core Airflow.

- Use `from airflow.providers.standard.operators.bash import BashOperator`.
- Use `from airflow.providers.standard.sensors.filesystem import FileSensor`.
- Ensure `apache-airflow-providers-standard` is installed. The verified standard provider version for this skill is `1.15.0`.
- For `FileSensor`, ensure the `fs_conn_id` exists or defaults correctly to `fs_default`, and that the connection extra JSON contains a valid `path` when using `FSHook`.

## Connection ID Or Hook Problems

Symptoms:

- Hook cannot find a connection id.
- UI does not show the expected connection type.
- Connection test fails or is unavailable.

Fixes:

- Confirm the hook defines `conn_name_attr`, `default_conn_name`, `conn_type`, and `hook_name`.
- Confirm `provider.yaml` has a matching `connection-types` entry with the hook class path and `connection-type`.
- Confirm the provider package is installed in the webserver/API server so the connection type is discoverable in UI/API contexts.
- For environment variable connections, use `AIRFLOW_CONN_<CONN_ID>` uppercase naming. Environment-defined connections are resolved dynamically and do not appear in the UI or `airflow connections list`.
- Keep `test_connection()` safe and bounded. Airflow disables test connection functionality by default for security reasons; absence of a UI test button is not necessarily a provider bug.

## Custom Operator Behaves Slowly Or Breaks Dag Parsing

Likely causes:

- The operator constructor creates hooks, clients, network calls, or database queries.
- Module import time performs service discovery or loads credentials.
- Templated fields refer to constructor argument names that differ from stored attribute names.

Fixes:

- Move service work into `execute`, `poke`, trigger code, or helpers called from execution.
- Store only constructor arguments in `__init__` and call `super().__init__(**kwargs)`.
- Ensure every name in `template_fields` is an instance attribute.
- Use a hook for reusable service access rather than duplicating client setup across operators.

## Bash Templating Or Exit Codes Surprise Users

- A Bash command that contains failing subcommands may still succeed if the shell exits with zero. Prefix with `set -e;` when any failing subcommand should fail the task.
- The standard Bash operator skips by default on exit code `99`; set `skip_on_exit_code=None` if any non-zero exit should fail.
- Do not inject user-controlled `dag_run.conf` directly into `bash_command`. Pass it through `env` and reference the environment variable from the command.
- A `.sh` or `.bash` command string is treated as a template file path. Add a trailing space when you want to execute a script path without template loading.

## Deferrable Sensor Or Trigger Fails

Symptoms:

- Non-deferrable mode works, deferrable mode fails.
- Trigger class cannot be imported.
- Task defers but never resumes.

Fixes:

- Ensure the trigger module is installed in triggerer and worker images.
- Ensure the trigger class is listed under `triggers` in provider metadata when it is public provider functionality.
- Keep trigger kwargs serializable. Do not pass hooks, clients, open files, or connection objects to triggers.
- Confirm the triggerer component is running and has the same provider packages as the scheduler/worker where needed.
- Test `serialize()`/event output for triggers and `execute_complete()` event handling for operators/sensors.

## Plugin Does Not Load Or Update

- Confirm the plugin class subclasses `airflow.plugins_manager.AirflowPlugin` and sets `name`.
- Confirm the module is importable from the deployment’s plugin path or package environment.
- Run `airflow plugins` to inspect loaded plugins.
- Restart scheduler/webserver/workers as needed. Plugins are lazily loaded by default and are not always reloaded in long-running processes.
- Define `on_load(*args, **kwargs)` rather than a narrow signature to tolerate future parameters.

## Listener Registration Fails

- Listener functions must use `airflow.listeners.hookimpl`.
- Method parameter names must match the listener hookspec exactly; Pluggy rejects incompatible signatures.
- Register the listener module through a plugin’s `listeners` list.
- Keep listener code lightweight and fault-tolerant because it runs inside Airflow components.
- For version-spanning plugins, account for listener signature changes across Airflow versions.

## Timetable Is Not Available Or Schedules Incorrectly

- Register timetable classes through a plugin’s `timetables` list.
- Return timezone-aware `pendulum` datetimes from timetable logic.
- Implement both `infer_manual_data_interval` and `next_dagrun_info` for predictable manual and scheduled runs.
- Implement `serialize()` and `deserialize()` for parameterized timetables.
- Respect `restriction.earliest`, `restriction.latest`, and `restriction.catchup` in `next_dagrun_info`.

## Notifier Does Not Render Or Send

- Subclass `airflow.sdk.BaseNotifier`.
- Add fields that need Jinja rendering to `template_fields`.
- Implement `notify(context)` for sync sending; implement `async_notify(context)` only for async-capable clients.
- Resolve credentials through connections, secrets, or deployment config, not constructor literals.
- Test callbacks with realistic context dictionaries and mocked clients.

## Provider Metadata Check Fails

- If `provider.yaml` package name differs from `pyproject.toml` project name, align the provider id and package naming.
- If the `apache_airflow_provider` entry point is missing, add it to `pyproject.toml` so Airflow can discover provider info.
- If `get_provider_info.py` package name differs, do not hand-edit it. Regenerate provider files from metadata.
- If modules listed in `provider.yaml` do not exist, either add the module, fix the module path, or remove stale metadata.
- If the checker warns that generated headers are missing, verify whether the file is truly generated before editing manually.

## Docs, Changelog, And Generated File Mistakes

- Provider user-visible changes belong in the provider changelog, not an Airflow core newsfragment.
- Do not add provider newsfragments; provider release managers use provider changelogs.
- Do not hand-edit generated `get_provider_info.py`, generated docs indexes, README files, or generated `pyproject.toml` sections outside preserved dependency blocks.
- When changing dependencies, update the dependency section and run the repository’s dependency update/check workflow when available.
- If a generated file changes unexpectedly, identify the metadata/template input that produced it instead of polishing generated output by hand.

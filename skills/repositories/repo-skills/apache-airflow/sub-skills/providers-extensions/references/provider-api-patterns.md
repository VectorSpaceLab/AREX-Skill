<!-- SPDX-License-Identifier: Apache-2.0 -->

# Provider API Patterns

This reference distills Airflow provider and extension conventions from the public interface, provider metadata, and the standard provider. It is self-contained and does not require opening the original repository.

## Public Extension Boundaries

- `airflow.sdk` is the stable public namespace for Dag authors and task execution. Use it for `BaseOperator`, `BaseSensorOperator`, `BaseHook`, `BaseNotifier`, `BaseOperatorLink`, `Connection`, `Variable`, `Context`, `DAG`, and task decorators where available.
- Custom operators and sensors may subclass `airflow.sdk.BaseOperator` and `airflow.sdk.BaseSensorOperator`; custom hooks may subclass `airflow.sdk.BaseHook`.
- Published Airflow operator parameters and behavior are public, but operator internals and protected/private methods are not stable. Do not build new provider behavior by overriding undocumented internals.
- Providers can expose operators, sensors, hooks, triggers, decorators, connection types, extra links, notifiers, timetables, secrets backends, logging integrations, and plugin endpoints.
- Direct metadata database access from task code is not part of the public interface. Use task context, `airflow.sdk` utilities, REST APIs, or provider hooks that operate through supported interfaces.

## Package And Import Naming

- Provider distribution names use the `apache-airflow-providers-<provider-id>` pattern. Nested provider ids use hyphens in package names and slash/dot-like source paths, for example `apache-airflow-providers-common-sql` maps to `airflow.providers.common.sql`.
- Provider source modules live under `airflow.providers.<provider_id>`, such as `airflow.providers.standard`, `airflow.providers.postgres`, or `airflow.providers.common.sql`.
- Provider packages expose an entry point in `pyproject.toml`:
  - group: `apache_airflow_provider`
  - name: usually `provider_info`
  - target: `airflow.providers.<provider>.get_provider_info:get_provider_info`
- `provider.yaml` and `get_provider_info()` must describe the same provider package, modules, connection types, hooks, operators, sensors, triggers, decorators, and extra links.

## Extras And Provider Selection

- Airflow core installation does not imply every provider is installed. If a Dag imports `airflow.providers.standard.operators.bash.BashOperator`, the environment needs `apache-airflow-providers-standard` or an Airflow extra that includes it.
- Prefer explicit provider packages in deployment requirements when a Dag depends on provider imports. Extras are convenient for installation bundles, but explicit packages make dependency ownership clearer.
- Standard provider verified package facts for this generated skill: `apache-airflow-providers-standard` version `1.15.0` and import root `airflow.providers.standard`.
- Common standard provider imports:
  - `airflow.providers.standard.operators.bash.BashOperator`
  - `airflow.providers.standard.operators.python.PythonOperator`, `BranchPythonOperator`, `ShortCircuitOperator`
  - `airflow.providers.standard.operators.empty.EmptyOperator`
  - `airflow.providers.standard.operators.trigger_dagrun.TriggerDagRunOperator`
  - `airflow.providers.standard.sensors.filesystem.FileSensor`
  - `airflow.providers.standard.sensors.python.PythonSensor`
  - `airflow.providers.standard.hooks.filesystem.FSHook`
  - `airflow.providers.standard.hooks.subprocess.SubprocessHook`

## Standard Operator Patterns

- Operators should keep `__init__` cheap: store parameters, call `super().__init__(**kwargs)`, and avoid network calls, database calls, filesystem probes, or hook construction that can run on every Dag parse.
- Put runtime behavior in `execute(self, context)` or helpers called by `execute`. If a service operation needs a hook, create the hook in `execute`, not in the constructor.
- Set `template_fields` to attribute names that should be rendered, not necessarily constructor argument names. If file extensions should be loaded and rendered, set `template_ext` and ensure the Dag’s template search path or working directory is appropriate.
- Add `template_fields_renderers` for UI rendering when fields hold JSON, SQL, Bash, YAML, Markdown, or nested values.
- UI attributes such as `ui_color`, `ui_fgcolor`, and `custom_operator_name` are safe presentation customization points.
- For shell execution, pass user-controlled templated values through `env` instead of interpolating them directly into shell strings. Prefix Bash snippets with `set -e;` when failures in subcommands should fail the task.
- Use specific public exceptions or provider-specific exceptions where possible. In Airflow repository production code, avoid adding new direct `AirflowException` raises unless narrowing an existing case is impossible.

## Standard Sensor And Trigger Patterns

- Sensors subclass `BaseSensorOperator` and implement `poke(self, context) -> bool` for polling behavior.
- Deferrable sensors/operators should pair a runtime class with a trigger class and an `execute_complete` callback. The standard `FileSensor` uses `FileTrigger` when deferrable.
- Deferrable behavior requires the triggerer component and any provider trigger dependencies to be available in the deployment. If a sensor works in non-deferrable mode but not in deferrable mode, check trigger imports and triggerer status.
- `start_from_trigger` and `StartTriggerArgs` are advanced patterns for starting work directly in the triggerer; keep their arguments serializable and aligned with the trigger constructor.

## Standard Hook Patterns

- Hooks represent reusable service/client access and connection lookup. Operators should call hooks instead of embedding all client setup inline when the integration can be reused.
- Hooks commonly define:
  - `conn_name_attr`, for the operator argument storing the connection id.
  - `default_conn_name`, such as `fs_default` for `FSHook`.
  - `conn_type`, such as `fs`.
  - `hook_name`, the display name for connection UI.
  - `get_connection_form_widgets()` for custom UI fields when needed.
  - `get_ui_field_behaviour()` for hidden fields, relabeling, and placeholders.
  - `test_connection()` returning `(bool, message)` when safe.
- The standard `FSHook` stores its base path in the connection extra JSON field `path`; `FileSensor` joins this base path with its templated `filepath`.

## Provider Metadata Sections

A provider can advertise these common capabilities in `provider.yaml` and generated `get_provider_info()`:

- `integrations` with integration names, external docs, tags, logos, and how-to guide paths.
- `operators`, `sensors`, `hooks`, and `triggers`, each grouped by `integration-name` and listing Python modules.
- `connection-types` mapping `hook-class-name`, `hook-name`, and `connection-type`, with optional UI behavior and custom fields.
- `extra-links` listing `BaseOperatorLink` class paths.
- `task-decorators` listing decorator class paths and decorator names.
- `config` sections for provider-specific configuration.
- Other provider families may include dialects, secrets backends, log handlers, executors, notifiers, transfers, auth managers, or queue providers.

## Testing Expectations

- Operator tests should cover constructor assignment, templated fields, execution branches, exceptions, and hook interactions using `mock` with `spec` or `autospec`.
- Hook tests should cover connection lookup, UI field behavior, client construction, safe connection tests, and error translation without requiring real external services.
- Sensor tests should cover `poke` true/false behavior, timeout/error handling, deferrable `defer` setup, and `execute_complete` handling.
- Trigger tests should cover async event output and serialization without depending on live external systems.
- Provider metadata tests or checks should verify that `provider.yaml`, generated `get_provider_info()`, package entry points, docs, and package names remain aligned.

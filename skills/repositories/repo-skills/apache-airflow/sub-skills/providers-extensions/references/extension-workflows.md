<!-- SPDX-License-Identifier: Apache-2.0 -->

# Extension Workflows

Use these recipes when implementing provider-backed behavior or custom Airflow extensions. They focus on public interfaces and provider conventions.

## Add A Provider Operator

1. Pick the provider package and module path: `airflow.providers.<provider>.operators.<domain>`.
2. Subclass `airflow.sdk.BaseOperator` or the provider compatibility base used by that provider.
3. Keep `__init__` cheap: call `super().__init__(**kwargs)`, store typed parameters, and avoid hook/client/network/database work.
4. Add `template_fields`, `template_ext`, and `template_fields_renderers` for user-controlled runtime values.
5. Put service interaction in `execute(self, context)`; create hooks inside `execute` or helpers called from it.
6. Return only serializable values that make sense for XCom. Avoid returning large payloads, credentials, or service clients.
7. Add or update provider metadata so the module is listed under `operators` for the correct `integration-name`.
8. Add focused unit tests for constructor assignment, templating declarations, success, failure, hook calls, and any provider-specific exceptions.

## Add A Provider Sensor

1. Subclass `airflow.sdk.BaseSensorOperator` or the provider compatibility base.
2. Implement `poke(self, context) -> bool` for non-deferrable polling behavior.
3. For deferrable mode, add a trigger class and call `self.defer(...)` from `execute` when the condition is not immediately met.
4. Implement `execute_complete(self, context, event)` to validate trigger events and raise a clear error for failure events.
5. Keep trigger kwargs JSON-serializable and avoid passing clients, connections, or non-serializable objects.
6. List the sensor module under `sensors` and the trigger module under `triggers` in provider metadata.
7. Test `poke`, deferral arguments, trigger serialization/events, and `execute_complete` success/failure.

## Add A Provider Hook And Connection Type

1. Subclass `airflow.sdk.BaseHook` or the provider compatibility base.
2. Define `conn_name_attr`, `default_conn_name`, `conn_type`, and `hook_name`.
3. Use `self.get_connection(conn_id)` to resolve Airflow connections and read `conn.extra_dejson` for structured extras.
4. Keep low-level client creation in `get_conn()` or named helper methods; do not create a client in module import time.
5. Add `get_connection_form_widgets()` only when the provider needs custom UI fields.
6. Add `get_ui_field_behaviour()` to hide irrelevant fields, relabel fields, and provide placeholders.
7. Implement `test_connection()` only when it is safe and bounded. Return `(False, message)` rather than raising for expected validation failures.
8. Add a `connection-types` metadata entry with `hook-class-name`, `hook-name`, and `connection-type`.
9. Test connection parsing, custom UI behavior, client construction, and safe failure messages with mocked external clients.

## Add A Custom Operator In A Deployment

1. Put the custom operator in importable Python code available to the deployment, such as a packaged library, `dags/`, `plugins/`, or `config/`.
2. Import public bases from `airflow.sdk` where possible.
3. Keep the constructor parse-safe and move service work into `execute`.
4. If the operator talks to a service, split reusable connection/client logic into a hook.
5. Use the operator from a Dag with a stable import path. If it lives under `plugins/`, remember that long-running components may need a restart to reload plugin code.
6. Add a Dag parsing smoke test and unit tests for operator behavior.

## Add A Plugin

1. Create an `AirflowPlugin` subclass with a required `name`.
2. Register only the components needed: `macros`, `fastapi_apps`, `fastapi_root_middlewares`, `external_views`, `react_apps`, `global_operator_extra_links`, `operator_extra_links`, `timetables`, `deadline_references`, or `listeners`.
3. Keep `on_load(*args, **kwargs)` tolerant of extra arguments for forward compatibility.
4. Restart scheduler/webserver/workers as needed because plugins are lazily loaded and not always reloaded in long-running processes.
5. Use `airflow plugins` to inspect loaded plugins when debugging.
6. Test importability of the plugin module and the registered components without starting a full deployment when possible.

## Add A Listener

1. Implement listener methods decorated with `airflow.listeners.hookimpl`.
2. Match the hookspec parameter names exactly. Pluggy rejects implementations with incompatible signatures.
3. Register the listener module through an Airflow plugin’s `listeners` list.
4. Keep listener code lightweight and failure-tolerant because listeners run inside Airflow components and can slow or break them.
5. Do not use listeners for one specific Dag or one specific operator. Use Dag/operator callbacks such as `on_success_callback`, `on_failure_callback`, `pre_execute`, or `post_execute` for local behavior.
6. If supporting multiple Airflow versions, branch on installed Airflow version for listener signature changes.

## Add A Timetable

1. Subclass `airflow.timetables.base.Timetable`.
2. Register the timetable class through an Airflow plugin’s `timetables` list.
3. Implement `infer_manual_data_interval(run_after)` for manually triggered runs.
4. Implement `next_dagrun_info(last_automated_data_interval, restriction)` for scheduled runs.
5. Return timezone-aware `pendulum` datetimes. Timetable intervals and `run_after` values must be aware.
6. For parameterized timetables, implement `serialize()` and `deserialize()` using JSON-serializable values.
7. Consider overriding `summary` for a useful schedule label in the UI.
8. Test manual interval inference, next-run calculation, catchup/restriction handling, serialization round trips, and plugin registration.

## Add A Notifier

1. Subclass `airflow.sdk.BaseNotifier`.
2. Add `template_fields` for message fields that should render from task context.
3. Implement `notify(self, context)` for synchronous notifications.
4. Implement `async_notify(self, context)` only if the notifier supports async sending.
5. Use notifiers in callback slots such as task or Dag failure/success callbacks.
6. Avoid embedding credentials in notifier instances; resolve credentials through connections, secrets backends, or deployment configuration.
7. Test templating, message construction, sync/async send paths, and failure behavior with mocked clients.

## Add An Extra Link

1. Subclass `airflow.sdk.BaseOperatorLink`.
2. Set a human-readable `name`.
3. Implement `get_link(self, operator, *, ti_key)` and return the URL to show in task details.
4. Attach operator-specific links with `operator_extra_links = (MyLink(),)` on the operator class.
5. Register global or overriding links through plugin `global_operator_extra_links` or `operator_extra_links`, or provider metadata `extra-links`.
6. Persist link state through XCom only when the link needs runtime values that are not available from task identifiers.
7. Test URL construction and override behavior using task instance keys with realistic `dag_id`, `task_id`, `run_id`, and `map_index` values.

## Add Or Maintain A Provider Package

1. Confirm the provider id, source module, and distribution name align:
   - distribution: `apache-airflow-providers-<id-with-hyphens>`
   - module: `airflow.providers.<id.with.dots>`
   - metadata file: `provider.yaml`
2. Add source under the provider’s `src/airflow/providers/...` subtree.
3. Add tests under the provider’s `tests/unit/...` subtree mirroring operators, hooks, sensors, triggers, decorators, and utils.
4. Update `provider.yaml` for new public modules and capabilities.
5. Update dependency sections in `pyproject.toml` only in the preserved generated-file sections when dependencies change.
6. Add or update provider docs and changelog only when user-visible behavior changes. Provider changelogs live in provider docs, not Airflow core newsfragments.
7. Run the bundled checker: `python scripts/check_provider_metadata.py --provider-dir <provider-dir>`.
8. Run focused provider tests for changed modules and any project-required formatting/linting in the appropriate environment.

## Safe Review Checklist

- Public imports use `airflow.sdk` or documented provider compatibility modules, not unstable internals.
- Constructors do not perform expensive work or create external connections.
- Connections use connection ids and extras, not hard-coded credentials.
- Deferrable operators/sensors have trigger coverage and triggerer dependency notes.
- Provider metadata lists new modules and connection types.
- Generated files are not hand-edited outside preserved dependency sections.
- Unit tests mock external services and cover the behavior changed by the patch.

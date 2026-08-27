# Configuration and Resource Troubleshooting

## Import or Install Errors

Symptom: `ModuleNotFoundError: No module named 'dagster'` or CLI help works in one shell but tests fail in another.

Fix:

- Verify the command runs in the environment where Dagster is installed.
- Check `python -c "import dagster; print(dagster.__version__)"` before debugging application code.
- If repository code uses optional integrations, install the package that provides the integration instead of adding it to core config/resource code.
- Keep examples that only need `dagster` free of integration-specific imports so config/resource tests remain lightweight.

## Pydantic Validation Failures

Symptom: constructing a `Config`, `PermissiveConfig`, or `ConfigurableResource` raises a validation error before Dagster execution starts.

Fix:

- Check Python type annotations first; Dagster's Pythonic config is Pydantic-backed.
- Use `Field(default=..., gt=..., description=...)` for constraints and documentation.
- Use `PermissiveConfig` only when extra keys are intentional. With `Config`, misspelled or unexpected fields should fail.
- For nested config, pass nested config objects or dictionaries that match the nested model fields.
- For enums, prefer enum values or names consistently and assert the final `RunConfig.to_config_dict()` shape.

## Wrong Run Config Shape

Symptom: `DagsterInvalidConfigError`, missing `config` wrappers, or values appear under the wrong node/resource key.

Fix:

- Prefer `dg.RunConfig(ops={...}, resources={...})` in Python code.
- Use node names under `ops`, not arbitrary class names. Assets usually use the asset op name unless a job/graph changes the node path.
- Use resource keys under `resources`, matching `Definitions(resources={"key": ...})` and asset/op parameter names.
- Run `dg.validate_run_config(job_def, run_config)` when a job definition is available.
- Print or assert `RunConfig(...).to_config_dict()` in tests to compare with the launchpad/YAML shape.

## EnvVar Resolves Too Early or Not at All

Symptoms:

- Direct `str(dg.EnvVar("TOKEN"))`, `print(dg.EnvVar("TOKEN"))`, or `int(dg.EnvVar.int("PORT"))` raises an exception.
- A field receives the literal string `"TOKEN"` instead of the environment value.
- A raw unstructured run config dict containing `EnvVar` fails validation.

Fix:

- Put `EnvVar` inside a `Config`, `RunConfig`, `ConfigurableResource`, or Dagster-supported config object.
- Use `.get_value(default=...)` only in standalone code that intentionally reads the environment outside Dagster.
- For nested resources, define the sub-resource as a typed field on the parent resource so Dagster initializes it.
- Do not instantiate a sub-resource with `EnvVar` at module scope and then manually read it inside a parent resource method.
- Use `EnvVar.int("NAME")` for integer config fields.

## Resource Dependency Validated as Config

Symptom: a callable, client object, string-like resource, or IO manager dependency is treated like config and fails schema inference or validation.

Fix:

- Annotate non-config dependencies with `dg.ResourceDependency[T]`.
- If assets/ops should receive a third-party object, override `create_resource` and annotate user code with `dg.ResourceParam[ClientType]`.
- Keep config values and resource dependencies separate in class fields.
- If the dependency is itself a `ConfigurableResource`, use a typed field directly and let Dagster resolve nested resources.

## Launch-Time Resource Config Missing

Symptom: a resource registered with `configure_at_launch()` fails because required config was not supplied.

Fix:

- Supply `dg.RunConfig(resources={"resource_key": ResourceClass(...)})` when executing in Python.
- In raw YAML or dict config, place values under `resources: resource_key: config:`.
- Check that the resource key matches the key in `Definitions`, not necessarily the class name.
- For nested launch-time resources, include top-level resources that require launch-time config in `Definitions` so Dagster can collect their schema.

## Lifecycle Hook Surprises

Symptom: setup/teardown code does not run in a unit test, or runs more often than expected.

Fix:

- Direct resource instantiation does not exercise Dagster resource lifecycle.
- Use `Definitions`, `materialize`, `execute_in_process`, or `build_resources` to test lifecycle behavior.
- Keep external side effects out of constructors; put them in `setup_for_execution`, `yield_for_execution`, `teardown_after_execution`, or lazy methods.
- In tests, use fakes/mocks for external systems and assert calls through the Dagster execution path.

## ConfigurableIOManager Issues

Symptoms:

- Asset materialization cannot find `io_manager`.
- `handle_output` or `load_input` receives unexpected context values.
- The IO manager needs a separate runtime object but subclasses `ConfigurableIOManager` directly.

Fix:

- Register the default IO manager under the resource key `io_manager`, or configure asset-level IO manager keys consistently.
- Use `ConfigurableIOManager` when the class implements the IO manager protocol directly.
- Use `ConfigurableIOManagerFactory` when config should create and return a separate IO manager instance.
- Test with actual materialization when behavior depends on `OutputContext`, `InputContext`, asset keys, partitions, or metadata.

## CLI/API Misuse

Symptom: a config example works in Python but fails from the CLI or Launchpad.

Fix:

- Python APIs can pass `RunConfig` and structured objects; CLI and Launchpad use YAML/dict run config shapes.
- Convert examples with `RunConfig(...).to_config_dict()` to see the equivalent dictionary shape.
- Do not put Python objects, clients, callables, or `EnvVar(...)` constructors in YAML. Use Dagster's environment variable YAML representation or define the value in Python code.
- If a schedule/sensor returns run config, test the final run config emitted by the schedule/sensor, not only the helper that builds it.

## Optional Dependency Gaps

Symptom: resource code imports a database/cloud/client library that is absent in the base Dagster environment.

Fix:

- Keep the `ConfigurableResource` model importable without optional clients when possible.
- Import optional clients lazily inside `create_resource`, `setup_for_execution`, or the method that actually needs them.
- Raise an actionable error naming the missing optional package.
- In tests for core config conversion, replace external clients with fakes so the test only requires `dagster`.

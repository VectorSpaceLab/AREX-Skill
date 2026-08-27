# Component Project Troubleshooting

Use this when component project creation, `dg`/`create-dagster`, YAML/template validation, component loading, or component tests fail.

## Fast Environment Triage

Start with the bundled non-mutating doctor:

```bash
python skills/dagster/sub-skills/components-projects/scripts/component_project_doctor.py
python skills/dagster/sub-skills/components-projects/scripts/component_project_doctor.py --json
python skills/dagster/sub-skills/components-projects/scripts/component_project_doctor.py --require-dg
```

Interpretation:

- `dagster` import failure means no Dagster runtime is available in the active Python environment.
- `dagster.components` import failure means the installed Dagster package does not include component APIs or the environment is broken.
- Missing `dg` or `create-dagster` command entry points means component project CLI tooling is not installed or not on `PATH`.
- Missing `dagster_dg_cli`, `dagster_dg_core`, or `create_dagster` modules often points to optional/development dependency gaps rather than user-code errors.

## `dg` Or `create-dagster` Is Unavailable

Symptoms:

```text
dg: command not found
create-dagster: command not found
No module named 'dagster_dg_cli'
No module named 'dagster_dg_core'
No module named 'create_dagster'
No matching distribution found for dagster-cloud-cli==1!0+dev
```

Likely causes:

- The active environment installed `dagster` but not the newer project/component CLI packages.
- The command exists in a virtual environment that is not active or not on `PATH`.
- A local Dagster source checkout references unpublished development versions, including a `dagster-cloud-cli==1!0+dev` dependency required by some `dg` packages.
- The user is in a source checkout where `dg` was intentionally not verified because its dependency closure cannot be satisfied from public packages.

Safe response:

1. Run the doctor script and show command/module availability.
2. If only `dagster` is available, use Python-level component APIs and route classic CLI work to the local CLI sub-skill.
3. Do not run package installation or editable installs unless the user approves environment mutation.
4. If the task explicitly needs `dg`, explain that the environment needs a compatible install of the `dg` packages and any unpublished dev dependencies used by the checkout.
5. For source checkouts with the unpublished dependency gap, skip `dg` native tests and document the skip.

## Project Config Errors

Symptoms:

```text
Could not find dg.toml or pyproject.toml
TOML configuration file errors
workspace.scaffold_project_options must be a dict
```

Fixes:

- Run `dg check toml` from the project root or pass the command's path option if supported by the installed version.
- Confirm the project root contains `pyproject.toml` or the workspace root contains `dg.toml`.
- Keep workspace settings under workspace config and project settings under project config.
- If both `dg.toml` and `pyproject.toml` exist in relevant parents, confirm which one the current command discovers.
- Avoid moving generated `defs` or `components` directories without updating project metadata.

## Component Discovery Misses A Custom Type

Symptoms:

```text
dg list components does not show MyComponent
Unknown component type
Could not import registry module
```

Checks:

- Confirm the project package is installed in the active environment.
- Import the module directly with `python -c "import my_project.components.my_component"`.
- Confirm the component class inherits from `dagster.Component`.
- Confirm YAML-configurable components also inherit from `dagster.Resolvable` and a model base such as `dagster.Model`.
- Confirm the component module is listed in project registry metadata or is exposed through the installed package's supported entry mechanism.
- Avoid import-time network calls, database connections, or secret reads in component modules; discovery imports modules.

## `defs.yaml` Schema Or Type Errors

Symptoms:

```text
Check defs.yaml files against their schemas
Unknown field in attributes
field required
Object type ... does not have a scaffolder
component directory requires defs.yaml or component.py
```

Fixes:

- Use `dg check yaml path/to/defs.yaml` for source-positioned schema errors.
- Confirm top-level YAML has a `type` that resolves to an importable component type.
- Put user parameters under `attributes`, not as arbitrary top-level keys unless the component's schema explicitly supports them.
- Match attribute names to the component class annotations exactly.
- Use `ResolvedAssetKey`, `ResolvedAssetSpec`, and `ResolvedAssetCheckSpec` shapes where component schemas expect them; do not pass raw strings where a structured spec is required unless the installed schema documents that shorthand.
- Ensure custom scaffolders write either `defs.yaml` or `component.py` into the target directory.
- Re-run `dg check defs` after YAML succeeds, because YAML validation does not prove that generated definitions are valid.

## Template Variable Failures

Symptoms:

```text
template_vars_module could not be imported
UndefinedError: ... is undefined
Invalid template variable signature
Wrong context type
```

Fixes:

- For colocated helpers, prefer `template_vars_module: .template_vars` and put `template_vars.py` next to the component YAML/module path expected by the loader.
- For shared helpers, use an absolute module path that imports in the active project environment.
- Template functions should take zero parameters or one parameter annotated as `dagster.ComponentLoadContext`.
- Static template variables on a component class should follow the same zero-argument or context-argument rule.
- Keep template functions deterministic; avoid reading secrets, connecting to services, or mutating files during YAML validation.
- If the template depends on component path/name, use the context-aware form instead of guessing filesystem paths.

## `@dagster.definitions` Signature Errors

Symptoms:

```text
Function requires a ComponentLoadContext but none was provided
Function must accept either no parameters or exactly one ComponentLoadContext parameter
Function must return a Definitions or RepositoryDefinition object
```

Fixes:

- Use either `def defs() -> dg.Definitions` or `def defs(context: dg.ComponentLoadContext) -> dg.Definitions`.
- Do not add extra parameters, even optional ones.
- Annotate the context parameter with the actual `dagster.ComponentLoadContext` class used by the installed Dagster version.
- Return a `dg.Definitions` object, not a list of assets or a bare asset function.
- If a direct unit test calls a context-aware definitions function, pass the proper component loading context through component tree APIs instead of calling it manually.

## Component Test Failures

Symptoms:

```text
ComponentTree.for_project cannot find project root
load_component cannot find path
build_defs_at_path fails
materialize fails after defs load succeeds
```

Fixes:

- Pass the project root directory to `ComponentTree.for_project`, usually the directory containing project metadata.
- Pass component paths relative to the project `defs` folder, not absolute paths.
- Separate load assertions from execution assertions: first confirm `tree.load_component`, then `tree.build_defs_at_path`, then materialize only safe pure-local assets.
- If execution fails due to resources, IO managers, credentials, or external services, route resource/config issues to the configuration-resources sub-skill and avoid pretending YAML validation should catch them.
- If the component returns jobs/schedules/sensors as well as assets, inspect the `Definitions` object rather than assuming asset materialization is the right smoke test.

## `dg check defs` Fails After `dg check yaml` Passes

Likely causes:

- Component YAML is schema-valid but `build_defs` produces invalid or conflicting Dagster definitions.
- Import-time side effects fail during full definitions loading.
- Asset keys collide across component paths.
- A resource, IO manager, or environment-dependent object is required at definitions construction time.
- The command is running in a workspace context where the expected project environment differs from the active shell environment.

Fixes:

- Re-run with debug or verbose flags supported by the installed version.
- Set `DAGSTER_IS_DEFS_VALIDATION_CLI=1` behavior in user code only to skip expensive validation-time side effects, not to hide real definition errors.
- Load one component path in a Python test with `ComponentTree.for_project` to isolate the failing component.
- Resolve asset key collisions or invalid definitions in the component's `build_defs` method.
- If the error is unrelated to components, route to asset-definitions or configuration-resources.

## Scaffolding Misuse

Symptoms:

```text
A file or directory already exists
Workspace already exists
The current workspace already specifies a project
scaffold must be either 'yaml' or 'python'
```

Fixes:

- Use a new target directory for `create-dagster project <path>`, or pass `.` only when intentionally scaffolding into the current directory.
- Use `create-dagster project` to add a project inside an existing workspace; do not nest a new workspace inside a workspace.
- Confirm custom scaffold format is `yaml` or `python`.
- Ask before using `--uv-sync` because it can mutate the environment by creating lockfiles and virtual environments.
- If the target path already has user files, inspect before overwriting; do not delete files to make scaffolding pass.

## Optional Dependency Gaps

Component projects can reference optional or development-only dependencies. Handle these as environment issues:

- Missing `dagster-webserver`: `dg dev` or web UI docs cannot start; component APIs may still load.
- Missing `dagster_dg_cli`: `dg` command and CLI tests cannot run.
- Missing `create_dagster`: modern project/workspace scaffolding command cannot run.
- Missing `dagster-cloud-cli` development package: local checkout `dg` packages may be un-installable from public package sources.
- Missing provider integration libraries: generic component registration may work, but provider-specific component instances should be routed or skipped.

Do not add cloud-only dependencies or run network/credentialed commands unless the user explicitly requests that setup.

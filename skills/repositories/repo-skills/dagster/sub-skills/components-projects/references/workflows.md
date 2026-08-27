# Component Project Workflows

This reference is self-contained for agents working in a Dagster environment with component support installed. Commands are intentionally local and offline-safe unless a note says otherwise.

## Choose The Tooling Path

Use this decision order:

1. If the user wants a modern component-ready project or workspace, use `create-dagster` when it is installed.
2. If the user is inside an existing component-ready project, use `dg` for component discovery, scaffolding, and validation.
3. If `dg` or `create-dagster` is unavailable, run the bundled doctor script and fall back to Python-level component APIs or legacy `dagster project` scaffolding where appropriate.
4. If the task is about assets or jobs after component loading, route to the asset-definitions sub-skill.

Run help before relying on flags in an unknown version:

```bash
create-dagster --help
create-dagster project --help
create-dagster workspace --help
dg --help
dg list components --help
dg scaffold --help
dg check yaml --help
dg check defs --help
```

If those commands are absent, do not install them automatically. From this sub-skill directory, first run:

```bash
python scripts/component_project_doctor.py --json
```

## Component-Ready Project Layout

A `create-dagster project <path>` scaffold creates a Python package layout shaped for components:

```text
<project>/
  pyproject.toml
  src/<project_package>/
    definitions.py
    defs/
      __init__.py
    components/
      __init__.py
  tests/
    __init__.py
```

Operational conventions:

- Component instances live under the package `defs` tree.
- Reusable component classes live under the package `components` module.
- Project metadata configures the package root and registry modules so `dg list components` can find custom component types.
- In a workspace scaffold, `dg.toml` describes workspace/project membership; a project-level `pyproject.toml` describes an individual code location.
- If both workspace and project config are present, validate the file that applies to the command context before changing paths.

## Create Projects And Workspaces

Modern commands:

```bash
create-dagster project my_project
create-dagster project . --no-uv-sync
create-dagster workspace analytics_workspace
create-dagster workspace . --no-uv-sync
```

Notes:

- Use `--no-uv-sync` when the user only wants files scaffolded and does not approve environment mutation.
- `--uv-sync` may create a lockfile and virtual environment; ask before running it in an existing repo.
- `create-dagster project` fails if the target path already exists, except `.` is allowed for the current directory flow.
- Inside a workspace, a new project is added to the workspace project list.

Legacy local scaffold commands still exist in many Dagster installs:

```bash
dagster project scaffold --name my_project
dagster project scaffold --name my_project --excludes README.md --excludes tests
dagster project scaffold --name my_project --ignore-package-conflict
```

Prefer the modern path for component-first work, but use legacy `dagster project scaffold` when `create-dagster` is unavailable and the user only needs a classic Dagster package skeleton.

## Discover Component Capabilities

Inside or targeting a component project:

```bash
dg list projects
dg list components
dg list components --json
dg list components --package my_project
dg list registry-modules
```

Use JSON output when an agent must parse results. If component discovery misses a custom type:

- Confirm the project package is installed in the active environment.
- Confirm the component module is importable.
- Confirm the module is registered in project metadata or exposed through the package entry mechanism for the current version.
- Rerun `dg list components --package <package>` after fixing imports.

## Scaffold Reusable Components

For a component with a YAML interface, scaffold a component class in the project `components` module:

```bash
dg scaffold component ShellCommand my_project.components.shell_command
```

For a Pythonic-only component, request no generated model interface if supported by the installed `dg` version:

```bash
dg scaffold component ShellCommand my_project.components.shell_command --no-model
```

Expected implementation shape for a YAML-configurable component:

```python
import dagster as dg

class ShellCommand(dg.Component, dg.Model, dg.Resolvable):
    command: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(name="shell_command_result")
        def shell_command_result() -> str:
            return self.command

        return dg.Definitions(assets=[shell_command_result])
```

Guidelines:

- Inherit from `dg.Component` and implement `build_defs`.
- Add `dg.Resolvable` plus `dg.Model` for YAML-backed configuration.
- Use `dg.ComponentTypeSpec` through `get_spec` to provide description, owners, tags, or metadata.
- Keep external execution, credentials, or network calls out of component import time.
- Prefer small deterministic component examples; route richer asset semantics to asset-definitions.

## Scaffold Component Instances

A component instance usually lives under the package `defs` tree as a directory containing `defs.yaml` or `component.py`.

Common patterns:

```bash
dg scaffold defs my_project.components.shell_command.ShellCommand path/to/component
```

A YAML instance has this general shape:

```yaml
type: my_project.components.shell_command.ShellCommand
attributes:
  command: "echo hello"
```

A Pythonic instance can use `component.py` where the component class or loader supports it. Component scaffolding code enforces that a scaffolded component directory produces either `defs.yaml` or `component.py`.

## Inline Components

Use inline components when the user wants a one-off component colocated with its instance rather than a reusable package-level type. The scaffolded code generally creates both a Python component file and a matching `defs.yaml` in the requested component path.

A minimal inline component body is:

```python
import dagster as dg

class InlineComponent(dg.Component, dg.Model, dg.Resolvable):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
```

Use inline components for local customization and quick migration. Use reusable component classes when multiple component instances share behavior or need generated documentation.

## Validate Component Projects

Run validation in increasing cost/order:

```bash
dg check toml
dg check yaml
dg check yaml path/to/defs.yaml
dg check yaml --validate-requirements path/to/defs.yaml
dg check defs
dg check defs --check-yaml
dg check defs --no-check-yaml --log-level debug
```

Behavior to expect:

- `dg check toml` validates `dg.toml` and `pyproject.toml` configuration shapes.
- `dg check yaml` validates component YAML against schemas and reports source-positioned errors.
- `dg check defs` loads definitions through a generated workspace context and sets `DAGSTER_IS_DEFS_VALIDATION_CLI=1` while validating.
- In a project context, `dg check defs` checks YAML first by default; in a workspace context, YAML checking is not always supported as a single workspace-wide option.

If `dg` is unavailable, use Python smoke checks and route full target loading to the local CLI sub-skill:

```bash
python - <<'PY'
import dagster as dg
from dagster.components import Component, ComponentLoadContext
print(dg.__version__)
print(Component, ComponentLoadContext)
PY
```

## Load And Test Component Definitions

Use `ComponentTree.for_project` in tests to load component instances relative to the project `defs` folder:

```python
from pathlib import Path
import dagster as dg


def project_component_defs(component_path: str) -> tuple[dg.Component, dg.Definitions]:
    project_root = Path(__file__).parent.parent
    tree = dg.ComponentTree.for_project(project_root)
    component = tree.load_component(component_path)
    defs = tree.build_defs_at_path(component_path)
    return component, defs


def test_component_loads() -> None:
    component, defs = project_component_defs("path/to/component")
    assert isinstance(component, dg.Component)
    assert dg.AssetKey("shell_command_result") in defs.resolve_asset_graph().get_all_asset_keys()
```

For execution tests, use in-memory materialization only when the component emits pure local assets with no external services:

```python
def test_component_asset_executes() -> None:
    _component, defs = project_component_defs("path/to/component")
    assert dg.materialize([defs.get_assets_def("shell_command_result")]).success
```

## Template Variables

Component YAML supports Jinja-style template expressions during loading. Template variables can come from a nearby module or component class static methods.

Module-level template variables:

```yaml
template_vars_module: .template_vars
type: my_project.components.shell_command.ShellCommand
attributes:
  command: "{{ default_command() }}"
```

Rules:

- Relative module paths beginning with `.` resolve relative to the current component module path.
- Absolute module paths must be importable in the active environment.
- Template functions may accept zero parameters or one `dagster.ComponentLoadContext` parameter.
- Component static methods can be exposed as template variables by using the public template variable decorator available in the installed version.
- Keep template variables deterministic and side-effect-light; do not resolve secrets or start external connections during validation.

## Definitions-Backed Components

`DefinitionsComponent` and the `@dagster.definitions` decorator support lazy Definitions-backed loading. Use this when a component path should wrap existing Python definitions while preserving component tree behavior.

A lazy definitions entry point can accept no arguments or one `ComponentLoadContext` argument:

```python
import dagster as dg

@dg.definitions
def defs(context: dg.ComponentLoadContext) -> dg.Definitions:
    @dg.asset(name=context.path.name)
    def generated_asset() -> str:
        return "ok"

    return dg.Definitions(assets=[generated_asset])
```

The decorated function must return a `Definitions` or repository object. If it declares any other signature, Dagster raises an invariant error during loading.


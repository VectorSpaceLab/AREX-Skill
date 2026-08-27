# Component API Reference

This reference summarizes public component APIs and source-confirmed patterns useful for future agents. Prefer `import dagster as dg` in examples because many component APIs are re-exported on the main Dagster namespace in component-ready installs.

## Core Classes

### `dg.Component`

Base class for component types. Implement:

```python
def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
    ...
```

Use it for classes that produce one or more Dagster definitions from a reusable configuration or a colocated component instance.

Key points:

- `build_defs` returns `dg.Definitions`.
- Component classes can be discovered by `dg` when the containing module is registered for the project.
- Components can attach metadata by overriding `get_spec`.
- Component classes can attach custom scaffolding behavior with `@dg.scaffold_with`.

### `dg.ComponentLoadContext`

Context object passed while loading a component from a component tree or defs folder. Use it for path-aware or environment-aware loading, but keep validation safe and side-effect-light.

Common uses:

- Computing names from the component path.
- Reading colocated local files that are part of the project.
- Supplying context-aware template variables.
- Avoiding expensive work when `DAGSTER_IS_DEFS_VALIDATION_CLI=1` is set.

### `dg.Resolvable` And `dg.Model`

Use `dg.Resolvable` when a component should be instantiated from YAML attributes. Use `dg.Model` for new schema-backed components.

```python
import dagster as dg

class TableComponent(dg.Component, dg.Model, dg.Resolvable):
    table_name: str
    asset_key: dg.ResolvedAssetKey

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(key=self.asset_key)
        def table_asset() -> str:
            return self.table_name

        return dg.Definitions(assets=[table_asset])
```

Guidelines:

- Annotated fields become the YAML-facing schema.
- Prefer `dg.Model` over raw Pydantic models for new component code.
- Keep field types serializable and easy to validate.
- Use Dagster's resolved schema models for asset keys/specs/check specs instead of hand-parsing YAML.

## Schema Helper Models

Component YAML schemas commonly use these public models:

- `dg.ResolvedAssetKey`: YAML-friendly asset key that resolves to `AssetKey`-compatible data.
- `dg.ResolvedAssetSpec`: YAML-friendly asset spec for assets emitted by a component.
- `dg.ResolvedAssetCheckSpec`: YAML-friendly asset check spec.
- `dg.AssetAttributesModel`: common asset attributes used in component schemas.

Example with one emitted asset spec:

```python
import dagster as dg

class QueryComponent(dg.Component, dg.Model, dg.Resolvable):
    sql: str
    asset_spec: dg.ResolvedAssetSpec

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(spec=self.asset_spec)
        def query_asset() -> str:
            return self.sql

        return dg.Definitions(assets=[query_asset])
```

For multiple emitted assets, annotate a sequence of `dg.ResolvedAssetSpec` values and route deeper asset semantics to the asset-definitions sub-skill.

## Component Metadata

Use `dg.ComponentTypeSpec` to describe a reusable component type:

```python
import dagster as dg

class OwnedComponent(dg.Component, dg.Model, dg.Resolvable):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

    @classmethod
    def get_spec(cls) -> dg.ComponentTypeSpec:
        return dg.ComponentTypeSpec(
            description="Builds local demo definitions.",
            owners=["team:data-platform"],
            tags=["demo"],
            metadata={"kind": "example"},
        )
```

Owner strings must be valid Dagster owner strings, such as email addresses or `team:<name>` values.

## Definitions Loading APIs

### `@dg.definitions`

Use `@dg.definitions` to expose a lazy function that returns `dg.Definitions` for autoloaded definitions folders and component contexts.

Valid signatures:

```python
@dg.definitions
def defs() -> dg.Definitions: ...

@dg.definitions
def defs(context: dg.ComponentLoadContext) -> dg.Definitions: ...
```

Invalid signatures include multiple parameters or a first parameter that is not annotated exactly as `dg.ComponentLoadContext` in versions that enforce that annotation. The function must return `dg.Definitions` or a repository object.

### Component Tree Loading

Use these APIs for tests and local inspection:

```python
tree = dg.ComponentTree.for_project(project_root)
component = tree.load_component("path/to/component")
defs = tree.build_defs_at_path("path/to/component")
```

The component path is relative to the project `defs` folder, not an arbitrary filesystem path. Use this for unit tests and smoke checks before running full CLI validation.

### Lower-Level Loading Helpers

The installed component package exposes these helpers for advanced loading:

- `dagster.components.load_defs`
- `dagster.components.load_from_defs_folder`
- `dagster.components.build_component_defs`
- `dagster.components.build_defs_for_component`

Prefer `ComponentTree.for_project` or `dg check defs` unless the task specifically needs lower-level loading.

## Scaffolding APIs

### `@dg.scaffold_with`

Attach a scaffolder to a component or scaffoldable object:

```python
from pathlib import Path
import dagster as dg

class DemoScaffolder(dg.Scaffolder):
    def scaffold(self, request: dg.ScaffoldRequest) -> None:
        request.target_path.mkdir(parents=True, exist_ok=True)
        (request.target_path / "defs.yaml").write_text(
            "type: my_project.components.DemoComponent\nattributes: {}\n"
        )

@dg.scaffold_with(DemoScaffolder)
class DemoComponent(dg.Component, dg.Model, dg.Resolvable):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
```

Scaffolding rules:

- A component scaffold must produce either `defs.yaml` or `component.py` in the target directory.
- `request.target_path` points to the requested component instance directory or file target, depending on the scaffolder.
- `request.type_name` identifies the component type being scaffolded.
- `request.scaffold_format` is usually `yaml` or `python`.
- Custom scaffolders may define parameter models by overriding `get_scaffold_params`.

### `dagster.components.scaffold_component`

This lower-level helper writes component instances in YAML or Python form. Prefer `dg scaffold defs` from the CLI when available because it also uses project context and registry resolution.

## Built-In Component Types

The component package exposes several built-in component classes. Availability can vary by Dagster version and optional dependencies, so always confirm imports in the target environment.

Common public exports include:

- `dg.DefinitionsComponent`
- `dg.FunctionComponent`
- `dg.PythonScriptComponent`
- `dg.UvRunComponent`
- `dg.SqlComponent`
- `dg.TemplatedSqlComponent`
- `dg.StateBackedComponent`

Use built-ins for simple local definitions, scripts, SQL, and state-backed workflows when they fit. Do not assume provider-specific integration components are installed; broad integration libraries are outside this sub-skill's runtime scope.

## `dg` Command Families

The `dg` CLI source defines command families that matter for component projects:

- `dg list projects`: list projects in a workspace or emit `.` in a standalone project.
- `dg list components`: list available component types, optionally with `--package` or `--json`.
- `dg list registry-modules`: list modules that provide discoverable component/plugin objects.
- `dg check toml`: validate `dg.toml` and project `pyproject.toml` configuration.
- `dg check yaml`: validate component `defs.yaml` files against schemas.
- `dg check defs`: load and validate all definitions, optionally checking YAML first.
- `dg scaffold component`: create reusable component type source under a module.
- `dg scaffold defs`: create a component instance under the project `defs` tree.

Because `dg` depends on development-time packages that may not be published in source checkouts, treat command absence as an environment fact to troubleshoot rather than a Dagster API failure.

## `create-dagster` Commands

`create-dagster` exposes:

- `create-dagster project <path>`: scaffold a component-ready Dagster project.
- `create-dagster workspace <path>`: scaffold a workspace with project and local deployment structure.

Important options and behavior:

- `--uv-sync`/`--no-uv-sync` controls whether the command tries to create a uv-managed environment after scaffolding.
- `--use-editable-dagster` can be available in development contexts to scaffold editable Dagster dependencies.
- Project scaffolds include `src/<package>/defs`, `src/<package>/components`, tests, and project metadata.
- Workspace scaffolds include project slots, deployment/local environment metadata, and `dg.toml`.

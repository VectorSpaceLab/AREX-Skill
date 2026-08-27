# Plugin Development

DataDesigner supports installable third-party extensions through Python entry points in the `data_designer.plugins` group. A plugin package exposes one `Plugin` descriptor per extension; DataDesigner discovers descriptors on import and uses them to extend config-layer discriminated unions and engine registries.

## Extension surfaces

| Plugin type | `PluginType` value | Config discriminator | Implementation dispatch |
|---|---:|---|---|
| Custom column type | `column-generator` | `column_type` | `create_default_column_generator_registry()` maps the plugin name to `plugin.impl_cls`. |
| Seed reader | `seed-reader` | `seed_type` | `DataDesigner` appends `plugin.impl_cls()` to default seed readers. |
| Processor | `processor` | `processor_type` | `create_default_processor_registry()` maps the plugin name to `plugin.impl_cls`. |

Use installable plugins when a reusable package needs a new discriminator value. Use in-process custom columns (`column_type: custom`) only for user/session-local generation logic; see [custom columns and MCP](custom-columns-and-mcp.md) and `../../config-authoring/SKILL.md`.

## `Plugin` descriptor contract

A descriptor is a `data_designer.plugins.Plugin` Pydantic model with:

- `impl_qualified_name`: fully qualified implementation class path, for example `my_pkg.generators.MarkdownColumnGenerator`.
- `config_qualified_name`: fully qualified config class path, for example `my_pkg.config.MarkdownColumnConfig`.
- `plugin_type`: a `PluginType` enum value (`COLUMN_GENERATOR`, `SEED_READER`, or `PROCESSOR`).

Validation performed by `Plugin`:

1. The implementation and config paths must be fully qualified (`module.Object`).
2. `importlib.util.find_spec(module)` must find the module and source file.
3. The named class must exist in the source file; the validator parses the file AST before the descriptor is accepted.
4. The config class must contain the discriminator field required by `plugin_type`.
5. The discriminator annotation must be a `typing.Literal[...]` and its default must be a string.
6. The discriminator default is the runtime plugin name. Its uppercase hyphen-to-underscore enum key must be a valid Python identifier.

Example package entry point and descriptor:

```toml
[project.entry-points."data_designer.plugins"]
markdown-section = "my_pkg.plugin:plugin"
```

```python
from __future__ import annotations

from data_designer.plugins import Plugin, PluginType

plugin = Plugin(
    impl_qualified_name="my_pkg.generators.MarkdownSectionGenerator",
    config_qualified_name="my_pkg.config.MarkdownSectionConfig",
    plugin_type=PluginType.COLUMN_GENERATOR,
)
```

For a column-generator plugin, the config class usually inherits from `SingleColumnConfig` and declares a unique discriminator:

```python
from __future__ import annotations

from typing import Literal

from data_designer.config.base import SingleColumnConfig

class MarkdownSectionConfig(SingleColumnConfig):
    column_type: Literal["markdown-section"] = "markdown-section"
    name: str
    source_column: str
```

## Discovery and injection flow

Discovery is controlled by `PluginRegistry`:

1. `PluginRegistry()` is a singleton; first construction scans `importlib.metadata.entry_points(group="data_designer.plugins")`.
2. If `DISABLE_DATA_DESIGNER_PLUGINS=true`, discovery returns without loading entry points.
3. Each entry point is loaded. Only objects that are instances of `Plugin` are registered.
4. A failed entry point logs a warning and discovery continues, so one bad package does not block unrelated plugins.
5. Registered plugins are keyed by `plugin.name`, where `name` comes from the config discriminator default.

Import-time union injection happens in the config layer:

- `config/column_types.py` builds `ColumnConfigT` from built-ins, then calls `PluginManager.inject_into_column_config_type_union(...)`; `DataDesignerColumnType` is created from that expanded union.
- `config/seed_source_types.py` expands the annotated `SeedSourceT` union with seed-reader plugin configs.
- `config/processor_types.py` expands `ProcessorConfigT` with processor plugin configs.

Engine/runtime dispatch is separate from config validation:

- Column-generator plugins are registered in `engine/column_generators/registry.py` when `create_default_column_generator_registry(with_plugins=True)` iterates `PluginRegistry().get_plugins(PluginType.COLUMN_GENERATOR)`.
- Processor plugins are registered in `engine/processing/processors/registry.py`.
- Seed-reader plugins are instantiated in `interface/data_designer.py` with `plugin.impl_cls()` and appended to `DEFAULT_SEED_READERS`, so a packaged seed-reader implementation must be constructible with no required constructor arguments.

Because union construction and default seed-reader construction happen at import time, install a plugin before importing DataDesigner in a long-lived Python process. After installing into a running shell/notebook, restart the process unless you have a deliberate test harness that resets plugin registry state.

## Implementation base classes

The descriptor validates object existence and discriminator shape. For stronger plugin-package tests, use DataDesigner engine testing utilities to assert implementation base classes:

- `PluginType.COLUMN_GENERATOR` implementation should subclass `ConfigurableTask` / a column generator base.
- `PluginType.SEED_READER` implementation should subclass `SeedReader`.
- `PluginType.PROCESSOR` implementation should subclass `Processor`.

Native tests prove these checks in `packages/data-designer-engine/tests/engine/testing/test_plugin_testing_utils.py` and plugin union behavior in `packages/data-designer-engine/tests/test_plugin_manager.py`.

## Seed-reader plugin notes

A seed-reader plugin config uses `seed_type: Literal["..."]`. For filesystem-backed readers, subclass `FileSystemSeedReader` and implement:

- `build_manifest(context=...)`: cheap logical rows available under the root path.
- optional `hydrate_row(manifest_row=..., context=...)`: expensive row expansion or enrichment.
- `output_columns`: required when hydrated rows differ from manifest columns.

The Markdown seed-reader recipe demonstrates the `build_manifest`/`hydrate_row` contract, but it injects a reader into one `DataDesigner(seed_readers=[...])` instance; packaging it as a plugin additionally requires the `Plugin` descriptor and `data_designer.plugins` entry point.

## Validation checklist for future agents

- Confirm `DISABLE_DATA_DESIGNER_PLUGINS` is not set to `true` unless the task explicitly wants plugins disabled.
- Inspect entry-point metadata safely with `scripts/inspect_installed_plugins.py`; this does not load plugin code.
- Confirm the runtime plugin name equals the config discriminator default and does not collide with built-in or other plugin discriminator values.
- Confirm hyphen/underscore normalization does not create the same enum key as another runtime plugin (for example `foo-bar` and `foo_bar` collide as `FOO_BAR`).
- For a package in a catalog, validate catalog metadata before install; catalog validation rejects duplicate package names, duplicate runtime plugin names, invalid entry-point groups, invalid version specifiers, and unsupported schema versions.
- Use targeted native tests where possible: plugin manager tests, plugin catalog service/repository tests, plugin install service tests, and plugin testing utility checks.

## Evidence consulted

- `packages/data-designer-config/src/data_designer/plugins/plugin.py`
- `packages/data-designer-config/src/data_designer/plugins/registry.py`
- `packages/data-designer-config/src/data_designer/plugin_manager.py`
- `packages/data-designer-config/src/data_designer/config/column_types.py`
- `packages/data-designer-config/src/data_designer/config/seed_source_types.py`
- `packages/data-designer-config/src/data_designer/config/processor_types.py`
- `packages/data-designer-engine/src/data_designer/engine/column_generators/registry.py`
- `packages/data-designer-engine/src/data_designer/engine/processing/processors/registry.py`
- `packages/data-designer/src/data_designer/interface/data_designer.py`
- `architecture/plugins.md`

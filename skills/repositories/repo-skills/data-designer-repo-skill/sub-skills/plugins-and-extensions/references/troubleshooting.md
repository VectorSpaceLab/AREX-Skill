# Troubleshooting Plugins and Extensions

Start with safe inspection:

```bash
python scripts/inspect_installed_plugins.py
python scripts/inspect_installed_plugins.py --json
data-designer plugin installed
```

The bundled script reads `importlib.metadata` only. It does not import DataDesigner, does not call `EntryPoint.load()`, does not contact catalogs, and does not run package managers.

## Failure map

| Symptom | Likely cause | What to check | Recovery |
|---|---|---|---|
| Installed plugin entry points exist but plugin types are not exposed. | Plugin loading is disabled. | `DISABLE_DATA_DESIGNER_PLUGINS=true`; safe inspector `plugins_disabled` field. | Unset the variable or set it to `false`, then restart the Python process before importing DataDesigner. |
| Plugin installed during a notebook/session but `DataDesignerColumnType` does not include it. | Discovery and union injection already happened at import time. | Was `data_designer.config.column_types`, seed source types, or processor types imported before install? | Restart the process. In tests only, `PluginRegistry.reset()` can force rediscovery under controlled mocks. |
| Catalog load rejects duplicate runtime names or enum-key collisions. | Two catalog runtime plugin names collide directly or after hyphen/underscore normalization. | Catalog error mentions duplicate runtime plugin name or enum-key normalization such as `FOO_BAR`. | Rename the plugin discriminator default and catalog runtime `name`; avoid `foo-bar`/`foo_bar` pairs. |
| A plugin silently shadows another plugin after load. | Runtime plugin descriptors share the same discriminator default; `PluginRegistry` keys by `plugin.name`. | Compare each descriptor config discriminator default, not only entry-point names. | Make every plugin discriminator default globally unique in the environment; avoid built-in values like `custom`, `sampler`, or `llm-text`. |
| `plugin install text-column` says package not found. | User supplied a runtime plugin name instead of a package name or package alias. | `data-designer plugin search text-column` or the CLI recovery hint. | Use the suggested package alias, for example `data-designer plugin --catalog local install text-transform`. Preserve version specifiers on the package alias if present. |
| A plugin is hidden from `list`/`search`. | It is incompatible with local Python or DataDesigner version. | Run with `--include-incompatible`; inspect `data-designer plugin info <package>`. | Use a compatible package version or a different environment. Unversioned real installs are blocked when compatibility fails. |
| Versioned install warns about incompatible catalog metadata. | Catalog compatibility may describe default package version, not requested version. | Install target includes `==...` or `--version`. | Treat as a warning, not proof of compatibility. Dry-run first; package manager constraints still preserve installed DataDesigner packages. |
| `--manager uv` fails, or auto falls back to pip. | `uv` is missing, unreadable, unparsable, or older than `0.10.0`. | Error/warning mentions `uv >= 0.10.0` and `uv self update`. | Upgrade uv, or explicitly choose `--manager pip` if mutating the current Python environment is acceptable. |
| Auto/pip planning fails with pip unavailable. | Current interpreter lacks working pip. | Error from `<sys.executable> -m pip --version`. | Activate the intended environment, install/repair pip, or use a suitable uv environment. |
| Installing a plugin upgrades/downgrades DataDesigner unexpectedly. | User bypassed the DataDesigner plugin planner or ignored constraints. | Compare versions of `data-designer`, `data-designer-config`, and `data-designer-engine`; safe inspector reports metadata versions. | Prefer `data-designer plugin install ...`; its plans pin/preserve all three DataDesigner distributions. If manual install is required, pass equivalent constraints. |
| Install reports success but warns that entry points could not load. | Entry-point name/value/distribution mismatch, missing module, descriptor loads a non-`Plugin`, bad discriminator, or dependency import failure. | `data-designer plugin installed` and safe inspector show metadata; install verification loads entries and failed. | Check package code and `pyproject.toml` entry point. With user approval, perform a targeted import/load in an isolated environment; otherwise do not claim the plugin works. |
| `data-designer plugin installed` is empty after install. | Wrong interpreter/environment. | Safe inspector Python executable; package manager target in dry-run plan (`uv pip --python`, pip interpreter, or uv project root). | Re-run install in the interpreter where DataDesigner will run, or invoke the same Python executable. |
| `ToolConfig 'x' references provider(s) ... which are not registered`. | `ToolConfig.providers` names do not match `DataDesigner(..., mcp_providers=[...])`. | Provider `name` values vs `ToolConfig.providers`. | Pass matching `MCPProvider`/`LocalStdioMCPProvider` objects to `DataDesigner`. |
| `No tool config with alias 'x' found`. | Column `tool_alias` does not match any `ToolConfig.tool_alias`, or tool configs were not passed to the builder. | Builder `tool_configs`, `add_tool_config`, and model-generated columns with `tool_alias`. | Add or rename the `ToolConfig`; use `builder.get_tool_config(alias)` for config-level checks. |
| `Tool alias(es) [...] specified but no MCPRegistry configured`. | A model-generated column uses `tool_alias` but no MCP registry/resource provider was created. | Was `DataDesigner` constructed with `mcp_providers` and was `DataDesignerConfigBuilder` given `tool_configs`? | Provide MCP providers and tool configs, then run `designer.check_models(builder)` before generation. |
| Missing MCP tool in allow list. | `allow_tools` names do not exist on any configured provider. | `designer.list_mcp_tool_names(provider_name)`; `MCPFacade.get_tool_schemas()` error. | Fix `allow_tools`, provider server, or `ToolConfig.providers`. |
| Duplicate MCP tool names across providers. | Multiple providers in one `ToolConfig` expose the same function name. | `DuplicateToolNameError` lists duplicate tool names and providers. | Rename tools at the server layer or split providers into separate `ToolConfig`s; duplicate detection happens before allowlist filtering. |
| Local stdio MCP server cannot start or remote server unavailable. | Bad command/args/env, missing executable, wrong endpoint, bad secret, or server not running. | `LocalStdioMCPProvider.command/args/env`, `MCPProvider.endpoint/api_key`, and `list_mcp_tool_names`. | Fix provider config or start the MCP server. Do not claim readiness until `check_models` or startup readiness succeeds. |
| Custom column drops an extra generated field. | Field was created but not declared as a side effect. | Warning about undeclared columns. | Add the column name to `@custom_column_generator(side_effect_columns=[...])`. |
| Custom column model is not health-checked or unavailable inside generator. | Missing `model_aliases` decorator metadata. | `config.get_model_aliases()` result and readiness test behavior. | Add every needed alias to `@custom_column_generator(model_aliases=[...])` and accept a `models` parameter. |

## Triage order for agents

1. Identify the current Python executable and DataDesigner distribution versions.
2. Inspect entry-point metadata without loading plugin code.
3. Check disabled loading and import-time timing before assuming package bugs.
4. Separate catalog package lookup from runtime plugin names.
5. Dry-run any package mutation and confirm DataDesigner package preservation.
6. For MCP, validate provider names, tool aliases, and actual server tool names in that order.
7. Escalate to explicit `EntryPoint.load()`/targeted imports only after the user approves loading third-party plugin code.

## Evidence consulted

- `packages/data-designer-config/src/data_designer/plugins/registry.py`
- `packages/data-designer-config/src/data_designer/plugins/plugin.py`
- `packages/data-designer/src/data_designer/cli/controllers/plugin_catalog_controller.py`
- `packages/data-designer/src/data_designer/cli/services/plugin_catalog_service.py`
- `packages/data-designer/src/data_designer/cli/services/plugin_install_service.py`
- `packages/data-designer/src/data_designer/cli/repositories/plugin_catalog_repository.py`
- `packages/data-designer-engine/src/data_designer/engine/readiness.py`
- `packages/data-designer-engine/src/data_designer/engine/mcp/registry.py`
- `packages/data-designer-engine/src/data_designer/engine/mcp/facade.py`
- `packages/data-designer-engine/tests/engine/test_readiness.py`
- `packages/data-designer-engine/tests/engine/resources/test_resource_provider.py`
- `packages/data-designer/tests/cli/services/test_plugin_install_service.py`

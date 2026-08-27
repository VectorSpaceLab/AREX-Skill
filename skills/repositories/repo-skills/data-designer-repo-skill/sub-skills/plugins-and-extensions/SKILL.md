---
name: plugins-and-extensions
description: "Work with DataDesigner plugin descriptors, catalog package
  workflows, custom generators, MCP tool aliases, and installed plugin
  inspection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Plugins and Extensions

Use this sub-skill when a DataDesigner task touches extension surfaces: installable plugin packages, `data_designer.plugins` entry points, plugin-provided column/seed/processor types, plugin catalog commands, safe installed-plugin inspection, in-process custom column generators, or MCP tool aliases used by model-generated columns.

## Use this for

- Explaining or validating `Plugin` descriptors, `PluginType` values, and discriminator fields for column-generator, seed-reader, and processor plugins.
- Diagnosing entry-point discovery through the `data_designer.plugins` group and import-time injection into config unions.
- Planning `data-designer plugin` catalog, list/search/info/install/uninstall/installed workflows without accidentally mutating the active environment.
- Distinguishing installable plugin packages from runtime plugin names and resolving package aliases such as `github` → `data-designer-github`.
- Working with custom columns only when the extension concern is `@custom_column_generator` metadata: `required_columns`, `side_effect_columns`, and `model_aliases`.
- Troubleshooting MCP tool config aliases when plugin/custom generation tasks also depend on tool readiness.

## Do not use this for

- Ordinary config and builder authoring that does not involve extension surfaces → `../config-authoring/SKILL.md`.
- Pure preview/create/runtime execution, artifact output, scheduler, or model-provider behavior → `../generation-runtime/SKILL.md`.
- General CLI/agent tooling outside plugin commands → `../cli-and-agent-tools/SKILL.md`.
- Recipe-by-recipe narratives or integration walkthroughs unless the question is specifically about extension contracts → `../recipes-and-integrations/SKILL.md`.

## Operating order

1. Classify the extension mode: installable entry-point plugin, plugin catalog package workflow, in-process custom column, MCP tool alias, or a mix.
2. For installable plugins, validate the descriptor contract first: one `Plugin` object per entry point, correct `PluginType`, fully qualified config/implementation class names, and a unique string `Literal` discriminator default.
3. Inspect installed state with `scripts/inspect_installed_plugins.py` or `data-designer plugin installed` before assuming a package is visible to the interpreter.
4. For package changes, prefer `data-designer plugin ... --dry-run`; only run real `install`/`uninstall` after explicit user approval because those commands mutate the active project or Python environment.
5. For runtime-name confusion, search/info the catalog and convert the runtime plugin name to the package or package alias suggested by the CLI.
6. For custom columns, ensure decorator metadata preserves every generated side-effect column and every model alias needed for readiness. For broader builder details, route to `../config-authoring/SKILL.md`.
7. For MCP issues, trace all three names separately: MCP provider `name`, `ToolConfig.tool_alias`, and column `tool_alias`. Use readiness checks through DataDesigner rather than ad-hoc generation. For runtime behavior, route to `../generation-runtime/SKILL.md`.
8. Keep evidence claims tied to source files, native tests, installed-package facts, or the safe inspector output; do not claim a plugin loads unless an explicit load/verification step was run.

## Safe checks

```bash
# Metadata-only; never imports plugin modules and never calls package managers.
python scripts/inspect_installed_plugins.py
python scripts/inspect_installed_plugins.py --json

# CLI browsing checks. `installed` is metadata-only; catalog commands may populate/refresh cache but do not install packages.
data-designer plugin installed
data-designer plugin list
data-designer plugin search <query>
data-designer plugin info <package-or-alias>

# Mutation plans only; no environment changes.
data-designer plugin install <package-or-alias> --dry-run
data-designer plugin uninstall <package-or-alias> --dry-run
```

## Reference map

- [Plugin development](references/plugin-development.md) — plugin descriptor contract, entry-point group, import-time union injection, engine registry integration, and validation checklist.
- [Plugin CLI](references/plugin-cli.md) — catalog schema, package aliases, compatibility filters, dry-run/install/uninstall semantics, and installed-plugin listing.
- [Custom columns and MCP](references/custom-columns-and-mcp.md) — in-process custom column metadata, model alias readiness, side-effect preservation, and MCP provider/tool alias readiness.
- [Troubleshooting](references/troubleshooting.md) — disabled loading, duplicate discriminators, runtime-vs-package names, compatibility, uv/pip planner problems, DataDesigner upgrade protection, entry-point load failures, and missing MCP aliases.

## What good output looks like

- Names the exact interpreter/environment being inspected before discussing installed plugins.
- Separates package names (`data-designer-...`) from runtime plugin names and entry-point names.
- Uses dry-run plans and explicit approval before environment mutation.
- Mentions `DISABLE_DATA_DESIGNER_PLUGINS=true` whenever installed entry points are present but DataDesigner does not expose plugin types.
- Verifies MCP readiness through provider names, tool aliases, `ToolConfig`, and `check_models`/startup readiness rather than by only checking config syntax.

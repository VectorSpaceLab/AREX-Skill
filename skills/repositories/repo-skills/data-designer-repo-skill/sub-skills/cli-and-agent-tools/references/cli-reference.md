# CLI Reference

This reference summarizes the `data-designer` command tree, important flags, and controller/API mapping. For detailed config object fields, use `../../config-authoring/SKILL.md`; for runtime generation behavior, use `../../generation-runtime/SKILL.md`; for plugin implementation details, use `../../plugins-and-extensions/SKILL.md`.

## Root command tree

| Command | Purpose | Notes |
| --- | --- | --- |
| `data-designer --help` | Show root command groups | Root help lists setup, agent, and generation groups. |
| `data-designer --version` | Print installed `data-designer` version | Eager option; skips default config bootstrap. |
| `data-designer config ...` | Manage local provider/model/MCP/tool config state | Uses `DATA_DESIGNER_HOME`. |
| `data-designer download personas ...` | Download managed Nemotron-Persona datasets | Requires NGC CLI/config except for dry-run/list flows. |
| `data-designer plugin ...` | Browse catalogs and install/uninstall plugin packages | Catalog-aware package commands support `--catalog`. |
| `data-designer agent ...` | Emit agent-facing context and state | Best bootstrap for future agents. |
| `data-designer preview/create/validate/check-models ...` | Generation CLI entry points | Thin wrappers around public `DataDesigner` APIs. |

The CLI uses lazy command loading so group help can list command names without importing every command implementation.

## `config` group

```text
data-designer config list
data-designer config providers
data-designer config models
data-designer config mcp
data-designer config tools
data-designer config reset
```

| Subcommand | Role | Behavior |
| --- | --- | --- |
| `list` | Read-only state display | Prints the config directory and tables for providers, models, MCP providers, and tool configs. |
| `providers` | Interactive provider editor | Opens the provider controller/form flow. |
| `models` | Interactive model alias editor | Opens the model controller/form flow. |
| `mcp` | Interactive MCP provider editor | Opens the MCP provider controller/form flow. |
| `tools` | Interactive tool config editor | Opens the tool controller/form flow. |
| `reset` | Delete provider/model config files | Prompts per file and targets only `model_providers.yaml` and `model_configs.yaml`. |

`config list` table columns:

- Model Providers: `Name`, `Endpoint`, `Type`, `API Key`.
- Model Configurations: `Alias`, `Model`, `Provider`, `Inference Parameters`.
- MCP Providers: `Name`, `Endpoint / Command`, `Type`, `API Key / Env`.
- Tool Configurations: `Alias`, `Providers`, `Allowed Tools`, `Max Turns`, `Timeout`.

## `download personas`

```text
data-designer download personas [--locale/-l LOCALE ...] [--all] [--dry-run] [--list]
```

| Flag | Meaning |
| --- | --- |
| `--locale`, `-l` | Repeatable locale selection. Invalid locale codes are rejected. |
| `--all` | Select every built-in locale. |
| `--dry-run` | Show what would be downloaded without NGC checks or downloads. |
| `--list` | List available locales, sizes, and downloaded status. |

Download routing:

- `--list` → list built-in persona metadata and current downloaded status.
- regular download → select locales → confirm → run NGC resource download → move parquet files into managed assets.
- install state is per-locale; one installed locale does not imply any other locale is installed.

## `plugin` group

```text
data-designer plugin [--catalog CATALOG] list|search|info|install|uninstall|installed
data-designer plugin catalog list
data-designer plugin catalog add ALIAS URL
data-designer plugin catalog remove ALIAS
```

| Command | Purpose | Important flags/args |
| --- | --- | --- |
| `plugin list` | List packages from a catalog | `--catalog`, `--refresh`, `--include-incompatible`. |
| `plugin search QUERY` | Search by keyword, package/alias, runtime plugin name, or plugin type | `--catalog`, `--refresh`, `--include-incompatible`. |
| `plugin info PACKAGE` | Show package metadata and install strategy | `--catalog`, `--refresh`. |
| `plugin install PACKAGE` | Install one package and verify runtime entry points | `--catalog`, `--refresh`, `--manager auto|uv|pip`, `--version`, `--yes/-y`, `--dry-run`. |
| `plugin uninstall PACKAGE` | Uninstall one package and verify entry points are gone | `--catalog`, `--refresh`, `--manager auto|uv|pip`, `--yes/-y`, `--dry-run`. |
| `plugin installed` | List installed plugin packages | Current Python environment only; ignores parent `--catalog`. |
| `plugin catalog list/add/remove` | Manage catalog aliases | Catalog management ignores parent `--catalog`. |

Plugin command notes:

- Package commands take package names or package aliases. Runtime plugin names are not install targets; the CLI points to the owning package when possible.
- `PACKAGE==1.2.3` and `--version 1.2.3` are alternatives; do not use both.
- `--manager auto` prefers `uv`; in active uv projects it records install/uninstall in project metadata, otherwise it mutates the active environment through `uv pip` or `pip`.
- The built-in catalog alias is `nvidia`; user aliases live under `DATA_DESIGNER_HOME`.

## `agent` group

```text
data-designer agent context
data-designer agent types [family]
data-designer agent state model-aliases
data-designer agent state persona-datasets
```

| Command | Output | Use when |
| --- | --- | --- |
| `agent context` | Full bootstrap: config module path, type catalogs, model aliases, persona state, command registry | Starting any agent-assisted config or CLI session. |
| `agent types [family]` | Type names, descriptions, and source files | Discovering available columns, samplers, validators, processors, or constraints. |
| `agent state model-aliases` | Alias/model/provider/generation type/usability/reason table | Deciding whether model-backed operations can run. |
| `agent state persona-datasets` | Locale/size/installed table | Deciding whether persona locales are ready. |

Accepted `types` families: `columns`, `samplers`, `validators`, `processors`, `constraints`. Singular forms normalize to plural families.

## Generation commands and CLI-to-API mapping

| Command | Key flags | Controller/API mapping |
| --- | --- | --- |
| `preview CONFIG_SOURCE` | `--num-records/-n`, `--non-interactive`, `--save-results`, `--artifact-path/-o`, `--theme dark|light`, `--display-width`, args after `--` | `GenerationController.run_preview()` → `DataDesigner.preview()`. |
| `create CONFIG_SOURCE` | `--run-config/-c`, `--num-records/-n`, `--dataset-name/-d`, `--artifact-path/-o`, `--resume/-r never|always|if_possible`, `--output-format/-f jsonl|csv|parquet`, `--tui/--no-tui`, args after `--` | `GenerationController.run_create()` → `DataDesigner.create()`. |
| `validate CONFIG_SOURCE` | args after `--` | `GenerationController.run_validate()` → `DataDesigner.validate()`. |
| `check-models CONFIG_SOURCE` | args after `--` | `GenerationController.run_check_models()` → `DataDesigner.check_models()`. |

Generation syntax rules:

- `CONFIG_SOURCE` can be local `.yaml`, `.yml`, `.json`, or local `.py` with `load_config_builder()`.
- Remote YAML/JSON config URLs are supported; remote Python modules are not.
- Script arguments are only for local Python modules and must come after `--`.
- `create --run-config/-c` takes a local `.yaml` or `.yml` whose root is a direct `RunConfig` mapping, not a nested `run_config:` object.
- `preview` uses interactive browsing only when stdin and stdout are TTYs and more than one record exists; otherwise it displays all records or saves artifacts.

## Canonical examples

```bash
# Bootstrap exact local types, aliases, persona state, and command registry
data-designer agent context

# Check usable aliases before model-backed operations
data-designer agent state model-aliases

# Validate a config module with forwarded script args
data-designer validate workflow.py -- --seed-path seeds.parquet

# Preview from the same module without TTY navigation
data-designer preview workflow.py --num-records 3 --non-interactive -- --seed-path seeds.parquet

# Create from the same module with a run-config overlay
data-designer create workflow.py --run-config run-config.yaml --num-records 32 --dataset-name run_a -- --seed-path seeds.parquet

# Inspect persona locales before downloading
data-designer download personas --list

# Dry-run plugin installation without mutating the environment
data-designer plugin install github==0.1.0 --dry-run
```

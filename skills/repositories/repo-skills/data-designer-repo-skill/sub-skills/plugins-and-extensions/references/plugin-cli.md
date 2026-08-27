# Plugin CLI

The plugin CLI is package-first. Commands operate on installable plugin packages from catalogs, while runtime plugin names describe the extensions exposed by those packages.

## Command map

```bash
# Catalog browsing; no package install/uninstall, but may populate/refresh the catalog cache.
data-designer plugin list [--catalog ALIAS] [--refresh] [--include-incompatible]
data-designer plugin search QUERY [--catalog ALIAS] [--refresh] [--include-incompatible]
data-designer plugin info PACKAGE [--catalog ALIAS] [--refresh]

# Package mutation; use --dry-run first.
data-designer plugin install PACKAGE [--catalog ALIAS] [--manager auto|uv|pip] [--version VERSION] [--yes] [--dry-run]
data-designer plugin uninstall PACKAGE [--catalog ALIAS] [--manager auto|uv|pip] [--yes] [--dry-run]

# Installed state; read-only metadata inspection of the current Python environment.
data-designer plugin installed

# Catalog alias management.
data-designer plugin catalog list
data-designer plugin catalog add ALIAS URL
data-designer plugin catalog remove ALIAS
```

`--catalog` may appear on the parent `plugin` command or the subcommand for list/search/info/install/uninstall. It is intentionally ignored by `plugin installed` because installed plugins come from the current interpreter, and by `plugin catalog list` because catalog management operates on aliases directly.

## Catalog contract

The catalog repository reads a versioned JSON document. Current schema is `schema_version: 2` with a package-first shape:

```json
{
  "schema_version": 2,
  "packages": [
    {
      "name": "data-designer-github",
      "version": "0.1.0",
      "description": "GitHub and local git repository seed reader",
      "install": {
        "requirement": "data-designer-github",
        "index_url": "https://example.test/simple/"
      },
      "compatibility": {
        "python": {"specifier": ">=3.10"},
        "data_designer": {
          "requirement": "data-designer>=0.5.7",
          "specifier": ">=0.5.7",
          "marker": null
        }
      },
      "docs": {"url": "https://example.test/plugins/data-designer-github/"},
      "plugins": [
        {
          "name": "github",
          "plugin_type": "seed-reader",
          "entry_point": {
            "group": "data_designer.plugins",
            "name": "github",
            "value": "data_designer_github.plugin:plugin"
          }
        }
      ]
    }
  ]
}
```

Important validation rules:

- Catalog fields are strict; unexpected fields require a schema-version bump.
- Catalog alias names must match `^[A-Za-z0-9_.-]+$`; aliases are compared case-insensitively.
- The default built-in catalog alias is `nvidia`; `DATA_DESIGNER_DEFAULT_PLUGIN_CATALOG_URL` can override the default URL for QA/staging.
- GitHub repository/tree/blob URLs are normalized to raw `catalog/plugins.json` URLs; local directories normalize to `<dir>/catalog/plugins.json`.
- `entry_point.group` must be exactly `data_designer.plugins`.
- `plugin_type` must be one of `column-generator`, `seed-reader`, or `processor`.
- Duplicate canonical package names are rejected (`data-designer-foo` and `data_designer_foo` collide).
- Duplicate runtime plugin names and enum-key collisions are rejected (`foo-bar` and `foo_bar` both normalize to `FOO_BAR`).
- Package install requirements must name the catalog package.
- `compatibility.data_designer.requirement`, `specifier`, and `marker` must agree.

## Package alias and runtime plugin name resolution

`PluginCatalogService.get_package_entries()` resolves install/info/uninstall targets in this order:

1. Exact package name, canonicalized with packaging rules.
2. Package alias formed by removing the `data-designer-` prefix.

Examples:

- `data-designer-github` resolves to package `data-designer-github`.
- `github` resolves to package `data-designer-github` when no exact package named `github` exists.
- A runtime plugin name that is not also a package alias does **not** resolve for install/info/uninstall.

If the user gives a runtime plugin name, the controller searches runtime plugin entries and prints a recovery hint such as:

```bash
# User provided runtime plugin name text-column.
data-designer plugin --catalog local install text-transform
```

When the mistaken runtime name includes a version specifier, the hint preserves it:

```bash
data-designer plugin --catalog local install text-transform==0.1.0
```

## Compatibility behavior

- `list` and `search` hide incompatible catalog packages by default. Use `--include-incompatible` to see them.
- Compatibility evaluates local Python version and installed `data-designer` version against catalog specifiers and markers.
- `info` shows compatibility details even when install plan construction fails.
- Unversioned real installs are blocked when compatibility fails.
- Versioned installs warn instead of being blocked solely by catalog compatibility metadata, because catalog metadata may describe the default package version rather than the requested version. The package manager still receives constraints that preserve the installed DataDesigner package family.

## Install planning and DataDesigner package preservation

`PluginInstallService` builds the exact command before mutation. Always dry-run first when assisting a user.

Manager resolution:

- `--manager auto` prefers `uv` when present and `uv --version` is at least `0.10.0`.
- If auto mode finds old/malformed/unavailable `uv`, it falls back to pip when pip is available and prints a warning.
- `--manager uv` fails instead of falling back when uv is missing or too old.
- `--manager pip` uses the current interpreter's `python -m pip`.

Install target modes:

- `uv-project`: active virtualenv plus a nearby non-DataDesigner user `pyproject.toml`; command starts with `uv add --project ... --active --no-install-project`.
- `uv-environment`: no suitable active project; command starts with `uv pip install --python <sys.executable>`.
- `pip-environment`: command starts with `<sys.executable> -m pip install`.

DataDesigner preservation is deliberate:

- The protected distribution names are `data-designer`, `data-designer-config`, and `data-designer-engine`.
- `uv-environment` passes exact pins via `--constraint -` and stdin.
- `pip-environment` materializes a temporary constraint file only while the command runs.
- `uv-project` adds `--no-install-package` for each DataDesigner distribution.
- Install planning fails if installed DataDesigner package-family versions cannot be resolved or are invalid versions.

Uninstall planning uses the catalog package name, not the install requirement string. In `uv-project` mode it runs `uv remove --no-sync` only when the package is declared in the project dependencies, then also runs `uv pip uninstall --python <sys.executable> <package>` so the active environment is cleaned.

## Verification after mutation

After install, the CLI invalidates import caches and checks that every declared entry point is installed, matches by entry-point name/value/distribution, and loads to a `Plugin` instance. If verification fails, the install may still have succeeded but DataDesigner cannot load every runtime entry point.

After uninstall, the CLI invalidates import caches and checks that declared entry points are absent. If they remain visible, restart the shell or inspect the package environment.

`data-designer plugin installed` and `PluginCatalogService.list_installed_plugins()` are read-only metadata inspections: they call `importlib.metadata.entry_points(group="data_designer.plugins")` and do not load plugin modules.

## Safe agent workflow

1. Run `data-designer plugin search <query>` or `data-designer plugin list` to identify the package.
2. If the user provided a runtime plugin name, convert to the package or package alias suggested by the CLI.
3. Run `data-designer plugin info <package-or-alias>` for docs, runtime plugins, compatibility, and install strategy.
4. Run `data-designer plugin install <package-or-alias> --dry-run` or `uninstall ... --dry-run`.
5. Ask for explicit approval before a real install/uninstall.
6. After mutation, run `data-designer plugin installed` and the bundled safe inspector to confirm entry-point visibility in the intended interpreter.
7. Restart long-lived Python processes before expecting new plugin types in import-time unions.

## Evidence consulted

- `packages/data-designer/src/data_designer/cli/commands/plugin.py`
- `packages/data-designer/src/data_designer/cli/controllers/plugin_catalog_controller.py`
- `packages/data-designer/src/data_designer/cli/plugin_catalog.py`
- `packages/data-designer/src/data_designer/cli/services/plugin_catalog_service.py`
- `packages/data-designer/src/data_designer/cli/services/plugin_install_service.py`
- `packages/data-designer/src/data_designer/cli/repositories/plugin_catalog_repository.py`
- `packages/data-designer/tests/cli/commands/test_plugin_command.py`
- `packages/data-designer/tests/cli/controllers/test_plugin_catalog_controller.py`
- `packages/data-designer/tests/cli/repositories/test_plugin_catalog_repository.py`
- `packages/data-designer/tests/cli/services/test_plugin_catalog_service.py`
- `packages/data-designer/tests/cli/services/test_plugin_install_service.py`

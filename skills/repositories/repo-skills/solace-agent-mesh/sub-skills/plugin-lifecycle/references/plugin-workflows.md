# SAM plugin workflows

This reference covers plugin package creation, component addition, installation, catalog browsing, and building. It is for safe planning and dry inspection; it does not require starting a broker, gateway, LLM, or SAM app.

## Command map

| Goal | Command | Primary side effects | Pre-flight |
| --- | --- | --- | --- |
| Create a reusable plugin package | `sam plugin create PLUGIN_NAME [--type TYPE] [--skip] ...` | Creates or rewrites files in `./<plugin-name>/`; may query official registry names | Choose type/name; ensure target directory/files are disposable or backed up |
| Install a plugin package/module | `sam plugin install PLUGIN_SOURCE [--install-command "uv pip install {package}"]` | May run package-manager command; imports installed module to locate package files | Inspect source, isolate Python env, verify installer command contains `{package}` |
| Install and add one component config | `sam plugin add COMPONENT_NAME --plugin PLUGIN_SOURCE [--install-command "..."]` | Installs/locates plugin, writes `configs/.../<component>.yaml`, overwriting if present | Run `inspect_plugin.py`; check target path; confirm project root |
| Browse catalog | `sam plugin catalog [--port 5003] [--install-command "..."]` | Starts local Flask server, contacts/clones registries, opens browser, writes catalog state/cache | Confirm network/browser/port; do not use for dry validation |
| Build artifacts | `sam plugin build [PLUGIN_PATH]` | Runs `python -m build`; creates/updates `dist/` | Confirm `pyproject.toml`; install Python `build` package; expect build backend behavior |

## Plugin source choices

`sam plugin install` and `sam plugin add --plugin` route plugin sources as follows in SAM 1.28.7:

| Source form | Example | Behavior |
| --- | --- | --- |
| Already installed module name | `my_plugin` or `my-plugin` | Treated as an importable module (`-` normalized to `_`). For non-official package-index names, install the package yourself first or provide a local path/wheel/Git URL. |
| Official plugin name | `sam-rest-gateway` | Resolved through the official plugin list. Some official names are installed from PyPI-style package names; others resolve to `git+...#subdirectory=...`. Requires registry/network access unless cached. |
| Local plugin directory | `./my-plugin` | Reads `pyproject.toml` for `[project].name`, runs installer command on the directory, then imports the normalized module name. |
| Wheel file | `./dist/my_plugin-0.1.0-py3-none-any.whl` | Runs installer command on the wheel and infers module name from the first wheel filename segment. Prefer wheels for portable local sharing. |
| Git repository URL | `https://github.com/user/repo.git` | Requires `git`; clones to a temporary directory to read `pyproject.toml`, then installs from the repository URL. |
| Pip-style Git URL | `git+https://github.com/user/repo.git#subdirectory=my-plugin` | Runs installer command directly and infers module name from the repository basename or `#subdirectory=` value. |

Notes:

- A local source distribution ending in `.tar.gz` is not a reliable path in this version because extension detection is suffix-based; prefer a wheel, local directory, or Git source.
- `file://` sources are excluded from official registry resolution, but ordinary installation still depends on the installer command accepting that source.
- URLs not ending in `.git` are not handled as plain repository URLs; use `git+...` pip syntax when in doubt.

## Plugin package layout and metadata

A plugin created by `sam plugin create` normally contains:

```text
<plugin-kebab-name>/
├── config.yaml
├── pyproject.toml
├── README.md
└── src/
    └── <plugin_snake_name>/
        ├── __init__.py
        └── type-specific files
```

Important metadata contracts:

- `[project].name` is the Python package/project name. SAM normalizes hyphens to underscores when deriving import module names.
- `[tool.<project_name_with_underscores>.metadata].type` controls where `sam plugin add` writes the component config:
  - `agent` or `tool` -> `configs/agents/<component-kebab>.yaml`
  - `gateway` -> `configs/gateways/<component-kebab>.yaml`
  - `workflow` -> `configs/workflows/<component-kebab>.yaml`
  - missing/unknown/custom -> `configs/plugins/<component-kebab>.yaml`
- `config.yaml` is the component template. `sam plugin add` replaces these placeholders:
  - `__COMPONENT_SNAKE_CASE_NAME__`
  - `__COMPONENT_UPPER_SNAKE_CASE_NAME__`
  - `__COMPONENT_KEBAB_CASE_NAME__`
  - `__COMPONENT_PASCAL_CASE_NAME__`
  - `__COMPONENT_SPACED_NAME__`
  - `__COMPONENT_SPACED_CAPITALIZED_NAME__`
- The generated `pyproject.toml` uses hatchling and force-includes `config.yaml`, `README.md`, and `pyproject.toml` into the installed package directory. This matters because `sam plugin add` imports the package and then reads those files from the installed module path.

## `sam plugin create`

Typical non-interactive command:

```bash
sam plugin create my-rag-agent \
  --type agent \
  --author-name "Example Team" \
  --author-email "team@example.com" \
  --description "Reusable RAG agent plugin" \
  --version 0.1.0 \
  --skip
```

Supported types are `agent`, `gateway`, `tool`, `workflow`, and `custom`. Defaults in skip mode are type `agent`, author `Your Name`, email `your.email@example.com`, version `0.1.0`, and description `A SAM plugin: <spaced name>`.

Name behavior:

- Input names are normalized by splitting spaces, hyphens, underscores, and camel-case boundaries.
- The output directory is kebab-case (`My Test Plugin` -> `my-test-plugin`).
- The Python module directory is snake_case (`my_test_plugin`).
- Pascal/spaced variants populate class/config placeholders.
- Creation checks official plugin names before writing. If the registry check cannot reach the network, it may print an error and continue without detecting a conflict.

Template outputs by type:

| Type | Generated source | Config route when added | Notes |
| --- | --- | --- | --- |
| `agent` | `src/<module>/tools.py` with example Python tools | `configs/agents` | Agent config includes model/session/artifact sections and example tool references. |
| `tool` | `src/<module>/tools.py` | `configs/agents` | Tool plugins are packaged as agent-style configs that expose tools. |
| `gateway` | `src/<module>/app.py` and `component.py` | `configs/gateways` | Gateway skeleton extends SAM gateway base classes; live activation belongs elsewhere. |
| `workflow` | comment-only `__init__.py`; YAML workflow template | `configs/workflows` | Declarative workflow plugin; no Python workflow code required by template. |
| `custom` | `src/<module>/app.py` | `configs/plugins` | For custom integrations/configs outside agent/gateway/workflow routes. |

Caution: `sam plugin create` uses `mkdir(..., exist_ok=True)` and normal file writes. It can overwrite `config.yaml`, `pyproject.toml`, `README.md`, and source skeleton files in an existing target directory.

## `sam plugin install`

Use install when you want the plugin package available in the environment but do not yet want to create a project component YAML.

```bash
sam plugin install ./my-plugin --install-command "uv pip install {package}"
sam plugin install ./my-plugin/dist/my_plugin-0.1.0-py3-none-any.whl
sam plugin install 'git+https://github.com/org/plugins.git#subdirectory=my-plugin'
sam plugin install sam-rest-gateway
```

Installer command behavior:

- Default is `pip3 install {package}`.
- `SAM_PLUGIN_INSTALL_COMMAND` can set the default, and `--install-command` overrides it for that invocation.
- Include the literal `{package}` placeholder yourself. The implementation formats the string but does not robustly reject commands that omit the placeholder.
- The command is split on whitespace rather than executed through a shell. Avoid shell syntax, pipes, redirections, or quoted arguments with spaces.
- For `uv`, prefer `uv pip install {package}`. For Poetry/Conda, verify the command works as a plain argument list.

Post-install, SAM imports the module to find its package directory. If installation succeeds but the module name differs from `[project].name` normalized to underscores, `sam plugin install` can still fail at the import/location step.

## `sam plugin add`

Use add from a SAM project root after confirming the plugin package and target component path.

```bash
python sub-skills/plugin-lifecycle/scripts/inspect_plugin.py ../my-plugin \
  --component-name my-agent \
  --project-dir .

sam plugin add my-agent --plugin ../my-plugin --install-command "uv pip install {package}"
```

What the command does:

1. Calls the same installer/locator logic as `sam plugin install`.
2. Reads `config.yaml` and `pyproject.toml` from the installed plugin module path.
3. Replaces component-name placeholders in `config.yaml`.
4. Chooses the output config directory from plugin metadata type.
5. Writes `<component-kebab>.yaml` under `configs/agents`, `configs/gateways`, `configs/workflows`, or `configs/plugins`.

Important operational details:

- The target config file is opened with write mode; an existing file is overwritten.
- If `pyproject.toml` or `config.yaml` is missing from the installed package directory, add fails.
- If metadata type is missing, malformed, or unknown, add falls back to `configs/plugins`.
- `sam plugin add` only creates the component config; any live app run, broker connection, gateway startup, or task execution is outside this sub-skill.

## Official registry and catalog behavior

Official plugin resolution uses a default official registry at SolaceLabs' core plugin repository on branch `main`, plus a list of official plugins published to package indexes. Official names may resolve to a PyPI-normalized package name or to a Git URL with `#subdirectory=<plugin>`.

The catalog command provides a web UI:

```bash
sam plugin catalog --port 5003 --install-command "uv pip install {package}"
```

Runtime behavior to expect:

- Host defaults to `127.0.0.1`; set `CONFIG_PORTAL_HOST` to bind another host.
- Default port is `5003`.
- The URL includes `?config_mode=pluginCatalog`.
- The command starts a child process running the catalog backend, waits briefly, then tries to open a browser.
- It fetches/clones registries, caches Git checkouts under SAM CLI home, and stores user registry state there.
- The catalog install action shells out to `sam plugin add COMPONENT --plugin <local-plugin-path>` and forwards `SAM_PLUGIN_INSTALL_COMMAND` if set.
- On interrupt, the command terminates or kills the child process if needed.

Do not use catalog as a non-interactive dry validator. Use `inspect_plugin.py` for local structural checks and reserve catalog for intentional interactive browsing.

## `sam plugin build`

From a plugin root:

```bash
python -m pip install build
sam plugin build .
```

Behavior:

- Requires `pyproject.toml` in the target directory.
- Temporarily changes into the plugin path, runs `python -m build`, then restores the original working directory.
- Prints stdout and stderr/warnings from the build process.
- On success, lists generated files in `dist/` when present.
- On failure, reports the build exit code, missing Python executable, missing `build` package, or backend errors.

Before building, check that source/config files are included in the package. A plugin that builds but omits `config.yaml` or `pyproject.toml` from the installed module will later fail in `sam plugin add`.

## Safe inspection workflow

Run the bundled helper before install/add/build operations:

```bash
python sub-skills/plugin-lifecycle/scripts/inspect_plugin.py path/to/plugin \
  --component-name desired-component \
  --project-dir path/to/project \
  --json
```

The helper only reads files. It checks pyproject metadata, plugin type, config placeholders, package layout, build force-includes, component target path, and whether the target file already exists. It is safe to run from arbitrary directories.

If the helper reports warnings that are intentional, document the reason before proceeding. If it reports errors, fix the plugin package or install source before running SAM CLI commands.

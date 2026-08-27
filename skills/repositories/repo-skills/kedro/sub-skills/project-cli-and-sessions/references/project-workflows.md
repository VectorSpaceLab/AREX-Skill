# Project Workflows

Use this reference for concrete project creation, layout, metadata, settings, packaging, and notebook workflows. It is self-contained for Kedro 1.4.0 and does not require reading the source repository.

## Create a New Project Safely

For an automated, non-interactive project with no examples and telemetry denied:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro new --name="Customer Churn" --tools=lint,test --example=n --telemetry=no
```

Expected derivations:

- `project_name`: human-readable name, for example `Customer Churn`.
- `repo_name`: local directory name, typically lower-hyphen, for example `customer-churn`.
- `python_package`: importable package name, typically lower-underscore, for example `customer_churn`.

Name rules to preserve:

- Project names must be at least two characters long.
- Project names can include alphanumeric characters, spaces, underscores, and hyphens.
- The derived or configured `python_package` must not be a Python keyword or a standard library module name.
- If a user provides `python_package` in a `--config` file, that explicit value wins over the name-derived value and is validated.

Tool choices:

- `lint`: adds Ruff configuration and dependencies.
- `test` or `tests`: adds pytest setup and tests.
- `log` or `logs`: adds custom logging configuration.
- `docs` or `doc`: adds Sphinx documentation setup.
- `data`: adds the standard data directory structure.
- `pyspark`: adds PySpark-oriented setup and can trigger the PySpark starter path.
- `none`: selects no optional tools.
- `all`: selects all available tools.

Avoid `--tools=viz`; it is rejected in this version. Kedro Viz is a separate plugin workflow.

## Non-Interactive Config File

Use `--config` when the template has prompts or when the agent must make project creation reproducible. A minimal config for the default template should include:

```yaml
project_name: Customer Churn
repo_name: customer-churn
python_package: customer_churn
tools: lint,test
example_pipeline: no
```

Then run:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro new --config=project.yml --telemetry=no
```

CLI flags `--name`, `--tools`, and `--example` override values from the config file. When using a starter, do not include `tools` or `example_pipeline` in the config unless that starter explicitly defines compatible prompts; Kedro rejects core `tools`/`example_pipeline` keys with `--starter`.

## Starters and Templates

Use a starter when the user wants a prebuilt layout or example project:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro starter list
KEDRO_DISABLE_TELEMETRY=1 kedro new --starter=spaceflights-pandas --name=spaceflights --telemetry=no
```

Official starter aliases in this version include `astro-airflow-iris`, `spaceflights-pandas`, `spaceflights-pyspark`, `databricks-iris`, and `support-agent-langgraph`.

Remote starter and example workflows can require Git and network access:

- `--starter=<alias>` resolves to the official Kedro starters repository.
- `--starter=git+https://...` asks Cookiecutter/Git to fetch the repository.
- `--example=yes` uses a spaceflights starter.
- `--tools=pyspark` uses the PySpark spaceflights starter even when `--example=no`.
- `--checkout=<tag-or-branch>` pins a starter repository version. Without an explicit starter, `--checkout` only matters when PySpark/example selection triggers a starter.
- `--directory=<subdir>` is valid for explicit local/remote starter repositories, not for official aliases.

If Git is unavailable or network access is unsafe, prefer the default template with `--tools=none --example=n`, a local starter path, or a user-approved predownloaded archive/path.

## Project Layout and Detection

A Kedro project is detected by a `pyproject.toml` file in the current directory or a parent directory containing a `[tool.kedro]` section. A generated project normally includes:

```text
project-root/
  pyproject.toml
  conf/
    base/
    local/
  src/
    <package_name>/
      __init__.py
      __main__.py
      settings.py
      pipeline_registry.py
      pipelines/
  requirements.txt
  README.md
```

For a minimal project, these are mandatory for project-mode command discovery and execution:

- `pyproject.toml` with `[tool.kedro]` metadata.
- A Python package matching `package_name`.
- `settings.py` inside the package; it can be empty when defaults are enough.
- `pipeline_registry.py` inside the package with `register_pipelines()` for runnable pipelines.

The default generated `[tool.kedro]` metadata includes:

```toml
[tool.kedro]
package_name = "customer_churn"
project_name = "Customer Churn"
kedro_init_version = "1.4.0"
tools = "['Linting', 'Testing']"
example_pipeline = "False"
source_dir = "src"
```

`source_dir` defaults to `src`. For a flat/minimal layout, set `source_dir = ""` or another relative path and ensure that the package path exists under the project root. Kedro validates that the source path exists and is inside the project root.

## Project Settings

Project settings live in `<package_name>/settings.py`. Defaults in Kedro 1.4.0 include:

- `CONF_SOURCE = "conf"`
- `HOOKS = tuple()`
- `CONTEXT_CLASS = kedro.framework.context.KedroContext`
- `SESSION_CLASS = kedro.framework.session.KedroSession`
- `SESSION_STORE_CLASS = kedro.framework.session.store.BaseSessionStore`
- `SESSION_STORE_ARGS = {}`
- `DISABLE_HOOKS_FOR_PLUGINS = tuple()`
- `CONFIG_LOADER_CLASS = kedro.config.OmegaConfigLoader`
- `CONFIG_LOADER_ARGS = {"base_env": "base", "default_run_env": "local"}`
- `DATA_CATALOG_CLASS = kedro.io.DataCatalog`

Settings are application settings, not runtime data configuration. Runtime configuration lives under `conf/` and is owned by `../data-catalog-and-config/SKILL.md`.

For a nonstandard minimal project whose config files live beside the package rather than in `conf/base` and `conf/local`, set:

```python
CONF_SOURCE = "."
CONFIG_LOADER_ARGS = {"base_env": ".", "default_run_env": "."}
```

Custom session/context/catalog classes must be subclasses or protocol-compatible classes expected by Kedro's settings validators. If settings validation fails with an invalid class message, fix the import path or inheritance rather than suppressing validation.

## Packaging a Project

Run packaging from inside a Kedro project:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro package
```

Expected behavior:

- Builds a wheel into `dist/` using `python -m build --wheel --outdir dist` when `pyproject.toml` is at the project root.
- For older layouts without root `pyproject.toml`, builds from the source directory and writes to `../dist`.
- Creates `dist/conf-<package_name>.tar.gz` from the configured `CONF_SOURCE` directory.
- Excludes `local/*.yml` from the configuration archive.

A packaged project includes source code, not local `data/` or unarchived `conf/`. To run elsewhere, install the wheel and provide configuration/data separately. Typical package-mode invocations:

```bash
pip install dist/<project-wheel>.whl
python -m <package_name> --help
python -m <package_name> --pipelines __default__
kedro run --conf-source dist/conf-<package_name>.tar.gz
```

Programmatic package-mode entry point:

```python
from <package_name>.__main__ import main

result = main(["--pipelines", "__default__"])
```

If packaging fails with `No module named build`, install the project's packaging requirements. If `tar` is missing on the platform, use an environment with tar support or package configuration with an equivalent archive process approved by the user.

## Notebook and IPython Workflows

Project-aware interactive commands must be run in a detected project:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro ipython --env=local
KEDRO_DISABLE_TELEMETRY=1 kedro jupyter setup
KEDRO_DISABLE_TELEMETRY=1 kedro jupyter notebook --env=local
KEDRO_DISABLE_TELEMETRY=1 kedro jupyter lab --env=local
```

`kedro ipython` loads `kedro.ipython` and makes these variables available:

- `catalog`: the project catalog, equivalent to `context.catalog`.
- `context`: the `KedroContext` instance.
- `pipelines`: registered pipelines from the pipeline registry.
- `session`: the current `KedroSession`.

`kedro jupyter setup/notebook/lab` creates a kernel named `kedro_<package_name>` and display name `Kedro (<package_name>)`. The kernel argv loads `kedro.ipython`.

Optional dependency checks:

- `kedro ipython` requires `IPython`.
- `kedro jupyter setup` requires `ipykernel`.
- `kedro jupyter notebook` requires `notebook`.
- `kedro jupyter lab` requires `jupyterlab`.

If interactive variables are missing, inspect the terminal output for the full import/config error, then check settings, catalog/config files, and project dependencies. Use `%reload_kedro <project_root>` inside IPython/Jupyter when the current notebook directory is outside the project. `%reload_kedro --env=prod` changes the configuration environment, and `%reload_kedro --params=key:value` can pass runtime parameters.

## Decision Checklist

Before changing a project:

- Confirm whether the requested command is global or project-specific.
- For project commands, verify `pyproject.toml` contains `[tool.kedro]` and the configured package exists under `source_dir`.
- For project creation, decide whether network/Git access is allowed before using starters, examples, or PySpark tool selection.
- Use `--telemetry=no` for generated projects when the user wants opt-out persisted, and `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for safe probes.
- Route pipeline authoring, catalog/config, run semantics, hooks/plugins, or server details to the sibling sub-skill that owns that surface.

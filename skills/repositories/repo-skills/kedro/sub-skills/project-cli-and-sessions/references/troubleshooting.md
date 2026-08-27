# Troubleshooting Project CLI and Sessions

Use this reference for Kedro project creation, CLI discovery, project detection, settings, session, packaging, notebook, and telemetry issues. For pipeline graph errors, catalog/config errors, runner failures, hooks/plugins, or server details, route to the sibling sub-skill that owns that surface.

## Install, Import, and CLI Availability

### `kedro: command not found`

Likely causes:

- Kedro is not installed in the active environment.
- The environment's script directory is not on `PATH`.
- The command is being run from a different Python environment than the one where Kedro was installed.

Checks:

```bash
python -c "import kedro; print(kedro.__version__)"
python -m kedro --version
KEDRO_DISABLE_TELEMETRY=1 kedro --version
```

If `python -m kedro` works but `kedro` does not, fix the environment activation or `PATH`. If import fails, install `kedro` in the current Python environment. Do not use stale import paths such as `kedro.pipeline.modular_pipeline`; for Kedro 1.4.0 reusable pipeline construction uses `kedro.pipeline.pipeline`.

### `kedro info` shows unexpected plugins

`kedro info` reports installed plugin entry points. Plugin commands can override built-in commands. If command behavior differs from the built-in reference, check installed plugins and project-level `<package_name>.cli`. Route plugin/custom CLI debugging to `../hooks-and-extensions/SKILL.md`.

## Project Detection Problems

### Project commands are missing or report `Kedro project not found`

Kedro project commands are available only when the current directory or a parent directory contains `pyproject.toml` with `[tool.kedro]`.

Check:

```bash
pwd
python - <<'PY'
from pathlib import Path
from kedro.utils import find_kedro_project
print(find_kedro_project(Path.cwd()))
PY
```

Fixes:

- `cd` into the project root or a subdirectory.
- Add or repair `[tool.kedro]` in `pyproject.toml`.
- Ensure the configured `source_dir` exists and is inside the project root.
- Ensure `package_name`, `project_name`, and `kedro_init_version` are present under `[tool.kedro]`.

### `Could not find the project configuration file 'pyproject.toml'`

This comes from `bootstrap_project(project_path)` when the path is not a Kedro project root. Pass the actual project root, or discover it with `find_kedro_project()` before bootstrapping.

### `There's no '[tool.kedro]' section in the 'pyproject.toml'`

The project may be a plain Python package, an old Kedro layout, or the metadata was removed. Add a `[tool.kedro]` section with at least:

```toml
[tool.kedro]
package_name = "your_package"
project_name = "Your Project"
kedro_init_version = "1.4.0"
source_dir = "src"
```

### `Missing required keys ... from 'pyproject.toml'`

Add the missing mandatory keys: `package_name`, `project_name`, and `kedro_init_version`.

### Kedro project version mismatch

If `kedro_init_version` has a different major version than the installed Kedro package, `bootstrap_project()` raises a version mismatch. Use an environment with a compatible Kedro major version or update/migrate the project template and metadata intentionally.

### `Source path ... cannot be found` or `has to be relative to your project root`

`source_dir` in `[tool.kedro]` is wrong. Set it to a relative path such as `src`, `.` for a flat project, or another existing directory inside the project root.

## `kedro new` Errors

### Invalid project name

Error signal includes that the name must contain only alphanumeric symbols, spaces, underscores, and hyphens and be at least two characters long.

Fix: choose a name such as `Customer Churn`, `customer-churn`, or `customer_churn_2`. Avoid dots and shell-special characters.

### Package name clashes with keyword or standard library module

Error signal says the package name clashes with a Python keyword or standard library module. This prevents imports from resolving correctly later.

Fix: use a different `project_name` or explicit `python_package` in the config file. For example, avoid `email`, `json`, and `import`; use `email_service`, `json_app`, or `import_data`.

### Invalid `--tools` value

Accepted values are `lint`, `test`, `tests`, `log`, `logs`, `docs`, `doc`, `data`, `pyspark`, `all`, and `none`. `all` and `none` cannot be combined with other tools. `viz` is not a valid tool in this version.

### `Cannot use the --starter flag with the --example and/or --tools flag`

A starter owns its own template prompts. Remove `--tools` and `--example`, or use the default template instead of `--starter`.

### `Cannot use the --directory flag without a --starter value`

`--directory` only makes sense when a starter repository has multiple template subdirectories. Add `--starter=<local-or-remote-starter>` or remove `--directory`.

### `Cannot use the --directory flag with a --starter alias`

Official aliases already define their directory. Remove `--directory`, or use the full remote/local starter path with a directory.

### Starter/template not found

Error signal includes `Kedro project template not found` and may list official aliases. Likely causes are a bad alias/path, unavailable network/Git, or invalid checkout.

Fixes:

- Run `kedro starter list` to confirm aliases.
- Use a local starter path when network access is not allowed.
- Check the `--checkout` tag/branch/commit.
- Avoid remote starters unless the user has approved network access.

### Telemetry prompt blocks automation

Use both environment-level and project-level opt-out when appropriate:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro new --name="My Project" --tools=none --example=n --telemetry=no
```

`KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` disables telemetry for the current process. `--telemetry=no` creates `.telemetry` in the generated project with `consent: false`. If the project already exists, a manual `.telemetry` file containing `consent: false` also works.

## Settings and Bootstrap Errors

### `Package name not found. Make sure you have configured the project using 'bootstrap_project'`

This appears when code calls settings-dependent APIs before project setup. In source-tree scripts, call:

```python
from pathlib import Path
from kedro.framework.startup import bootstrap_project

bootstrap_project(Path("/path/to/project"))
```

In installed package mode, call:

```python
from kedro.framework.project import configure_project

configure_project("your_package")
```

### `find_pipelines cannot be called before the project is configured`

Call `bootstrap_project(project_root)` or `configure_project(package_name)` before `find_pipelines()` or before reading `kedro.framework.project.pipelines`.

### `No 'settings.py' found, defaults will be used`

This is a warning. It is acceptable if defaults are intended, but a generated project should normally include an empty `<package_name>/settings.py` for clarity.

### Invalid settings class errors

Signals include `Invalid value ... received for setting ... It must be a subclass of ...` or catalog protocol compatibility messages.

Fixes:

- Check the dotted import path in `settings.py`.
- Ensure custom context/config loader/session store classes subclass the expected Kedro base class.
- Ensure custom data catalog classes implement the required catalog protocol.
- Route custom class/plugin design to `../hooks-and-extensions/SKILL.md` or catalog customization to `../data-catalog-and-config/SKILL.md`.

### Logging configuration errors

Kedro validates logging classes and rejects unsafe `()` factory keys in logging configuration. Fix invalid logging class import paths and remove factory keys from `conf/logging.yml`. Use `configure_project(package_name, preserve_logging=True)` when repeated package-mode setup must keep runtime-added logging handlers.

## Session and Context Errors

### `KedroSession expect an instance of Runner instead of a class`

Pass `SequentialRunner()` rather than `SequentialRunner`:

```python
from kedro.runner import SequentialRunner
session.run(runner=SequentialRunner())
```

Route runner choice and constraints to `../runners-and-execution/SKILL.md`.

### `A run has already been completed as part of the active KedroSession`

A `KedroSession` can have only one successful run. Create a new session for the next run:

```python
with KedroSession.create(project_path=project_root) as session:
    session.run()

with KedroSession.create(project_path=project_root) as session:
    session.run()
```

For long-lived multi-run services, evaluate `KedroServiceSession`, but expect a different runtime parameter flow.

### Failed to find a pipeline name

Error signal says the pipeline must be generated and returned by `register_pipelines()`, sometimes with close-match suggestions. Check `<package_name>/pipeline_registry.py`, the value passed to `pipeline_names`, and whether the requested pipeline is registered. Route pipeline registry and graph authoring details to `../pipelines-and-nodes/SKILL.md`.

### Missing config while loading context

If `session.load_context()` or `context.catalog` fails with missing `conf/base`, `conf/local`, catalog, parameters, or credentials errors, the project was detected but its runtime configuration is incomplete or has a nonstandard layout. Check `settings.CONF_SOURCE` and `CONFIG_LOADER_ARGS`; route detailed config behavior to `../data-catalog-and-config/SKILL.md`.

### Runtime parameters not applied

For `KedroSession`, pass `runtime_params` to `KedroSession.create()` or `--params` to `kedro run`. For `KedroServiceSession`, runtime parameters are passed to `run()` for each run. Ensure keys use the same naming convention expected by the project parameters, for example nested keys through dictionaries in Python or dotted keys on the CLI.

## Optional Dependency Problems

### `Module 'IPython' not found`

`kedro ipython` requires `IPython`. Install the project requirements or add the missing interactive dependency to the environment.

### Jupyter kernel setup fails

`kedro jupyter setup` requires `ipykernel`; `kedro jupyter notebook` requires `notebook`; `kedro jupyter lab` requires `jupyterlab`. The commands create or replace a user-level Jupyter kernel named `kedro_<package_name>`. If the kernel command has stale Python paths, rerun `kedro jupyter setup` from the intended environment.

### `kedro server` optional dependencies missing

Server behavior is owned by `../inspection-and-server/SKILL.md`. In this version, server startup requires optional packages such as `fastapi`, `pydantic`, and `uvicorn`.

## Packaging Problems

### `kedro package` cannot import `build`

Install the project's build/packaging dependency, then rerun `kedro package` from the project root.

### No root `pyproject.toml` during packaging

Kedro falls back to an older layout by building from the source directory and writing the wheel to `../dist`. Verify the project layout before assuming artifacts appear under project-root `dist/`.

### Config archive includes or excludes wrong files

`kedro package` archives the configured `CONF_SOURCE` directory and excludes `local/*.yml`. If configuration is not under `conf`, confirm `settings.CONF_SOURCE` and expect the archive command to use that source's parent directory.

## Quick Diagnostic Flow

1. Run `scripts/kedro_cli_probe.py --info` from the current directory.
2. If CLI import/version fails, fix the Python environment.
3. If project detection is false, inspect `pyproject.toml` and `[tool.kedro]`.
4. If project detection is true but commands fail, inspect `source_dir`, package importability, `settings.py`, and `pipeline_registry.py`.
5. If a run/session fails after context loads, route to runners, pipelines, or data/config based on the failing surface.

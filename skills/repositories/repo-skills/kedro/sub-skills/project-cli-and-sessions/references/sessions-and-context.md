# Sessions and Context

Use this reference when Python code needs to load a Kedro project, create a context, start a session, or run package-mode entry points. Route detailed run filtering and runner behavior to `../runners-and-execution/SKILL.md`.

## Startup APIs

### `bootstrap_project(project_path)`

Import path:

```python
from kedro.framework.startup import bootstrap_project
```

Behavior:

- Resolves `project_path` and reads `pyproject.toml` under that directory.
- Requires a `[tool.kedro]` section with `package_name`, `project_name`, and `kedro_init_version`.
- Verifies that the major version of `kedro_init_version` matches the installed Kedro major version.
- Resolves `source_dir`, validates it is inside the project root, and adds it to `sys.path` and `PYTHONPATH` when needed.
- Calls `configure_project(package_name)`.
- Returns project metadata with fields such as `config_file`, `package_name`, `project_name`, `project_path`, `source_dir`, `kedro_init_version`, `tools`, and `example_pipeline`.

Use `bootstrap_project()` for source-tree project mode, especially scripts started outside `kedro run`, notebooks, tests, and automation that begins outside the project root.

### `configure_project(package_name, preserve_logging=False)`

Import path:

```python
from kedro.framework.project import configure_project
```

Behavior:

- Configures Kedro settings from `<package_name>.settings`.
- Configures lazy pipeline loading from `<package_name>.pipeline_registry`.
- Stores the package name globally so settings validation and multiprocessing bootstrap can find the project.
- Configures project logging for the package logger.

Use `configure_project()` for installed package mode where the package is already importable. Use `preserve_logging=True` in long-running applications that add logging handlers before reconfiguring Kedro, because the default behavior can overwrite runtime-added handlers.

### `find_kedro_project(current_dir)` and project detection

Import path:

```python
from kedro.utils import find_kedro_project, is_kedro_project
```

`is_kedro_project(path)` returns true only when `path/pyproject.toml` exists and contains `[tool.kedro]`. `find_kedro_project(current_dir)` checks the directory and its parents and returns the first matching project root or `None`.

## `KedroSession.create()`

Import path:

```python
from kedro.framework.session import KedroSession
```

Verified signature:

```python
KedroSession.create(
    project_path=None,
    save_on_close=True,
    env=None,
    runtime_params=None,
    conf_source=None,
)
```

Arguments:

- `project_path`: project root. If omitted, the session tries `find_kedro_project(Path.cwd())` and then falls back to the current directory.
- `save_on_close`: whether to save session metadata when the session closes. The default for `create()` is `True`.
- `env`: configuration environment; if omitted, `KEDRO_ENV` is used when set.
- `runtime_params`: dictionary merged into project parameters and stored in session data.
- `conf_source`: alternate configuration source passed to the config loader.

Session data can include project path, generated session ID, CLI context when created under Click, environment, runtime parameters, username if available, and Git commit/dirty status when Git metadata is available.

Use `KedroSession.create()` as a context manager:

```python
from pathlib import Path

from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

project_root = Path("/path/to/project")
bootstrap_project(project_root)

with KedroSession.create(project_path=project_root, env="local") as session:
    context = session.load_context()
    catalog = context.catalog
```

For public generated skills and reusable snippets, do not hard-code local paths. In user code, replace `/path/to/project` with a project path supplied by the user or discovered with `find_kedro_project()`.

## Running From Scripts Outside a Project

A robust source-tree script pattern:

```python
from pathlib import Path

from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.utils import find_kedro_project

start = Path.cwd()
project_root = find_kedro_project(start)
if project_root is None:
    raise RuntimeError("Run this script inside a Kedro project or pass project_root.")

bootstrap_project(project_root)

with KedroSession.create(project_path=project_root, runtime_params={"example": 1}) as session:
    context = session.load_context()
    print(context.project_path)
```

If the script is stored outside the project, replace `start = Path.cwd()` with a user-provided root or the script's known search directory. Always call `bootstrap_project(project_root)` before relying on project settings, pipeline registry, or `KedroSession` defaults.

## Running a Pipeline Programmatically

This sub-skill gives the session pattern; read `../runners-and-execution/SKILL.md` for filtering semantics and runner tradeoffs.

```python
from pathlib import Path

from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.runner import SequentialRunner

project_root = Path("/path/to/project")
bootstrap_project(project_root)

with KedroSession.create(project_path=project_root, env="local") as session:
    result = session.run(
        pipeline_names=["__default__"],
        runner=SequentialRunner(),
        tags=["reporting"],
    )
```

Important session rules:

- A `KedroSession` has a one-to-one mapping with a successful run. After one successful `session.run()`, a second run on the same session raises a `KedroSessionError` telling you to create a new session.
- If a run raises an exception before completing, the same session may be reused after the failure, but clearer automation usually creates a fresh session for retries.
- Pass a runner instance such as `SequentialRunner()`, not the class `SequentialRunner`; otherwise Kedro raises that it expected an instance of `Runner` and asks whether `()` was forgotten.
- `pipeline_name` is deprecated in favor of `pipeline_names`.
- Missing pipeline names raise `ValueError` explaining that the pipeline must be generated and returned by `register_pipelines()`, with close-match suggestions when available.

## `session.load_context()` and `KedroContext`

`session.load_context()` creates the configured context class, usually `kedro.framework.context.KedroContext`.

The context receives:

- `package_name` from configured project state.
- `project_path` from the session.
- Config loader from `settings.CONFIG_LOADER_CLASS`, usually `OmegaConfigLoader`.
- `env` and `runtime_params` from session data.
- The session hook manager.

Useful context properties:

- `context.project_path`: resolved project root.
- `context.env`: active configuration environment.
- `context.catalog`: a catalog built from config and credentials.
- `context.params`: validated parameters plus runtime parameter overrides.

Catalog and config details are owned by `../data-catalog-and-config/SKILL.md`. Pipeline registry and graph details are owned by `../pipelines-and-nodes/SKILL.md`.

## Configuration Source and Environments

`KedroSession.create(env="prod")` or `kedro run --env=prod` sets the environment that `OmegaConfigLoader` uses. If `env` is omitted, the `KEDRO_ENV` environment variable is used when set.

`KedroSession.create(conf_source="path-or-archive")` or `kedro run --conf-source <path>` overrides where configuration is loaded from. Package-mode deployment can use a compressed configuration archive created by `kedro package`:

```bash
kedro run --conf-source dist/conf-<package_name>.tar.gz
```

For nonstandard projects, update `settings.py` instead of passing `conf_source` everywhere when the project permanently uses a different config layout.

## Package Mode

A generated Kedro project includes `<package_name>/__main__.py` that configures the project package and forwards command-line arguments to Kedro's run command. After installing a built wheel:

```bash
python -m <package_name> --help
python -m <package_name> --pipelines __default__
```

Programmatic package mode:

```python
from <package_name>.__main__ import main

result = main(["--pipelines", "__default__"])
```

If you need lower-level setup in installed package mode:

```python
from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession

configure_project("<package_name>", preserve_logging=True)
with KedroSession.create(project_path=".") as session:
    context = session.load_context()
```

Choose `bootstrap_project(project_root)` for source checkouts and `configure_project(package_name)` for installed packages.

## Common Startup Decisions

- Need to run a CLI command from a project? Let `kedro` bootstrap the project automatically by running from the project or a subdirectory.
- Need to inspect a project from Python source code? Use `find_kedro_project()` and `bootstrap_project()`.
- Need to run an installed packaged project? Use `python -m <package_name>` or call `configure_project(package_name)` before creating sessions.
- Need multiple successful runs in one long-lived process? Consider `KedroServiceSession` if appropriate for the application, or create a fresh `KedroSession` per run.
- Need run filtering, runner choice, or `only_missing_outputs` behavior? Read `../runners-and-execution/SKILL.md`.

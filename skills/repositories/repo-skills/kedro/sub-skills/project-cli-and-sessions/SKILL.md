---
name: project-cli-and-sessions
description: "Create and manage Kedro projects through the CLI, project
  metadata, settings, sessions, packaging, notebooks, and safe diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Project CLI and Sessions

Use this sub-skill when a task is about creating a Kedro project, identifying whether a directory is a Kedro project, using global or project-specific `kedro` commands, configuring project metadata/settings, bootstrapping a project for Python code, using `KedroSession`, packaging a project, or opening project-aware IPython/Jupyter sessions.

## Route Here

- Create projects with `kedro new`, `--config`, `--tools`, `--example`, `--starter`, `--checkout`, `--directory`, or `--telemetry`.
- Diagnose CLI command availability, project detection, `pyproject.toml` metadata, project layout, starter/template behavior, and telemetry prompts.
- Use `bootstrap_project()`, `configure_project()`, `KedroSession.create()`, `session.load_context()`, project `settings.py`, `kedro package`, `kedro ipython`, or `kedro jupyter`.
- Prepare a packaged-project command such as `python -m <package_name>` or programmatic package-mode startup.

## Route Elsewhere

- Pipeline graph authoring, `node()`, `Pipeline`, `pipeline()`, namespacing, tags, or `kedro pipeline create/delete` design choices: read [pipelines and nodes](../pipelines-and-nodes/SKILL.md).
- `kedro run` execution semantics, runner selection, node slicing, resume, and `KedroSession.run()` filtering behavior: read [runners and execution](../runners-and-execution/SKILL.md).
- Catalog, credentials, parameters, config loaders, and data/config validation: read [data catalog and config](../data-catalog-and-config/SKILL.md).
- Hooks, plugins, custom CLI commands, custom datasets, and extension entry points: read [hooks and extensions](../hooks-and-extensions/SKILL.md).
- Inspection snapshots or optional HTTP server behavior: read [inspection and server](../inspection-and-server/SKILL.md).
- Package-wide install/import or router guidance: read the [Kedro root skill](../../SKILL.md).

## Current Facts

- Kedro version target: `1.4.0`; distribution and import name: `kedro`; Python requirement: `>=3.10`.
- Console script: `kedro = kedro.framework.cli:main`; `python -m kedro` is also supported.
- Global commands include `info`, `new`, and `starter`; project commands include `catalog`, `ipython`, `jupyter`, `package`, `pipeline`, `registry`, `run`, and `server`.
- `KedroSession.create(project_path=None, save_on_close=True, env=None, runtime_params=None, conf_source=None)` creates a one-successful-run session.
- `bootstrap_project(project_path)` reads project metadata, adds the source directory to import paths, and calls `configure_project(package_name)`.
- `configure_project(package_name, preserve_logging=False)` configures settings, pipeline registry, package name, and project logging for package mode.

## Reference Map

- Read [CLI reference](references/cli-reference.md) for exact global/project commands, `kedro new` flags, project command routing, telemetry-safe command forms, and optional notebook dependencies.
- Read [project workflows](references/project-workflows.md) for project creation, starter/template choices, metadata/layout requirements, settings defaults, packaging, and notebook/IPython workflows.
- Read [sessions and context](references/sessions-and-context.md) for `bootstrap_project()`, `configure_project()`, `KedroSession`, context loading, runtime parameters, config source overrides, and package-mode startup.
- Read [troubleshooting](references/troubleshooting.md) when CLI commands are missing, project detection fails, starter creation errors, settings/session/bootstrap fails, optional dependencies are absent, or telemetry prompts block automation.
- Run [kedro_cli_probe.py](scripts/kedro_cli_probe.py) to perform safe `kedro --version`, `kedro --help`, and `kedro info` checks with telemetry opt-out and a read-only current-directory Kedro project probe.

## Fast Patterns

- Prefer telemetry-safe probes in automated workflows: `KEDRO_DISABLE_TELEMETRY=1 kedro --version`, `KEDRO_DISABLE_TELEMETRY=1 kedro --help`, and `KEDRO_DISABLE_TELEMETRY=1 kedro info`.
- Create a non-interactive project with explicit choices: `KEDRO_DISABLE_TELEMETRY=1 kedro new --name="My Project" --tools=lint,test --example=n --telemetry=no`.
- Use starters only when Git/network access is acceptable, or use a local starter path; official aliases and remote VCS starters may invoke Cookiecutter/Git.
- Check project detection before project commands: Kedro looks for `pyproject.toml` containing `[tool.kedro]` in the current directory or a parent directory.
- For Python scripts outside a project command, call `bootstrap_project(project_root)` before `KedroSession.create(project_path=project_root)`.
- For installed package mode, call `configure_project(package_name, preserve_logging=True)` when repeated configuration must not remove runtime logging handlers.

## Safety Notes

- `kedro new` writes a new project directory; run it from the intended parent directory or pass an explicit `output_dir` through a config file.
- `--starter`, `--tools=pyspark`, or `--example=yes` may fetch templates through Git/Cookiecutter; warn users before networked or remote-template workflows.
- `kedro package` builds artifacts under `dist/` and requires packaging tools such as `build`; it also archives configuration while excluding `local/*.yml`.
- `kedro ipython` and `kedro jupyter` require optional interactive dependencies; missing modules are an install issue, not a project-detection issue.

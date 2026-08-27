# CLI Reference

This reference covers Kedro 1.4.0 command discovery and safe command construction for project creation, project-aware commands, notebooks, packaging, and diagnostics.

## Entry Points and Command Groups

Kedro exposes the console script `kedro = kedro.framework.cli:main`. You can also invoke the framework CLI with `python -m kedro` when the package is importable.

Kedro command availability depends on project detection:

- Global commands are available anywhere: `kedro --help`, `kedro --version` or `kedro -V`, `kedro info`, `kedro new`, and `kedro starter list`.
- Project commands are available only inside a Kedro project directory or one of its subdirectories: `catalog`, `ipython`, `jupyter`, `package`, `pipeline`, `registry`, `run`, and `server`.
- Kedro decides project mode by searching the current directory and parents for `pyproject.toml` containing a `[tool.kedro]` section.
- If a project command is run outside a project, the CLI reports that a Kedro project was not found and hints that it is looking for `pyproject.toml`.

Plugin and project command precedence matters: a plugin command can override a built-in command, and a project-level `<package_name>.cli` can override plugin and built-in project commands. Route custom CLI/plugin work to `../hooks-and-extensions/SKILL.md`.

## Telemetry-Safe Probes

Kedro includes telemetry support through the `kedro-telemetry` dependency. Automated agents should avoid interactive prompts or analytics surprises by setting one of these environment variables for probes:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro --version
KEDRO_DISABLE_TELEMETRY=1 kedro --help
KEDRO_DISABLE_TELEMETRY=1 kedro info
```

`DO_NOT_TRACK=1` also disables telemetry. A project-level `.telemetry` file with `consent: false` disables telemetry for that project, and `kedro new --telemetry=no` writes that file in the generated project. The `--telemetry` flag accepts `yes`, `no`, `y`, or `n` case-insensitively. If the flag is omitted, a first project command may prompt for consent.

Run `scripts/kedro_cli_probe.py` for a bundled read-only helper that sets telemetry opt-out by default, checks `kedro --version`, `kedro --help`, optionally runs `kedro info`, and inspects whether the current directory looks like a Kedro project.

## Global Commands

### `kedro --version` and `kedro -V`

Use these to verify the installed framework version. For this generated skill, the verified target is Kedro `1.4.0`.

### `kedro --help`

Use this to list commands visible in the current working directory. If project commands are missing, first check that the current directory is inside a project.

### `kedro info`

`kedro info` prints the Kedro banner, a short framework description, and installed plugin versions grouped by entry point type. It is safe as a read-only probe, but use a telemetry opt-out environment variable in non-interactive automation.

### `kedro starter list`

`kedro starter list` prints official and plugin-provided starter aliases. Official aliases in this version include:

- `astro-airflow-iris`
- `spaceflights-pandas`
- `spaceflights-pyspark`
- `databricks-iris`
- `support-agent-langgraph`

Starter aliases resolve to starter metadata; remote official starters use the Kedro starters repository and may require Git/network access during project creation.

## `kedro new`

`kedro new` creates a project from the default template, an official starter alias, a local starter path, or a remote VCS starter supported by Cookiecutter.

Common non-interactive forms:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro new --name="My Project" --tools=none --example=n --telemetry=no
KEDRO_DISABLE_TELEMETRY=1 kedro new --name=spaceflights --tools=test --example=y --telemetry=no
KEDRO_DISABLE_TELEMETRY=1 kedro new --config=project.yml --telemetry=no
KEDRO_DISABLE_TELEMETRY=1 kedro new --starter=spaceflights-pandas --name=spaceflights --telemetry=no
```

Important flags:

- `--name` or `-n`: human-readable project name. It must contain only alphanumeric characters, spaces, underscores, and hyphens, and be at least two characters long.
- `--tools` or `-t`: one of `none`, `all`, or a comma-separated subset of `lint`, `test`, `log`, `docs`, `data`, and `pyspark`.
- `--example` or `-e`: `y`, `yes`, `n`, or `no`; when enabled, Kedro uses a spaceflights starter. With PySpark selected it uses the PySpark starter; otherwise it uses the pandas starter.
- `--config` or `-c`: YAML configuration for non-interactive prompts. Without a custom starter, include `project_name`, `repo_name`, and `python_package`; `tools` and `example_pipeline` are optional and default to no tools/no example.
- `--starter` or `-s`: local starter path, remote VCS starter URL, or a known starter alias.
- `--checkout`: tag, branch, or commit for a starter repository. Without `--starter`, it only has an effect when `--tools=pyspark` or `--example=yes` triggers a starter.
- `--directory`: subdirectory inside a starter repository. It is valid for explicit local/remote starters, but not for official starter aliases.
- `--telemetry` or `-tc`: writes `.telemetry` in the generated project with `consent: true` or `consent: false`.

Validation and conflicts:

- `--starter` cannot be combined with `--tools` or `--example`; custom starters own their prompts.
- `--directory` cannot be used without `--starter`, and it cannot be combined with an official starter alias.
- `--tools=all` and `--tools=none` cannot be combined with other tool choices.
- `viz` is not a valid `--tools` value in this version; remove it from tool selection.
- A derived or configured package name that is a Python keyword or standard library module, such as `import`, `json`, or `email`, is rejected because it would make the generated project hard to import.
- Names that merely contain such words can be valid after transformation, such as `email-service` becoming `email_service`.

Side effects:

- `kedro new` writes a project directory in the current directory unless the template context sets another `output_dir`.
- Default template creation is local. Official starters, `--example=yes`, `--tools=pyspark`, and remote starter URLs can use Git/Cookiecutter and may make network calls.
- The generated project contains `pyproject.toml`, source package files, settings, pipeline registry, requirements, and optional directories depending on tool selection.

## Project Commands

Project commands require a detected project. They receive project metadata from `pyproject.toml` after `bootstrap_project()` runs.

### `kedro run`

This sub-skill only covers command placement and session handoff. For execution semantics, read `../runners-and-execution/SKILL.md`.

High-level options include:

- `--env` or `-e` for configuration environment.
- `--runner` or `-r` with `SequentialRunner`, `ThreadRunner`, `ParallelRunner`, or a dotted runner object.
- `--async` for asynchronous dataset load/save through runner support.
- `--tags` or `-t`, `--nodes` or `-n`, `--from-nodes`, `--to-nodes`, `--from-inputs`, `--to-outputs`, `--namespaces` or `-ns` for filtering.
- `--load-versions` or `-lv` for versioned datasets.
- `--pipelines` for comma-separated registered pipelines; `--pipeline` is deprecated and cannot be combined with `--pipelines`.
- `--config` or `-c` for YAML/JSON run arguments; command-line options override config-file options.
- `--conf-source` for alternate configuration source.
- `--params` for runtime parameters, using `key=value` or nested `group.key:value` syntax.
- `--only-missing-outputs` to run nodes whose persisted outputs are missing.

### `kedro package`

Builds a wheel into `dist/` and archives project configuration as `dist/conf-<package_name>.tar.gz`. The config archive excludes `local/*.yml`. It calls Python's build module, so install the project's packaging/build requirements first.

### `kedro ipython`

Starts IPython with the `kedro.ipython` extension loaded and project variables available: `catalog`, `context`, `pipelines`, and `session`. Use `--env` or `-e` to set `KEDRO_ENV` before launch. It requires `IPython`; if absent, Kedro reports that `IPython` is not installed and suggests installing project requirements.

### `kedro jupyter`

`kedro jupyter setup`, `kedro jupyter notebook`, and `kedro jupyter lab` create/use a project kernel named `kedro_<package_name>` with display name `Kedro (<package_name>)` and load `kedro.ipython`. They require optional packages such as `ipykernel`, `notebook`, or `jupyterlab` depending on the subcommand. These commands write a user-level Jupyter kernelspec and may open a browser/server.

### `kedro pipeline`

`kedro pipeline create <name>` and `kedro pipeline delete <name>` scaffold/delete modular pipeline artifacts. This sub-skill covers that the commands are project commands; route pipeline design and reusable-pipeline API guidance to `../pipelines-and-nodes/SKILL.md`.

### `kedro catalog`, `kedro registry`, and `kedro server`

These are project commands. Route catalog/config details to `../data-catalog-and-config/SKILL.md`; route inspection/server behavior and optional server dependencies to `../inspection-and-server/SKILL.md`.

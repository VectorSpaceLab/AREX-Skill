# CCDS CLI Reference

## Purpose

Read this when you need exact `ccds` command behavior, install guidance, template/version selection, noninteractive generation options, output-directory rules, or v1 fallback guidance.

## Install and command identity

Cookiecutter Data Science v2 is distributed as the `cookiecutter-data-science` Python package. It installs a console script named `ccds` and imports as the Python module `ccds`.

Recommended install:

```bash
pipx install cookiecutter-data-science
```

Alternative when pipx is unavailable or the package belongs inside an existing tool environment:

```bash
python -m pip install cookiecutter-data-science
```

Runtime requirements and dependencies verified for v2.3.0:

- Python `>=3.9`.
- Runtime dependencies: `click`, `cookiecutter`, `tomlkit`.
- Console entry point: `ccds = ccds.__main__:main`.

Safe checks:

```bash
ccds --help
ccds --version
```

`ccds --version` reports the underlying Cookiecutter version because the command delegates to Cookiecutter's CLI.

## What CCDS changes relative to plain Cookiecutter

CCDS uses Cookiecutter's CLI and API but applies package-level monkey patches before command execution:

- The default `TEMPLATE` argument becomes the public CCDS template repository.
- The default `--checkout` becomes `v<installed ccds package version>`, for example `v2.3.0` when CCDS 2.3.0 is installed.
- Cookiecutter context loading is redirected from `cookiecutter.json` to `ccds.json` for v2.
- Prompt behavior supports nested choices such as cloud-storage subfields.

Use `ccds`, not plain `cookiecutter`, for CCDS v2 generation unless you are intentionally using the deprecated v1 template.

## Core invocation forms

### Interactive generation

```bash
# From the parent directory where the project folder should be created
ccds
```

The CLI prompts for project name, repository/module names, environment manager, dependency file, pydata packages, tests, linting, license, docs, scaffold, and cloud storage choices.

### Generate into a specific parent directory

```bash
ccds -o /path/to/parent
```

`--output-dir` is the parent directory. Cookiecutter creates the project folder below it using the rendered `repo_name`.

### Pin the template branch, tag, or commit

```bash
ccds -c master
ccds -c v2.3.0
ccds -c <commit-sha>
```

Use this for unreleased changes, historical tags, or exact commit recovery. When omitted, CCDS uses the checkout that matches the installed package version.

### Noninteractive generation

Cookiecutter accepts extra context as positional `KEY=VALUE` arguments with `--no-input`:

```bash
ccds --no-input \
  project_name="Demo Analysis" \
  repo_name="demo_analysis" \
  module_name="demo_analysis" \
  author_name="Data Team" \
  description="Demo project"
```

For nested values such as `dataset_storage`, prefer a JSON config file and the bundled bake helper rather than hand-quoting complex dictionaries in a shell. Noninteractive mode uses defaults for omitted values; for list choices, the first option is selected unless overridden.

### Config and replay controls

Useful Cookiecutter flags inherited by `ccds`:

| Flag | Use |
| --- | --- |
| `--config-file PATH` | Load a Cookiecutter user config file. |
| `--default-config` | Ignore user config and use defaults. |
| `--replay` | Reuse previously entered answers. Do not combine with `--no-input` or extra context. |
| `--replay-file PATH` | Use a specific replay file instead of the default. |
| `-f`, `--overwrite-if-exists` | Overwrite an existing generated project directory. Use cautiously. |
| `-s`, `--skip-if-file-exists` | Skip files that already exist in corresponding directories. |
| `--accept-hooks yes|ask|no` | Control execution of Cookiecutter hooks. CCDS normally needs hooks enabled. |
| `--keep-project-on-failure` | Preserve partial output for debugging if generation fails. |
| `-v`, `--verbose` and `--debug-file PATH` | Capture more debug information. |
| `--directory TEXT` | Use a subdirectory within a template repo when working with advanced multi-template repos. |

## v1 template guidance

CCDS v2 changed from the original v1 template and requires the `cookiecutter-data-science` package for v2 behavior. Use v1 only when the user explicitly needs the deprecated v1 layout:

```bash
ccds https://github.com/drivendataorg/cookiecutter-data-science -c v1
# or, if using plain Cookiecutter for the old template:
cookiecutter https://github.com/drivendataorg/cookiecutter-data-science -c v1
```

Do not mix v1 layout expectations with v2 option/hook behavior.

## Safety notes

- Generate in a parent directory or temporary directory first; do not run inside a directory that already contains unrelated work unless `repo_name` is intentionally isolated.
- Do not use `--overwrite-if-exists` on a project with uncommitted or valuable work unless the user explicitly wants overwrite behavior.
- Do not disable hooks for normal generation. Without hooks, dependency files, docs/tests pruning, license removal, scaffold pruning, and Python version metadata may be wrong.
- Do not run generated cloud sync or environment-manager commands immediately after baking unless credentials, network, and tool availability are intentionally confirmed.

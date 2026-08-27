# Helper API and Runtime Facts Reference

## Package facts

Verified for CCDS v2.3.0:

- Distribution name: `cookiecutter-data-science`.
- Import package: `ccds`.
- Console script: `ccds = ccds.__main__:main`.
- Python requirement: `>=3.9`.
- Runtime dependencies: `click`, `cookiecutter`, `tomlkit`.

The `ccds` CLI delegates to Cookiecutter's Click command. `ccds --help` exposes Cookiecutter options such as `--no-input`, `-c/--checkout`, `--directory`, `--replay`, `--replay-file`, `-f/--overwrite-if-exists`, `-s/--skip-if-file-exists`, `-o/--output-dir`, `--config-file`, `--default-config`, `--debug-file`, `--accept-hooks`, `--list-installed`, and `--keep-project-on-failure`.

## `ccds.__main__.default_ccds_main(f)`

Signature:

```python
def default_ccds_main(f)
```

Purpose:

- Wraps Cookiecutter's CLI function.
- Sets the template argument default to the public CCDS template repository.
- Sets the checkout option default to `v<ccds.__version__>`.

Use this fact to explain why a released CCDS package defaults to its matching template tag.

## `ccds.monkey_patch.prompt_for_config(context, no_input=False)`

Signature:

```python
def prompt_for_config(context, no_input=False)
```

Purpose:

- Replacement for Cookiecutter prompt handling.
- Supports nested choices whose list entries are dictionaries.
- Renders variables with the Cookiecutter/Jinja context.
- In `no_input` mode, selects default values without prompting.

Important behavior:

- It first handles simple variables and choices.
- It handles dictionary variables in a second pass.
- Undefined Jinja variables are wrapped as `UndefinedVariableInTemplate`.
- For nested choices, `_prompt_choice_and_subitems` selects the top-level choice first, then prompts or defaults any subfields.

## `ccds.monkey_patch.generate_context_wrapper(*args, **kwargs)`

Signature:

```python
def generate_context_wrapper(*args, **kwargs)
```

Purpose:

- Cookiecutter hardcodes `cookiecutter.json`; this wrapper swaps the context file name to `ccds.json`.
- After parsing, it renames the top-level key from `ccds` to `cookiecutter` so downstream Cookiecutter internals can render the template normally.

Use this to debug cases where plain Cookiecutter uses the wrong context schema.

## `ccds.hook_utils.dependencies.resolve_python_version_specifier(python_version)`

Signature:

```python
def resolve_python_version_specifier(python_version)
```

Behavior:

| Input | Output |
| --- | --- |
| `3.12` | `~=3.12.0` |
| `3.12.2` | `==3.12.2` |

A version with neither two nor three dot-separated components raises `ValueError` with guidance to use `<major>.<minor>` or `<major>.<minor>.<patch>`.

## `ccds.hook_utils.dependencies.write_python_version(python_version)`

Signature:

```python
def write_python_version(python_version)
```

Behavior:

- Opens the generated project's `pyproject.toml` in the current working directory.
- Parses it with `tomlkit`.
- Sets `[project].requires-python` to the resolved specifier from `resolve_python_version_specifier`.
- Writes the file back.

Because it mutates the current working directory's `pyproject.toml`, use it only in a generated-project hook context or disposable test.

## `ccds.hook_utils.dependencies._generate_pixi_dependencies_config(...)`

Signature:

```python
def _generate_pixi_dependencies_config(
    packages,
    pip_only_packages,
    repo_name,
    module_name,
    python_version,
    description,
)
```

Returns a tuple:

1. `conda_dependencies`
2. `pypi_dependencies`
3. `project_config`

Important output rules:

- Pixi project config includes `name`, `description`, `version = 0.1.0`, `channels = ["conda-forge"]`, and platforms `linux-64`, `osx-64`, `osx-arm64`, `win-64`.
- Conda dependencies include `python = ~=<python_version>.0`.
- Packages listed in `pip_only_packages` are excluded from Conda dependencies and added under PyPI dependencies.
- The generated module is always added as editable PyPI dependency with `path = "."`.

## `ccds.hook_utils.dependencies.write_dependencies(...)`

Signature:

```python
def write_dependencies(
    dependencies,
    packages,
    pip_only_packages,
    repo_name,
    module_name,
    python_version,
    environment_manager=None,
    description=None,
)
```

Supported `dependencies` values:

| Value | Behavior |
| --- | --- |
| `requirements.txt` | Writes sorted packages plus `-e .`. |
| `pyproject.toml` | Adds `[project].dependencies`; if `environment_manager=pixi`, writes `tool.pixi` sections; if `environment_manager=poetry`, switches build system to Poetry core. |
| `environment.yml` | Writes Conda YAML with `conda-forge`, Python version, Conda dependencies, pip subsection for pip-only packages, and `-e .`. |
| `Pipfile` | Writes `[packages]` entries plus editable local module and `[requires] python_version`. |
| `pixi.toml` | Writes Pixi `[project]`, `[dependencies]`, and optional `[pypi-dependencies]`. |

Use the options reference to validate the selected manager/file pair before relying on this writer.

## `ccds.hook_utils.custom_config.write_custom_config(user_input_config)`

Signature:

```python
def write_custom_config(user_input_config)
```

Behavior:

- If no config value is provided, returns without changes.
- If the value is a relative path, checks it relative to the parent of the generated project.
- If it points to a local directory, copies that directory tree into the current generated project.
- If it points to a local zip or HTTP(S) zip URL, extracts it and copies content into the project.
- Otherwise, treats the value as a VCS URI and asks Cookiecutter's `clone` helper to clone it.

This helper mutates the generated project. Treat it as an overlay mechanism, not a read-only validation API.

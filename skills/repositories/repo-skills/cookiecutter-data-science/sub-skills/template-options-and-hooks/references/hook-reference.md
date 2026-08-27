# Prompt and Hook Behavior Reference

## Purpose

Read this to predict how CCDS v2.3.0 turns option answers into generated files. The generated project is not a raw copy of the template tree; pre-prompt, prompt, and post-generation code modify behavior.

## Pre-prompt hook

Before prompting, CCDS checks the installed package version when available. If an installed CCDS version is older than `2.0.1`, it warns that the version always applies the newest template and recommends upgrading for stable behavior.

If CCDS is not importable in the hook context, the warning check is skipped.

## CLI and prompt monkey patches

The `ccds` entry point imports Cookiecutter internals and then applies these runtime changes before invoking the Cookiecutter CLI:

- `jinja2.StrictUndefined` is patched to `jinja2.Undefined` so variables that do not yet exist can be tolerated during nested option rendering.
- `cookiecutter.prompt.prompt_for_config` is replaced by CCDS's custom `prompt_for_config` to support nested choices with subfields.
- `cookiecutter.generate.generate_context` is wrapped so `ccds.json` is used instead of `cookiecutter.json` for v2 context.
- The CLI default template becomes the public CCDS template repository.
- The CLI default checkout becomes `v<installed ccds version>`.

Prompt behavior:

1. Simple variables and choices are prompted in order.
2. For a list of dictionaries, CCDS treats it as a choice with optional nested subfields. Example: `dataset_storage` can select `s3`, then prompt for `bucket` and `aws_profile`.
3. In `no_input` mode, the first choice is selected for list options unless extra context overrides it.
4. Dictionary-valued prompt items are handled in a second pass after simple values are available.

## Post-generation hook order

The post-generation hook runs inside the newly generated project and mutates files based on rendered option values.

### 1. Start package list

Base packages:

- `pip`
- `python-dotenv`

Then option-dependent additions:

- `dataset_storage=s3` adds `awscli`.
- `include_code_scaffold=Yes` adds `typer`, `loguru`, `tqdm`.
- `pydata_packages=basic` adds common PyData packages.
- `linting_and_formatting=ruff` adds `ruff` and removes `setup.cfg`.
- `linting_and_formatting=flake8+black+isort` adds `black`, `flake8`, `isort`.
- `testing_framework=pytest` adds `pytest`.
- `docs=mkdocs` adds `mkdocs` and treats it as pip-only.

### 2. Track pip-only packages

Pip-only packages include:

- `awscli`
- `python-dotenv`
- the selected docs package when docs are enabled, such as `mkdocs`

These are placed under pip sections for Conda/Pixi-oriented files.

### 3. Tests selection and pruning

If `testing_framework=none`:

- The `tests/` directory is removed.

Otherwise:

- The selected subdirectory under `tests/` (`pytest` or `unittest`) is moved up into `tests/`.
- Remaining test-template directories are removed.
- The starter test intentionally fails until replaced with project-specific assertions.

### 4. Docs selection and pruning

If `docs != none`:

- The selected docs template subdirectory, currently `mkdocs`, is moved into `docs/`.
- The docs dependency is added.

Then remaining docs template subdirectories are removed. If docs are disabled, only placeholder docs content remains.

### 5. Dependency file writing

`write_dependencies(...)` writes the selected dependency file:

- `requirements.txt`: sorted package names plus `-e .`.
- `pyproject.toml`: `[project].dependencies`; if Pixi, writes `tool.pixi` sections; if Poetry, switches build backend to Poetry core.
- `environment.yml`: Conda YAML with `conda-forge`, Python version, Conda dependencies, and pip subsection for pip-only packages plus `-e .`.
- `Pipfile`: `[packages]` plus editable local package and `[requires]` Python version.
- `pixi.toml`: Pixi `[project]`, `[dependencies]`, and `[pypi-dependencies]` with editable local module.

### 6. Python version metadata

`write_python_version(...)` updates `pyproject.toml`:

- `3.12` becomes `~=3.12.0`.
- `3.12.2` becomes `==3.12.2`.
- Other formats raise a `ValueError`.

### 7. Custom config overlay

`write_custom_config(...)` copies user-supplied overlay content into the project if a value is provided. It may come from:

- local directory;
- local zip file;
- HTTP(S) zip URL;
- VCS URI cloned through Cookiecutter.

The overlay can overwrite generated files. It is powerful and should be inspected before use.

### 8. License cleanup

If `open_source_license=No license file`, the generated `LICENSE` file is removed.

### 9. Pyproject quote cleanup

Jinja `tojson` escapes single quotes as `\u0027`; the hook rewrites those escape sequences to literal single quotes in `pyproject.toml` for readability.

### 10. Code scaffold cleanup

If `include_code_scaffold=No`:

- Every file and subdirectory inside the generated package is removed except `__init__.py`.
- `__init__.py` is emptied.
- Scaffold-only modules and the `modeling/` package disappear.

## Predicting generated output safely

When a generated project surprises a user:

1. Identify the selected options.
2. Validate environment-manager/dependency-file compatibility.
3. Apply the post-generation hook order above.
4. Check whether a custom config overlay replaced expected files.
5. Route to `../generated-project-workflows/` to validate the actual tree and Makefile commands.

Do not run the original hook manually against a valuable project. Hooks are mutating scripts intended for disposable generation contexts.

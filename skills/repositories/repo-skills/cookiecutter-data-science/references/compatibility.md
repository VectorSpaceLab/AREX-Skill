# Compatibility and Verification Baseline

## Package compatibility

Cookiecutter Data Science (CCDS) v2.3.0 is a Python package with:

- distribution name `cookiecutter-data-science`;
- import name `ccds`;
- console script `ccds`;
- Python requirement `>=3.9`;
- runtime dependencies `click`, `cookiecutter`, and `tomlkit`.

Public installation choices:

```bash
pipx install cookiecutter-data-science
python -m pip install cookiecutter-data-science
```

Use `pipx` when the user wants a standalone CLI tool and `pip` when the package belongs in a controlled Python environment.

## Supported generated-project Python versions

The source package declares support for Python 3.9, 3.10, 3.11, 3.12, and 3.13. Generated projects ask for `python_version_number`; the dependency writer converts:

- `3.12` to `~=3.12.0`;
- `3.12.2` to `==3.12.2`.

Use a two-part or three-part version only.

## Generated-project manager support

CCDS v2.3.0 supports these environment managers in generated projects:

- `virtualenv`
- `conda`
- `pipenv`
- `uv`
- `pixi`
- `poetry`
- `none`

Manager commands are generated into the project Makefile, but the corresponding manager CLIs are not installed automatically. Missing `conda`, `mkvirtualenv`, `pipenv`, `uv`, `pixi`, or `poetry` is an expected local setup problem, not necessarily a CCDS generation bug.

## Backend and hardware requirements

There are no CUDA, ROCm, MPS, TPU, or vendor-accelerator requirements for CCDS package inspection or normal project generation. The relevant required backend is CPU/Python.

Cloud sync commands in generated projects can require external provider CLIs and credentials:

- S3: `aws` CLI and AWS credentials/profile.
- Azure Blob Storage: `az` CLI and Azure credentials.
- Google Cloud Storage: `gsutil` and Google Cloud credentials.

Treat cloud sync as an optional external side-effect workflow. Do not run it as a generic validation step.

## Native verification baseline used for this skill

The skill was prepared against CCDS v2.3.0 with these checks:

- distribution metadata for `cookiecutter-data-science==2.3.0`;
- isolated imports of `ccds`, `ccds.__main__`, `ccds.monkey_patch`, `ccds.hook_utils.dependencies`, and `ccds.hook_utils.custom_config`;
- `ccds --help` and `ccds --version`;
- helper smoke checks for Python version specifier behavior and dependency writer behavior;
- prompt/config smoke over `ccds.json` in no-input mode.

Final native verification should prefer a fast bake test and bundled helper checks before executing optional external-manager harnesses.

## When optional native checks are safe

Safe or usually safe:

- `ccds --help` and `ccds --version`.
- Import and helper function smokes.
- Generating a temporary project with `--no-input` and deleting it after validation.
- Read-only structural validation of a generated project.

Tool-dependent or potentially expensive:

- Full generated-project harnesses for Conda, virtualenvwrapper, Pipenv, uv, Pixi, or Poetry.
- `make requirements`, because it can resolve/download packages.
- `make create_environment`, because it creates local environments.

Credentialed or external side-effect:

- `make sync_data_up` and `make sync_data_down`.

Only run tool-dependent or credentialed cases when the user explicitly wants them and the environment has the required tools, network, credentials, and time.

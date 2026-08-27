# Generated Makefile Reference

A CCDS-generated project uses `Makefile` as a self-documenting task runner. The default goal is `help`, so `make` and `make help` print `Available rules:` followed by rule names and descriptions extracted from `##` comments.

Generated rules are option-dependent. Always inspect the project's actual `Makefile` or run `make` before assuming a rule exists.

## Core variables

Generated Makefiles define:

```make
PROJECT_NAME = <repo_name>
PYTHON_VERSION = <python_version_number>
PYTHON_INTERPRETER = python
```

Rules use these variables for environment names, Python version selection, and script execution.

## Common rules

### `help`

Behavior:

- Default target.
- Prints `Available rules:` and a table of documented rules.
- Safe and read-only.

Use when onboarding to any generated project or before invoking option-dependent commands.

### `requirements`

Present when a dependency file is generated. It installs project dependencies according to the selected dependency-file/environment-manager combination.

Common generated command forms:

| Dependency file / manager | `make requirements` behavior |
| --- | --- |
| `requirements.txt` with `uv` | `uv pip install -r requirements.txt` |
| `requirements.txt` with other managers | Upgrades pip with `python -m pip install -U pip`, then installs `-r requirements.txt`. |
| `pyproject.toml` with `uv` | `uv sync` |
| `pyproject.toml` with `pixi` | `pixi install` |
| `pyproject.toml` with `poetry` | `poetry install` |
| `pyproject.toml` with other managers | `pip install -e .` |
| `environment.yml` | `conda env update --name $(PROJECT_NAME) --file environment.yml --prune` |
| `Pipfile` | `pipenv install` |
| `pixi.toml` | `pixi install` |

Run this after creating/activating the environment when the manager expects activation, or through the manager when appropriate. See `environment-managers.md` for manager-specific activation details.

### `clean`

Always present. Behavior:

```bash
find . -type f -name "*.py[co]" -delete
find . -type d -name "__pycache__" -delete
```

It removes Python bytecode files and `__pycache__` directories. It does not remove data, environments, model outputs, notebooks, reports, or dependency lock files.

### `lint`

Present because CCDS offers a linting/formatting choice. Behavior depends on `linting_and_formatting`:

| Choice | `make lint` behavior |
| --- | --- |
| `ruff` | Runs `ruff format --check`, then `ruff check`. |
| `flake8+black+isort` | Runs `flake8 <module_name>`, `isort --check --diff <module_name>`, and `black --check <module_name>`. |

If using `pixi` or `poetry`, run linting through the environment (`pixi run make lint` or `poetry run make lint`) unless dependencies are otherwise active.

### `format`

Present with linting/formatting support. Behavior depends on `linting_and_formatting`:

| Choice | `make format` behavior |
| --- | --- |
| `ruff` | Runs `ruff check --fix`, then `ruff format`. |
| `flake8+black+isort` | Runs `isort <module_name>`, then `black <module_name>`. |

This rule mutates source files. Use it only when code formatting changes are intended.

### `test`

Present only when `testing_framework` is not `none`.

| Choice | `make test` behavior |
| --- | --- |
| `pytest` | Runs `python -m pytest tests`. |
| `unittest` | Runs `python -m unittest discover -s tests`. |
| `none` | Rule is omitted and `tests/` is removed. |

The generated starter test is intentionally failing. Replace it with meaningful project assertions before treating `make test` as a project-health signal.

### `create_environment`

Present only when `environment_manager` is not `none`. It creates or configures the selected environment. Generated commands:

| Manager | `make create_environment` behavior |
| --- | --- |
| `conda` with `environment.yml` | `conda env create --name $(PROJECT_NAME) -f environment.yml`, then prints `conda activate $(PROJECT_NAME)`. |
| `conda` without `environment.yml` | `conda create --name $(PROJECT_NAME) python=$(PYTHON_VERSION) -y`, then prints `conda activate $(PROJECT_NAME)`. |
| `virtualenv` | Uses `virtualenvwrapper.sh` when available and calls `mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER)`, otherwise attempts `mkvirtualenv.bat`; prints `workon $(PROJECT_NAME)`. |
| `pipenv` | Runs `pipenv --python $(PYTHON_VERSION)`, then prints `pipenv shell`. |
| `uv` | Runs `uv venv --python $(PYTHON_VERSION)`, then prints platform-specific activation commands for `.venv`. |
| `pixi` with `pixi.toml` | Prints that the Pixi environment will be created by `make requirements`; prints `pixi shell`. |
| `pixi` with `pyproject.toml` | Prints that Pixi is configured in `pyproject.toml` and `make requirements` installs dependencies; prints `pixi shell`. |
| `poetry` | Runs `poetry env use $(PYTHON_VERSION)`, then prints activation and `poetry run <command>` hints. |
| `none` | Rule is omitted. |

This rule can create or modify local environments. Do not run it in constrained or shared environments unless you intend to create the environment and have the manager CLI installed.

### `data`

Present only when `include_code_scaffold=Yes`.

Behavior:

```make
data: requirements
	$(PYTHON_INTERPRETER) <module_name>/dataset.py
```

It first invokes `requirements`, then runs the scaffold's `dataset.py`. The scaffold logic is placeholder code and does not produce real data until the project replaces it with a real data build step. If the scaffold is absent, this rule is omitted.

### `sync_data_down` and `sync_data_up`

Present only when `dataset_storage` is not `none`. These rules call provider CLIs and may transfer substantial data.

| Provider | Down command | Up command |
| --- | --- | --- |
| S3 | `aws s3 sync s3://<bucket>/data/ data/` plus `--profile <profile>` when the configured profile is not `default`. | `aws s3 sync data/ s3://<bucket>/data` plus optional profile. |
| Azure Blob Storage | `az storage blob download-batch -s <container>/data/ -d data/` | `az storage blob upload-batch -d <container>/data/ -s data/` |
| Google Cloud Storage | `gsutil -m rsync -r gs://<bucket>/data/ data/` | `gsutil -m rsync -r data/ gs://<bucket>/data/` |
| None | Rules are omitted. | Rules are omitted. |

Credential, account, bucket/container, and network failures are expected if the local machine is not configured for the selected provider. Treat these rules as external side-effect commands.

## Safe command order

For a new generated project, a typical local order is:

1. `make` to list available rules.
2. `make create_environment` if the manager is not `none` and the required CLI is installed.
3. Activate the environment or use the manager's `run` command.
4. `make requirements` to install dependencies.
5. Replace starter tests and placeholder scaffold logic.
6. `make lint` and `make test` once dependencies are available.
7. `make format` only when you intend to rewrite formatting.
8. `make sync_data_down` or `make sync_data_up` only with verified credentials and expected transfer scope.

## Editing the Makefile

The generated Makefile is ordinary Make. Add project-specific rules for reproducible DAG steps such as:

- downloading source data into `data/raw` or `data/external`;
- transforming raw data into `data/interim` and `data/processed`;
- training models into `models/`;
- generating figures into `reports/figures`;
- building or serving docs.

Prefer explicit input/output dependencies where practical. Avoid rules that overwrite `data/raw` or rely on hidden manual state. Keep commands compatible with the selected environment manager, especially when using Pixi or Poetry wrappers.

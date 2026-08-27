# Environment Managers and Dependency Files

CCDS separates two choices that interact closely:

- `environment_manager`: how the project creates or activates a Python environment.
- `dependency_file`: where generated dependencies are recorded.

Generated projects use Python package metadata in `pyproject.toml` and add an editable local package dependency so notebooks and scripts can import the generated module after installing requirements.

## Valid pairings

The CCDS test matrix rejects invalid manager/file combinations. Use these pairings when diagnosing an existing project or reconstructing selected options:

| Environment manager | Valid dependency files | Notes |
| --- | --- | --- |
| `conda` | `requirements.txt`, `pyproject.toml`, `environment.yml` | `environment.yml` is only valid with Conda. |
| `virtualenv` | `requirements.txt`, `pyproject.toml` | Uses virtualenvwrapper-style commands for environment creation. |
| `pipenv` | `Pipfile` only | `Pipfile` is only valid with Pipenv. |
| `uv` | `requirements.txt`, `pyproject.toml` | Uses `.venv` creation and `uv` install/sync commands. |
| `pixi` | `pixi.toml`, `pyproject.toml` | Pixi supports a dedicated `pixi.toml` or Pixi sections in `pyproject.toml`. |
| `poetry` | `pyproject.toml` only | Poetry uses `pyproject.toml` and a Poetry build backend. |
| `none` | `requirements.txt`, `pyproject.toml` | No `create_environment` rule; dependency installation is left to the user. |

Invalid combinations include:

- `environment.yml` with anything except `conda`.
- `Pipfile` with anything except `pipenv`.
- `pixi.toml` with anything except `pixi`.
- `pipenv` with anything except `Pipfile`.
- `poetry` with anything except `pyproject.toml`.
- `pixi` with `requirements.txt`, `environment.yml`, or `Pipfile`.

## Generated dependency contents

Base dependencies commonly include:

- `pip`
- `python-dotenv`

Additional dependencies depend on selected options:

| Option | Added packages |
| --- | --- |
| `dataset_storage=s3` | `awscli` |
| `include_code_scaffold=Yes` | `typer`, `loguru`, `tqdm` |
| `pydata_packages=basic` | `ipython`, `jupyterlab`, `matplotlib`, `notebook`, `numpy`, `pandas`, `scikit-learn` |
| `linting_and_formatting=ruff` | `ruff` |
| `linting_and_formatting=flake8+black+isort` | `black`, `flake8`, `isort` |
| `testing_framework=pytest` | `pytest` |
| `docs=mkdocs` | `mkdocs` |

Some packages are treated as pip-only when generating Conda/Pixi-style dependency files, notably `python-dotenv`, `awscli`, and `mkdocs` when selected.

Python version handling:

- A two-part version such as `3.10` becomes a compatible release specifier like `~=3.10.0` in `pyproject.toml`.
- A three-part version such as `3.10.1` becomes an exact specifier like `==3.10.1`.
- Conda/Pixi generated files encode Python separately in their manager-specific sections.

## Manager-specific behavior

### Conda

Generated `make create_environment` behavior:

- With `environment.yml`: `conda env create --name $(PROJECT_NAME) -f environment.yml`.
- Without `environment.yml`: `conda create --name $(PROJECT_NAME) python=$(PYTHON_VERSION) -y`.
- Prints activation guidance: `conda activate $(PROJECT_NAME)`.

Generated `make requirements` behavior:

- With `environment.yml`: `conda env update --name $(PROJECT_NAME) --file environment.yml --prune`.
- With `requirements.txt`: pip installs from requirements using the active Python.
- With `pyproject.toml`: `pip install -e .` in the active environment.

Operational notes:

- Activate the named environment before running Python, lint, test, and scaffold commands unless invoking through a wrapper.
- Conda is the intended choice when non-Python dependencies matter.

### Virtualenv

Generated `make create_environment` behavior:

- Uses `virtualenvwrapper.sh` if present and calls `mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER)`.
- Otherwise attempts a Windows `mkvirtualenv.bat` path.
- Prints activation guidance: `workon $(PROJECT_NAME)`.

Generated `make requirements` behavior:

- `requirements.txt`: upgrades pip and installs `-r requirements.txt`.
- `pyproject.toml`: `pip install -e .`.

Operational notes:

- The generated command assumes virtualenvwrapper commands are installed and available.
- If `mkvirtualenv` is missing, create a standard virtual environment manually or install/configure virtualenvwrapper.

### Pipenv

Valid only with `Pipfile`.

Generated `make create_environment` behavior:

- `pipenv --python $(PYTHON_VERSION)`.
- Prints activation guidance: `pipenv shell`.

Generated `make requirements` behavior:

- `pipenv install`.

Operational notes:

- Use `pipenv run make lint`, `pipenv run make format`, and `pipenv run make test` when not inside `pipenv shell`.
- The generated `Pipfile` includes the local module as editable with `path = "."`.

### uv

Valid with `requirements.txt` or `pyproject.toml`.

Generated `make create_environment` behavior:

- `uv venv --python $(PYTHON_VERSION)`.
- Prints activation guidance for `.venv`:
  - Windows: `.\\.venv\\Scripts\\activate`
  - Unix/macOS: `source ./.venv/bin/activate`

Generated `make requirements` behavior:

- With `requirements.txt`: `uv pip install -r requirements.txt`.
- With `pyproject.toml`: `uv sync`.

Operational notes:

- Activate `.venv` before plain `make lint` and `make test`, or use `uv run` where appropriate for project-specific commands.
- Missing `uv` produces command-not-found errors before any dependency installation occurs.

### Pixi

Valid with `pixi.toml` or `pyproject.toml` containing `tool.pixi` sections.

Generated `make create_environment` behavior:

- Does not create the environment directly.
- Prints that Pixi environment creation happens during `make requirements` and suggests `pixi shell`.

Generated `make requirements` behavior:

- `pixi install` for both `pixi.toml` and Pixi-configured `pyproject.toml`.

Generated Pixi config includes:

- project name, description, version, channels `conda-forge`, and platforms `linux-64`, `osx-64`, `osx-arm64`, `win-64`;
- Conda dependencies including `python ~=<version>.0`;
- PyPI dependencies for pip-only packages and the local module as editable.

Operational notes:

- Use `pixi run python`, `pixi run make lint`, and `pixi run make format` if not in `pixi shell`.
- Pixi must be installed as a system binary before these commands can work.

### Poetry

Valid only with `pyproject.toml`.

Generated `make create_environment` behavior:

- `poetry env use $(PYTHON_VERSION)`.
- Prints activation guidance and suggests `poetry run <command>`.

Generated `make requirements` behavior:

- `poetry install`.

Generated `pyproject.toml` behavior:

- Uses standard project dependencies.
- Switches build system to `poetry-core>=2.0.0,<3.0.0` with backend `poetry.core.masonry.api`.

Operational notes:

- Use `poetry run make lint`, `poetry run make format`, and `poetry run make test` when not inside the Poetry environment.
- Poetry must be installed as a system binary.

### none

Generated behavior:

- No `create_environment` rule.
- Dependency installation still depends on the selected dependency file when present.

Operational notes:

- The project intentionally leaves environment creation to the team.
- Validate imports using whichever environment the team provides.

## Dependency-file specifics

### `requirements.txt`

- Contains sorted packages plus `-e .` for editable local package installation.
- `make requirements` installs the file with pip or `uv pip` depending on manager.

### `pyproject.toml`

- Always exists for package metadata.
- May also hold dependency lists under `[project]`.
- With Ruff, contains `[tool.ruff]`, `[tool.ruff.lint]`, and `[tool.ruff.lint.isort]` configuration.
- With Black/isort, contains `[tool.black]` and `[tool.isort]` configuration.
- With Pixi, contains `[tool.pixi.project]`, `[tool.pixi.dependencies]`, and possibly `[tool.pixi.pypi-dependencies]`.
- With Poetry, build system changes to Poetry core.

### `environment.yml`

- Contains Conda environment `name: <repo_name>`, channel `conda-forge`, Python version, Conda-available packages, and a pip subsection for pip-only dependencies plus `-e .`.

### `Pipfile`

- Contains `[packages]` entries and an editable local module entry.
- Contains `[requires] python_version = "<version>"`.

### `pixi.toml`

- Contains `[project]`, `[dependencies]`, and optional `[pypi-dependencies]` sections.
- Includes the local module as editable PyPI dependency.

## Safe troubleshooting checks

1. Determine selected manager from available files and `Makefile` commands.
2. Verify the manager CLI exists before running `make create_environment` or `make requirements`.
3. Confirm `python --version` or manager-specific `run python --version` matches the project expectation.
4. Install dependencies before interpreting scaffold imports, lint, or test failures.
5. For Pixi and Poetry, prefer `pixi run ...` or `poetry run ...` when in doubt.
6. If the starter tests fail immediately, inspect whether they are still placeholders rather than assuming application code is broken.

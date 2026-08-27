# CCDS Options Reference

## Purpose

Read this for CCDS v2.3.0 option names, defaults, choices, nested subfields, valid manager/dependency pairings, and custom configuration semantics.

## Canonical options

| Option | Type | Default | Choices or meaning |
| --- | --- | --- | --- |
| `project_name` | string | `project_name` | Human-readable project name. |
| `repo_name` | string/template | derived from `project_name` | Project directory/repository folder name: lowercased project name with spaces replaced by underscores. |
| `module_name` | string/template | derived from `project_name` | Python import package name: lowercased project name with spaces and hyphens replaced by underscores. |
| `author_name` | string | `Your name (or your organization/company/team)` | Individual, organization, company, or team. |
| `description` | string | `A short description of the project.` | Short README/package description. |
| `python_version_number` | string | `3.10` | Python version used in generated environment/dependency metadata. Two-part versions become compatible release specifiers; three-part versions become exact specifiers in `pyproject.toml`. |
| `dataset_storage` | nested choice | `none` | `none`, `azure`, `s3`, `gcs`; cloud choices add provider-specific Makefile sync commands and some dependencies. |
| `environment_manager` | choice | `virtualenv` | `virtualenv`, `conda`, `pipenv`, `uv`, `pixi`, `poetry`, `none`. |
| `dependency_file` | choice | `requirements.txt` | `requirements.txt`, `pyproject.toml`, `environment.yml`, `Pipfile`, `pixi.toml`. Must be compatible with environment manager. |
| `pydata_packages` | choice | `none` | `none` or `basic`; `basic` adds common PyData packages. |
| `testing_framework` | choice | `none` | `none`, `pytest`, `unittest`. |
| `linting_and_formatting` | choice | `ruff` | `ruff` or `flake8+black+isort`. |
| `open_source_license` | choice | `No license file` | `No license file`, `MIT`, `BSD-3-Clause`. |
| `docs` | choice | `mkdocs` | `mkdocs` or `none`. |
| `include_code_scaffold` | choice | `Yes` | `Yes` or `No`. |
| `custom_config` | hook-consumed value | usually empty | Not a normal prompt field in the public schema table, but the post-generation hook reads it and overlays local/zip/URL/VCS content when provided. |

## Nested `dataset_storage` choices

| Choice | Subfields | Generated effect |
| --- | --- | --- |
| `none` | none | No cloud sync Makefile rules. |
| `azure` | `container` | Adds Azure Blob Storage sync commands using `az storage blob download-batch` and `az storage blob upload-batch`. |
| `s3` | `bucket`, `aws_profile` | Adds AWS S3 sync commands using `aws s3 sync`; adds `awscli` to generated dependencies. Non-default profile adds `--profile <profile>`. |
| `gcs` | `bucket` | Adds Google Cloud Storage sync commands using `gsutil -m rsync`. |

Cloud sync commands require external CLIs, credentials, network, and intentionally selected buckets/containers. Do not run them as validation unless the user authorizes those side effects.

## Valid environment-manager/dependency-file pairings

The native test matrix considers only these combinations valid:

| Environment manager | Valid dependency files |
| --- | --- |
| `conda` | `requirements.txt`, `pyproject.toml`, `environment.yml` |
| `virtualenv` | `requirements.txt`, `pyproject.toml` |
| `pipenv` | `Pipfile` only |
| `uv` | `requirements.txt`, `pyproject.toml` |
| `pixi` | `pixi.toml`, `pyproject.toml` |
| `poetry` | `pyproject.toml` only |
| `none` | `requirements.txt`, `pyproject.toml` |

Reject or correct these invalid pairs before generation:

- `environment.yml` with anything except `conda`.
- `Pipfile` with anything except `pipenv`.
- `pixi.toml` with anything except `pixi`.
- `pipenv` with anything except `Pipfile`.
- `poetry` with anything except `pyproject.toml`.
- `pixi` with `requirements.txt`, `environment.yml`, or `Pipfile`.

## Package groups added by options

Base dependency list starts with:

- `pip`
- `python-dotenv`

Additional package groups:

| Option | Added packages |
| --- | --- |
| `dataset_storage=s3` | `awscli` |
| `include_code_scaffold=Yes` | `typer`, `loguru`, `tqdm` |
| `pydata_packages=basic` | `ipython`, `jupyterlab`, `matplotlib`, `notebook`, `numpy`, `pandas`, `scikit-learn` |
| `linting_and_formatting=ruff` | `ruff` |
| `linting_and_formatting=flake8+black+isort` | `black`, `flake8`, `isort` |
| `testing_framework=pytest` | `pytest` |
| `docs=mkdocs` | `mkdocs` |

The helper code treats `awscli`, `python-dotenv`, and selected `mkdocs` as pip-only packages for Conda/Pixi-style dependency generation.

## Option-dependent generated files

| Choice | Result |
| --- | --- |
| `docs=mkdocs` | Starter MkDocs files appear under `docs/`, including `docs/mkdocs.yml`, `docs/README.md`, `docs/docs/index.md`, and `docs/docs/getting-started.md`. |
| `docs=none` | Template docs subdirectories are pruned; `docs/.gitkeep` remains. |
| `testing_framework=pytest` | `tests/test_data.py` is a pytest-style starter test that intentionally fails until replaced. |
| `testing_framework=unittest` | `tests/test_data.py` is a unittest-style starter test that intentionally fails until replaced. |
| `testing_framework=none` | The `tests/` directory is removed. |
| `linting_and_formatting=ruff` | Ruff config is written in `pyproject.toml`; `setup.cfg` is removed. |
| `linting_and_formatting=flake8+black+isort` | `setup.cfg` remains for flake8; Black/isort config is written in `pyproject.toml`. |
| `include_code_scaffold=Yes` | The package contains `config.py`, `dataset.py`, `features.py`, `modeling/train.py`, `modeling/predict.py`, and `plots.py`; Makefile includes `data`. |
| `include_code_scaffold=No` | Everything inside the package except `__init__.py` is removed and `__init__.py` is emptied; Makefile omits `data`. |
| `open_source_license=No license file` | `LICENSE` is removed and no license file field is kept. |
| `open_source_license=MIT` or `BSD-3-Clause` | `LICENSE` remains and package metadata includes a corresponding classifier. |

## Custom config overlay

The custom configuration helper accepts:

- a local directory path;
- a local `.zip` file;
- an HTTP(S) URL ending in `.zip`;
- otherwise, a VCS URI that Cookiecutter can clone.

It copies the overlay content into the generated project. Treat this as an override layer that can replace generated files. Inspect overlays before use, especially for `.env`, credentials, data, local environments, dependency files, Makefiles, and package modules.

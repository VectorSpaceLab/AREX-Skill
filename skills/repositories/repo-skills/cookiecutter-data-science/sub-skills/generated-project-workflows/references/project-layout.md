# Generated Project Layout

Cookiecutter Data Science (CCDS) 2.3.0 generates a standardized but option-dependent data science project. Treat the layout as a starting contract for reproducibility, collaboration, and code review, not as a rigid framework.

## Core paths normally present

A generated project root normally contains these core paths:

| Path | Purpose |
| --- | --- |
| `Makefile` | Self-documenting task runner for environment setup, dependency installation, cleaning, linting, formatting, tests, data generation, and optional cloud sync. Run `make` or `make help` to list available rules. |
| `README.md` | Top-level project overview and generated organization summary for collaborators. |
| `pyproject.toml` | Python project metadata for the generated package plus tool configuration. It always exists, even when dependencies are stored in another file. |
| `.gitignore` | Defaults to ignoring `data/`, `.env`, local environments, caches, build artifacts, docs build output, notebook checkpoints, and tool caches. |
| `.env` | Template for local secrets and configuration loaded by scaffold code through `python-dotenv`; it is ignored by git and should not be committed. |
| `data/raw/` | Original immutable data dump. Do not edit raw data manually or overwrite it with cleaned versions. |
| `data/external/` | Data from third-party sources that is not the project's original raw dump. |
| `data/interim/` | Intermediate transformed data; useful for caching long-running steps in a reproducible pipeline. |
| `data/processed/` | Final canonical data sets for modeling or reporting. |
| `docs/` | Documentation area. With `docs=mkdocs`, it contains MkDocs configuration and starter docs; with `docs=none`, it remains a placeholder directory with `.gitkeep`. |
| `models/` | Trained models, serialized artifacts, predictions, summaries, and experiment outputs. |
| `notebooks/` | Exploration and communication notebooks. The recommended naming convention is a numbered prefix, creator initials or handle, and a short hyphen-delimited description, for example `1.0-jqp-initial-data-exploration.ipynb`. |
| `references/` | Data dictionaries, manuals, schema notes, explanatory material, and other non-generated references. |
| `reports/` | Generated analysis artifacts such as HTML, PDF, LaTeX, and other report outputs. |
| `reports/figures/` | Generated figures and graphics for reports and communication. |
| `<module_name>/` | Importable project package for reusable source code. The directory name is the CCDS `module_name` option. |

The generated data, model, notebook, references, reports, and many placeholder folders may contain `.gitkeep` files so empty directories survive initial source control commits.

## Option-dependent paths

Do not assume every generated CCDS project has exactly the same files. Check the actual tree before modifying it.

| Option | Generated result |
| --- | --- |
| `open_source_license=MIT` or `BSD-3-Clause` | Adds `LICENSE` and a license field/classifier in `pyproject.toml`. |
| `open_source_license=No license file` | Removes `LICENSE`. |
| `dependency_file=requirements.txt` | Adds `requirements.txt`. |
| `dependency_file=pyproject.toml` | Stores dependencies in `pyproject.toml`; for Poetry the build backend switches to `poetry.core.masonry.api`; for Pixi the file contains `tool.pixi` sections. |
| `dependency_file=environment.yml` | Adds Conda `environment.yml`. Valid only with `environment_manager=conda`. |
| `dependency_file=Pipfile` | Adds `Pipfile`. Valid only with `environment_manager=pipenv`. |
| `dependency_file=pixi.toml` | Adds `pixi.toml`. Valid only with `environment_manager=pixi`. |
| `docs=mkdocs` | Moves starter docs into `docs/`: expected starter files include `docs/mkdocs.yml`, `docs/README.md`, `docs/docs/index.md`, and `docs/docs/getting-started.md`. |
| `docs=none` | Leaves `docs/.gitkeep` and no MkDocs starter files. |
| `testing_framework=pytest` | Adds `tests/test_data.py` using pytest style. The starter test intentionally fails until replaced with a real assertion. |
| `testing_framework=unittest` | Adds `tests/test_data.py` using `unittest` style. The starter test intentionally fails until replaced with a real assertion. |
| `testing_framework=none` | Removes the `tests/` directory. |
| `linting_and_formatting=ruff` | Adds Ruff configuration to `pyproject.toml` and removes `setup.cfg`. |
| `linting_and_formatting=flake8+black+isort` | Keeps `setup.cfg` for flake8 and writes Black/isort configuration in `pyproject.toml`. |
| `include_code_scaffold=Yes` | Adds scaffold modules such as `config.py`, `dataset.py`, `features.py`, `modeling/train.py`, `modeling/predict.py`, and `plots.py`. |
| `include_code_scaffold=No` | Leaves only an empty `<module_name>/__init__.py` in the package directory. |
| `dataset_storage=s3`, `azure`, or `gcs` | Adds `sync_data_down` and `sync_data_up` Makefile rules for the selected cloud provider. |
| `dataset_storage=none` | Omits cloud sync Makefile rules. |

## Project opinions to preserve

- **Data analysis is a DAG.** The project should let collaborators trace outputs back to code and inputs, and rerun steps to recreate final products.
- **Raw data is immutable.** Code may read or copy from `data/raw/`, but should not edit raw files in place or overwrite them with processed versions.
- **Data mostly stays out of source control.** The default `.gitignore` ignores `/data/`. Small, stable data may be committed only when the team intentionally changes the default policy; larger data usually belongs in external storage.
- **Notebooks are for exploration and communication.** Use notebooks to iterate and explain results; move reusable functions, data transformations, model code, and plotting helpers into `<module_name>/` so they can be tested and reused.
- **Secrets and local config belong in `.env`.** Do not commit credentials, tokens, database URLs, cloud keys, or machine-specific paths. Scaffold code loads `.env` through `python-dotenv` when present.
- **Make is the task runner.** Generated workflows expose reproducible commands through `make`; project-specific commands can be added without treating the Makefile as magic.
- **The default structure is adaptable.** You may delete, flatten, or extend folders when the project needs it, but preserve internal consistency and document changes for collaborators.

## Practical first checks inside a generated project

1. List top-level files and identify the module directory: look for the directory containing `__init__.py` that is not `tests/` or `docs/`.
2. Check which dependency file exists: `requirements.txt`, `environment.yml`, `Pipfile`, `pixi.toml`, or dependency sections in `pyproject.toml`.
3. Run `make` or inspect `Makefile` to see available rules. Some rules are omitted by selected options.
4. Inspect `pyproject.toml` to determine package name, Python version specifier, dependencies, and tool configuration.
5. If scaffold code exists, check imports in `<module_name>/config.py` and executable Typer scripts before editing pipeline modules.
6. Before committing, ensure `.env`, local environments, large data files, and generated caches remain ignored unless the project intentionally changed that policy.

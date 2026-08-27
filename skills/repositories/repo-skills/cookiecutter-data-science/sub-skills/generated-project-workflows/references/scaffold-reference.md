# Generated Code Scaffold Reference

The generated package directory is named by the CCDS `module_name` option. It is intended to be an importable local package after dependency installation. Notebook exploration can import reusable code from this package instead of copy/pasting logic across notebooks.

## `include_code_scaffold=Yes`

When code scaffold is included, the package contains:

```text
<module_name>/
├── __init__.py
├── config.py
├── dataset.py
├── features.py
├── modeling/
│   ├── __init__.py
│   ├── predict.py
│   └── train.py
└── plots.py
```

These files are starter scaffolds. They import `typer`, `loguru`, and `tqdm`, so those packages are added to generated dependencies when scaffold is enabled.

### `config.py`

Purpose:

- Loads environment variables from `.env` through `python-dotenv` if the file exists.
- Defines project-root-relative path constants.
- Configures Loguru to cooperate with `tqdm` when `tqdm` is installed.

Generated path constants:

```python
PROJ_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
MODELS_DIR = PROJ_ROOT / "models"
REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
```

Operational guidance:

- Use these constants rather than hard-coded absolute paths.
- Store secrets, tokens, database URLs, and local configuration in `.env`; do not commit `.env`.
- If `from <module_name> import config` fails, first confirm the package was installed/editable or that you are running from the project root with dependencies installed.

### `dataset.py`

Purpose:

- Typer command-line app for downloading or generating data.
- Imports `PROCESSED_DATA_DIR` and `RAW_DATA_DIR` from `config.py`.
- Default placeholder arguments read from `data/raw/dataset.csv` and write to `data/processed/dataset.csv`.
- Logs progress through Loguru and loops with `tqdm` as placeholder logic.

Generated execution pattern:

```bash
python <module_name>/dataset.py
```

The `make data` rule, when present, runs this script after `make requirements`.

Operational guidance:

- Replace placeholder code with real data acquisition/transformation logic.
- Do not overwrite raw input files; write cleaned or transformed outputs to `data/interim` or `data/processed`.
- Keep parameters explicit so DAG steps can be rerun and reviewed.

### `features.py`

Purpose:

- Typer app for feature generation.
- Imports `PROCESSED_DATA_DIR`.
- Default placeholder input is `data/processed/dataset.csv` and output is `data/processed/features.csv`.
- Uses Loguru and `tqdm` placeholder progress logging.

Operational guidance:

- Convert stable feature-engineering logic from notebooks into functions or command code here.
- Keep model-training-specific logic in `modeling/train.py` and shared transformations in reusable functions.

### `modeling/train.py`

Purpose:

- Typer app for model training.
- Imports `MODELS_DIR` and `PROCESSED_DATA_DIR`.
- Default placeholder paths are `data/processed/features.csv`, `data/processed/labels.csv`, and `models/model.pkl`.
- Uses Loguru and `tqdm` placeholder progress logging.

Operational guidance:

- Serialize model artifacts under `models/`.
- Record enough experiment metadata to connect artifacts to data provenance and code version.
- Avoid training from mutable notebook-only state; make file inputs and outputs explicit.

### `modeling/predict.py`

Purpose:

- Typer app for model inference.
- Imports `MODELS_DIR` and `PROCESSED_DATA_DIR`.
- Default placeholder paths are `data/processed/test_features.csv`, `models/model.pkl`, and `data/processed/test_predictions.csv`.
- Uses Loguru and `tqdm` placeholder progress logging.

Operational guidance:

- Load trained artifacts from `models/` and write predictions to a documented output path.
- Keep feature schema expectations close to the prediction code or in `references/`.

### `plots.py`

Purpose:

- Typer app for visualization generation.
- Imports `FIGURES_DIR` and `PROCESSED_DATA_DIR`.
- Default placeholder paths are `data/processed/dataset.csv` and `reports/figures/plot.png`.
- Uses Loguru and `tqdm` placeholder progress logging.

Operational guidance:

- Write generated figures to `reports/figures/`.
- Keep exploratory plots in notebooks until they become reproducible report artifacts.

## `include_code_scaffold=No`

When code scaffold is disabled:

- The generated package directory remains present.
- Only an empty `<module_name>/__init__.py` remains.
- `config.py`, `dataset.py`, `features.py`, `modeling/`, and `plots.py` are removed.
- The `make data` rule is omitted.
- Scaffold-only dependencies (`typer`, `loguru`, `tqdm`) are not added unless another project choice adds them separately.

Use this mode when the team wants package structure without starter scripts. Add modules deliberately as the project evolves.

## Refactoring notebook code into modules

A CCDS project makes the generated module importable so reusable notebook logic can move into package files. A typical workflow:

1. Explore in `notebooks/` with clear notebook names such as `<phase>.<notebook>-<owner>-<description>.ipynb`.
2. Identify duplicated or stable transformations, metrics, plotting helpers, and I/O code.
3. Move reusable code into `<module_name>/` modules.
4. Add or update tests under `tests/` when a testing framework exists.
5. Import package code from notebooks. If notebooks cache stale code, use autoreload:

```python
%load_ext autoreload
%autoreload 2

import <module_name>
```

Replace `<module_name>` with the actual generated package directory name.

## Linting impact on scaffold edits

Generated lint/format commands focus on the module directory:

- Ruff configuration includes `pyproject.toml` and `<module_name>/**/*.py`, selects import sorting, and uses line length 99.
- Flake8+Black+isort uses `setup.cfg` for flake8 and `pyproject.toml` for Black/isort; the generated flake8 exclusion skips `.git`, `notebooks`, `references`, `models`, and `data`.

Before large scaffold rewrites, install dependencies and run the appropriate lint/format commands in the selected environment.

## Common scaffold import patterns

- From another module: `from <module_name>.config import PROCESSED_DATA_DIR`.
- From a notebook: `from <module_name> import config` or `from <module_name>.features import main` after installing the project editable.
- From Makefile: `python <module_name>/dataset.py` for data generation when scaffold is enabled.

If imports fail:

1. Confirm you are in the generated project root or have installed the package editable.
2. Run the manager-specific dependency installation (`make requirements`, `pixi install`, `poetry install`, etc.).
3. Verify the module directory name matches the import name exactly.
4. Confirm scaffold dependencies exist when scaffold files import `typer`, `loguru`, `tqdm`, and `python-dotenv`.
5. Avoid running scaffold files from a different working directory if relying on implicit project-root behavior; prefer installed package imports.

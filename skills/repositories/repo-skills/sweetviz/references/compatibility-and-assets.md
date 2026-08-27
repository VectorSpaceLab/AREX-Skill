# Sweetviz compatibility and package assets

## When to read

Read this when choosing an install plan, diagnosing package-data failures, or deciding whether Sweetviz has a CLI, optional backend, or asset requirement for a task.

## Package shape

- Distribution name: `sweetviz`
- Import name: `sweetviz`
- Verified version for this skill: `2.3.3`
- Primary runtime interface: Python API, not a command-line executable.
- Public objects exposed from `import sweetviz as sv`: `analyze`, `compare`, `compare_intra`, `FeatureConfig`, `DataframeReport`, and `config_parser`.

Sweetviz is a pandas-based exploratory data analysis library. It builds a `DataframeReport` from one or two pandas DataFrames and renders a self-contained HTML report.

## Dependencies

Base package dependencies are enough for the selected skill workflows:

- `pandas`
- `numpy`
- `matplotlib`
- `scipy`
- `jinja2`
- `tqdm`
- `importlib_resources`
- `importlib_metadata` only on Python versions before 3.8

Optional development and documentation extras are not needed to use the runtime API. Optional Comet.ml upload support is not a declared package extra in this checkout; it depends on an externally installed/configured `comet_ml` package and account/API-key setup.

## Python and data expectations

Package metadata declares Python `>=3.7`, but current pandas/numpy/matplotlib wheels may impose stricter practical constraints in new environments. For new inspection or agent smoke environments, Python 3.10 or 3.11 is a stable default unless the user's project already constrains the version.

Sweetviz operates on pandas DataFrames. The most common data problems are not install problems:

- Duplicate columns are unsupported.
- Target feature names are case-sensitive and must exist in the source DataFrame.
- Target values cannot contain missing values.
- Targets must be numeric or boolean after Sweetviz type detection or forcing.
- Mixed object columns can raise a mixed inferred type error; clean to one dtype before report construction.
- Low-cardinality numeric columns infer as categorical by default unless forced numeric or type thresholds are changed.

Use `sub-skills/configuration-and-data-handling/` for preflight and configuration guidance.

## Packaged assets

Sweetviz report rendering uses bundled package data:

- Jinja2 templates for report pages and feature panels.
- CSS and JavaScript assets embedded into generated HTML.
- Matplotlib styles for graph rendering.
- Fonts, including CJK-compatible font support when `[General] use_cjk_font = 1` is configured.
- `sweetviz_defaults.ini` for default layouts, verbosity, type thresholds, graph sizing, and Comet layout defaults.

If an installed package can import but report rendering fails with template, CSS, JavaScript, style, or font errors, suspect package-data installation issues or a partial source/package copy. Reinstall from a complete wheel/source distribution or run the bundled root checker with `--render-smoke`.

## No CLI route

The package metadata for this skill snapshot exposes no console entry point. Prefer Python snippets or the bundled skill scripts:

- `scripts/check_sweetviz_install.py`
- `sub-skills/report-generation/scripts/sweetviz_smoke_report.py`
- `sub-skills/dataset-comparison/scripts/sweetviz_compare_smoke.py`
- `sub-skills/configuration-and-data-handling/scripts/validate_sweetviz_inputs.py`
- `sub-skills/configuration-and-data-handling/scripts/write_sweetviz_override.py`

These helpers are skill-owned wrappers or adapted examples. They are not upstream Sweetviz CLI commands.

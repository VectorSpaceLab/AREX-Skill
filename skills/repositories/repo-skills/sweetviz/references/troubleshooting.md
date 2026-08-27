# Sweetviz troubleshooting

## When to read

Read this for cross-cutting Sweetviz install/import, package-data, browser/notebook, font, and optional Comet.ml problems. For workflow-specific input validation, use the nearest sub-skill troubleshooting file.

## Import fails or wrong package is imported

Symptoms:

```text
ModuleNotFoundError: No module named 'sweetviz'
AttributeError: module 'sweetviz' has no attribute 'analyze'
```

Likely causes:

- Sweetviz is installed in a different Python environment than the one running the code.
- A local file or notebook named `sweetviz.py` shadows the package.
- A stale or partial installation is still on `sys.path`.

Recovery:

1. Check the Python executable and package version from the same environment that will run the report:

   ```bash
   python -m pip show sweetviz
   python - <<'PY'
   import sweetviz as sv
   print(sv.__version__)
   print(sv.__file__)
   print(hasattr(sv, 'analyze'))
   PY
   ```

2. Rename any user script named `sweetviz.py` and remove stale `sweetviz.pyc` / `__pycache__` files near it.
3. Reinstall in the intended environment:

   ```bash
   python -m pip uninstall -y sweetviz
   python -m pip install sweetviz
   ```

4. Run the bundled checker:

   ```bash
   python scripts/check_sweetviz_install.py --json
   ```

## Public API rejects `verbosity`

Symptom:

```text
TypeError: analyze() got an unexpected keyword argument 'verbosity'
```

Sweetviz 2.3.3 public constructors `analyze()`, `compare()`, and `compare_intra()` do not accept `verbosity`. Use a config override instead:

```python
import sweetviz as sv
sv.config_parser["General"]["default_verbosity"] = "off"
report = sv.analyze(df, pairwise_analysis="off")
```

Or use `sub-skills/configuration-and-data-handling/scripts/write_sweetviz_override.py` to create an INI file and load it before report construction.

## Report rendering fails after import succeeds

Symptoms:

- Template lookup failures.
- Missing CSS/JavaScript/style/font resources.
- HTML file is tiny, empty, or lacks report content.
- Matplotlib style or font errors during graph rendering.

Likely causes:

- Package-data files were not installed with the package.
- A source copy omitted `templates`, `mpl_styles`, `fonts`, or `sweetviz_defaults.ini`.
- A partially editable install points at an incomplete checkout.

Recovery:

1. Reinstall from a complete wheel or source checkout.
2. Verify assets with:

   ```bash
   python scripts/check_sweetviz_install.py --render-smoke --output sweetviz_install_smoke.html
   ```

3. If the output generates but prints font warnings, treat that as cosmetic unless glyphs are missing or CJK text is unreadable. For CJK text, set `[General] use_cjk_font = 1` before constructing the report.

## Browser or notebook display surprises

Use `open_browser=False` when running from scripts, SSH sessions, CI, containers, or agents:

```python
report.show_html("report.html", open_browser=False)
```

`show_notebook()` expects an IPython/Jupyter display context. If a notebook task also needs a persisted file, pass `filepath=...` and set `file_layout` / `file_scale` for the saved HTML. If live display is not available, route to `show_html()` and inspect the output file instead.

## Optional Comet.ml logging is noisy or unconfigured

Sweetviz attempts Comet logging only when `comet_ml` is importable and an experiment can be created. If Comet is installed but credentials or network service are not configured, Sweetviz can print a warning and skip upload.

Recovery:

- For ordinary local reports, do not install or require `comet_ml`.
- For Comet tasks, configure Comet credentials and use `DataframeReport.log_comet(experiment)` intentionally.
- In smoke scripts, disable optional auto-upload behavior so local verification does not depend on external services.

## Data errors that look like Sweetviz bugs

Common construction failures are usually input validation issues:

- Duplicate columns: rename columns before constructing the report.
- Target missing or containing NaN: choose a valid target, fill/drop target-missing rows, or omit `target_feat`.
- Categorical target: force a truly numeric target with `FeatureConfig(force_num=[...])` only if the data is numerically meaningful.
- Mixed object columns: cast to string or numeric explicitly before report construction.
- Numeric columns with a few distinct values infer as categorical: force numeric or adjust `[Type_Detection] max_numeric_distinct_to_be_categorical`.
- Wide data with `pairwise_analysis='auto'`: choose `'off'` for deterministic reports or `'on'` when the association cost is acceptable.

Use `sub-skills/configuration-and-data-handling/scripts/validate_sweetviz_inputs.py --help` for CSV preflight checks.

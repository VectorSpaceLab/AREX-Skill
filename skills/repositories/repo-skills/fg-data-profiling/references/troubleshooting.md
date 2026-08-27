# Cross-Cutting Troubleshooting

## When to read

Read this when installation, imports, optional dependencies, CLI discovery,
report rendering, or data handling fail before a specific workflow is clear.
Then route to the nearest sub-skill for workflow-specific recovery.

## Install or import problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'data_profiling'` | Package not installed in the Python environment that is running the code | Run `python -m pip install -U fg-data-profiling` with the exact interpreter used by the notebook, script, or service. Then run `python -c "import data_profiling; print(data_profiling.__version__)"`. |
| Old code uses `import ydata_profiling` | Deprecated compatibility name still exists but is not the preferred import | Replace imports with `import data_profiling` and `from data_profiling import ProfileReport, compare`. Treat the warning as a migration reminder. |
| CLI command is not found | Console scripts were installed in a different environment or not on PATH | Prefer `python -m pip show fg-data-profiling` with the target interpreter, then run the bundled `scripts/check_environment.py`. If PATH is the issue, invoke the environment's script directory or use the Python API instead. |
| Outdated error such as `_plot_histogram() got an unexpected keyword argument 'title'` | Stale package or notebook kernel is using an old install | Upgrade in the active environment and restart the notebook kernel/runtime. |

## Optional dependency problems

- Notebook widgets need the `notebook` extra and frontend widget support. If the
  output is text like `IntSlider(value=0)`, enable/reinstall ipywidgets in the
  notebook environment and restart the kernel.
- Spark requires PySpark and a Java runtime. The base package import does not
  prove Spark support works. Use the Spark readiness script in
  `sub-skills/integrations-and-backends/scripts/` before constructing a Spark
  `ProfileReport`.
- Rich Unicode script/block labels need the `unicode` extra. Without it, the
  package falls back to Python's Unicode categories and may show less detailed
  labels.
- Great Expectations integration is legacy in current docs. If
  `to_expectation_suite()` raises `ImportError`, either install a compatible GE
  version for a legacy workflow or use the profile JSON/description output as
  the supported current data-quality surface.

## Data and privacy pitfalls

- Empty pandas DataFrames raise `ValueError`; create a non-empty sample or set
  up a lazy report only when you know how data will be attached later.
- Unknown file extensions in the CLI/data-reader path are treated as CSV with a
  warning. `.tar` is explicitly unsupported by the package reader.
- Sensitive identifiers such as phone numbers should be read as strings. If
  pandas coerces them to numeric values, aggregates such as min/max/quantiles can
  leak information even if samples are hidden.
- `sensitive=True`, `samples=None`, and `duplicates=None` reduce report leakage,
  but they do not replace data-governance review for private data.

## Rendering and output problems

- `ProfileReport.to_file("name.json")` writes JSON; other unknown suffixes are
  treated as HTML with a warning and a `.html` suffix.
- If `html.inline=False`, the package writes a sibling assets directory. Keep
  that directory with the HTML file when sharing the report.
- If output assets are missing, regenerate the report or set `html.inline=True`
  for a single-file report.
- If configuration changes after a report has already rendered, call
  `profile.invalidate_cache()` or create a new `ProfileReport` so cached HTML,
  JSON, widgets, and report structures do not hide the change.

## Where to go next

- Basic API report problem: `sub-skills/profiling-workflows/references/troubleshooting.md`
- CLI/automation problem: `sub-skills/cli-and-automation/references/troubleshooting.md`
- Config/output problem: `sub-skills/configuration-and-output/references/troubleshooting.md`
- Comparison/privacy problem: `sub-skills/comparison-and-quality/references/troubleshooting.md`
- Spark/notebook/integration problem: `sub-skills/integrations-and-backends/references/troubleshooting.md`

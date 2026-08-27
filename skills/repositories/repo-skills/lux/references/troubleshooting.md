# Lux troubleshooting

## When to read

Read this for cross-cutting Lux install, import, widget, version, Pandas patching, or optional backend issues. Use sub-skill troubleshooting files for workflow-specific failures.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'lux'` | The installed distribution is named `lux-api`, not `lux`; package is missing from the active Python. | Install with `pip install lux-api`, then verify with `python -c "import lux; print(lux.__version__)"` or `scripts/check_lux_environment.py`. |
| `pip install lux-api` cannot satisfy `pandas==1.4` | Lux 0.5.1 pins Pandas 1.4, which may not have wheels for very new Python versions. | Use a Python version compatible with Pandas 1.4, or choose a newer Lux package release if available and refresh this skill. |
| Pandas dataframes do not have `intent`, `recommendation`, or Lux display behavior | `import lux` happened after the dataframe was created or not in the same Python session. | Import `lux` before calling `pd.DataFrame(...)` or `pd.read_*`. Recreate/reload the dataframe. |
| Lux import succeeds but recommendations fail with an unexpected renderer/import error | Missing or incompatible visualization dependency such as Altair, Matplotlib, or lux-widget. | Run `scripts/check_lux_environment.py --json` and `python -m pip check`; reinstall `lux-api` in a clean environment if dependencies are inconsistent. |

## Widget and notebook display failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The dataframe shows only the Pandas table or no Lux toggle appears | Lux widget frontend is not enabled in the active notebook frontend, or the browser/frontend is unsupported. | In the notebook Python, run `import lux; lux.debug_info()`. For classic notebook, try `jupyter nbextension install --py luxwidget` and `jupyter nbextension enable --py luxwidget`. For JupyterLab, install/enable the Jupyter widgets manager and `luxwidget` as required by the frontend version. |
| `ModuleNotFoundError: No module named 'luxwidget'` | Widget package/version not installed or out of sync. | Reinstall `lux-api` and `lux-widget`, then rerun Lux diagnostics. |
| Widget state exists in a saved notebook but does not display later | The kernel/widget state was not restored or the frontend cannot find widget state. | Re-run the dataframe display cell in an active kernel. |
| Non-notebook scripts appear not to display Lux widgets | Lux widgets require a notebook-like frontend; terminal scripts should inspect `df.recommendation`, `df.current_vis`, or run bundled smoke scripts instead. | Use `scripts/lux_recommendation_smoke.py` or sub-skill scripts for terminal validation. |

## Stale recommendations or stale metadata

- Lux caches generated recommendations.
- After changing global config such as `plotting_backend`, `plotting_style`, `topk`, `sort`, sampling, or heatmap settings, call `df.expire_recs()` before redisplaying or accessing recommendations.
- After mutating columns, dtypes, indexes, or semantic data type overrides, call `df.expire_metadata()` and `df.expire_recs()` or recreate the dataframe.
- If a dataframe operation such as `head()` or `tail()` shows a message saying Lux is visualizing a previous dataframe version, run the operation you want explicitly and regenerate recommendations on that result.

## Intent and recommendation issues

- A bare string intent is invalid; set a list such as `df.intent = ["sales"]`.
- A value alone can trigger a warning such as “looks like a value that belongs to ...”; write it as `"attribute=value"`.
- An invalid attribute or filter value leaves intent/recommendations empty or warning-backed. Confirm column names and unique values from Pandas first.
- A `Vis` can represent only one visualization. If wildcard/list intent expands to multiple charts, use `VisList`.

## Optional SQL backend issues

- SQL workflows are optional and service-backed; base Lux installation does not prove PostgreSQL behavior.
- Missing `psycopg2`, SQLAlchemy, database credentials, table privileges, or a running PostgreSQL service can all block `LuxSQLTable`.
- Before constructing a `LuxSQLTable`, use `sub-skills/sql-backend/scripts/sql_table_probe.py` with a user-provided DSN or SQLAlchemy URL to test a non-destructive `SELECT` against the table.
- Do not run the upstream upload scripts as troubleshooting shortcuts: they hardcode localhost credentials, download datasets, and drop/create tables.

## When to refresh this skill

Refresh this repo skill when Lux package version, public API signatures, source directories, dependency constraints, or supported notebook/SQL behavior differ from `references/repo-provenance.md`.

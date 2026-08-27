# Orange3 cross-cutting troubleshooting

Use this for package-level install/import/CLI/Qt issues before routing into a focused sub-skill.

## Import or install fails

**Symptoms**

- `import Orange` fails.
- Compiled extension build errors appear during pip install.
- `pip check` reports incompatible scientific packages.
- `orange-canvas` is missing after installation.

**Likely causes**

- Package installed into the wrong environment.
- Missing compiler/build dependencies for pip installs from source.
- PyQt / WebEngine not installed or not compatible with the environment.
- `numpy`, `scipy`, `scikit-learn`, `pandas`, or Orange Canvas/widget dependencies are inconsistent.

**Recovery**

1. Prefer a fresh isolated environment.
2. For end users, install with conda-forge when possible.
3. For pip, install Qt bindings first (`PyQt6` and `PyQt6-WebEngine`) and then `Orange3`.
4. Run:

```bash
python -m pip check
python - <<'PY'
import Orange
from Orange.data import Table
print(Orange.__version__, len(Table("iris")))
PY
```

5. If running from a checkout, make sure the checkout is installed editable and that commands are using the same Python environment.

## `orange-canvas` or Qt fails in headless Linux

**Symptoms**

- Qt platform plugin errors such as `xcb` load failures.
- Widget tests or catalog rendering hang or crash before showing output.
- Canvas or `WidgetPreview` exits immediately in CI/headless sessions.

**Recovery**

- Set `QT_QPA_PLATFORM=offscreen` for non-interactive checks.
- Avoid launching the full interactive GUI in automation; use `--help`, widget imports, `WidgetPreview(...).run(..., no_exec=True/no_exit=True)` where suitable, or the bundled smoke/catalog helpers.
- Confirm PyQt and PyQtWebEngine are installed if help URL discovery or web-based widgets are involved.
- If QtWebEngine reports `Running as root without --no-sandbox`, prefer running the GUI check as a normal user. For trusted, non-interactive container checks only, set `QTWEBENGINE_DISABLE_SANDBOX=1`; for catalog discovery where help URLs are not needed, prefer `--no-help`.
- Use the `widget-development` sub-skill for WidgetTest/Canvas workflow loading details.

## Widget discovery or Canvas workflow loading fails

**Symptoms**

- Canvas toolbox misses widgets.
- `.ows` workflows cannot load or signal links disappear.
- Widget catalog generation reports empty categories.

**Likely causes**

- Entry points were not installed in the active environment.
- Discovery cache is stale.
- Add-on widgets are not installed.
- A widget changed input/output signal names or types.

**Recovery**

- Run Canvas with `--force-discovery` or clear discovery/settings if the environment changed.
- Confirm `Config.widgets_entry_points()` sees `Orange Widgets` and installed add-ons.
- For `.ows` loading, populate a `WidgetRegistry`, pause signal propagation during load, then resume only for workflows intended to execute.
- Use `sub-skills/widget-development/scripts/create_widget_catalog.py --list-categories --no-icons --no-help` to sanity-check discovery.

## Data or model task goes wrong after routing

- Data parse, missing value, duplicate header, save/load, sparse writer, or SQL issues → `sub-skills/data-preparation/references/troubleshooting.md`.
- Missing target, multiple target, single-class target, learner failure, scoring mismatch, or evaluation-memory issues → `sub-skills/supervised-modeling/references/troubleshooting.md`.
- Plot, projection, distance matrix, clustering bound, sparse/large-data, or stale visualization context issues → `sub-skills/exploration-visualization/references/troubleshooting.md`.
- `OWWidget`, settings/context migration, signal declarations, preview/test, concurrency, SQL widget helper, or workflow-loading issues → `sub-skills/widget-development/references/troubleshooting.md`.

## Optional SQL backend is unavailable

Orange's SQL table support is optional. A missing backend should not block ordinary local-file and in-memory data workflows.

For SQL tasks:

1. Confirm whether backend packages are installed and visible through `Backend.available_backends()`.
2. Confirm the live database service is reachable.
3. Verify host, port, database, schema, username, password, and table permissions.
4. Try a simple table selection before custom SQL or materialization.
5. If credentials or a service are unavailable, document SQL as not verified and continue with local data guidance only if that satisfies the user task.

## Quick bundled checks

```bash
python scripts/orange3_smoke.py --skip-gui
QT_QPA_PLATFORM=offscreen python scripts/orange3_smoke.py --with-gui
```

For data-specific checks:

```bash
python sub-skills/data-preparation/scripts/data_smoke.py
```

For widget discovery/catalog checks:

```bash
QT_QPA_PLATFORM=offscreen python sub-skills/widget-development/scripts/create_widget_catalog.py \
  --list-categories --no-icons --no-help
```

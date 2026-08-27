# Troubleshooting

## Purpose

Use this file for cross-cutting leafmap failures that affect more than one sub-skill. Workflow-specific guidance lives in the nearest sub-skill troubleshooting file.

## Fast checks

Run the bundled smoke helper before deeper debugging:

```bash
python scripts/check_leafmap_smoke.py --mode all
```

If you only need one area:

- `--mode core` for default ipyleaflet/folium maps.
- `--mode data` for conversion and data-helper sanity checks.
- `--mode maplibre` for MapLibre HTML and `view-vector`.
- `--mode cli` for `python -m leafmap` help output.
- `--mode optional` for missing optional backend reporting.

## Install or import failure

### Symptom
- `ModuleNotFoundError` for `leafmap`, `geopandas`, `planetary_computer`, `rioxarray`, `xarray`, `localtileserver`, or a backend package.
- `python -m pip check` reports broken requirements.

### Likely causes
- Base package installed without the optional dependencies needed by the selected workflow.
- A backend package is intentionally missing because it is optional.
- A stale environment still points at an older install.

### Recovery
1. Re-run `python -m pip check`.
2. Install the missing package or the targeted extra.
3. Re-run `python scripts/check_leafmap_smoke.py --mode ...` for the affected workflow.
4. If the missing package is optional and the workflow can use another backend, switch routes instead of forcing the missing dependency.

## Notebook widget or map rendering issues

### Symptom
- `Error displaying widget: model not found`
- Interactive map renders in one environment but not another
- A notebook falls back to folium when you expected ipyleaflet

### Likely causes
- ipyleaflet or Jupyter widget support is missing or not enabled.
- Colab or marimo is intentionally choosing folium.
- The notebook kernel needs a restart after install.

### Recovery
- Use `interactive-maps` guidance to pick the right backend.
- Restart the kernel after installing widget packages.
- If running in Colab or marimo, expect folium unless the environment explicitly supports ipyleaflet.

## Data and service issues

### Symptom
- Empty STAC / Planetary Computer / OSM / fire / Terrascope results
- `No module named planetary_computer`, `rioxarray`, or `xarray`
- CRS or bbox errors when converting data

### Likely causes
- Missing helper dependencies.
- Incorrect coordinate order or invalid bbox/CRS.
- Network or credential limits on the remote service.

### Recovery
- Use `data-workflows` and run `scripts/check_leafmap_smoke.py --mode data` for local conversion sanity.
- Confirm coordinate order, CRS, and column names.
- Treat remote-service failures as environment or network limitations unless the request explicitly requires live data.

## MapLibre viewer issues

### Symptom
- `view-raster` appears to hang
- A local vector file viewer works but the raster viewer does not
- `No module named fiona` when running `view-vector`
- HTML output is confused with opening a browser

### Likely causes
- `view-raster` intentionally keeps a tile server alive.
- `localtileserver` is missing.
- The file path or layer type is invalid.

### Recovery
- Use `maplibre-viewers` guidance and `scripts/check_leafmap_smoke.py --mode maplibre`.
- Prefer `view-vector` for a quick no-browser smoke.
- If `view-vector` fails on local file reading, install `fiona` or the MapLibre vector-file stack and rerun the smoke helper.
- Run `view-raster --help` or the root smoke helper instead of launching a long-lived server during verification.

## Optional backend issues

### Symptom
- `ImportError` for kepler, bokeh, pydeck, lonboard, or HERE widgets
- `heremap` fails with a shapely compatibility complaint
- A backend-specific notebook example requires API keys

### Likely causes
- Optional extras were not installed.
- The backend requires a service key or a different widget stack.
- The current Python/package combination is not supported for that backend.

### Recovery
- Use `alternate-backends` to choose a supported backend or record the backend as unverified.
- Install only the missing backend if that workflow is truly needed.
- Prefer MapLibre, ipyleaflet, folium, or another verified route when the optional backend is missing.

## When to stop

Stop and change the environment, backend choice, or workflow scope when:
- a required dependency is unavailable,
- a remote service needs credentials you do not have,
- a viewer requires a long-running server that is not appropriate for the task,
- or the package install is inconsistent with the current repository snapshot.

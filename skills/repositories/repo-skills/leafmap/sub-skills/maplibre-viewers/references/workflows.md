# MapLibre Viewer Workflows

## Purpose

Use these recipes when the user wants a standalone viewer or a MapLibre-first workflow.

## Build a MapLibre map

```python
import leafmap.maplibregl as leafmap

m = leafmap.Map(style="positron", height="600px")
m.add_geojson("data.geojson", name="Layer")
html = m.to_html(title="My Map")
```

## View a local vector file

```bash
python -m leafmap view-vector data.geojson --no-browser
```

This is the preferred no-browser smoke path because it exits after building the viewer HTML.

## View a local raster file

```bash
python -m leafmap view-raster image.tif --no-browser
```

Use this only when you actually want the tile-server behavior. It is normal for the command to stay alive until interrupted.

## View PMTiles

- Use `view_pmtiles(...)` for PMTiles-focused workflows.
- Use `Map.add_pmtiles(...)` when you want to compose a larger MapLibre map.

## Smoke strategy

- Start with `python scripts/check_leafmap_smoke.py --mode maplibre`.
- Use `--mode cli` when you only need the parser and help text.
- If the user needs a long-lived raster server, say so explicitly and avoid forcing that behavior during verification.

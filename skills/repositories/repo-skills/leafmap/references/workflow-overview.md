# Leafmap Workflow Overview

## Purpose

Read this first when you need to decide which sub-skill owns a leafmap task. It gives a fast route map from common user requests to the generated skill tree.

## Route map

| User intent | Owning sub-skill | Key entry points | Quick validation |
| --- | --- | --- | --- |
| Create or customize an interactive notebook map | `interactive-maps` | `leafmap.Map`, `leafmap.foliumap.Map`, `split_map`, `linked_maps`, `toolbar`, `basemaps`, `legends` | `scripts/check_leafmap_smoke.py --mode core` |
| Convert or fetch geospatial data for mapping | `data-workflows` | `csv_to_gdf`, `csv_to_geojson`, `gdf_to_geojson`, `stac_search`, `download_naip`, `osm_gdf_from_place`, `search_fires`, `create_time_layers` | `scripts/check_leafmap_smoke.py --mode data` |
| Render a standalone MapLibre HTML viewer or use `leafmap view-vector` / `view-raster` | `maplibre-viewers` | `leafmap.maplibregl.Map`, `view_vector`, `view_raster`, `view_pmtiles`, `python -m leafmap` | `scripts/check_leafmap_smoke.py --mode maplibre` and `--mode cli` |
| Choose a non-default backend such as kepler, plotly, bokeh, pydeck, deck.gl, HERE, or mapbox | `alternate-backends` | `leafmap.kepler`, `leafmap.plotlymap`, `leafmap.bokehmap`, `leafmap.deck`, `leafmap.deckgl`, `leafmap.heremap`, `leafmap.mapbox` | `scripts/check_leafmap_smoke.py --mode optional` |

## Verified entry points

- Distribution: `leafmap` 0.63.1.
- Console scripts: `leafmap`, `view-raster`, `view-vector`.
- Top-level package import: `import leafmap`.
- Known installed signatures from inspection:
  - `leafmap.leafmap.Map.__init__(self, **kwargs)`
  - `leafmap.foliumap.Map.__init__(self, **kwargs)`
  - `leafmap.maplibregl.Map.__init__(center=(0, 20), zoom=1, pitch=0, bearing=0, style='dark-matter', height='600px', controls=..., projection='mercator', use_message_queue=None, add_sidebar=None, add_floating_sidebar=None, sidebar_visible=False, sidebar_width=360, sidebar_args=None, layer_manager_expanded=True, **kwargs)`
  - `leafmap.common.csv_to_gdf(in_csv, latitude='latitude', longitude='longitude', geometry=None, crs='EPSG:4326', encoding='utf-8', **kwargs)`
  - `leafmap.common.get_local_tile_url(...)`
  - `leafmap.cli.view_raster(...)` and `leafmap.cli.view_vector(...)`

## How to use this overview

1. Start from the route map above.
2. Open the owning sub-skill `SKILL.md`.
3. Use the matching reference file for deeper API notes and troubleshooting.
4. Run `scripts/check_leafmap_smoke.py` with the matching mode if you need a quick local sanity check.


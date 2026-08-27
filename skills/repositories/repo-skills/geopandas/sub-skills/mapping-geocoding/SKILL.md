---
name: mapping-geocoding
description: "Use when plotting GeoPandas data, building interactive maps,
  classifying choropleths, adding tile context, or geocoding and
  reverse-geocoding addresses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Mapping and Geocoding

Use this sub-skill when the task turns GeoPandas data into static/interactive maps or uses geocoding providers to convert between addresses and coordinates.

## Read First

- [Visualization and geocoding reference](references/visualization-geocoding-reference.md): API notes for `.plot()`, `.explore()`, choropleths, classification, tiles, `geocode`, and `reverse_geocode`.
- [Workflows](references/workflows.md): recipes for static maps, interactive maps, optional-dependency checks, no-network geocoding tests, and safe provider usage.
- [Troubleshooting](references/troubleshooting.md): missing matplotlib/folium/mapclassify/geopy, display issues, CRS/tile problems, provider errors, rate limits, and API-key boundaries.
- [check_mapping_optional_deps.py](scripts/check_mapping_optional_deps.py): reports optional visualization/geocoding modules.
- [mock_geocode_smoke.py](scripts/mock_geocode_smoke.py): validates GeoPandas geocoding result handling without calling a real provider.

## Route Here When

- The user asks for `GeoDataFrame.plot`, `GeoSeries.plot`, choropleth maps, legends, colormaps, classification schemes, or matplotlib axes handling.
- The task mentions `GeoDataFrame.explore`, folium, interactive HTML maps, tiles, mapclassify, basemaps, or `xyzservices` providers.
- The task uses `geopandas.tools.geocode`, `reverse_geocode`, geopy providers, provider kwargs, timeouts, rate limits, or address-to-point conversion.
- The problem is an optional mapping/geocoding dependency error or a network/provider boundary.

## Route Elsewhere

- Use `../core-data-model/SKILL.md` for CRS assignment/reprojection and geometry-column repairs before plotting.
- Use `../spatial-operations/SKILL.md` for clipping, joins, dissolves, simplification, or metric preprocessing before map output.
- Use `../io-formats/SKILL.md` for saving map input/output vector data.
- Use `../validation-testing/SKILL.md` for assertions around map/geocode outputs.

## Default Operating Rules

1. Check optional dependencies before planning a map output. Static plots require matplotlib; interactive `explore()` workflows commonly need folium/branca/mapclassify and sometimes tile-provider packages.
2. Reproject to an appropriate display CRS when tiles or metric styling require it, but preserve original analysis data when needed.
3. Downsample or simplify large geometries before interactive maps if performance matters.
4. Treat geocoding as a network/service workflow. Specify provider, timeout, API key/credentials policy, rate limits, and terms of service.
5. Do not call real geocoding providers in tests or smoke scripts. Use mocked provider behavior for validation.
6. Keep map output expectations explicit: matplotlib `Axes`, folium map object, HTML file, or serialized vector data.

## Minimal Checks

```bash
python scripts/check_mapping_optional_deps.py --json
python scripts/mock_geocode_smoke.py --json
```

The mock geocode smoke returns success without network if `geopy` is available; if it is missing, it reports a skipped optional workflow unless `--require-geopy` is used.

## Handoff

- Prepare and validate input layers with `core-data-model` and `spatial-operations` before plotting.
- Use `io-formats` for input/output data files.
- Use `validation-testing` to compare expected geocoded GeoDataFrames or geometry outputs.

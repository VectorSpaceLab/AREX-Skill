# Data Workflows Recipes

## Purpose

Use these recipes when the user is handling data before mapping.

## Convert a CSV into GeoJSON

```python
from leafmap.common import csv_to_gdf, csv_to_geojson, gdf_to_geojson

gdf = csv_to_gdf("points.csv", latitude="latitude", longitude="longitude")
geojson = csv_to_geojson("points.csv")
roundtrip = gdf_to_geojson(gdf)
```

## Query a STAC endpoint

```python
from leafmap.stac import stac_search, cog_tile

items = stac_search("https://example.com/stac")
tile = cog_tile("https://example.com/cog.tif")
```

## Work with Planetary Computer or OSM data

- Use `leafmap.download.download_naip(...)` for NAIP imagery downloads.
- Use `leafmap.download.view_pc_items(...)` to inspect Planetary Computer items.
- Use `leafmap.osm.osm_gdf_from_place(...)` when the request is about place-based OSM features.
- Use `leafmap.pc.get_pc_collection_list()` and `leafmap.pc.get_bands(...)` for collection discovery.

## Use remote-source helpers safely

- Validate bbox order, CRS, and tag filters before trying the remote query.
- Prefer small discovery or metadata queries before large downloads.
- Treat credentials or network access as part of the request, not as a hidden assumption.

## Smoke strategy

- Start with `python scripts/check_leafmap_smoke.py --mode data`.
- If the user only needs a conversion proof, keep the test local and synthetic.
- If the user needs a live remote source, call out the network or credential requirement explicitly before attempting it.

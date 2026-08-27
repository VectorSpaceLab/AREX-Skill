---
name: remote-geospatial-data
description: "This sub-skill routes authenticated Google Earth Engine catalog,
  land-cover, building-footprint, and bounded satellite-timelapse workflows for
  geospatial applications."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Remote geospatial data

Use this sub-skill when the task needs **geemap's Google Earth Engine
integration** for catalog search, NLCD, Dynamic World/ESA/ESRI land cover,
Microsoft building footprints, or a Landsat, Sentinel-2, GOES, MODIS, or NAIP
timelapse. Route to [earth-engine-api.md](references/earth-engine-api.md) for
catalog, asset, authentication, and ROI decisions. Route to
[timelapse-workflows.md](references/timelapse-workflows.md) for a timelapse
family and bounded execution plan. Use
[scripts/validate_ee_config.py](scripts/validate_ee_config.py) before a remote
request and [troubleshooting.md](references/troubleshooting.md) when a request
or media conversion fails.

## Router

1. Decide whether the operation is catalog/NLCD, land-cover comparison,
   building footprints, or a timelapse. Do not use this route for generic
   Leafmap layer composition or local dashboard data.
2. Normalize the input ROI. Prefer a small sample ROI. For an uploaded
   GeoJSON/KML-derived GeoDataFrame, confirm that its CRS is WGS84 (`EPSG:4326`)
   or reproject it before calling `gdf_to_ee(gdf, geodesic=False)`.
3. Validate dates, JSON visualization/palette values, and GeoJSON structure
   without contacting Earth Engine. The bundled validator checks token-variable
   presence only; it never authenticates and never exposes a token value.
4. Set `USE_FOLIUM=1` **before** `import geemap.foliumap as geemap`. This makes
   the Streamlit process select the folium map backend used by this app instead
   of leaving backend selection implicit.
5. Authenticate only at the explicit Earth Engine boundary, using the exact
   initialization contract in [earth-engine-api.md](references/earth-engine-api.md).
   Search or instantiate the intended asset, then make one bounded request.
6. Select one timelapse family, keep ROI/date/frame/output bounds explicit, and
   verify the requested GIF/MP4 exists before presenting it. Treat remote asset
   availability and imagery presence as runtime facts.

## Hard boundaries

- Never put a token or token value in a prompt, source file, log, or result.
- Never report that an asset exists, imagery was returned, or a timelapse
  completed unless an authenticated Earth Engine call and local output check
  actually observed it. This skill does not perform live remote verification.
- Do not submit malformed JSON, an invalid/empty ROI, a reversed date range, or
  an unbounded global/time-span timelapse.
- Keep review notes and evidence outside this runtime subtree; the references
  here are operational instructions, not links to source application files.

---
name: raster-dem-and-basemaps
description: "Use BlenderGIS raster, DEM, ASCII grid, web elevation, basemap,
  cache, and image-engine workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Raster, DEM, and Basemaps

Use this sub-skill when a task involves BlenderGIS georeferenced raster import, ASCII grid import, raster-as-DEM terrain creation, web DEM download, or the interactive basemap tile viewer.

## Load This First

1. For concrete operator sequences, read [references/workflows.md](references/workflows.md).
2. For operator IDs, class/function surfaces, option names, and engine behavior, read [references/api-reference.md](references/api-reference.md).
3. For raster, world-file, ASCII grid, web DEM, tile-service, and GeoPackage cache formats, read [references/data-formats.md](references/data-formats.md).
4. For failures and recovery, read [references/troubleshooting.md](references/troubleshooting.md).
5. To preflight an image/world-file pair outside Blender, run [scripts/inspect_georaster.py](scripts/inspect_georaster.py). It uses Pillow when available and does not require GDAL.

## Covered Workflows

- `importgis.georaster` import modes `PLANE`, `BKG`, `MESH`, `DEM`, and `DEM_RAW`.
- `importgis.asc_file` ASCII grid modes `MESH` and `CLOUD`.
- `importgis.dem_query` web DEM download and follow-on DEM import.
- `view3d.map_start`, `view3d.map_viewer`, and `view3d.map_search` basemap viewing, search, export-to-mesh, and tile caching.
- Optional raster/image/projection engines: GDAL, Pillow/PIL, ImageIO FreeImage, pyproj, and built-in fallbacks where BlenderGIS supports them.

## Route Elsewhere

- Generic scene CRS/origin repair, custom CRS presets, `GeoScene`, `SRS`, and reprojection engine selection: `../georeferencing-and-crs/`.
- OSM vector query/import and Overpass tag filters: `../vector-data-and-osm/`.
- Terrain triangulation, terrain-analysis material nodes, drop-to-ground, and earth-sphere/curvature transforms after data import: `../terrain-mesh-and-analysis/`.
- Georeferenced camera render output and world-file render export: `../geocameras-and-rendering/`.
- Cross-cutting add-on enablement, logs, optional dependency checks, and privacy guidance: `../../references/addon-overview.md` and `../../references/troubleshooting.md`.

## Quick Decision Guide

- Need a flat georeferenced image in the scene: use `importgis.georaster` with `importMode='PLANE'`.
- Need a non-rendering viewport reference image and the raster is not rotated/reprojected: use `importMode='BKG'`.
- Need to drape an image onto an existing georeferenced mesh: use `importMode='MESH'`.
- Need elevation as a displacement modifier: use `importMode='DEM'` and decide `fillNodata`, `subdivision`, `step`, and `demOnMesh` deliberately.
- Need actual DEM vertices/point cloud: use `importMode='DEM_RAW'` or ASCII `importMode='CLOUD'`, usually with `step > 1` for large rasters.
- Need online context imagery: use `view3d.map_start`; verify image engines and cache folder before blaming the map service.
- Need OpenTopography SRTM/GMRT elevation: use `importgis.dem_query`; confirm scene georef, extent size, latitude range, network, and OpenTopography API key requirements first.

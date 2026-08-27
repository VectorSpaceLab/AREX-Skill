# BlenderGIS Cross-Cutting Troubleshooting

## Purpose

Use this root troubleshooting guide for add-on enablement, import/logging, optional dependencies, service credentials, and privacy issues that affect more than one BlenderGIS workflow. For workflow-specific failures, route to the nearest sub-skill troubleshooting reference.

## Install and Enablement

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'bpy'` while running ordinary Python | BlenderGIS is a Blender add-on, not a normal standalone package. | Run inside Blender's Python or a compatible `bpy` runtime for inspection. Do not promise ordinary Python can execute UI operators. |
| Add-on enable fails with a Blender version error | Blender is older than `2.83` or an untested major version greater than 5. | Use a supported Blender version, or treat newer-major support as an unverified source update requiring refresh/testing. |
| `View3D > GIS` menu is missing | Add-on is not installed/enabled, registration failed, or Blender is in the wrong context. | Enable the add-on in Blender preferences, inspect the console/logs, and run `scripts/check_blendergis_environment.py` for module availability. |
| Operator exists but button is disabled | Many operators require Object Mode, a 3D View context, selected meshes, active object, or georeferenced scene. | Read the owning sub-skill's operator reference and fix context/selection before changing data. |

## Logs

BlenderGIS writes logs through Python logging and exposes `GIS > Logs` / `bgis.logs` to open `bgis.log` in Blender. If an operator reports “check logs for more infos,” inspect that text block or the add-on log file in the user's Blender data/cache area. Do not include private local log paths in reusable instructions.

## Optional Dependency Failures

| Symptom | Likely cause | Route |
| --- | --- | --- |
| `Missing reproj engine`, CRS transform fails, EPSG.io/MapTiler fallback needed | GDAL/pyproj absent or CRS pair unsupported by built-in math | `sub-skills/georeferencing-and-crs/references/troubleshooting.md` |
| Raster opens without georef or fails with unsupported format | Missing world file/GeoTIFF tags or unavailable GDAL/PIL/ImageIO engine | `sub-skills/raster-dem-and-basemaps/references/troubleshooting.md` |
| DEM/raw mesh import is too slow or memory-heavy | Full-resolution raster point cloud or DEM mesh requested | `sub-skills/raster-dem-and-basemaps/references/workflows.md` and `terrain-mesh-and-analysis` |
| Shapefile import/export loses fields or fails on empty selection | DBF field constraints, invalid field selection, or no selected mesh | `sub-skills/vector-data-and-osm/references/troubleshooting.md` |
| Geophoto camera creation reports missing GPS tags | JPEG/TIFF has no required EXIF GPS tags | `sub-skills/geocameras-and-rendering/scripts/read_exif_gps.py` |

## Network and Credentials

BlenderGIS can contact several external services: Overpass for OSM, OpenTopography/GMRT for DEMs, basemap tile servers, Nominatim search, and EPSG.io/MapTiler coordinate services. Before running live network calls:

1. Ask whether network use is allowed for the user's task and data location.
2. Check whether credentials are required. OpenTopography SRTM templates require an API key.
3. Reduce request extents. DEM queries reject very large extents and SRTM has latitude coverage limits.
4. Prefer bundled preflight helpers where possible: Overpass query building, raster/world-file inspection, and point transforms.
5. Do not paste API keys into generated scripts, logs, or public artifacts.

## Environment Diagnostic

Run the bundled root helper from any directory:

```bash
python /path/to/blender-gis/scripts/check_blendergis_environment.py --addon-path /path/to/BlenderGIS --json
```

Use `--module BlenderGIS` only when the add-on is importable as a Python module in the current environment. The helper reports Blender Python module availability, optional dependency availability, add-on version, feature flags, and registration-surface facts without executing Blender UI operators.

## When to Stop

Stop and ask the user for more context when:

- a workflow requires network/API credentials and none are provided;
- a task requires executing GUI operators but no Blender scene/context/files are supplied;
- a destructive export/write path could overwrite user data;
- requested behavior depends on optional GDAL/network/runtime evidence not installed in the current environment;
- the current checkout differs from [repo-provenance.md](repo-provenance.md) and source behavior may have changed.

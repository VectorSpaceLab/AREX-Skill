---
name: georeferencing-and-crs
description: "Route BlenderGIS CRS, geoscene origin, coordinate transform, and
  reprojection-engine tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# georeferencing-and-crs

Use this sub-skill when a task depends on BlenderGIS scene georeferencing: CRS/SRID state, scene origin coordinates, WGS84/Web Mercator/UTM transforms, projection engine selection, predefined CRS preferences, or recovery from broken partial georef state.

## Use this sub-skill for

- Inspecting or repairing `GeoScene` state stored on `bpy.context.scene` custom properties.
- Setting or switching the scene CRS through `geoscene.*` operators or `GeoScene.crs`.
- Linking geographic origin (`longitude`, `latitude`) and projected origin (`crs x`, `crs y`).
- Choosing among `AUTO`, `GDAL`, `PYPROJ`, `BUILTIN`, and `EPSGIO` / MapTiler Coordinates reprojection engines.
- Transforming one point safely outside Blender with [scripts/transform_point.py](scripts/transform_point.py).

## Route elsewhere

- Raster images, DEMs, world files, GeoTIFF details, basemap tiles, and raster reprojection outputs belong to `raster-dem-and-basemaps`.
- Shapefile, OSM XML, Overpass query, feature fields, and imported vector geometry workflows belong to `vector-data-and-osm`.
- Camera geophotos, georeferenced render cameras, and camera world-file output belong to `geocameras-and-rendering`.

## Read next

- [references/api-reference.md](references/api-reference.md) for `GeoScene`, `SRS`, `Reproj`, custom keys, operators, preferences, and engine behavior.
- [references/workflows.md](references/workflows.md) for CRS setup, origin linking, broken-state recovery, engine choice, and point-transform examples.
- [references/troubleshooting.md](references/troubleshooting.md) for invalid CRS, partial georef state, missing engines, MapTiler/EPSG.io network risk, optional dependency differences, and axis-order gotchas.

## Fast checks

1. A usable BlenderGIS scene is georeferenced when `GeoScene(scene).isGeoref` is true and `GeoScene(scene).isBroken` is false.
2. Required scene custom keys are exactly `SRID`, `crs x`, and `crs y`; `longitude` and `latitude` are synchronized convenience keys when reprojection succeeds.
3. For a quick WGS84-to-Web-Mercator smoke test, run:

```bash
python sub-skills/georeferencing-and-crs/scripts/transform_point.py --src-crs EPSG:4326 --dst-crs EPSG:3857 --x 2 --y 48 --json
```

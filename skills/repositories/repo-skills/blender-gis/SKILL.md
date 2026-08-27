---
name: blender-gis
description: "Route BlenderGIS add-on tasks for georeferencing, vector and OSM
  data, raster/DEM basemaps, terrain analysis, and geocamera rendering in
  Blender."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# BlenderGIS Repo Skill

Use this repo skill when a task asks about BlenderGIS, Blender geodata/GIS workflows, georeferenced scenes, shapefile/OSM/raster/DEM import, basemap tiles, terrain meshes, or georeferenced cameras and render world files.

BlenderGIS is a Blender add-on. Most runtime actions happen inside Blender through `bpy.ops.*` operators and the `View3D > GIS` menu. Use the bundled references and scripts here for planning, preflight, troubleshooting, and exact operator/API facts before running Blender operations.

## Install and Enable

For an end-user Blender setup, install BlenderGIS as a Blender add-on directory or zip that contains `__init__.py`, then enable it in `Edit > Preferences > Add-ons`. After enablement, verify that `View3D > GIS` appears and that `GIS > Logs` can open the add-on log.

For scripted inspection or CI-style checks, use a Blender-compatible Python runtime; ordinary Python without `bpy`, `bmesh`, and `mathutils` cannot execute BlenderGIS UI operators. Optional dependencies such as `pyproj`, GDAL/`osgeo`, Pillow/PIL, and ImageIO FreeImage only affect specific reprojection or raster/image paths.

## First Checks

- BlenderGIS source says Blender `>= 2.83` is required and rejects untested major versions above 5.
- The add-on version in `bl_info` is `2.2.14` for this skill snapshot.
- Main menu route: `View3D > GIS`, with submenus `Web geodata`, `Import`, `Export`, `Camera`, `Mesh`, `Object`, `Nodes`, and `Logs`.
- Run [scripts/check_blendergis_environment.py](scripts/check_blendergis_environment.py) to inspect an installed add-on/module path and optional Python dependencies before giving execution advice.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.

## Route by Task

| User task | Read |
| --- | --- |
| Set CRS, initialize or repair scene origin, transform coordinates, choose projection engine, debug broken georef state | [sub-skills/georeferencing-and-crs/SKILL.md](sub-skills/georeferencing-and-crs/SKILL.md) |
| Import/export shapefiles, import local OSM XML, build Overpass queries, configure OSM tags, choose elevation/extrusion fields | [sub-skills/vector-data-and-osm/SKILL.md](sub-skills/vector-data-and-osm/SKILL.md) |
| Import GeoTIFF/JPEG/PNG/BMP rasters with world files, use ASCII grids, DEM displacement/raw meshes, web DEM, basemap viewer, cache/image engines | [sub-skills/raster-dem-and-basemaps/SKILL.md](sub-skills/raster-dem-and-basemaps/SKILL.md) |
| Build Delaunay/Voronoi terrain meshes, drop objects to ground, globe/earth-curvature transforms, terrain analysis nodes/reclassification | [sub-skills/terrain-mesh-and-analysis/SKILL.md](sub-skills/terrain-mesh-and-analysis/SKILL.md) |
| Create cameras from geotagged photos, switch geophoto cameras, create orthographic georeferenced render cameras and world-file text output | [sub-skills/geocameras-and-rendering/SKILL.md](sub-skills/geocameras-and-rendering/SKILL.md) |

## Shared References

- [references/addon-overview.md](references/addon-overview.md) summarizes add-on metadata, menu/operator map, preferences, optional dependencies, and feature flags.
- [references/troubleshooting.md](references/troubleshooting.md) covers install/enable/import failures, logs, optional dependencies, service/API-key limits, and cross-workflow debugging.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for DisCo's managed repo-skills router.

## Operating Rules

1. Do not treat BlenderGIS as a normal command-line Python package; it is a Blender add-on whose public workflow is mostly `bpy.ops` and UI panels.
2. Before any data import, check scene georeferencing. Many operators cancel or produce shifted geometry when CRS/origin state is missing or broken.
3. Separate optional dependencies from core add-on availability: GDAL, pyproj, Pillow/PIL, ImageIO FreeImage, network services, and API keys affect specific workflows, not every workflow.
4. For network workflows, do not run live Overpass, Nominatim, basemap, or OpenTopography requests unless the user approves network use and supplies required API keys.
5. Prefer bundled helpers for preflight: Overpass query generation, raster/world-file inspection, point-cloud validation, EXIF GPS checks, and CRS point transforms.

## Minimal Verification Pattern

Use a Blender Python-capable environment and run a read-only import check:

```bash
python scripts/check_blendergis_environment.py --module BlenderGIS --json
```

If the add-on is not importable as a module, pass the directory containing its `__init__.py`:

```bash
python scripts/check_blendergis_environment.py --addon-path /path/to/BlenderGIS --json
```

Then route to the relevant sub-skill for workflow-specific preflight and recovery.

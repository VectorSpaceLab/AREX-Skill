---
name: geocameras-and-rendering
description: "Create BlenderGIS geophoto cameras and georeferenced render
  cameras with world-file output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Geocameras and Rendering

Use this sub-skill when a task needs BlenderGIS camera workflows: placing cameras, empties, or the 3D cursor from geotagged photos; switching a geophoto camera with its background image; or creating an orthographic map-render camera with a world-file text block.

## Route First

- Scene CRS/origin setup, CRS validation, and reprojection engine choices belong to [georeferencing-and-crs](../georeferencing-and-crs/SKILL.md).
- Raster import, georeferenced images, DEMs, and basemap tiles belong to [raster-dem-and-basemaps](../raster-dem-and-basemaps/SKILL.md).
- Add-on enablement and cross-cutting dependency issues belong to the root [add-on overview](../../references/addon-overview.md) and root [troubleshooting](../../references/troubleshooting.md).

## Use These Files

- [references/workflows.md](references/workflows.md): end-to-end geophoto and georender procedures, validation, and world-file computations.
- [references/operator-reference.md](references/operator-reference.md): operator IDs, options, side effects, custom properties, and exact world-file equation.
- [references/troubleshooting.md](references/troubleshooting.md): recovery steps for georef, GPS, format, context, selection, and pixel-size failures.
- [scripts/read_exif_gps.py](scripts/read_exif_gps.py): standalone preflight helper for JPEG/TIFF photo sets before running Blender operators.

## Core Operator Map

| Workflow | Operator ID | Use when |
| --- | --- | --- |
| Geotagged photo placement | `camera.geophotos` | Create target cameras, cameras, empties, or move the cursor from EXIF GPS photos. |
| Switch geophoto view | `camera.geophotos_setactive` | Make a BlenderGIS geophoto camera active and show its photo as the camera background. |
| Georeferenced render camera | `camera.georender` | Create or update an orthographic top-view camera over a selected mesh and generate a world-file text block. |

## Required Preconditions

- BlenderGIS is enabled and its camera module is available from `GIS > Camera`.
- The scene must be georeferenced (`GeoScene.isGeoref` true): valid CRS plus projected origin coordinates.
- Geophoto inputs must be JPEG or TIFF files with EXIF `GPSLatitude`, `GPSLatitudeRef`, `GPSLongitude`, and `GPSLongitudeRef` tags.
- `camera.geophotos_setactive` must run from a 3D View context.
- `camera.georender` must run in Object Mode with either exactly one selected mesh, or one selected mesh plus one BlenderGIS georender camera carrying the `mapRes` custom property.

## Expected Success Signals

- Geophotos create objects at projected photo coordinates minus the scene projected origin. Cameras get camera-data custom properties `background`, `imageWidth`, `imageHeight`, and `orientation`.
- Switching a geophoto sets `scene.camera`, render resolution, and a visible camera background image for the selected geophoto.
- Georender creates or updates an orthographic camera, sets render resolution from mesh extent and `target_res`, stores `mapRes`, and writes a `<camera name>.wld` text block in Blender containing six world-file lines.

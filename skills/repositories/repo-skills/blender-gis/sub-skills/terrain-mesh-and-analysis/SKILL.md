---
name: terrain-mesh-and-analysis
description: "Use BlenderGIS terrain meshing, object drop, globe/curvature, and
  terrain analysis material workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Terrain Mesh and Analysis

Use this sub-skill when a BlenderGIS task needs terrain point-cloud meshing, Voronoi diagrams, dropping objects onto a terrain surface, transforming lon/lat meshes to a globe, applying earth-curvature correction, or building/reclassifying terrain analysis materials.

## Route Here For

- `bpy.ops.tesselation.delaunay()` and `bpy.ops.tesselation.voronoi(...)` terrain point-cloud triangulation/diagram work.
- `bpy.ops.object.drop(...)` workflows where selected objects must be dropped onto the active ground object.
- `bpy.ops.earth.sphere(radius=...)` and `bpy.ops.earth.curvature()` mesh transforms.
- `bpy.ops.analysis.nodes()` and `bpy.ops.reclass.*` terrain height/slope/aspect material setup and color-ramp reclassification.
- Preflighting an XYZ point cloud with [scripts/validate_point_cloud.py](scripts/validate_point_cloud.py) before running the Delaunay/Voronoi operators.

## Route Elsewhere

- Importing shapefiles, OSM, contours, rasters, DEMs, or point source files belongs to the vector or raster/DEM sub-skills first.
- Creating or repairing scene CRS/georeferencing belongs to `georeferencing-and-crs`.
- Camera placement, EXIF geophotos, georeferenced rendering, and world-file output belong to `geocameras-and-rendering`.

## Required Reading

1. [references/workflows.md](references/workflows.md) for complete step-by-step workflows and recovery paths.
2. [references/operator-reference.md](references/operator-reference.md) for operator IDs, options, selection/context requirements, inputs, and outputs.
3. [references/troubleshooting.md](references/troubleshooting.md) when an operator cancels, logs warnings, silently skips objects, or produces a material/node result that does not look right.
4. [scripts/validate_point_cloud.py](scripts/validate_point_cloud.py) for an offline point-cloud preflight helper that reads CSV or whitespace XYZ points and reports duplicates, same-XY different-Z points, too few unique points, and colinear XY geometry.

## Operating Notes

- Delaunay and Voronoi use XY coordinates for topology. Z is retained for Delaunay terrain height but ignored by the 2D Voronoi diagram output.
- BlenderGIS mesh tools expect object-mode selections. Exact active-object and selection state matters; fix that before changing operator options.
- Terrain analysis node setup assumes a mesh-like active terrain object and forces the render engine to Cycles.
- Reclassification operators are Node Editor tools. They act on the active `ShaderNodeValToRGB` color ramp node, not merely on the selected mesh object.

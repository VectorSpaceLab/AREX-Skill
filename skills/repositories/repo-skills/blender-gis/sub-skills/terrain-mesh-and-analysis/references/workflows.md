# Terrain Mesh and Analysis Workflows

This reference is self-contained operating guidance for BlenderGIS terrain mesh, drop-to-ground, globe/curvature, and terrain-analysis material workflows. It assumes the BlenderGIS add-on is installed and enabled in Blender and that any source geodata has already been imported by the appropriate vector or raster/DEM sub-skill.

## 1. Preflight an XYZ Point Cloud Before Tesselation

Use this before `tesselation.delaunay` or `tesselation.voronoi`, especially for data imported from contours, DEM raw points, CSVs, or generated vertices.

```bash
python sub-skills/terrain-mesh-and-analysis/scripts/validate_point_cloud.py points.xyz
python sub-skills/terrain-mesh-and-analysis/scripts/validate_point_cloud.py points.csv --json
```

Accepted input rows are either comma-separated or whitespace-separated `x y z` triples. Blank lines and `#` comments are ignored; a simple header row is skipped.

The helper reports:

- exact duplicate XYZ rows;
- repeated XY coordinates with different Z values, matching the add-on's "z colinear" duplicate concept;
- the number of unique XY points after source-compatible duplicate collapse;
- too few unique points for triangulation/diagram creation;
- colinear XY points, including the source operator's all-X or all-Y check and a general all-points-on-one-line check.

Duplicates are warnings by default because BlenderGIS removes/ignores duplicate XY rows before using the legacy Voronoi/Delaunay implementation. Use `--strict-duplicates` if a pipeline should fail on duplicates instead of only warning.

## 2. Point Cloud to Delaunay Terrain Mesh

Goal: convert a mesh object whose vertices are terrain sample points into a TIN surface.

1. Obtain or create a Blender mesh object whose vertices are point samples. Import routes are outside this sub-skill:
   - contours/shapefiles/OSM: use the vector sub-skill;
   - DEM raw points or raster-derived points: use the raster/DEM sub-skill;
   - CRS/origin setup: use `georeferencing-and-crs` before importing when coordinates matter.
2. Preflight the points with [../scripts/validate_point_cloud.py](../scripts/validate_point_cloud.py). Resolve `FAIL` status before entering BlenderGIS tesselation.
3. In Blender Object Mode, select exactly one mesh object: the point-cloud mesh. Do not leave helper meshes or imported contour objects selected.
4. Run **GIS > Mesh > Delaunay** or call:

   ```python
   bpy.ops.tesselation.delaunay()
   ```

5. Expected result:
   - a new mesh datablock named `TIN`;
   - a new object named `TIN` linked into the scene;
   - the output object receives the source object's location, rotation, and scale;
   - the output object becomes active and selected while the source point cloud is deselected;
   - report text is shaped like `N triangles created in S seconds`.

Recovery notes:

- If the operator reports `Selection is empty or too much object selected`, leave only one mesh selected.
- If it reports `Selection isn't a mesh`, convert/import the points as a mesh object first.
- If it reports `Not enough points` or `Points are colinear`, use the validator and fix the point data. Three unique non-colinear XY points are the minimum.
- On Blender builds that use the native `mathutils.geometry.delaunay_2d_cdt` path, explicit duplicate/colinear reports may be less visible; still preflight because degenerate point clouds can create unusable or failed triangulations.

## 3. Point Cloud to Voronoi Diagram

Goal: create a 2D Voronoi diagram from point-cloud XY positions.

1. Select exactly one mesh object containing the input points.
2. Run **GIS > Mesh > Voronoi** or call one of:

   ```python
   bpy.ops.tesselation.voronoi(meshType="Edges")
   bpy.ops.tesselation.voronoi(meshType="Faces")
   ```

3. Choose `meshType`:
   - `Edges`: creates a wire/edge diagram;
   - `Faces`: creates polygon faces for cells.
4. Expected result:
   - a new mesh/object named `VoronoiDiagram`;
   - output Z coordinates are set to zero in the output object's local mesh data;
   - the source object's transform is copied to the diagram object;
   - `Edges` reports edge count; `Faces` reports polygon count.

Important behavior:

- Voronoi topology is 2D. Z values are only used during duplicate/same-XY filtering and are not preserved in the output geometry.
- The source operator expands the point extent by a hardcoded 5% XY buffer before clipping the Voronoi edges/polygons.
- `Faces` output uses uncluttered polygon vertex lists suitable for mesh faces, not duplicate closing vertices.

## 4. Imported Contours to TIN to Terrain Analysis Material

This is a common integrated workflow after contour/vector import.

1. Use the vector sub-skill to import contour or elevation-bearing geometry. Ensure elevation has become Blender Z coordinates or mesh vertex heights.
2. If the import produced curves/lines rather than a point mesh, convert or sample them into mesh vertices. Keep only the terrain sample mesh selected for tesselation.
3. Run the point-cloud validator against the same exported/sampled XYZ points if available, or inspect the mesh for duplicate XY stacks and colinear-only samples.
4. Select the point mesh and run `bpy.ops.tesselation.delaunay()`.
5. Make the resulting `TIN` active.
6. Run **GIS > Nodes > Terrain analysis** or:

   ```python
   bpy.ops.analysis.nodes()
   ```

7. The operator creates/updates terrain analysis materials:
   - `Height_<object name>`: appended to the active object and assigned to all faces;
   - `Slope`: created or rebuilt for slope visualization;
   - `Aspect`: created or rebuilt for aspect visualization;
   - a `Normalize` node group used by height scaling.
8. In the Shader/Node Editor, select the color ramp node in the material you want to tune. Use the Reclassify panel/operators described in [operator-reference.md](operator-reference.md).

Recovery notes:

- Run `analysis.nodes` only after a valid terrain mesh exists. The operator uses mesh polygons/material slots and active object bounds.
- If the material appears flat, verify the active object has meaningful Z range for height, non-flat normals for slope/aspect, and that the render engine/view mode can display material colors.
- If the Reclassify panel does not appear, open the Node Editor, select a `ShaderNodeValToRGB` color ramp node, and refresh the panel.

## 5. Drop Selected Objects onto Active Ground

Goal: project selected objects downward onto the active terrain/ground object.

1. In Object Mode, select the ground object and every object to drop.
2. Make the ground object the **active** object. It should usually be a mesh terrain object for reliable raycasting.
3. Run **GIS > Object > Drop** or call:

   ```python
   bpy.ops.object.drop(align=False, useOrigin=False)
   bpy.ops.object.drop(align=True, axisAlign="Z", useOrigin=False)
   bpy.ops.object.drop(useOrigin=True)
   ```

4. Options:
   - `useOrigin=False`: use each object's lowest mesh vertex in world coordinates as the drop point;
   - `useOrigin=True`: drop each object origin; use this for non-mesh objects or when origin placement is the intended contact point;
   - `align=True`: rotate dropped objects to the hit normal;
   - `axisAlign`: with `align=True`, constrain alignment to `N`, `X`, `Y`, or `Z` behavior from the redo panel.
5. Expected result: each non-ground selected object with a raycast hit moves vertically onto the active object. Objects without a hit are skipped and logged.

Recovery notes:

- If the operator is disabled, ensure Object Mode, at least two selected objects, and an active object of an accepted object type.
- If objects do not move, confirm their XY coordinates overlap the active ground object's bounding area.
- If a non-mesh object errors or logs that it works only with center/origin behavior, rerun with `useOrigin=True`.
- If objects drop to the wrong surface, the wrong object is active. Re-select and set the terrain as active.

## 6. Longitude/Latitude Mesh to Earth Sphere

Goal: transform mesh vertices whose world X/Y coordinates are longitude/latitude degrees into a sphere-like globe.

1. Ensure selected mesh vertices represent longitude in X and latitude in Y, in degrees.
2. Keep mesh dimensions within longitude width <= 360 and latitude height <= 180. Oversized objects are skipped with warnings.
3. Select one or more mesh objects.
4. Run **GIS > Mesh > lonlat to sphere** or:

   ```python
   bpy.ops.earth.sphere(radius=100)
   ```

5. Expected result: selected mesh vertices are rewritten in-place to spherical XYZ positions. Non-mesh objects are skipped.

Recovery notes:

- This operator does not establish CRS. Reproject projected coordinates to lon/lat first using the georeferencing/CRS workflow.
- Apply or simplify transforms if object matrices make longitude/latitude interpretation confusing; the operator reads world coordinates and writes inverse-transformed local coordinates.
- The output is a visualization transform, not a precision geodesy operation.

## 7. Earth Curvature Correction for Viewshed-style Terrain

Goal: lower terrain vertices according to distance from the scene cursor, approximating earth curvature.

1. Place the 3D cursor at the viewpoint/reference location in the terrain's XY plane.
2. Make the target terrain mesh active.
3. Run **GIS > Mesh > Earth curvature correction** or:

   ```python
   bpy.ops.earth.curvature()
   ```

4. Expected result: each vertex Z is decreased by `sqrt(6378137^2 + d^2) - 6378137`, where `d` is the XY distance from the 3D cursor.

Recovery notes:

- The operator requires an active mesh object.
- It compares the scene cursor XY to vertex XY. For best results, use terrain with clear object transforms or apply transforms before correction.
- This is destructive to vertex Z values; duplicate the terrain before applying if the original elevations must be preserved.

## 8. Terrain Analysis Reclassification

Use this after `analysis.nodes` has created the materials and you have selected a color ramp node in the Node Editor.

Common actions:

```python
bpy.ops.reclass.list_refresh()
bpy.ops.reclass.list_add()
bpy.ops.reclass.list_rm()
bpy.ops.reclass.list_clear()
bpy.ops.reclass.switch_interpolation()
bpy.ops.reclass.flip()
bpy.ops.reclass.auto(autoReclassMode="CLASSES_NB", value=6)
bpy.ops.reclass.quick_gradient(colorSpace="RGB", method="LINEAR", nbColors=5)
bpy.ops.reclass.svg_gradient(colorSpace="RGB", method="LINEAR", fitGradient=True)
bpy.ops.reclass.export_svg(name="my_gradient", gradientType="SELF_STOPS")
```

Most reclassification operators are designed for interactive Node Editor context; prefer UI use when context overrides are not already prepared.

Suggested reclassification sequence:

1. Select the target terrain object and active material.
2. Open the Shader/Node Editor.
3. Select the color ramp node in the Height, Slope, or Aspect material.
4. In the Reclassify panel, set `analysisMode` to `HEIGHT`, `SLOPE`, or `ASPECT` so the value labels match the target analysis.
5. Use list add/remove/clear/refresh to manage stops, or `reclass.auto` for equal interval, quantile, one-dimensional k-means natural breaks, fixed class count, target step, or aspect bins.
6. Use quick or SVG gradient presets to recolor existing stops.
7. Switch interpolation to constant for discrete classes or linear for continuous ramps.

Key limits:

- Blender color ramps are limited to 32 colors/stops; several reclassification operators cancel when requested classes reach that limit.
- Quantile and k-means modes need enough mesh values for the requested number of classes.
- Packaged SVG gradient presets are loaded from the installed BlenderGIS add-on assets; if the add-on assets are missing, the preset list is empty and `reclass.svg_gradient` cancels.

# Terrain Mesh and Analysis Troubleshooting

## Fast Triage

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `tesselation.delaunay` or `tesselation.voronoi` reports `Selection is empty or too much object selected`. | Not exactly one selected object. | Switch to Object Mode, deselect everything, select only the point-cloud mesh, and rerun. |
| Tesselation reports `Selection isn't a mesh`. | Selected object is a curve, empty, font, image plane, or other non-mesh object. | Convert/import to a mesh point-cloud object first. Import workflow details belong to the vector or raster/DEM sub-skill. |
| Tesselation reports `Not enough points`. | Fewer than three unique XY points remain after duplicate collapse. | Run [../scripts/validate_point_cloud.py](../scripts/validate_point_cloud.py); remove duplicate XY stacks or add more points. |
| Tesselation reports `Points are colinear` or creates unusable geometry. | All useful points lie on one XY line. | Add non-colinear sample points, triangulate a broader contour/DEM area, or fix a bad import/sampling step. |
| Voronoi output is flat at Z=0. | Expected behavior: Voronoi is 2D. | Use Delaunay for terrain Z surfaces; use Voronoi for planar cells/edges. |
| `object.drop` is disabled. | Poll requires Object Mode, at least two selected objects, and an active object of an accepted type. | Select the ground and objects to drop, make ground active, and retry in Object Mode. |
| Dropped object does not move; log says it did not hit the active object. | Vertical ray at the object's XY location does not intersect the active ground. | Check XY overlap, active ground object, transforms, and ground mesh extent. |
| Objects drop to the wrong surface. | Wrong active object. | Re-select all target objects, then make the intended terrain/ground active last. |
| Non-mesh object fails during drop. | `useOrigin=False` tries to inspect mesh vertices for the lowest point. | Rerun `object.drop(useOrigin=True)` or convert the object to mesh. |
| `earth.sphere` skips an object. | Non-mesh object, no selection, or object dimensions exceed lon/lat bounds. | Select mesh objects only; ensure world X longitude span <= 360 and world Y latitude span <= 180. |
| `earth.curvature` cancels. | No active object or active object is not a mesh. | Make the target terrain mesh active; place 3D cursor at the viewpoint. |
| `analysis.nodes` creates materials but colors look wrong/flat. | Active terrain lacks useful Z/normals, material not assigned, or viewport/render mode hides material output. | Use a real TIN/terrain mesh, check Z range and normals, assign the intended material, and view with material/rendered shading. |
| Reclassify panel does not appear. | Active Node Editor node is not a `ShaderNodeValToRGB` color ramp. | Open the Shader/Node Editor, select the Height/Slope/Aspect color ramp node, then run `reclass.list_refresh()`. |
| SVG gradient presets are missing. | Installed add-on package lacks `rsrc/gradients/*.svg` or cannot read the asset directory. | Reinstall/repair the add-on package. The expected preset names are listed in [operator-reference.md](operator-reference.md). |

## Point Cloud Validation Failures

Run the bundled helper before tesselation:

```bash
python sub-skills/terrain-mesh-and-analysis/scripts/validate_point_cloud.py points.xyz
```

Interpretation:

- `duplicate_xyz_count > 0`: exact duplicate XYZ rows were found. BlenderGIS can ignore duplicates, but they are usually a data hygiene issue.
- `z_colinear_duplicate_count > 0`: at least two rows share XY but differ in Z. BlenderGIS collapses these to one XY location for legacy tesselation, so terrain information may be lost.
- `unique_xy_point_count < 3`: tesselation cannot create a triangle or diagram.
- `colinear_xy = true`: all unique XY points lie on a single line. The source operator explicitly checks all-X or all-Y cases; the helper also detects diagonal colinearity.

Recovery steps:

1. Remove exact duplicate rows.
2. Decide how to resolve same-XY/different-Z stacks: choose one elevation, average them, jitter only if scientifically justified, or revisit the import/sampling step.
3. Ensure at least three unique non-colinear XY locations remain.
4. Re-export/rebuild the Blender mesh and rerun Delaunay/Voronoi.

## Empty, Multiple, or Non-Mesh Selections

BlenderGIS mesh tesselation operators are strict:

- zero selected objects: cancel;
- more than one selected object: cancel;
- selected object is not `MESH`: cancel.

Do not keep imported source contours, helper empties, basemap planes, or previous TIN outputs selected when running tesselation. Select only the point-cloud mesh.

For `object.drop`, selection rules are different: select the active ground plus at least one object to drop. The active object is the ground, not a drop target.

## No Raycast Hit in Drop-to-Ground

`object.drop` casts a vertical ray down at each object's XY drop point from above the active ground object's bounding box. Misses are skipped, not fatal.

Common causes:

- the object is outside the ground's XY footprint;
- transforms or origins make the chosen drop point unexpected;
- the wrong active object is being raycast;
- the ground object has holes/non-manifold gaps at that XY location;
- the object should use origin dropping but `useOrigin=False` is using a different lowest vertex.

Recovery:

1. Make the intended ground object active.
2. Inspect top view for XY overlap.
3. Try `useOrigin=True`.
4. Apply transforms or simplify the ground mesh if raycasts remain inconsistent.
5. Check BlenderGIS logs if the UI gives no report.

## Wrong Active Object

Several operators use the active object rather than merely selected objects:

- `object.drop`: active object is the ground; all other selected objects are dropped.
- `earth.curvature`: active object is modified in-place.
- `analysis.nodes`: active object receives the Height material and supplies height bounds.
- `reclass.auto`: sampled values come from the active object for height/slope/aspect classification.

When results are surprising, verify the active object in the Outliner before changing parameters.

## Cycles Node and Material Assumptions

`analysis.nodes` is opinionated:

- it forces the render engine to `CYCLES`;
- it clears/rebuilds materials named `Height_<object>`, `Slope`, and `Aspect` if they already exist;
- it clears/rebuilds a node group named `Normalize`;
- it appends and assigns only the Height material to the active object's faces;
- it uses Diffuse BSDF nodes and color ramps for visualization.

Recovery:

- Duplicate important custom materials before running the operator.
- If you want Slope or Aspect visible, assign that material to the terrain or switch the active material slot manually.
- If height colors are flat, check that the active object's bounding box has different `zmin` and `zmax`.
- If slope/aspect colors are flat, check mesh normals and whether the terrain is actually planar.

## Reclassification and Gradient Asset Issues

Reclassification acts on the active color ramp node in the Node Editor. It is not enough to select the mesh or material in the viewport.

Common failures:

- `Ramp is limited to 32 colors`: reduce requested class/color count.
- `Too many classes`: requested classes exceed available data values or range.
- SVG preset dropdown empty: add-on gradient SVG assets are missing/unreadable.
- `reclass.export_svg` cannot write: add-on asset directory is not writable; choose a manual export workflow instead of relying on preset registration.
- Quantile/k-means classes look wrong: update `analysisMode`, select the correct active object, refresh the list, and verify mesh values.

Recommended recovery sequence:

1. Select the intended terrain object.
2. Select the intended material and color ramp node.
3. Set `analysisMode` to the correct target (`HEIGHT`, `SLOPE`, or `ASPECT`).
4. Run `reclass.list_refresh()`.
5. Apply auto/quick/SVG gradient changes.
6. Switch interpolation to constant for discrete classification or linear for continuous visualization.

## Earth Sphere and Curvature Data Assumptions

`earth.sphere` assumes world X/Y are longitude/latitude degrees, not projected meters. If the mesh came from a projected CRS, reproject or transform it before using this operator.

`earth.curvature` assumes the terrain XY coordinates and scene cursor XY are in compatible units, and it modifies Z in-place. Duplicate the object before applying if the uncorrected elevation must remain available.

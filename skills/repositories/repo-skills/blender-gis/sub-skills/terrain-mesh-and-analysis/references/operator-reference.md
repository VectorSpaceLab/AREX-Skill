# Terrain Mesh and Analysis Operator Reference

## Menu Placement

When BlenderGIS is enabled, the relevant menus are under **3D View > GIS**:

- **GIS > Mesh > Delaunay** -> `tesselation.delaunay`
- **GIS > Mesh > Voronoi** -> `tesselation.voronoi`
- **GIS > Mesh > lonlat to sphere** -> `earth.sphere`
- **GIS > Mesh > Earth curvature correction** -> `earth.curvature`
- **GIS > Object > Drop** -> `object.drop`
- **GIS > Nodes > Terrain analysis** -> `analysis.nodes`
- **Node Editor > Sidebar > Item > Reclassify** -> `reclass.*` operators when a color ramp node is active

## Tesselation Operators

| Operator | Purpose | Required context | Options | Output | Primary cancel/report cases |
| --- | --- | --- | --- | --- | --- |
| `bpy.ops.tesselation.delaunay()` | 2.5D Delaunay triangulation from selected point-cloud mesh vertices. | Object Mode; exactly one selected object; selected object must be `MESH`. | None. | New mesh/object named `TIN`; copies selected object's location/rotation/scale; output becomes active and selected. | Empty or multiple selection: `Selection is empty or too much object selected`; non-mesh: `Selection isn't a mesh`; legacy path can report `Not enough points` or `Points are colinear`. |
| `bpy.ops.tesselation.voronoi(meshType="Edges")` | 2D Voronoi edge diagram from selected point-cloud mesh vertices. | Object Mode; exactly one selected `MESH`. | `meshType`: `Edges` or `Faces`. | New mesh/object named `VoronoiDiagram`; output vertices have local Z = 0; source transform is copied; output becomes active and selected. | Same selection errors; `Not enough points`; `Points are colinear`. |
| `bpy.ops.tesselation.voronoi(meshType="Faces")` | 2D Voronoi polygon-cell mesh. | Same as above. | `meshType="Faces"`. | New `VoronoiDiagram` mesh with polygon faces; hardcoded 5% XY clipping buffer. | Same as above. |

Implementation behavior distilled from the add-on:

- Both tools consume the selected mesh's vertex coordinates as point samples.
- Duplicate filtering compares XY first. Exact duplicate XYZ rows are ignored; same XY with different Z is counted as a Z-colinear duplicate and reduced to one XY location for the legacy path.
- Minimum viable topology after duplicate collapse is three unique, non-colinear XY points.
- The legacy colinear check catches all-X-equal or all-Y-equal point sets; use [../scripts/validate_point_cloud.py](../scripts/validate_point_cloud.py) to also catch diagonal colinearity before entering Blender.
- Delaunay uses Blender's native constrained Delaunay implementation when available and otherwise uses the bundled Fortune/QGIS-derived Python implementation.
- Voronoi uses the add-on's Python Voronoi implementation and clips output to an extent buffered by 5% in X and Y.

## Object Drop Operator

### `bpy.ops.object.drop(align=False, axisAlign="N", useOrigin=False)`

Purpose: drop selected objects vertically onto the active object.

Poll/context requirements:

- Blender must be in Object Mode.
- At least two objects must be selected.
- An active object must exist.
- The active object type must be one of `MESH`, `FONT`, `META`, `CURVE`, or `SURFACE`; a mesh active ground is the reliable path because the implementation raycasts the active object.

Options:

| Option | Values/default | Meaning |
| --- | --- | --- |
| `useOrigin` | Boolean, default `False` | `False`: drop from each object's lowest mesh vertex in world coordinates. `True`: drop from each object origin; use this for non-mesh objects or origin-based placement. |
| `align` | Boolean, default `False` | If true, rotate dropped objects to the raycast hit normal. |
| `axisAlign` | `N`, `X`, `Y`, `Z` | Alignment behavior used when `align=True`; exposed as Normal/Ground X/Y/Z normal in the operator UI/redo panel. |

Execution behavior:

1. The active object is treated as ground and removed from the drop-object list if it is selected.
2. For each remaining selected object, the operator chooses an XY drop point from either the origin or lowest world-space mesh vertex.
3. It casts a vertical downward ray from above the active ground object's bounding box.
4. If a hit is found, the object is moved down to the hit location; if `align=True`, rotation is adjusted to the hit normal.
5. If no hit is found, that object is skipped and a log entry is written; the operator continues with other objects.

## Earth Mesh Operators

| Operator | Purpose | Context | Options | Output/side effects | Cancel/skip cases |
| --- | --- | --- | --- | --- | --- |
| `bpy.ops.earth.sphere(radius=100)` | Convert selected lon/lat mesh vertices to a sphere-like globe. | One or more selected objects; mesh objects expected. | `radius`: integer, default `100`, minimum `1`. | Rewrites selected mesh vertex coordinates in-place. Reads world X/Y as lon/lat degrees, writes inverse-transformed spherical XYZ into local mesh data. | No selected object cancels with `No selected object`; non-mesh objects are skipped; objects with dimensions width > 360 or height > 180 are skipped with warnings. |
| `bpy.ops.earth.curvature()` | Apply earth curvature correction for viewshed-style analysis. | Active object required and must be `MESH`; 3D cursor is the viewpoint/reference. | None. | Rewrites active mesh vertex Z in-place by subtracting curvature delta from distance to scene cursor XY. Uses earth radius `6378137` meters. | No active object: `No active object`; non-mesh active object: `Selection isn't a mesh`. |

Caution: both earth operators modify mesh data in-place. Duplicate the object first when preservation matters.

## Terrain Analysis Node Builder

### `bpy.ops.analysis.nodes()`

Purpose: create node material setups for height, slope, and aspect visualization.

Required context:

- Active object must exist and should be a mesh terrain object with polygons/material slots.
- The operator is designed for Cycles node materials and sets `scene.render.engine = 'CYCLES'`.

Created/updated data:

| Data-block | Behavior |
| --- | --- |
| `Height_<active object name>` material | Created or cleared/rebuilt with nodes; uses Geometry Position Z, a `Normalize` node group, active object Z bounds, a green-to-red color ramp, Diffuse BSDF, and Material Output. This material is appended to the active object and assigned to all faces. |
| `Normalize` node group | Created or cleared/rebuilt. Inputs: `val`, `min`, `max`; output: normalized `val`; implemented with subtract/divide math nodes. |
| `Slope` material | Created or cleared/rebuilt; uses Geometry True Normal Z, arccos, radians-to-degrees, divide-by-100 normalization, green-to-red color ramp, Diffuse BSDF, and Material Output. |
| `Aspect` material | Created or cleared/rebuilt; computes aspect from Geometry True Normal X/Y, normalizes to 0..1 over 0..360 degrees, uses a constant multi-stop compass color ramp, mixes flat surfaces to white, and outputs Diffuse BSDF. |

Important side effects:

- Existing materials with names `Height_<object>`, `Slope`, or `Aspect` are cleared/rebuilt.
- Existing node group named `Normalize` is cleared/rebuilt.
- Only the Height material is automatically appended and assigned to the active object. Assign or switch to Slope/Aspect manually if needed.
- The active selected node after each material build is its color ramp, enabling reclassification workflows.

## Reclassification Panel and Operators

The reclassification UI is a Node Editor side panel named **Reclassify**. It appears when the active node is a `ShaderNodeValToRGB` color ramp. Registration adds scene properties used by the panel:

- `scene.analysisMode`: `HEIGHT`, `SLOPE`, or `ASPECT`;
- `scene.uiListCollec` and `scene.uiListIndex`: color-ramp stop list state;
- `scene.colorRampPreview`: quick/SVG gradient preview colors.

| Operator | Purpose | Key options/values | Notes |
| --- | --- | --- | --- |
| `bpy.ops.reclass.list_refresh()` | Refresh UI list from active color ramp. | None. | Use after selecting another material/node or after manual ramp edits. |
| `bpy.ops.reclass.list_add()` | Add a stop midway after the selected stop. | None. | Cancels at 32 ramp stops: `Ramp is limited to 32 colors`. |
| `bpy.ops.reclass.list_rm()` | Remove selected stop. | None. | Leaves at least one stop. |
| `bpy.ops.reclass.list_clear()` | Clear ramp to a single first stop then refresh. | None. | Useful before rebuilding classes. |
| `bpy.ops.reclass.switch_interpolation()` | Toggle continuous/discrete visual classes. | None. | Switches color mode to RGB, then toggles interpolation between `CONSTANT` and `LINEAR`. |
| `bpy.ops.reclass.flip()` | Flip ramp colors. | None. | Reverses colors while keeping current stop positions. |
| `bpy.ops.reclass.auto(...)` | Auto-classify height/slope/aspect values. | `autoReclassMode`: `CLASSES_NB`, `EQUAL_STEP`, `TARGET_STEP`, `QUANTILE`, `1DKMEANS`, `ASPECT`; `value`: integer class/step parameter; `color1`, `color2`. | Uses active object's height, slope, or aspect values according to `analysisMode`; cancels for >=32 classes or too many classes for data size. |
| `bpy.ops.reclass.quick_gradient(...)` | Generate colors from a user-defined quick gradient. | `colorSpace`: `RGB` or `HSV`; `method`: `LINEAR`, `SPLINE`, `DISCRETE`, `NEAREST`; `fitGradient`; `nbColors` min 2/default 4. | Interactive dialog previews colors in `scene.colorRampPreview`. |
| `bpy.ops.reclass.svg_gradient(...)` | Apply one packaged SVG gradient preset. | `colorPresets`: enum index string; `colorSpace`; `method`; `fitGradient`. | Reads SVG presets from the installed add-on assets; cancels if no presets are available. |
| `bpy.ops.reclass.export_svg(...)` | Export current color ramp to an SVG preset. | `name`; `gradientType`: `SELF_STOPS` or `INTERPOLATE`; `makeDiscrete`; `colorSpace`; `method`; `n` default 5. | Writes into the installed add-on gradient asset directory; requires write access and changes the add-on's preset list. |

### Auto Reclass Modes

| Mode | Meaning | Main failure conditions |
| --- | --- | --- |
| `CLASSES_NB` | Fixed number of classes across the active mode's value range. | Requested classes >= 32; requested classes >= value range. |
| `EQUAL_STEP` | Stops every fixed value interval. | Derived class count >= 32. |
| `TARGET_STEP` | Stops aligned to a target interval grid. | Derived class count >= 32. |
| `QUANTILE` | Classes with approximately equal numbers of sampled mesh values. | Classes >= 32 or classes >= sampled values. |
| `1DKMEANS` | Natural breaks via one-dimensional k-means. | Classes >= 32 or classes >= sampled values. |
| `ASPECT` | Aspect direction classes around 0..360 degrees. | Classes >= 32. |

## Packaged SVG Gradient Presets

`reclass.svg_gradient` expects SVG files shipped with the installed BlenderGIS add-on under its own gradient resource directory. The skill does not copy those assets; the operator uses the add-on package's assets at runtime. The inspected add-on ships these preset basenames:

`GMT_dem4`, `GMT_panoply`, `Gummy-Kids`, `Horizon_1`, `Ribbon-Colors`, `Spectral_11`, `Sunrise`, `abyss`, `alarm.p1.0.5`, `bath_114`, `bhw3_05`, `ch05p151010`, `cyanotype-sodableach_01`, `esri-bolivia`, `esri-ecuador`, `esri-europe_7`, `esri-italy`, `esri-mojave`, `esri-utah_1`, `fs2009`, `gem-16`, `heat`, `nrwc`, `pm3d01`, `precip_11lev`, `reds_01`, `sepiared_01`, `smart`, `stern`, `temp_19lev`, `temperature`, `wiki-plumbago`.

If the SVG preset dropdown is empty, troubleshoot add-on packaging rather than the material node itself.

# Vector Data and OSM Workflows

## Purpose

Read this for practical BlenderGIS workflows involving shapefile import/export, local OSM XML import, Overpass query preflight, OSM tag preferences, and elevation/extrusion/object separation choices. For exact properties and edge-case operator behavior, use `operator-reference.md`. For recovery steps after failures, use `troubleshooting.md`.

## Common Prerequisites

1. Enable BlenderGIS and work in Blender object mode.
2. For workflows that depend on scene coordinates, inspect scene georeferencing first:
   - valid CRS is stored as scene custom property `SRID`;
   - projected origin is stored as `crs x` and `crs y`;
   - a broken partial scene must be fixed before import/export/query.
3. If the task is only preflighting an Overpass query, use `../scripts/build_overpass_query.py` from this sub-skill and do not open Blender or contact the network.
4. Decide whether geometry should be one combined mesh or many separate objects before import. Separation is more useful for per-feature attributes/names but can be slow for large vector datasets.

## Workflow: Import a Shapefile Interactively

Use this when a user has a `.shp` file and wants BlenderGIS to present available DBF fields.

1. Open `View3D > GIS > Import > Shapefile (.shp)`.
2. Select the `.shp` file. BlenderGIS runs `importgis.shapefile_file_dialog`, validates the path, then opens `importgis.shapefile_props_dialog`.
3. Choose the coordinate reference behavior:
   - If the scene is not georeferenced, choose the shapefile CRS from predefined CRS entries. The import operator will set the scene CRS and initialize the projected origin to the shapefile bbox center.
   - If the scene is georeferenced and the shapefile CRS is the same as the scene CRS, leave reprojection disabled.
   - If the scene is georeferenced and the shapefile CRS differs, enable `Specifiy shapefile CRS` and choose the source shapefile CRS so geometry is reprojected to the scene CRS.
4. Choose elevation source:
   - `GEOM` (default): use Z coordinates from `PointZ`, `PolyLineZ`, or `PolygonZ`; otherwise z=0.
   - `NONE`: force flat z=0.
   - `FIELD`: choose a numeric/logical DBF elevation field.
   - `OBJ`: choose an existing mesh object to raycast onto for z.
5. Optional extrusion:
   - Enable `Extrusion from field` only when the DBF contains a numeric height/extrusion field.
   - Choose `Extrude along` = `Z` for vertical offsets or `NORMAL` for polygon face-normal extrusion. Points and lines still translate along z.
6. Optional object separation:
   - Leave `Separate objects` off for one combined mesh.
   - Turn it on to create a collection named after the shapefile and one object per feature.
   - If separated objects should have meaningful names, enable `Object name from field` and choose a DBF name field.
7. Run import and validate:
   - Confirm imported object(s) appear near the intended scene location.
   - Check that the scene CRS/origin is now set if the scene was previously empty.
   - For separated imports, inspect one object and confirm DBF fields were copied to Blender custom properties.
   - For extrusion, verify at least one feature has positive height and visible vertical faces/points/edges.

### Suggested Field Decision Table

| User goal | Elevation choice | Extrusion choice | Separation/name choice | Validation |
| --- | --- | --- | --- | --- |
| Flat parcels/building footprints | `NONE` or `GEOM` when source is 2D | none | optional | z values should be 0 unless source has Z and `GEOM` was used. |
| Contours/points with known elevation | `FIELD` with numeric elevation field | none | optional | invalid or nonnumeric fields cancel; spot-check z values in Blender. |
| Extruded footprints with height column | usually `NONE`, `FIELD`, or `OBJ` depending base elevation | numeric height/extrusion field | often separate + name field | field must exist and be numeric/logical; positive values extrude. |
| Features draped on terrain | `OBJ` | optional | optional | elevation object must be an existing mesh and should cover the vector extent. |
| Per-feature editing/export later | any | any | `Separate objects` true, optional name field | each object should preserve DBF attributes as custom properties. |

## Workflow: Script a Shapefile Import

Use direct `bpy.ops.importgis.shapefile` calls only when all fields and CRS are already known. This avoids the interactive field dialog.

```python
import bpy

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.importgis.shapefile(
    filepath='/path/to/buildings.shp',
    shpCRS='EPSG:3857',
    elevSource='FIELD',          # NONE, GEOM, FIELD, or OBJ
    fieldElevName='BASE_Z',      # only valid with elevSource='FIELD'
    objElevName='',              # only valid with elevSource='OBJ'
    fieldExtrudeName='HEIGHT_M', # empty string disables extrusion
    fieldObjName='NAME',         # meaningful only with separateObjects=True
    extrusionAxis='Z',           # Z or NORMAL
    separateObjects=True,
)
```

Preflight before scripting:

- Confirm file path exists and includes the usual shapefile sidecars needed by the pyshp reader/writer workflow (`.shp`, `.shx`, `.dbf`; `.prj` is useful but CRS is still passed explicitly).
- Confirm DBF field spelling exactly; field lookups are case-sensitive because they compare names from the shapefile field table.
- Confirm elevation/extrusion fields are DBF types `N`, `F`, or `L`.
- Confirm `objElevName` names an existing mesh when `elevSource='OBJ'`.
- Confirm the scene is not broken; route broken CRS/origin repair to the georeferencing sub-skill.

## Workflow: Export Mesh Objects to Shapefile

Use this when a user has mesh objects in Blender and wants Shapefile output.

1. Ensure object mode.
2. Decide source objects:
   - `SELECTED`: select one or more mesh objects.
   - `COLLEC`: choose a collection; only mesh objects in that collection are exported.
3. Run `View3D > GIS > Export > Shapefile (.shp)` (`exportgis.shapefile`).
4. Choose `Feature type`:
   - `POINTZ` for vertices / multipoints.
   - `POLYLINEZ` for edges / multipart lines.
   - `POLYGONZ` for faces / multipart polygons.
5. Choose export `Mode`:
   - `OBJ2FEAT`: one multipart feature per object.
   - `MESH2FEAT`: one feature per primitive.
6. Choose the output `.shp` path and run export.
7. Validate output:
   - `.shp`, `.shx`, `.dbf` should exist.
   - `.prj` is written only when the scene is georeferenced and CRS-to-WKT conversion succeeds.
   - DBF should include `objId` plus exportable object custom properties, with names truncated to 8 characters by this implementation.
   - Coordinates should include scene projected origin offsets when the scene is georeferenced.

If export reports `Selection is empty or does not contain any mesh`, select mesh objects or switch `Objects` to a populated collection.

## Workflow: Import a Local OSM XML File

Use this when a user already has `.osm` XML and wants it converted into Blender geometry without live Overpass access.

1. Open `View3D > GIS > Import > Open Street Map xml (.osm)` (`importgis.osm_file`).
2. Select the `.osm` file.
3. Choose shared OSM options:
   - `Type`: default is ways only. Enable nodes and/or relations if needed.
   - `Tags`: filter by tags from BlenderGIS preferences, or leave filters empty to group all imported types.
   - `Elevation from object`: enable only if a mesh ground object exists and covers the OSM extent.
   - `Buildings extrusion`: enabled by default; configure default height, level height, and random height threshold.
   - `Separate objects`: enable for per-element objects and custom properties; leave off for grouped meshes and vertex groups.
4. Run import.
5. Validate:
   - If the scene had no CRS, BlenderGIS should choose a UTM EPSG CRS from the OSM XML bounds center.
   - If the scene had no projected origin, BlenderGIS should set it from the OSM bounds center.
   - If `separate` is true, an `OSM` collection should exist and objects should carry `id` and OSM tags as custom properties.
   - If `separate` is false, expect grouped objects such as `Nodes`, `Ways`, `Areas`, or tag-specific names such as `Areas:building` depending on filters.

Important local XML caveat: the parser expects OSM data with enough referenced nodes for ways and useful bounds. Missing nodes can raise vendored Overpass `DataIncomplete` behavior or produce incomplete geometry.

## Workflow: Preflight an Overpass Query Without Network

Use the bundled helper when a user asks for a bbox/tag/type query but does not want to hit Overpass yet, or when future verification needs assertion-backed query shape checks.

From this sub-skill directory or any working directory:

```bash
python scripts/build_overpass_query.py \
  --bbox=-74.02,40.70,-73.95,40.78 \
  --tag building \
  --tag highway \
  --type way \
  --format xml
```

Equivalent component form:

```bash
python scripts/build_overpass_query.py \
  --west -74.02 --south 40.70 --east -73.95 --north 40.78 \
  --tag building --type node --type way --format json
```

Expected characteristics:

- Input bbox order is `west,south,east,north` or separate `--west --south --east --north`.
- Output bbox order follows Overpass/BlenderGIS queryBuilder: `south,west,north,east`.
- Repeated `--tag` values become tag filters such as `node[building]` and `way[building]`.
- Repeated `--type` values choose element families. If no type is supplied, the helper defaults to nodes, ways, and relations. If no tag is supplied, it follows the source helper default of `building` and `highway`.
- The helper prints only the QL string; it makes no network request.

Use `--format xml` when comparing with BlenderGIS `importgis.osm_query`, because the live operator calls `queryBuilder(..., format='xml')`. Use `--format json` when emulating the source helper default.

## Workflow: Query Overpass from Current BlenderGIS Extent

Use this only when a live network request is intended and the user accepts Overpass service limits.

1. Make sure the scene is georeferenced. If not, initialize CRS/origin first using the georeferencing sub-skill or by importing a georeferenced dataset.
2. Define extent by one of these methods:
   - Select exactly one active mesh object; BlenderGIS uses that object's bbox.
   - Or switch the 3D viewport to orthographic top view; BlenderGIS uses the visible top-view bbox.
3. Keep the extent small. BlenderGIS cancels when the bbox width or height in scene CRS exceeds `20000`.
4. Open `View3D > GIS > Web geodata > Get OSM` (`importgis.osm_query`).
5. Choose `Type`, `Tags`, elevation object, building extrusion, and separation options.
6. Run query. BlenderGIS will:
   - convert the scene/query bbox to EPSG:4326;
   - build Overpass QL with XML output;
   - send it to the selected Overpass server in preferences;
   - build meshes in the scene CRS.
7. Validate imported data:
   - grouped/separate outputs as in local OSM import;
   - building heights from OSM `height`, then `building:levels * levelHeight`, then randomized/default height;
   - vertex groups or tag collections corresponding to selected tags.

Before running a large or ambiguous live query, preflight with `scripts/build_overpass_query.py`, narrow the bbox/tags/types, and consider switching Overpass server only if the selected server is unavailable.

## Workflow: Configure OSM Tags and Overpass Servers

Open BlenderGIS preferences through `bgis.pref_show` or `View3D > GIS > Preferences`.

OSM filter tags:

- Default tags are `building`, `highway`, `landuse`, `leisure`, `natural`, `railway`, `waterway`.
- Add/edit/remove/reset with `bgis.add_osm_tag`, `bgis.edit_osm_tag`, `bgis.rmv_osm_tag`, `bgis.reset_osm_tags`.
- Tags may be simple keys (`building`) or key/value filters (`landuse=forest`) because the importer tests both tag keys and `key=value` strings.

Overpass servers:

- Defaults include overpass-api.de, overpass.openstreetmap.fr, and overpass.kumi.systems endpoints.
- Add/edit/remove/reset with `bgis.add_overpass_server`, `bgis.edit_overpass_server`, `bgis.rmv_overpass_server`, `bgis.reset_overpass_server`.
- Do not rotate servers aggressively after rate limits. Reduce request size and wait first; see `troubleshooting.md`.

## Workflow: Building Extrusion Choices for OSM

BlenderGIS extrudes only closed ways that are classified as areas and include the tag key `building`.

Height decision order:

1. If OSM tag `height` exists and parses as an integer or float, use that value.
2. Else if tag `building:levels` exists and parses as an integer, use `building:levels * levelHeight`.
3. Else use a random integer between `defaultHeight - randomHeightThreshold` and `defaultHeight + randomHeightThreshold`, with the minimum clipped to zero.

Practical guidance:

- Set `randomHeightThreshold=0` for deterministic default heights.
- Use `levelHeight=3` unless a local convention justifies another per-level height.
- If the base should follow terrain, enable `Elevation from object` and choose the ground mesh; BlenderGIS will make a flat roof at `max(base z) + height` for extruded features.
- If later terrain analysis or drop-to-ground operations are needed, route those steps to the terrain sub-skill rather than duplicating them here.

## Advanced Workflow: Shapefile Elevation, Extrusion, and Names

Use this pattern for building footprints or similar polygon data with separate base elevation, height, and display-name fields. The same pattern also applies to points and polylines, but polygon footprints make extrusion easiest to inspect.

1. Preflight the DBF fields and confirm exact field names such as `BASE_Z`, `HEIGHT_M`, and `NAME`.
2. Confirm `BASE_Z` and `HEIGHT_M` are numeric/logical DBF field types.
3. Import with:
   - `elevSource='FIELD'`;
   - `fieldElevName='BASE_Z'`;
   - `fieldExtrudeName='HEIGHT_M'`;
   - `fieldObjName='NAME'`;
   - `separateObjects=True`;
   - `extrusionAxis='Z'` unless face-normal extrusion is specifically desired.
4. Validate that the output is a collection named after the shapefile with one object per feature, per-object custom properties, names from `NAME`, z from `BASE_Z`, and extrusion from positive `HEIGHT_M` values.
5. If any field is missing or nonnumeric, cancel and repair the data table rather than accepting a silently flat import.

## Advanced Workflow: Offline Overpass Query Preflight

Use this pattern before making a live Overpass request for a small bbox with tags `building` and `highway`, types `node` and `way`, and XML output:

```bash
python scripts/build_overpass_query.py \
  --bbox=-74.02,40.70,-73.95,40.78 \
  --tag building --tag highway \
  --type node --type way \
  --format xml
```

Inspect the printed query before sending anything to a public service:

- The bbox is accepted as west/south/east/north and emitted in Overpass south/west/north/east order.
- The query should include `node[building]`, `node[highway]`, `way[building]`, `way[highway]`, and way recursion `>;`.
- If the query is broader than needed, narrow bbox, tags, or types before using `importgis.osm_query`.
- The helper does not contact the network, so it is safe for offline planning and reproducible command construction.

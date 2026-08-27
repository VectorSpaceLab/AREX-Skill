# Vector and OSM Operator Reference

## Purpose

Read this when you need exact BlenderGIS operator IDs, properties, accepted option values, defaults, and output behavior for vector data and OSM workflows. Operator facts are distilled from the BlenderGIS add-on registration, preferences, shapefile import/export operators, OSM import/query operators, `GeoScene`, and the vendored Overpass client.

## Menu Placement

- `View3D > GIS > Import > Shapefile (.shp)` calls `importgis.shapefile_file_dialog`.
- `View3D > GIS > Import > Open Street Map xml (.osm)` calls `importgis.osm_file`.
- `View3D > GIS > Export > Shapefile (.shp)` calls `exportgis.shapefile`.
- `View3D > GIS > Web geodata > Get OSM` calls `importgis.osm_query`.
- `View3D > GIS > Preferences` calls `bgis.pref_show`, where OSM tags and Overpass servers are edited.

All four data operators are object-mode operators. Scripted calls should run from object mode and should not expect successful execution from edit/sculpt/paint modes.

## Scene Georeferencing Contract Used by These Operators

The vector and OSM operators use `GeoScene` state from Blender scene custom properties:

- CRS key: `SRID`.
- projected origin keys: `crs x`, `crs y`.
- optional lon/lat keys: `longitude`, `latitude`.
- `GeoScene.isGeoref` is true only when CRS is valid and projected origin is set.
- `GeoScene.isBroken` is true for invalid CRS, an origin without CRS, or CRS plus lon/lat without projected origin.

Shapefile import can initialize a non-georeferenced scene from the shapefile CRS and data bbox. Shapefile export can also export ungeoreferenced meshes, but no `.prj` file is written. OSM query requires a fully georeferenced current extent. Local OSM XML import can initialize CRS/origin from XML bounds, but still cancels if the scene is already in a broken partial georef state.

## `importgis.shapefile_file_dialog`

Interactive file-selection entry point for shapefile import.

- Class: `IMPORTGIS_OT_shapefile_file_dialog`.
- `bl_idname`: `importgis.shapefile_file_dialog`.
- `bl_label`: `Import SHP`.
- File extension/filter: `.shp`, `*.shp`.
- Important property:
  - `filepath`: selected `.shp` path.
- Behavior:
  1. Opens a file selector.
  2. Verifies the selected path exists.
  3. Calls `importgis.shapefile_props_dialog('INVOKE_DEFAULT', filepath=...)` so fields can be loaded and import options chosen.
- Failure signal: reports `Invalid filepath` when the selected path does not exist.

## `importgis.shapefile_props_dialog`

Interactive property dialog that reads DBF fields, lets the user choose CRS/elevation/extrusion/name fields, and then calls `importgis.shapefile`.

- Class: `IMPORTGIS_OT_shapefile_props_dialog`.
- `bl_idname`: `importgis.shapefile_props_dialog`.
- Important properties:
  - `filepath`: `.shp` path passed from the file dialog.
  - `reprojection`: boolean, shown when the scene is partially georeferenced; use when the shapefile CRS differs from the scene CRS.
  - `shpCRS`: CRS chosen from BlenderGIS predefined CRS preferences.
  - `vertsElevSource`: enum, default `GEOM`; values:
    - `NONE`: flat geometry at z=0.
    - `GEOM`: use Shapefile Z geometry if the shape type is `PointZ`, `PolyLineZ`, or `PolygonZ`; otherwise z=0.
    - `FIELD`: read z from a DBF numeric/logical field selected in `fieldElevName`.
    - `OBJ`: raycast vertices onto an existing mesh object selected in `objElevLst`.
  - `objElevLst`: mesh object to use when `vertsElevSource == 'OBJ'`.
  - `fieldElevName`: DBF field for elevation when `vertsElevSource == 'FIELD'`.
  - `useFieldExtrude`: boolean enabling extrusion from a DBF field.
  - `fieldExtrudeName`: DBF field used as extrusion offset when `useFieldExtrude` is true.
  - `extrusionAxis`: enum values `Z` or `NORMAL`.
  - `separateObjects`: boolean; when true, each feature becomes a separate object in a new collection.
  - `useFieldName`: boolean; when true with `separateObjects`, object names come from `fieldObjName`.
  - `fieldObjName`: DBF field for object names.
- Field list behavior:
  - DBF `DeletionFlag` is excluded.
  - Elevation and extrusion field validation happens in `importgis.shapefile`; fields must exist and must have DBF type `N`, `F`, or `L` for numeric/logical values.
- CRS behavior:
  - If `GeoScene.isBroken`, the dialog cancels with `Scene georef is broken, please fix it beforehand`.
  - If the scene is already georeferenced and `reprojection` is false, the shapefile CRS passed to the import operator is the scene CRS.
  - If the scene is not georeferenced, `shpCRS` is required and later becomes the scene CRS.

## `importgis.shapefile`

Scriptable shapefile import operator. Use this only after you know the CRS and field names; otherwise use the file dialog route.

- Class: `IMPORTGIS_OT_shapefile`.
- `bl_idname`: `importgis.shapefile`.
- `bl_options`: `UNDO`.
- Poll: object mode only.
- Properties:
  - `filepath`: `.shp` path.
  - `shpCRS`: CRS string such as `EPSG:3857`, `EPSG:4326`, another `AUTH:code`, or a Proj4 string accepted by the configured reprojection engine.
  - `elevSource`: string, default `GEOM`; expected values are `NONE`, `GEOM`, `FIELD`, `OBJ`.
  - `objElevName`: mesh object name used when `elevSource == 'OBJ'`.
  - `fieldElevName`: DBF field name for z values when `elevSource == 'FIELD'`.
  - `fieldExtrudeName`: DBF field name for extrusion offset; leave empty to disable extrusion.
  - `fieldObjName`: DBF field name for object names when `separateObjects` is true.
  - `extrusionAxis`: enum `Z` or `NORMAL`; polygons can extrude along face normal, points/lines always translate along z.
  - `separateObjects`: boolean, default false.
- Supported shape types:
  - `Point`, `PolyLine`, `Polygon`, `PointZ`, `PolyLineZ`, `PolygonZ`.
  - The importer rejects multipoint, M variants, and multipatch shapes.
- Output behavior:
  - Non-separated import produces one mesh object named from the shapefile basename.
  - Separated import creates a collection named from the shapefile basename and one mesh object per feature.
  - Separate objects receive DBF fields as custom properties. Numeric (`N`, `F`) fields are cast to float; other fields are assigned as strings/bytes as read by the shapefile library.
  - With `fieldObjName`, object names come from that DBF value; blank byte values fall back to an empty string and may need manual cleanup in Blender.
  - When not separated and `fieldExtrudeName` is set, the operator builds per-feature extrusions in a temporary bmesh and joins them into one final bmesh.
  - If BlenderGIS preference `mergeDoubles` is true, duplicate vertices are merged at distance `0.0001` for the final non-separated bmesh.
  - If preference `adjust3Dview` is true, the 3D view clip/grid is adjusted to the imported bbox.
- CRS/reprojection behavior:
  - If the scene has no CRS, `shpCRS` is set as scene CRS.
  - If scene CRS differs from `shpCRS`, data and bbox are reprojected before placing geometry.
  - If the selected reprojection engine is the online EPSG.io path and the shapefile has more than 100 records, import cancels and asks for GDAL or pyproj.
  - If the scene has no origin, the importer sets projected origin to the shapefile bbox center.
- Geometry behavior:
  - Coordinates are shifted by the scene projected origin before creating Blender mesh vertices.
  - Polygon rings are reversed to match Blender face orientation; polygon holes are not fully handled by this importer.
  - Field extrusion only applies when the field value can be parsed and is positive; null or unparsable extrusion values are logged and treated as zero.
  - Elevation field parse failures are logged and use z=0 for that feature.

### Scripted Shapefile Import Pattern

Use in a Blender Python context after enabling BlenderGIS:

```python
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.importgis.shapefile(
    filepath='/data/buildings.shp',
    shpCRS='EPSG:3857',
    elevSource='FIELD',
    fieldElevName='ELEV_M',
    fieldExtrudeName='HEIGHT_M',
    fieldObjName='NAME',
    extrusionAxis='Z',
    separateObjects=True,
)
```

When using this pattern, replace field names with fields verified from the DBF table. Do not pass `fieldElevName` unless `elevSource='FIELD'`; do not pass `objElevName` unless the mesh object exists and `elevSource='OBJ'`.

## `exportgis.shapefile`

Exports Blender mesh objects to ESRI Shapefile.

- Class: `EXPORTGIS_OT_shapefile`.
- `bl_idname`: `exportgis.shapefile`.
- File extension/filter: `.shp`, `*.shp`.
- Poll: object mode only.
- Properties:
  - `filepath`: output `.shp` path from `ExportHelper`.
  - `exportType`: enum values:
    - `POINTZ`: point or multipoint output.
    - `POLYLINEZ`: line output.
    - `POLYGONZ`: polygon output.
  - `objectsSource`: enum values:
    - `SELECTED` (default): export selected mesh objects.
    - `COLLEC`: export all mesh objects from `selectedColl`.
  - `selectedColl`: collection name when `objectsSource == 'COLLEC'`.
  - `mode`: enum values:
    - `OBJ2FEAT` (default): one multipart feature per object.
    - `MESH2FEAT`: one feature per mesh primitive (each vertex for points, each edge for lines, each face for polygons).
- Output files:
  - `.shp`, `.shx`, `.dbf` are written by the shapefile writer.
  - `.prj` is written only when the scene is georeferenced and the scene CRS can be converted to WKT.
- CRS/georef behavior:
  - If the scene is georeferenced, object world coordinates are offset by scene projected origin (`crs x`, `crs y`) before writing geometry.
  - If the scene is not georeferenced, xy offsets are zero and no `.prj` is written.
  - If the scene georef is broken, export cancels.
- Attribute behavior:
  - A numeric `objId` field is always created.
  - Blender custom properties from exported objects are mapped to DBF fields.
  - Field names are truncated to 8 characters in this implementation.
  - Strings that parse as numbers become numeric fields; nonnumeric strings become character fields; unsupported property types are skipped.
  - Numeric DBF fields are written with length 20 and decimals 0 for ints or 5 for floats.
  - Missing custom properties for a field are written as nulls.
- Geometry behavior:
  - `POINTZ` + `MESH2FEAT`: each vertex becomes one point feature.
  - `POINTZ` + `OBJ2FEAT`: all vertices of an object become one multipoint feature.
  - `POLYLINEZ` + `MESH2FEAT`: each edge becomes one line feature.
  - `POLYLINEZ` + `OBJ2FEAT`: all edges of an object are written as a multipart line feature.
  - `POLYGONZ` + `MESH2FEAT`: each face becomes one polygon feature.
  - `POLYGONZ` + `OBJ2FEAT`: all faces of an object are written as a multipart polygon feature.
  - Polygon vertex order is reversed for Shapefile face orientation.

## OSM Shared Options (`OSM_IMPORT` mixin)

Both `importgis.osm_file` and `importgis.osm_query` inherit these options:

- `featureType`: enum flag, default `{'way'}`; allowed values:
  - `node`: import nodes that are not already part of ways.
  - `way`: import ways.
  - `relation`: include relations/relationship grouping.
- `filterTags`: enum flag populated from BlenderGIS preference `osmTagsJson`. A feature passes when either a tag key or a `key=value` string matches.
- `useElevObj`: boolean; when true, z comes from raycasting onto `objElevLst` mesh.
- `objElevLst`: mesh object index used for elevation when `useElevObj` is true.
- `separate`: boolean, default false. When true, each OSM element becomes a separate object and may be organized into tag/relation collections. When false, elements are grouped into combined bmeshes such as `Nodes`, `Ways`, `Areas`, or tag-specific names.
- `buildingsExtrusion`: boolean, default true. Only closed ways whose tags include `building` are eligible for extrusion.
- `defaultHeight`: float, default `20`; used when an extrudable building lacks a parseable height or levels tag.
- `levelHeight`: float, default `3`; used to convert `building:levels` to height.
- `randomHeightThreshold`: int, default `0`; when default height is used, the final height is a random integer in `[defaultHeight - threshold, defaultHeight + threshold]` with a floor at zero.

OSM area classification treats closed ways as polygons when they include tags from this key list: `aeroway`, `amenity`, `boundary`, `building`, `craft`, `geological`, `historic`, `landuse`, `leisure`, `military`, `natural`, `office`, `place`, `shop`, `sport`, `tourism`.

## `importgis.osm_file`

Imports a local OpenStreetMap XML `.osm` file.

- Class: `IMPORTGIS_OT_osm_file`.
- `bl_idname`: `importgis.osm_file`.
- File extension/filter: `.osm`, `*.osm`.
- Important property:
  - `filepath`: selected local OSM XML file.
- Behavior:
  1. Populates OSM tag choices from preferences.
  2. Validates that the file exists.
  3. Switches to object mode when possible and deselects all objects.
  4. Cancels if `GeoScene.isBroken`.
  5. Parses XML through the bundled Overpass/overpy parser.
  6. Reads XML bounds and computes center lon/lat.
  7. If the scene has no CRS, chooses a UTM EPSG CRS from the center lon/lat.
  8. If the scene has no projected origin, reprojects the center into scene CRS and sets projected origin.
  9. Builds Blender meshes using the shared OSM options.
- Output behavior:
  - The imported geometry is placed relative to scene projected origin.
  - If `separate` is true, a collection named `OSM` is created and per-feature objects receive OSM tags as Blender custom properties.

## `importgis.osm_query`

Queries an Overpass server for the current BlenderGIS extent and imports the result.

- Class: `IMPORTGIS_OT_osm_query`.
- `bl_idname`: `importgis.osm_query`.
- Poll: object mode only.
- Scene prerequisites:
  - The scene must be georeferenced (`GeoScene.isGeoref`).
  - The scene must not be broken.
  - Extent must come from exactly one selected active mesh object or from an orthographic top-view viewport.
- Extent limit:
  - If bbox width or height in scene CRS is greater than `20000`, the operator cancels with `Too large extent`.
- Server behavior:
  - Uses BlenderGIS preference `overpassServer`.
  - Sends a user agent from BlenderGIS settings.
  - Reprojects bbox from scene CRS to EPSG:4326 before building the query.
  - Calls `queryBuilder(..., format='xml')` and imports the Overpass result.
- Default query shape:
  - Overpass QL head: `[out:xml][bbox:south,west,north,east];` for the live operator.
  - Node filters include tags when node type is selected.
  - Way filters include selected tags and recurse down (`>;`) so way nodes are present.
  - Relations are requested without tag filtering when relation type is selected.

## OSM Preferences and Preference Operators

Preference data is edited through `bgis.pref_show` in BlenderGIS preferences.

- Default OSM filter tags: `building`, `highway`, `landuse`, `leisure`, `natural`, `railway`, `waterway`.
- OSM tag management operators:
  - `bgis.add_osm_tag`
  - `bgis.edit_osm_tag`
  - `bgis.rmv_osm_tag`
  - `bgis.reset_osm_tags`
- Default Overpass servers:
  - `https://lz4.overpass-api.de/api/interpreter` (`overpass-api.de`)
  - `http://overpass.openstreetmap.fr/api/interpreter` (`overpass.openstreetmap.fr`)
  - `https://overpass.kumi.systems/api/interpreter` (`overpass.kumi.systems`)
- Overpass server management operators:
  - `bgis.add_overpass_server`
  - `bgis.edit_overpass_server`
  - `bgis.rmv_overpass_server`
  - `bgis.reset_overpass_server`

## Vendored Overpass Client Error Surface

BlenderGIS uses a vendored `overpy`-style client.

- Default Overpass timeout constant: 120 seconds.
- A response with `Content-Type: application/json` is parsed as JSON.
- A response with `Content-Type: application/osm3s+xml` is parsed as XML.
- Recognized service exceptions include:
  - `OverpassBadRequest`: HTTP 400 / syntax error; stringifies server messages.
  - `OverpassTooManyRequests`: HTTP 429 / rate limit.
  - `OverpassGatewayTimeout`: HTTP 504 / server load too high.
  - `OverpassUnknownContentType`: content type not JSON or OSM XML.
  - `OverpassUnknownHTTPStatusCode`: other unhandled HTTP status.
  - `DataIncomplete`: referenced node/way/relation missing from the parsed result.

The add-on catches broad exceptions in `importgis.osm_query` and reports `Overpass query failed, ckeck logs for more infos.`, so troubleshooting usually requires checking BlenderGIS logs and reducing/extending the query appropriately.

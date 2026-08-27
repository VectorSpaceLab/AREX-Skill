# Vector and OSM Troubleshooting

## Purpose

Use this when BlenderGIS vector import/export or OSM workflows fail, produce empty output, or risk an expensive/impolite Overpass request. It covers failure modes owned by this sub-skill. For installing/enabling BlenderGIS or optional package imports, use the root troubleshooting reference. For CRS repair, use the georeferencing sub-skill.

## Quick Triage

1. Confirm object mode; all covered import/export/query operators expect object mode.
2. Confirm whether the scene is georeferenced or broken:
   - missing CRS/origin may be acceptable for some shapefile/local OSM workflows;
   - broken partial state blocks shapefile import, OSM import, OSM query, and shapefile export.
3. For shapefiles, confirm the `.shp` path exists and sidecar files are present enough for the shapefile library to read geometry and fields.
4. For exports, confirm selected source contains mesh objects or the chosen collection contains meshes.
5. For Overpass, preflight with `../scripts/build_overpass_query.py`, reduce bbox/tags/types, and respect rate limits.
6. Check BlenderGIS logs from `View3D > GIS > Logs` when the operator reports a generic `check logs` message.

## Scene Not Georeferenced or Broken

### Symptoms

- `Scene georef is broken, please fix it beforehand`.
- `Scene is not georef` from `importgis.osm_query`.
- `Scene is not correctly georeferencing` if using geoscene coordinate tools.
- OSM query dialog opens but execution cancels before contacting Overpass.

### Likely Causes

- Scene has an origin custom property without `SRID`.
- Scene has invalid `SRID`.
- Scene has CRS and longitude/latitude origin but no projected origin (`crs x`, `crs y`).
- The user is trying to query Overpass before importing/setting any georeferenced data.

### Recovery

- Route CRS/origin repair to the sibling `georeferencing-and-crs` sub-skill.
- For shapefile import into a blank scene, choose the shapefile CRS in `importgis.shapefile_props_dialog`; the importer can set CRS and origin from the shapefile bbox.
- For local OSM XML import into a blank scene, the importer can choose UTM from XML bounds and set origin from bounds center.
- For Overpass query, do not proceed until `GeoScene.isGeoref` is true; query bbox conversion depends on scene CRS/origin.
- If the scene is broken, clear or repair georef state first. Do not try to bypass this from vector operators.

## Invalid Shapefile Path or Unreadable Fields

### Symptoms

- `Invalid filepath` from `importgis.shapefile_file_dialog`.
- `Unable to read shapefile fields` logged by the properties dialog.
- `Unable to read shapefile, check logs` from `importgis.shapefile`.
- Field dropdowns are empty.

### Likely Causes

- The selected path does not exist or is not a `.shp` file.
- Required shapefile sidecars are missing or corrupt; `.shp`, `.shx`, and `.dbf` are commonly needed for geometry/attribute workflows.
- File permissions prevent reading.
- The shapefile has no usable DBF fields; a field-dependent import may then fail.

### Recovery

- Re-select the `.shp` file through `importgis.shapefile_file_dialog`.
- Confirm sidecars are in the same directory with the same basename.
- If no attributes are needed, avoid choosing elevation/extrusion/name fields.
- If attributes are required, inspect the DBF with a GIS tool or a small Python DBF/shapefile reader before calling the scriptable operator.
- If the shape type is unsupported, convert it externally to Point, PolyLine, Polygon, or their Z variants before import.

## Invalid Shapefile Field Choices

### Symptoms

- `Unable to find name field`.
- `Unable to find elevation field`.
- `Elevation field do not contains numeric values`.
- `Unable to find extrusion field`.
- `Extrusion field do not contains numeric values`.
- Imported features have z=0 or no visible extrusion when values were expected.

### Likely Causes

- Field name spelling/case differs from DBF metadata.
- `fieldElevName`, `fieldExtrudeName`, or `fieldObjName` was passed in a scripted call without first reading the shapefile field list.
- Elevation or extrusion field type is character/date/etc. instead of DBF `N`, `F`, or `L`.
- Some feature records contain null/unparseable values. The importer logs these and uses z=0 or extrusion offset 0 for that feature.
- Extrusion offsets are zero or negative; the importer extrudes only positive offsets.

### Recovery

- Use the interactive `importgis.shapefile_props_dialog` first when possible so BlenderGIS populates valid field choices.
- For scripted calls, preflight field names and types externally.
- Use `elevSource='FIELD'` only for a numeric/logical elevation field.
- Leave `fieldExtrudeName=''` unless the field is numeric/logical and positive for target features.
- If object names matter, set `separateObjects=True` and then choose `fieldObjName`; otherwise the name field is not used.
- If a field is textual numeric data, convert it to a numeric DBF field before import rather than relying on BlenderGIS to coerce it.

## Missing Elevation Object

### Symptoms

- `No elevation object` from shapefile properties dialog.
- `There is no elevation object in the scene to get elevation from` from OSM import/query.
- Import appears flat even though `Elevation from object` was intended.

### Likely Causes

- `vertsElevSource='OBJ'` or OSM `useElevObj=True` was selected without a mesh object.
- The selected object is not a mesh.
- The terrain/ground object does not cover the vector/OSM extent, so raycasts miss.

### Recovery

- Add or import the terrain/ground mesh first; for raster/DEM acquisition route to the raster sub-skill, and for terrain mesh post-processing route to the terrain sub-skill.
- Select the correct mesh in `objElevLst` / `objElevName`.
- If terrain is unavailable, use `GEOM`, `FIELD`, or `NONE` for shapefile elevation and disable OSM `Elevation from object`.
- Validate coverage by checking that the elevation object spans the vector bbox in scene coordinates.

## Empty Selection or No Meshes for Export

### Symptoms

- `Selection is empty or does not contain any mesh`.
- Export creates files with little/no geometry.
- Expected custom properties are missing from DBF.

### Likely Causes

- `objectsSource='SELECTED'` and nothing selected, or selected objects are not meshes.
- `objectsSource='COLLEC'` and selected collection contains no mesh objects.
- Export type does not match mesh content: points need vertices, polylines need edges, polygons need faces.
- Object custom property types are unsupported and skipped.

### Recovery

- Switch to object mode and select mesh objects, or choose a populated collection.
- Match `exportType` to the geometry you actually have:
  - `POINTZ` for vertices;
  - `POLYLINEZ` for edges;
  - `POLYGONZ` for faces.
- Choose `OBJ2FEAT` for one multipart feature per object; choose `MESH2FEAT` when each primitive should be a separate feature.
- Add simple numeric/string custom properties before export if DBF attributes are required.
- Remember field names are truncated to 8 characters by this implementation.

## Unsupported or Surprising Shapefile Geometry

### Symptoms

- `Cannot process multipoint, multipointZ, pointM, polylineM, polygonM and multipatch feature type`.
- Polygon holes are missing or filled unexpectedly.
- Output polygons have unexpected winding/face orientation.

### Likely Causes

- The input shapefile shape type is outside the implemented set: Point, PolyLine, Polygon, PointZ, PolyLineZ, PolygonZ.
- The importer notes that bmesh cannot fully handle polygon holes in the current branch.
- The importer reverses polygon rings for Blender face orientation; export reverses faces for shapefile orientation.

### Recovery

- Convert unsupported geometry types in a GIS tool before importing into BlenderGIS.
- For polygons with important holes, validate output visually and consider preprocessing holes into separate geometry or using a dedicated GIS conversion pipeline.
- For export, verify results in a GIS viewer after writing the shapefile.

## Large Overpass Requests

### Symptoms

- `Too large extent` before any network request.
- `Overpass query failed, ckeck logs for more infos.`
- Long waits followed by timeout, 429, or 504 errors.
- Blender becomes slow while importing a very dense urban bbox.

### Likely Causes

- Bbox width or height in scene CRS exceeds BlenderGIS' `20000` threshold.
- Extent is dense or too broad for public Overpass limits.
- Too many feature types and broad tags were selected.
- `Separate objects` is enabled for many OSM elements, creating many Blender objects and collections.

### Recovery

- Select one smaller reference mesh object or zoom to a smaller orthographic top-view extent.
- Preflight the query with `../scripts/build_overpass_query.py` and verify bbox order/tags/types.
- Start with `--type way --tag building` or another narrow tag rather than all defaults.
- Disable `separate` for large OSM queries unless per-feature object editing is essential.
- If you need a city-scale OSM dataset, download it outside BlenderGIS and import smaller extracts, rather than hammering public Overpass.

## Overpass Errors and Timeouts

### Symptoms

- `Overpass query failed, ckeck logs for more infos.` in Blender.
- Log mentions `OverpassBadRequest`, `OverpassTooManyRequests`, `OverpassGatewayTimeout`, `OverpassUnknownContentType`, or unhandled HTTP status.
- Bad syntax messages from the server in the log.
- Missing-node/way relation errors such as `Data incomplete`.

### Likely Causes

- HTTP 400: query syntax rejected, often from malformed tags or bbox.
- HTTP 429: too many requests to the selected server.
- HTTP 504: server load too high or query too expensive.
- Unknown content type: server returned HTML or another error page instead of JSON/XML.
- Data incomplete: local XML or Overpass response lacks referenced elements needed to build ways/relations.

### Recovery

- Use `../scripts/build_overpass_query.py` locally and inspect the query string before sending.
- Confirm bbox is WGS84 degrees and in `west,south,east,north` order for the helper; the query will emit `south,west,north,east`.
- Narrow tags and types.
- Wait before retrying after 429/504; do not immediately rotate through public mirrors.
- If syntax is bad, remove complex `key=value` tags one by one and confirm simple key filters first.
- For local XML, ensure ways include their referenced nodes; export/download a complete OSM extract.

## Network/API Etiquette for Overpass

BlenderGIS can contact public Overpass instances. Future agents should avoid causing service abuse.

- Do not run repeated broad queries while debugging. Preflight offline first.
- Keep bboxes small and tags selective.
- Prefer one explicit user-approved request over multiple exploratory retries.
- Respect 429/504 responses by reducing scope and waiting.
- Do not switch servers to evade rate limits; use another server only when the selected server is unavailable and the query is already small.
- Do not embed private API keys or credentials in skill files or scripts. Overpass itself usually does not require keys.
- Document when a workflow was skipped because network access, service uptime, or user permission was unavailable.

## OSM Building Extrusion Looks Wrong

### Symptoms

- All buildings have the same default height.
- Heights are random between imports.
- Buildings fail to extrude.
- Roofs float or clip through terrain.

### Likely Causes

- OSM features lack parseable `height` and `building:levels` tags.
- `randomHeightThreshold` is nonzero, causing randomized default heights.
- Closed ways do not carry the `building` tag, so they are areas but not extruded.
- Elevation object raycasts miss part of the footprint; the importer averages partial hits and makes a flat roof when elevation object is used.

### Recovery

- Set `randomHeightThreshold=0` for deterministic output.
- Adjust `defaultHeight` and `levelHeight` to local expectations.
- Include the `building` tag in filters and verify features have that tag.
- Ensure the elevation object covers the entire footprint or disable `Elevation from object`.
- If post-import terrain alignment is needed, route to terrain-mesh-and-analysis.

## Object Separation Is Slow or Produces Too Many Objects

### Symptoms

- Import is very slow.
- Blender UI becomes sluggish after import.
- Scene contains thousands of small OSM/shapefile objects.

### Likely Causes

- `separateObjects` for shapefile or `separate` for OSM creates one object per feature.
- OSM relation/tag organization creates nested collections.
- A large Overpass query or dense shapefile was imported with separation enabled.

### Recovery

- Use grouped import for exploration and only re-import a narrowed subset with separation enabled.
- Use tag filters or smaller bbox/clip area.
- For shapefiles, use separation only when per-feature custom properties or names are required.
- For OSM, leave `separate` off when the goal is visualization or mesh analysis rather than element-by-element editing.

## Preflight Helper Errors

### Symptoms

- `west/east longitude must be between -180 and 180`.
- `south/north latitude must be between -90 and 90`.
- `west must be smaller than east`.
- `provide exactly one bbox source`.
- Shell treats `-74.02,40.70,...` as an option.

### Likely Causes

- Bbox order was passed as south/west/north/east instead of helper input order west/south/east/north.
- Antimeridian-spanning bbox is not supported by this small helper.
- Mixed positional, `--bbox`, and component options.
- Negative positional bbox was not protected from shell/argparse parsing.

### Recovery

- Use `--bbox=-74.02,40.70,-73.95,40.78` with an equals sign for negative western longitudes.
- Or pass four components: `--west -74.02 --south 40.70 --east -73.95 --north 40.78`.
- Use exactly one bbox input style.
- Split antimeridian-spanning requests into two bboxes.

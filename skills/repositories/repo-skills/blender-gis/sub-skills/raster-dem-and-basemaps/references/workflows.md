# Raster, DEM, ASCII Grid, Web DEM, and Basemap Workflows

This reference is self-contained for future use of BlenderGIS raster and basemap workflows. Operator execution normally happens inside Blender with the BlenderGIS add-on enabled.

## Shared Preconditions

- Add-on enabled and available in the 3D View `GIS` menu. The root diagnostic script is linked from `../../scripts/check_blendergis_environment.py` when present.
- Run raster and basemap operators in Object Mode. The raster, ASCII grid, DEM-query, and map-start operators all poll for Object Mode or a 3D View context.
- If the scene georeference is broken, raster import, ASCII import, basemap, and DEM query cancel with messages such as `Scene georef is broken, please fix it beforehand`. Route CRS/origin repair to `../georeferencing-and-crs/`.
- Decide whether the incoming raster CRS equals the scene CRS. If not, enable the operator's raster/file CRS option and ensure a projection engine can transform coordinates. True raster pixel reprojection for background images and tile-grid reprojection needs GDAL.
- For large rasters/DEMs, choose the import mode and `step` before running; raw mesh/point-cloud modes can create millions of vertices.

## Import a Georeferenced Raster

Menu path: `GIS > Import > Georeferenced raster (.tif .jpg .jp2 .png)`.

Operator: `bpy.ops.importgis.georaster(...)` / Blender operator ID `importgis.georaster`.

Key properties:

| Property | Values / type | Use |
| --- | --- | --- |
| `filepath` | image path | Raster file. Supported headers include TIFF/GeoTIFF, BMP, PNG, JPEG, and JPEG2000. |
| `importMode` | `PLANE`, `BKG`, `MESH`, `DEM`, `DEM_RAW` | Main behavior. Exact values are case-sensitive. |
| `reprojection` | bool | Tell BlenderGIS the raster CRS differs from the scene CRS. |
| `rastCRS` | CRS enum key, commonly `EPSG:...` | Source raster CRS when setting a new scene CRS or enabling `reprojection`. |
| `objectsLst` | enum index string | Existing mesh target for `MESH`, `DEM` with `demOnMesh`, or clipped `DEM_RAW`. |
| `demOnMesh` | bool | Apply DEM displacement to an existing georeferenced mesh instead of creating a new plane. |
| `clip` | bool | Clip DEM/DEM_RAW to selected mesh extent when supported. |
| `subdivision` | `subsurf`, `none`, `mesh` | Plane subdivision strategy for `DEM`; `mesh` creates vertices at DEM pixels and exposes `step`. |
| `demInterpolation` | bool | Smooth displacement texture sampling for `DEM`. |
| `fillNodata` | bool | Interpolate nodata before building a DEM displacement texture. |
| `step` | int >= 1 | Pixel stride for `DEM` mesh subdivision and `DEM_RAW`; higher values reduce vertices. |
| `buildFaces` | bool | For `DEM_RAW`, build quad faces between valid samples instead of a pure point cloud. |

### Mode `PLANE`: basemap image on a new plane

Use when you need a textured rectangular plane matching the raster extent.

1. Preflight georeferencing with `scripts/inspect_georaster.py IMAGE`.
2. If the scene has no CRS, choose `rastCRS`; BlenderGIS sets the scene CRS from this value and sets the scene origin to the raster center.
3. If the scene already has a different CRS, enable `reprojection=True` and set `rastCRS` to the raster CRS.
4. Run `importgis.georaster` with `importMode='PLANE'`.
5. Expected result: a new mesh named after the file stem, a `rastUVmap` UV layer, material `rastMat`, image texture `rastText`, and optional 3D view adjustment.
6. Validate: object bounds align with the raster world-file/GeoTIFF bbox; texture appears in textured solid/material preview.

Python console sketch:

```python
bpy.ops.importgis.georaster(
    filepath="/path/to/orthophoto.tif",
    importMode='PLANE',
    reprojection=False,
    rastCRS='EPSG:3857',
)
```

### Mode `BKG`: raster as a background empty

Use for a quick non-mesh reference image.

Constraints from the operator:

- Reprojection is not supported in this mode; if `reprojection=True`, it cancels with `Raster reprojection is not possible in background mode`.
- Rotation terms in the georeference are not supported; rotated rasters cancel with `Cannot apply a rotation in background image mode`.
- Pixel size must be equal in x and y map units after rounding to three decimals; otherwise it cancels with `Background image needs equal pixel size in map units in both x ans y axis`.

Expected result: an empty object with `empty_display_type='IMAGE'`, the raster image assigned, and location/scale derived from the raster center and pixel size.

### Mode `MESH`: drape raster onto an existing georeferenced mesh

Use when a mesh already exists and you want a raster texture UV-mapped to its geospatial footprint.

1. Ensure the scene is fully georeferenced and at least one mesh exists.
2. Select or choose the target mesh from the operator's `objectsLst` list.
3. If the raster CRS differs, set `reprojection=True` and `rastCRS`.
4. BlenderGIS derives the target object's geographic bbox, optionally reprojects it into the raster CRS, and loads only the overlapping raster subset.
5. Expected result: the existing mesh gets a new `rastUVmap` UV layer plus material/image texture.
6. Recovery: `Non overlap data` means the mesh bbox and raster bbox do not intersect after CRS choice; check scene origin/CRS and the raster's metadata.

### Mode `DEM`: elevation as a displacement texture

Use for terrain that can remain a plane/subsurf mesh with a DEM image texture driving displacement.

Decision points:

- `demOnMesh=False`: BlenderGIS creates a new plane covering the DEM. If the scene has no origin, it sets origin from the DEM center.
- `demOnMesh=True`: target an existing georeferenced mesh through `objectsLst`; `clip=True` clips the DEM to that mesh bbox.
- `subdivision='subsurf'`: adds a `SUBSURF` modifier named `DEM`, simple subdivision, levels/render_levels set to 6.
- `subdivision='mesh'`: builds a flat mesh with one vertex per every `step` DEM pixels, then adds displacement. Choose `step` to reduce mesh density.
- `fillNodata=True`: raster data is loaded through the image engine, cast to float, nodata is inpainted, and a new `_bgis.tif` is written before loading into Blender.
- `demInterpolation=True`: smooths the displacement texture; turn off if exact stepped values are needed.

Expected result: new or existing mesh gets `demUVmap`, an image texture named `demText`, and a `DISPLACE` modifier named `DEM`. For non-float rasters, strength is `2**depth - 1`; for float32 DEMs, strength is `1`.

Hard-case diagnostic for later verification:

1. If terrain has spikes/holes, inspect nodata with `scripts/inspect_georaster.py` and rerun with `fillNodata=True` if nodata exists or the DEM contains gaps.
2. If Blender becomes slow or the mesh is huge, rerun with larger `step` or use `subdivision='subsurf'` instead of `mesh`/`DEM_RAW`.
3. If applying to an existing mesh yields `Non overlap data`, verify the mesh geospatial bbox and raster CRS; use `reprojection=True` only when source and scene CRS differ.

### Mode `DEM_RAW`: build DEM vertices or faces directly

Use only when actual DEM sample vertices are needed for point-cloud/mesh workflows.

- `buildFaces=True` creates quad faces where valid samples exist.
- `buildFaces=False` creates a raw vertex cloud.
- `step` skips pixels; `step=10` keeps roughly one point per 100 pixels.
- `clip=True` requires a georeferenced selected/target mesh to define the working extent; otherwise it cancels with `No working extent`.

Route downstream Delaunay/Voronoi/terrain-analysis tasks to `../terrain-mesh-and-analysis/` after import.

## Import an ESRI ASCII Grid

Menu path: `GIS > Import > ESRI ASCII Grid (.asc)`.

Operator: `bpy.ops.importgis.asc_file(...)` / Blender operator ID `importgis.asc_file`.

Key properties:

| Property | Values / type | Use |
| --- | --- | --- |
| `filepath` | `.asc` or `.grd` path | ESRI ASCII grid file. |
| `fileCRS` | CRS enum key | CRS of the ASCII grid. If scene has no CRS, BlenderGIS sets it from this. |
| `importMode` | `MESH` or `CLOUD` | Quad mesh or vertex point cloud. |
| `step` | int >= 1 | Read every Nth sample. |
| `newlines` | bool | Use faster row-by-line reading when rows are newline-delimited. Disable for whitespace-only grids. |

ASCII workflow:

1. Confirm the six-line header includes `ncols`, `nrows`, `cellsize`, `nodata_value`, and either `xllcorner`/`yllcorner` or `xllcenter`/`yllcenter`.
2. Choose `MESH` for connected terrain faces; choose `CLOUD` to skip nodata vertices and produce a point cloud.
3. Use `step > 1` for massive grids.
4. If the scene CRS differs from `fileCRS`, BlenderGIS reprojects sample positions to the scene CRS using `Reproj`.
5. Expected result: a mesh object named after the file stem, placed relative to the scene origin.

Python console sketch:

```python
bpy.ops.importgis.asc_file(
    filepath="/path/to/dem.asc",
    fileCRS='EPSG:4326',
    importMode='CLOUD',
    step=4,
    newlines=True,
)
```

Recovery notes:

- `Incorrect number of columns for row` usually means `newlines=True` was chosen for a file where values are not row-delimited, or the header dimensions are wrong.
- `Cannot convert value to float` points to non-numeric cell text.
- In `CLOUD` mode, nodata values are skipped; in `MESH` mode the operator currently keeps them, so prefer preprocessing/fill or a larger `step` if nodata creates bad faces.

## Download a Web DEM

Menu path: `GIS > Web geodata > Get elevation (SRTM)`.

Operator: `bpy.ops.importgis.dem_query()` / Blender operator ID `importgis.dem_query`.

Behavior:

1. Requires a fully georeferenced scene. If not, it cancels with `Scene is not georef`.
2. Extent source is either one selected active mesh's bbox or the current orthographic top view. Any other context cancels with `Please define the query extent in orthographic top view or by selecting a reference object`.
3. Extents wider or taller than 1,000,000 scene/geographic units before WGS84 conversion cancel as `Too large extent`.
4. The bbox is reprojected from scene CRS to EPSG:4326.
5. SRTM requests cancel above 60 degrees north or below 56 degrees south.
6. OpenTopography URLs require `opentopography_api_key` in add-on preferences; without it the operator cancels before the network request.
7. Download writes `srtm.tif` beside the saved `.blend`, or into Blender's temp folder if the file is unsaved.
8. The downloaded WGS84 GeoTIFF is imported by `importgis.georaster` with `importMode='DEM'`, `reprojection=True`, `rastCRS='EPSG:4326'`, `subdivision='subsurf'`, and `demInterpolation=True`.

OpenTopography hard-case explanation:

- Default OpenTopography SRTM server templates include `{API_KEY}`. If selected and the preference key is blank, BlenderGIS does not contact the service; it reports `Please register to opentopography.org and request for an API key`.
- A user-provided GMRT template may not require an API key, but it still requires network reachability and a valid bbox template containing `{W}`, `{E}`, `{S}`, and `{N}`.

## Use the Basemap Viewer

Menu path: `GIS > Web geodata > Basemap`.

Operators:

- `view3d.map_start`: opens the map/source/layer/grid/search/options dialogs and toggles map navigation.
- `view3d.map_viewer`: internal modal map navigation.
- `view3d.map_search`: internal Nominatim search that moves the scene origin.

Map-start properties:

| Property | Values / type | Use |
| --- | --- | --- |
| `src` | source key such as `OSM`, `GOOGLE`, `BING`, `ESRI`, `OSM_WMS`, `GEOPORTAIL`, `GEOPORTAIL2` | Tile/WMS/WMTS source from bundled service definitions. |
| `lay` | layer key | Layer under the selected source, e.g. `MAPNIK`, `SAT`, `AERIAL`, `ORTHO`. |
| `grd` | grid key such as `WM`, `WGS84`, `WM_SW`, `LB93`, `LB93_2`, `LB93_CRAIG` | Destination tile matrix/cache grid. If different from source grid, reprojection may require GDAL. |
| `dialog` | `MAP`, `SEARCH`, `OPTIONS` | Which dialog to display. |
| `query` | search text | Nominatim search string when `dialog='SEARCH'`. |
| `zoom` | int 0-25 | Search target zoom; active map zoom is bounded by layer/grid limits. |
| `recenter` | bool | Center to existing objects and choose a suitable zoom. |

Preflight:

1. At least one imaging library must be available: GDAL, Pillow/PIL, or ImageIO. If all are missing, `view3d.map_start` cancels with `No imaging library available. ImageIO module was not correctly installed.`
2. Run inside a `VIEW_3D` area, not from background/headless mode.
3. Preferences must contain a valid writable `cacheFolder`; the add-on default is a user application data folder.
4. If the scene CRS differs from the chosen destination grid CRS and GDAL is unavailable, the operator cancels with `Please install gdal to enable raster reprojection support`.

Modal controls from `view3d.map_viewer`:

| Key/mouse | Action |
| --- | --- |
| Mouse wheel / numpad `+` / `-` | Increase/decrease map zoom unless Ctrl is held; with Alt, change map scale by factor 10. |
| Mouse drag / middle drag | Pan map; Ctrl or `lockOrigin` pans viewport instead of moving scene origin. |
| Numpad `2/4/6/8` | Pan map or viewport. |
| `B` | Zoom-box mode. |
| `L` | Lock/unlock current tile zoom while changing view distance. |
| `SPACE` | Switch layer/source dialog. |
| `G` | Go-to/search dialog. |
| `O` | Options dialog (`zoomToMouse`, `lockObj`, `lockOrigin`, `synchOrj`). |
| `E` | Export current basemap mosaic to a packed image texture on a new mesh plane. |
| `ESC` | Exit or cancel zoom-box mode. |

Expected result: a temporary GeoTIFF mosaic is created for the active basemap, loaded as an image empty in the scene, and tile responses are cached in GeoPackage databases. `E` exports the current mosaic to a real textured mesh with `rastUVmap`.

## Choose an Image / Projection Engine

- Add-on preference `imgEngine='AUTO'`: BlenderGIS tries GDAL first, then ImageIO FreeImage, then Pillow/PIL; otherwise it raises `No image engine available`.
- `imgEngine='GDAL'`, `'IMGIO'`, or `'PIL'` forces that engine but fails if the dependency is unavailable.
- GDAL is optional for normal image loading when Pillow or ImageIO can read the file, but required for GDAL-backed raster reprojection, BigTIFF writing, and some robust GeoTIFF/data-type paths.
- Add-on preference `projEngine` is covered by `../georeferencing-and-crs/`; raster workflows only need to know whether the required CRS transformations are available.

## Validation Checklist

- The raster/DEM has georeferencing: world file or GeoTIFF tags; inspect with `scripts/inspect_georaster.py`.
- The scene has a coherent CRS/origin before operations that need overlap, clipping, MESH draping, web DEM, or basemap reprojection.
- Import mode matches the desired output object type: plane/image empty/existing mesh/displacer/raw samples.
- DEM `nodata`, `fillNodata`, `step`, `subdivision`, and `buildFaces` choices are documented for the run.
- Basemap cache folder is valid and writable; services and API keys are available before blaming BlenderGIS.

# Raster / DEM / Basemap API Reference

This reference distills the BlenderGIS source and installed API inspection for raster, DEM, ASCII grid, basemap, cache, and image-engine use. It names stable operator IDs and the internal classes that explain behavior. Use these facts without reopening the source repository.

## Add-on Registration and Menu Placement

The add-on registers raster and basemap modules when these feature flags are enabled in its package initializer:

| Feature flag | Module | Public menu/operator surface |
| --- | --- | --- |
| `IMPORT_GEORASTER=True` | `operators.io_import_georaster` | `GIS > Import > Georeferenced raster`, `importgis.georaster` |
| `IMPORT_ASC=True` | `operators.io_import_asc` | `GIS > Import > ESRI ASCII Grid`, `importgis.asc_file` |
| `GET_DEM=True` | `operators.io_get_dem` | `GIS > Web geodata > Get elevation (SRTM)`, `importgis.dem_query` |
| `BASEMAPS=True` | `operators.view3d_mapviewer` | `GIS > Web geodata > Basemap`, `view3d.map_start` |

The main `GIS` menu also exposes add-on preferences (`bgis.pref_show`) and logs (`bgis.logs`). Use the root skill for general add-on enablement and logging guidance.

## Dependency Flags and Preference Engines

`core.checkdeps` sets these booleans by import probing:

| Flag | Probe | Raster/basemap effect |
| --- | --- | --- |
| `HAS_GDAL` | `from osgeo import gdal` | Enables GDAL image/projection engine, GDAL GeoTIFF metadata reading, raster reprojection, BigTIFF writing, robust DEM subsets, and map-grid reprojection. |
| `HAS_PYPROJ` | `import pyproj` | Projection engine option; detailed CRS behavior is routed to `../georeferencing-and-crs/`. |
| `HAS_PIL` | `from PIL import Image` | Pillow image engine for `NpImage`; enough for many PNG/JPEG/TIFF image reads but not GDAL-only reprojection. |
| `HAS_IMGIO` | vendored ImageIO FreeImage plugin load | ImageIO image engine; the probe may try to install/download FreeImage and can fail. |

Add-on preferences relevant here:

| Preference | Type / values | Meaning |
| --- | --- | --- |
| `imgEngine` | `AUTO`, `GDAL`, `IMGIO`, `PIL` | Chosen by `NpImage._getIFACE()`. `AUTO` prefers GDAL, then ImageIO, then Pillow. |
| `cacheFolder` | directory path | Basemap tile GeoPackage cache folder. Must exist and be writable/executable. |
| `zoomToMouse` | bool | Basemap modal wheel zoom behavior. |
| `lockOrigin` | bool | Basemap panning moves viewport instead of scene origin. |
| `lockObj` | bool | Keep object geolocation when moving map origin. |
| `synchOrj` | bool | Keep scene projected and lon/lat origins synchronized; can be slow when projection uses remote services. |
| `resamplAlg` | `NN`, `BL`, `CB`, `CBS`, `LCZ` | GDAL resampling algorithm for map/raster reprojection; `MapService.RESAMP_ALG` is set from this preference. |
| `demServer` | URL template enum | DEM service template with `{W}`, `{E}`, `{S}`, `{N}`, and optionally `{API_KEY}`. |
| `opentopography_api_key` | string | Required when selected DEM URL contains OpenTopography. |
| `maptiler_api_key` | string | Used by CRS search/migration, not by normal raster import; route CRS search to `../georeferencing-and-crs/`. |

Default DEM server templates include OpenTopography SRTMGL1/SRTMGL3 GeoTIFF downloads and a GMRT GeoTIFF service. OpenTopography templates contain `{API_KEY}`.

## `importgis.georaster`

Class: `IMPORTGIS_OT_georaster`.

Installed operator metadata:

- `bl_idname`: `importgis.georaster`
- `bl_label`: `Import georaster`
- `bl_description`: `Import raster georeferenced with world file`
- `bl_options`: `UNDO`
- `poll`: Object Mode only.

Properties and behavior:

| Property | Type / values | Notes |
| --- | --- | --- |
| `filter_glob` | `*.tif;*.jpg;*.jpeg;*.png;*.bmp` | Dialog filter; core header reader also supports JPEG2000 and TIFF variants. |
| `rastCRS` | CRS enum from preferences | Used when scene has no CRS or when `reprojection=True`. |
| `reprojection` | bool | Exposes `rastCRS` when scene is already georeferenced; builds `Reproj` objects if `geoscn.crs != rastCRS`. |
| `importMode` | `PLANE`, `BKG`, `MESH`, `DEM`, `DEM_RAW` | Exact enum values. |
| `objectsLst` | enum of scene mesh object indices as strings | Target mesh for drape/displacement/clip. |
| `subdivision` | `subsurf`, `none`, `mesh` | `mesh` is hidden when applying DEM on an existing mesh. |
| `demOnMesh` | bool | Use selected existing mesh as DEM displacement receiver. |
| `clip` | bool | Clip DEM to working extent from selected mesh where applicable. |
| `demInterpolation` | bool | Sets texture interpolation for DEM displacer. |
| `fillNodata` | bool | Rewrites a `_bgis.tif` with filled nodata before Blender image load. |
| `step` | int >= 1 | Pixel stride for mesh subdivision/raw sample import. |
| `buildFaces` | bool | `DEM_RAW` quad-face generation. |

Execution outline:

1. Deselects all objects.
2. Builds `GeoScene` and cancels if scene georef is broken.
3. Determines `rastCRS`: scene CRS by default for georeferenced scenes, or operator `rastCRS` for new/unset scenes and explicit reprojection.
4. If scene has no CRS, tries to set `geoscn.crs = rastCRS`.
5. If scene and raster CRS differ, builds `Reproj(geoscn.crs, rastCRS)` and `Reproj(rastCRS, geoscn.crs)`.
6. Branches by `importMode` as documented in `workflows.md`.
7. Optionally adjusts 3D view and forces textured solid shading using preferences.

Important cancel/report messages:

- `Scene georef is broken, please fix it beforehand`
- `Cannot set scene crs, check logs for more infos`
- `Unable to open raster, check logs for more infos`
- `Raster reprojection is not possible in background mode`
- `Cannot apply a rotation in background image mode`
- `Background image needs equal pixel size in map units in both x ans y axis`
- `There isn't georef mesh to apply on`
- `Non overlap data`
- `No working extent`

## `importgis.asc_file`

Class: `IMPORTGIS_OT_ascii_grid`.

Installed operator metadata:

- `bl_idname`: `importgis.asc_file`
- `bl_label`: `Import ASCII Grid`
- `bl_description`: `Import ESRI ASCII grid with world file`
- `bl_options`: `UNDO`
- `poll`: Object Mode only.

Properties:

| Property | Type / values | Notes |
| --- | --- | --- |
| `filter_glob` | `*.asc;*.grd` | File dialog filter. |
| `fileCRS` | CRS enum from preferences | Source grid CRS. |
| `importMode` | `MESH`, `CLOUD` | Quad mesh or point cloud. |
| `step` | int >= 1 | Read every Nth point. |
| `newlines` | bool | `True` uses fast `readline().split()` per row; `False` reads whitespace chunks. |

Parsing facts:

- Reads the first six lines with regex `^([^\s]+)\s+([^\s]+)$` and lowercases header keys.
- Required numeric keys in practice: `nrows`, `ncols`, `cellsize`, `nodata_value`.
- Position anchor: `xllcorner`/`yllcorner` or `xllcenter`/`yllcenter`. Center anchor applies an offset of `(-cellsize/2, -cellsize/2)`.
- Iterates rows from `nrows - 1` down to `0` so the mesh coordinates increase from lower-left semantics.
- In `CLOUD` mode, values equal to nodata are skipped.
- In `MESH` mode, faces are built over the stepped grid; nodata is not skipped before face generation.

Important cancel/report messages:

- `Scene georef is broken, please fix it beforehand`
- `Cannot set scene crs, check logs for more infos`
- `Incorrect number of columns for row, check logs for more infos`
- `Cannot convert value to float`

## `importgis.dem_query`

Class: `IMPORTGIS_OT_dem_query`.

Installed operator metadata:

- `bl_idname`: `importgis.dem_query`
- `bl_label`: `Get elevation (SRTM)`
- `bl_description`: `Query for elevation data from a web service`
- `bl_options`: `UNDO`
- `poll`: Object Mode only.
- Network timeout constant: 120 seconds.

Inputs and preference use:

- Reads `prefs.demServer` URL template and `prefs.opentopography_api_key`.
- If selected template includes `opentopography`, dialog shows the API key field.
- Extent from either selected active mesh (`getBBOX.fromObj(aObj).toGeo(geoscn)`) or current orthographic top view (`getBBOX.fromTopView(context).toGeo(geoscn)`).
- Reprojects bbox from scene CRS to EPSG:4326 before URL formatting.
- Adds an extra `0.002` degrees around the requested bbox because OpenTopography may not return the full bbox.
- Writes to `srtm.tif` next to a saved `.blend` or to Blender's temp directory when unsaved.

Important cancel/report messages:

- `Scene is not georef`
- `Scene georef is broken, please fix it beforehand`
- `Please define the query extent in orthographic top view or by selecting a reference object`
- `Too large extent`
- `SRTM is not available beyond 60 degrees north`
- `SRTM is not available below 56 degrees south`
- `Please register to opentopography.org and request for an API key`
- `Cannot reach OpenTopography web service, check logs for more infos`
- `Cannot reach SRTM web service provider, server can be down or overloaded. Please retry later`

Follow-on import call:

- Top-view extent: `importgis.georaster(filepath=srtm.tif, reprojection=True, rastCRS='EPSG:4326', importMode='DEM', subdivision='subsurf', demInterpolation=True)`.
- Selected mesh extent: same plus `demOnMesh=True`, target `objectsLst`, `clip=False`, `fillNodata=False`.

## Basemap Operators

### `view3d.map_start`

Class: `VIEW3D_OT_map_start`.

Installed operator metadata:

- `bl_idname`: `view3d.map_start`
- `bl_label`: `Basemap`
- `bl_description`: `Toggle 2d map navigation`
- `bl_options`: `REGISTER`

Properties:

| Property | Values / type | Notes |
| --- | --- | --- |
| `src` | dynamic enum from `SOURCES` | Source key. |
| `grd` | dynamic enum from `GRIDS` | Destination cache tile matrix; source grid is listed first. |
| `lay` | dynamic enum from source layers | Layer key for the selected source. |
| `dialog` | `MAP`, `SEARCH`, `OPTIONS` | Internal dialog mode. |
| `query` | string | Search text. |
| `zoom` | int 0-25 | Search zoom. |
| `recenter` | bool | Recenter map to existing scene objects. |

Preflight/cancel behavior:

- `invoke` requires at least one of `HAS_PIL`, `HAS_GDAL`, or `HAS_IMGIO`.
- `invoke` requires a 3D View area.
- `execute` requires a valid writable cache folder.
- In map dialog, broken scene georef cancels.
- If scene CRS differs from selected grid CRS and GDAL is absent, it cancels because raster reprojection is needed.
- Search mode calls `view3d.map_search` then launches `view3d.map_viewer`.

### `view3d.map_viewer`

Class: `VIEW3D_OT_map_viewer`.

Installed operator metadata:

- `bl_idname`: `view3d.map_viewer`
- `bl_label`: `Map viewer`
- `bl_description`: `Toggle 2d map navigation`
- `bl_options`: `INTERNAL`
- `poll`: context area type `VIEW_3D`.

Properties: `srckey`, `laykey`, `grdkey`, `recenter`.

The modal operator constructs `BaseMap(context, srckey, laykey, grdkey)`, starts tile download/build work in a thread, displays a background image empty, and handles map-navigation keys. Export key `E` converts the current basemap mosaic to a packed image and a textured mesh plane.

### `view3d.map_search`

Class: `VIEW3D_OT_map_search`.

Installed operator metadata:

- `bl_idname`: `view3d.map_search`
- `bl_label`: `Map search`
- `bl_description`: `Search for a place and move scene origin to it`
- `bl_options`: `INTERNAL`

Behavior:

- Uses Nominatim through `nominatimQuery(query, referer='bgis', user_agent=USER_AGENT)`.
- Cancels on broken scene georef or query failure/no results.
- If scene is already georeferenced, updates origin lon/lat with object-location update controlled by `prefs.lockObj`; otherwise sets origin geo from result lon/lat.

## Core Raster Classes

### `GeoRaster(path, subBoxGeo=None, useGDAL=False)`

Represents a georeferenced raster file.

Important attributes:

- `path`, `wfPath`, `format`, `size`, `depth`, `dtype`, `nbBands`, `noData`, `georef`.
- Dynamic georef delegation: missing attributes are delegated to `self.georef`, so a `GeoRaster` exposes `origin`, `pxSize`, `bbox`, `center`, etc. when georef exists.

Initialization behavior:

- Locates world file with `_getWfPath()`.
- Non-GDAL path: detects format by header; supports `TIFF`, `BMP`, `PNG`, `JPEG`, and `JPEG2000`. TIFF uses vendored Tyf to inspect GeoTIFF tags and falls back to a world file if no TIFF georef was found. Non-TIFF images need a world file.
- GDAL path: uses `gdal.Open`, dataset geotransform, raster count, first-band nodata, and data type.
- Raises `IOError("Unsupported format ...")` for unsupported headers.
- Raises `IOError("Unable to read georef infos from worldfile or geotiff tags")` when no georeference is found.
- Applying `subBoxGeo` may raise `OverlapError`.

World-file search order for an image extension's last three characters:

1. first+third+`w` (`tfw`, `jgw`, `pgw`, ...)
2. same plus `x` (`tfwx`, ...)
3. extension+`w` (`tifw`, ...)
4. `wld`
5. uppercase variants of all of the above.

### `GeoRef(rSize, pxSize, origin, rot=(0,0), pxCenter=True, subBoxGeo=None, crs=None)`

Represents affine georeferencing. Image origin is upper-left; map origin is lower-left.

Key constructors/methods:

| Method | Use |
| --- | --- |
| `GeoRef.fromWorldFile(wfPath, rasterSize)` | Reads six numeric world-file values: x pixel size, y rotation, x rotation, y pixel size, x origin, y origin. Commas are accepted as decimal separators. |
| `GeoRef.fromTyf(tif)` | Reads GeoTIFF transformation matrix or model tiepoint + pixel scale; adjusts `RasterPixelIsArea` tiepoints to pixel center. |
| `GeoRef.fromGDAL(ds)` | Reads GDAL geotransform and CRS if possible. |
| `toWorldFile(path)` | Writes six world-file values. |
| `toGDAL()` | Returns GDAL geotransform tuple. |
| `geoFromPx` / `pxFromGeo` | Affine pixel/geographic coordinate transforms. |
| `setSubBoxGeo` / `setSubBoxPx` | Defines working subset; rotated rasters cannot use geographic subboxes. |

Useful properties: `hasCRS`, `hasRotation`, `cornersCenter`, `corners`, `bbox`, `bboxPx`, `center`, `geoSize`, `orthoGeoSize`, `orthoPxSize`, `subBoxPx`, `subBoxPxSize`, `subBoxGeoSize`, `subBoxGeoOrigin`.

### `NpImage(data, subBoxPx=None, noData=None, georef=None, adjustGeoref=False)`

Wraps raster pixels as a NumPy array and optionally carries `GeoRef`.

Input types: file path, bytes, NumPy array, another `NpImage`, PIL image (if Pillow available), or GDAL dataset (if GDAL available).

Key behaviors:

- `_getIFACE()` selects `GDAL`, `IMGIO`, or `PIL` from `settings.img_engine` and availability flags.
- If `noData` is provided, data is masked with `np.ma.masked_array(data, data == noData)`.
- `fillNodata()` uses `gdal.FillNodata` for GDAL or bundled local-mean inpainting after casting to float otherwise.
- `save(path)` writes with the selected image engine and writes a `.wld` world file when georeferenced.
- `reproj(...)` requires GDAL-backed `reprojImg` and georeferenced input.

### `bpyGeoRaster(path, subBoxGeo=None, useGDAL=False, clip=False, fillNodata=False, raw=False)`

Subclass used by raster import operators before loading image data into Blender.

It rewrites the raster to a new `_bgis.tif` when any of the following is true:

- Format is not directly one of `GTiff`, `TIFF`, `BMP`, `PNG`, `JPEG`, `JPEG2000`.
- `clip=True` and a subbox is present.
- `fillNodata=True`.
- Data type/depth is signed int16 (`ddtype == 'int16'`), which Blender does not handle correctly as displacement texture.

For DEM/raw data, it sets `bpyImg.colorspace_settings.is_data=True` so Blender treats the image as data rather than color.

## Basemap Core Classes

### `TileMatrix(gridDef)`

Builds a tile matrix from `GRIDS` definitions. Important fields inherited from a grid definition include `CRS`, `bbox`, `bboxCRS`, `tileSize`, `originLoc`, and either `resolutions` or resolution factor/initial resolution.

Useful methods/properties:

- `globalbbox`
- `geoToProj(long, lat)` / `projToGeo(x, y)`
- `getResList()`, `getRes(zoom)`, `getNearestZoom(res, rule='closer'|'lower'|'higher')`
- `getPrevResFac(z)`, `getNextResFac(z)`, `getFromToResFac(z1,z2)`
- `getTileNumber(x,y,zoom)`, `getTileCoords(col,row,zoom)`, `getTileBbox(col,row,zoom)`
- `bboxRequest(bbox, zoom)`

Grid keys present in bundled service definitions include `WM`, `WGS84`, `WM_SW`, `LB93`, `LB93_2`, and `LB93_CRAIG`.

### `MapService(srckey, cacheFolder, dstGridKey=None)`

Represents one tile service source and manages tile requests, reprojection, mosaics, and GeoPackage cache.

Important constants/fields:

- Status codes: `0` idle, `1` get cache, `2` downloading, `3` building mosaic, `4` reprojecting.
- `TIMEOUT=4` seconds for individual tile downloads.
- `MOSAIC_BKG_COLOR=(128,128,128,255)`, empty tile color pink, corrupted tile color red.
- Fake browser headers include `User-Agent` and source `Referer`.

Useful methods:

| Method | Use |
| --- | --- |
| `setDstGrid(grdkey)` / `getTM(dstGrid=False)` | Configure source/destination tile matrix. |
| `getCache(laykey, useDstGrid)` | Return/create a `GeoPackage` cache database named `{source}_{layer}_{grid}.gpkg`. |
| `buildUrl(laykey, col, row, zoom)` | Format TMS/WMTS/WMS tile URLs; WMS 1.3.0 EPSG:4326 swaps bbox axis order. |
| `downloadTile(...)` | Download one tile and validate image bytes. |
| `tileRequest(...)` / `buildDstTile(...)` | Fetch source tile or build/reproject a destination-grid tile. |
| `seedTiles(...)`, `seedCache(...)` | Download missing tiles with threads and write cache. |
| `getTiles(...)` | Fetch cached/downloaded tile byte tuples. |
| `getImage(laykey, bbox, zoom, path=None, bigTiff=False, outCRS=None, toDstGrid=True, nbThread=10, cpt=True)` | Build a georeferenced mosaic as `NpImage`, write an image, or write BigTIFF. |

### `GeoPackage(path, tm)`

SQLite GeoPackage tile cache used by basemap services.

Key facts:

- Table containing tiles is always `gpkg_tiles`.
- Application ID must be `1196437808` (`GP10`).
- Schema tables: `gpkg_contents`, `gpkg_spatial_ref_sys`, `gpkg_tile_matrix_set`, `gpkg_tile_matrix`, `gpkg_tiles`.
- Tile rows are uniquely keyed by `(zoom_level, tile_column, tile_row)`.
- Cached tiles older than `MAX_DAYS=90` are treated as missing.
- Useful methods: `isGPKG`, `hasTile`, `getTile`, `putTile`, `listExistingTiles`, `listMissingTiles`, `getTiles`, `putTiles`.

## Bundled Basemap Source Definitions

Current source keys and typical layers:

| Source | Service | Grid | Layers |
| --- | --- | --- | --- |
| `GOOGLE` | TMS | `WM` | `SAT`, `MAP` |
| `OSM` | TMS | `WM` | `MAPNIK` |
| `BING` | TMS with quadkey | `WM` | `SAT`, `MAP` |
| `ESRI` | TMS | `WM` | `AERIAL`, `NATGEO`, `USATOPO`, `PHYSICAL`, `RELIEF`, `STREET`, `TOPO`, `TERRAINB`, `CANVASLIGHTB`, `CANVASDARKB`, `OCEANB` |
| `OSM_WMS` | WMS | `WM` | `WRLD` |
| `GEOPORTAIL` | WMTS | `WM` | `ORTHO`, `CAD` |
| `GEOPORTAIL2` | WMTS | `WM` | `SCAN25`, `SCAN` |

Some service URLs may require network access, may have usage limits or terms, may return HTTP errors, or may change independently of the add-on. Do not treat service unavailability as an add-on install failure until cache folder, image engines, CRS/GDAL needs, and network/API conditions are checked.

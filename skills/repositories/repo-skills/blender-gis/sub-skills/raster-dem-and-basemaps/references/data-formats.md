# Raster, DEM, ASCII Grid, Tile, and Cache Data Formats

Use this reference to prepare inputs and interpret outputs for BlenderGIS raster/DEM/basemap workflows without reopening the source repository.

## Image and Raster Inputs

BlenderGIS's non-GDAL header reader recognizes these image families:

| Header format | Typical extensions | Notes |
| --- | --- | --- |
| `TIFF` / GeoTIFF | `.tif`, `.tiff` | GeoTIFF tags may provide georeferencing; world files can also be used. Vendored Tyf reads selected TIFF tags when GDAL is not used. |
| `PNG` | `.png` | Needs a world file for georeferenced import unless a GDAL path provides georeferencing. |
| `JPEG` | `.jpg`, `.jpeg` | Needs a world file for georeferenced import. |
| `JPEG2000` | `.jp2`, `.j2k` | Header recognized; support depends on Blender/Pillow/ImageIO/GDAL availability. |
| `BMP` | `.bmp` | Needs a world file for georeferenced import. |
| `GIF`, `EXR` | header detection exists | `GeoRaster` accepts only `TIFF`, `BMP`, `PNG`, `JPEG`, and `JPEG2000` in non-GDAL mode; unsupported formats raise an error. |

A valid georeferenced raster import requires both image dimensions and georeference information. If GDAL is unavailable, non-TIFF images require a world file; TIFF may use GeoTIFF tags or world file fallback.

## World Files

BlenderGIS searches for a world file beside the image. For an image path ending with a three-letter extension, search order is:

1. first and third extension letters + `w` (`tfw`, `jgw`, `pgw`, ...)
2. the same plus `x` (`tfwx`, `jgwx`, ...)
3. extension + `w` (`tifw`, `jpgw`, `pngw`, ...)
4. `wld`
5. uppercase variants of all of the above

A world file contains exactly six numeric values, one per line. BlenderGIS parses commas as decimal separators too.

| Line | World-file term | BlenderGIS use |
| --- | --- | --- |
| 1 | x pixel size / A | `pxSize.x` |
| 2 | y rotation / D | `rotation.x` in `GeoRef.fromWorldFile` source terminology |
| 3 | x rotation / B | `rotation.y` in affine transform use |
| 4 | y pixel size / E | `pxSize.y`, normally negative for north-up rasters |
| 5 | x coordinate of upper-left pixel center / C | `origin.x` |
| 6 | y coordinate of upper-left pixel center / F | `origin.y` |

Example `ortho.tfw`:

```text
0.5
0
0
-0.5
700000.25
6600000.25
```

Interpretation: 0.5 map units per pixel, north-up, top-left pixel center at `(700000.25, 6600000.25)`. A 1000 x 800 image covers roughly 500 x 400 map units.

Important subtleties:

- World files do not store CRS. You must provide `rastCRS`/`fileCRS` or already have a matching scene CRS.
- Background-image mode (`BKG`) rejects rotation and non-square pixel sizes.
- A missing world file for a PNG/JPEG/BMP usually produces `Unable to read georef infos from worldfile or geotiff tags`.
- Use `scripts/inspect_georaster.py IMAGE` to check image size, world-file path, affine values, bbox, center, and missing-georef conditions.

## GeoTIFF Tags

Without GDAL, BlenderGIS uses a vendored TIFF tag reader for selected GeoTIFF metadata.

Georeferencing may be derived from:

- `ModelTransformationTag`: a 4x4 transform matrix. BlenderGIS extracts 2D affine origin, pixel size, and rotation terms.
- `ModelTiepointTag` plus `ModelPixelScaleTag`: top-left tiepoint and pixel scale. The y pixel size is made negative for north-up raster convention.
- `GeoKeyDirectoryTag` and `GTRasterTypeGeoKey`: if raster type is `RasterPixelIsArea` (or the key is missing and defaults to area), BlenderGIS adjusts top-left corner tiepoints to pixel center.

Limitations:

- The non-GDAL path does not fully reconstruct CRS from GeoTIFF GeoKeys; CRS may still need to be supplied in the operator.
- GDAL provides stronger metadata/data-type/nodata support when installed.
- If TIFF geotags cannot be read, BlenderGIS logs a warning and can still use a world file if one exists.

## DEM Raster Data

DEM workflows rely on a georeferenced one-band or interpretable raster. Core facts:

- `GeoRaster` records first-band `noData` when GDAL or TIFF `GDAL_NODATA` is available.
- `NpImage` masks pixels equal to `noData` when `noData` is supplied.
- `bpyGeoRaster(fillNodata=True)` loads data through `NpImage`, casts to float, fills nodata, saves a new `_bgis.tif`, and reloads it.
- Signed int16 DEMs are rewritten to float `_bgis.tif` because Blender displacement textures mishandle signed 16-bit values.
- DEM image textures are marked as data (`colorspace_settings.is_data=True`) when loaded with `raw=True`.
- DEM displacement modifier strength is based on raster bit depth: `2**depth - 1` for non-float rasters and `1` for 32-bit float rasters.

Choose these options carefully:

| Scenario | Recommended option |
| --- | --- |
| DEM has holes/nodata that become spikes | `fillNodata=True` for `DEM`; inspect nodata first. |
| DEM is huge and raw mesh would be too dense | Use `DEM` with `subdivision='subsurf'`, or increase `step`. |
| Need actual elevation vertices | `DEM_RAW` with `step` and `buildFaces` chosen deliberately. |
| Need exact cell-value points, not faces | `DEM_RAW`, `buildFaces=False`, or ASCII `CLOUD`. |
| Need to drape DEM onto existing footprint | `DEM`, `demOnMesh=True`, optional `clip=True`. |

## ESRI ASCII Grid

The ASCII grid importer expects a six-line header followed by numeric grid values. Required keys are lowercased internally.

Common header forms:

```text
ncols 4
nrows 3
xllcorner 700000
yllcorner 6600000
cellsize 10
NODATA_value -9999
1 2 3 4
5 6 7 8
9 10 11 12
```

or center-anchored:

```text
ncols 4
nrows 3
xllcenter 700005
yllcenter 6600005
cellsize 10
nodata_value -9999
...
```

BlenderGIS behavior:

- `xllcorner`/`yllcorner` are used as the lower-left corner anchor.
- `xllcenter`/`yllcenter` are treated as a lower-left cell center, with an internal `(-cellsize/2, -cellsize/2)` offset for mesh placement.
- Rows can be read with `newlines=True` for one row per line, or `newlines=False` for whitespace-delimited values that may span arbitrary lines.
- `step` reads every Nth row/column and skips intervening rows.
- `MESH` creates quad faces over the stepped grid.
- `CLOUD` skips nodata samples and creates vertices only.

ASCII grid does not carry CRS in the header. Always set `fileCRS` or ensure the scene CRS already matches.

## Web DEM Service Templates

DEM preferences store URL templates as JSON-backed enum entries. Valid custom templates must contain all bbox placeholders:

- `{W}` west longitude
- `{E}` east longitude
- `{S}` south latitude
- `{N}` north latitude

Templates can optionally include `{API_KEY}`. The built-in OpenTopography templates include it; the built-in GMRT template does not.

Built-in DEM concepts:

| Server label | Typical output | Key condition |
| --- | --- | --- |
| OpenTopography SRTM 30m | GeoTIFF | Requires OpenTopography API key and SRTM latitude range. |
| OpenTopography SRTM 90m | GeoTIFF | Requires OpenTopography API key and SRTM latitude range. |
| Marine-geo.org GMRT | GeoTIFF | No OpenTopography key but still network/service dependent. |

The DEM query operator always requests EPSG:4326 bbox coordinates and imports the result as `rastCRS='EPSG:4326'`.

## Basemap Grids, Sources, and Layers

Bundled tile matrix grid keys:

| Grid key | CRS | Origin | Purpose |
| --- | --- | --- | --- |
| `WM` | `EPSG:3857` | northwest | Standard Web Mercator tile grid. |
| `WGS84` | `EPSG:4326` | northwest | Global latitude/longitude grid. |
| `WM_SW` | `EPSG:3857` | southwest | TMS/MBTiles-style Web Mercator. |
| `LB93` | `EPSG:2154` | northwest | France Lambert 93 example grid. |
| `LB93_2` | `EPSG:2154` | southwest | France Lambert 93 grid with explicit resolutions. |
| `LB93_CRAIG` | `EPSG:2154` | northwest | France CRAIG WMTS grid. |

Bundled source keys include `GOOGLE`, `OSM`, `BING`, `ESRI`, `OSM_WMS`, `GEOPORTAIL`, and `GEOPORTAIL2`. Each source defines service type (`TMS`, `WMS`, or `WMTS`), source grid, layer keys, URL template, and referer.

Cautions:

- Public tile services can change endpoints, require API keys, enforce usage policies, rate-limit clients, or block referers/user agents.
- A source key being present in BlenderGIS does not guarantee legal or network availability for a particular use.
- If source and destination grids differ, BlenderGIS may need GDAL to reproject tile mosaics.

## GeoPackage Tile Cache

Basemap tiles are cached as GeoPackage SQLite databases in the add-on preference `cacheFolder`.

Filename pattern:

```text
{source_key}_{layer_key}_{grid_key}.gpkg
```

Schema summary:

- `gpkg_contents`: one `tiles` entry named `gpkg_tiles` with bbox and SRS ID.
- `gpkg_spatial_ref_sys`: grid CRS entry.
- `gpkg_tile_matrix_set`: tile matrix bbox.
- `gpkg_tile_matrix`: matrix dimensions and pixel sizes by zoom.
- `gpkg_tiles`: tile rows with `zoom_level`, `tile_column`, `tile_row`, `tile_data`, and `last_modified`.

Cache freshness:

- `GeoPackage.MAX_DAYS` is 90.
- A tile older than 90 days is treated as missing and will be requested again.
- Invalid or corrupt cached bytes can produce pink/red placeholder imagery in mosaics; deleting the affected `.gpkg` or stale rows forces a re-download.

## Outputs Created by Workflows

| Workflow | Main output |
| --- | --- |
| `PLANE` georaster | New mesh plane, UV layer `rastUVmap`, material `rastMat`, image texture `rastText`. |
| `BKG` georaster | Empty image object with raster assigned and geospatial scale/location. |
| `MESH` georaster | Existing mesh gets `rastUVmap`, material, and raster texture. |
| `DEM` | New or existing mesh with `demUVmap`, data image texture `demText`, `DISPLACE` modifier `DEM`, optional `SUBSURF` modifier `DEM`. |
| `DEM_RAW` | New mesh from DEM samples, optionally with quad faces. |
| ASCII `MESH` | New quad mesh from grid samples. |
| ASCII `CLOUD` | New point cloud mesh, skipping nodata values. |
| Web DEM | Downloaded `srtm.tif` plus DEM import output. |
| Basemap viewer | Temporary GeoTIFF mosaic, background image empty, GeoPackage cache; `E` creates a textured mesh export with packed image. |

## Preflight with the Bundled Inspector

Use `scripts/inspect_georaster.py` before opening Blender when a raster import fails or when you need to verify metadata:

```bash
python scripts/inspect_georaster.py /path/to/image.tif
python scripts/inspect_georaster.py /path/to/image.png --json
python scripts/inspect_georaster.py /path/to/image.jpg --world-file /path/to/image.jgw
```

The inspector:

- Uses Pillow when available for dimensions and TIFF tag names.
- Falls back to lightweight header parsing for common image dimensions.
- Finds world files using BlenderGIS-compatible filename patterns.
- Parses the six affine world-file values and reports corner bbox, center, pixel size, rotation, and warnings.
- Does not require GDAL and does not contact network services.

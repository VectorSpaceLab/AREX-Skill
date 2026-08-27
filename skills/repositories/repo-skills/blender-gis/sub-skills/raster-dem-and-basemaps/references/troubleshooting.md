# Raster, DEM, Web DEM, and Basemap Troubleshooting

Start with the exact operator message if Blender shows one. Many failures are caused by missing georeference metadata, a broken scene CRS, optional imaging/projection dependencies, invalid DEM extent/credentials, or tile cache/network state.

## Fast Triage

1. **Preflight the input raster** with `scripts/inspect_georaster.py IMAGE`. Confirm dimensions, world file or GeoTIFF tags, pixel size, rotation, bbox, and center.
2. **Check scene georeferencing** if an operator says the scene is broken, not georeferenced, or cannot overlap data. Route generic CRS/origin repair to `../georeferencing-and-crs/`.
3. **Confirm optional dependencies**. GDAL is optional for some raster reads but required for raster/tile reprojection and BigTIFF/GDAL paths. At least GDAL, Pillow, or ImageIO must be present for basemaps.
4. **For DEMs, diagnose nodata and size** before retrying. Choose `fillNodata`, `step`, `subdivision`, `buildFaces`, and `clip` deliberately.
5. **For web DEM/basemaps, separate add-on errors from service failures**. Check API keys, latitude/extent limits, network, service terms/rate limits, and cache folder permissions.

## Missing World File or GeoTIFF Tags

Symptoms:

- `Unable to read georef infos from worldfile or geotiff tags`
- `Unable to open raster, check logs for more infos`
- Raster has image dimensions but no bbox in the inspector.

Causes:

- PNG/JPEG/BMP/JPEG2000 has no adjacent world file.
- World file basename/extension does not match BlenderGIS search patterns.
- GeoTIFF tags are absent or not readable by the available engine.
- World-file values are malformed or use unexpected separators/extra text.

Recovery:

1. Run `python scripts/inspect_georaster.py IMAGE`.
2. If it says no world file, create or locate one beside the image. Accepted names include `.tfw`, `.tfwx`, `.tifw`, `.jgw`, `.jgwx`, `.jpgw`, `.pgw`, `.pgwx`, `.pngw`, `.wld`, and uppercase variants depending on the image extension.
3. Ensure the world file has six numeric lines: x pixel size, y rotation, x rotation, y pixel size, x origin, y origin.
4. Remember that world files do not store CRS; set `rastCRS`/`fileCRS` in the operator or establish scene CRS first.
5. If the raster is a GeoTIFF and metadata still fails without GDAL, try adding a sidecar world file or install/enable GDAL for stronger GeoTIFF support.

## Unsupported Format or Bad Image Header

Symptoms:

- `Unsupported format None` or `Unsupported format ...`
- `Unable to read raster size`
- Blender image load fails after metadata preflight.

Causes:

- File extension does not match actual header.
- Format is not one of the supported georaster families.
- JPEG2000/TIFF variant needs an imaging backend unavailable in the current Blender Python.
- File is corrupt or partially downloaded.

Recovery:

1. Run `scripts/inspect_georaster.py`; it reports header format and Pillow format when available.
2. Convert the image to GeoTIFF, PNG+world-file, or JPEG+world-file with a known GIS/image tool.
3. For DEMs or unusual data types, prefer GeoTIFF and GDAL.
4. If BlenderGIS rewrites to `_bgis.tif`, confirm the output directory is writable and the original image can be read by the selected engine.

## Missing GDAL / Pillow / ImageIO

Symptoms:

- Basemap start cancels: `No imaging library available. ImageIO module was not correctly installed.`
- Basemap grid/scene CRS mismatch cancels: `Please install gdal to enable raster reprojection support`.
- `No image engine available` or `... interface unavailable` from image processing.
- Reprojection/BigTIFF operations fail.

What each dependency does:

- **Pillow/PIL**: common image reads/writes for `NpImage`; sufficient for many non-reprojecting workflows.
- **ImageIO FreeImage**: alternate image engine; plugin availability can fail.
- **GDAL**: best support for GeoTIFF metadata, nodata/data types, raster/tile reprojection, BigTIFF, and large subsets.
- **pyproj/projection engines**: CRS transform support; route detailed CRS engine troubleshooting to `../georeferencing-and-crs/`.

Recovery:

1. Open BlenderGIS preferences and set `Image processing engine` to `AUTO` unless you intentionally force one backend.
2. If only Pillow is available, avoid workflows requiring GDAL: `BKG` with reprojection, basemap destination grid different from scene/source CRS, BigTIFF, and robust raster reprojection.
3. If a forced engine fails, change `imgEngine` back to `AUTO` or install the missing dependency in Blender's Python environment.
4. Use the root environment diagnostic when present: `../../scripts/check_blendergis_environment.py`.

## Broken or Missing Scene Georeference

Symptoms:

- `Scene georef is broken, please fix it beforehand`
- `Scene is not georef`
- `Cannot set scene crs, check logs for more infos`
- `Non overlap data` after choosing what seems to be the right raster.

Recovery:

1. Route scene CRS/origin repair to `../georeferencing-and-crs/`.
2. For first raster import into an empty scene, provide `rastCRS`/`fileCRS`; BlenderGIS can set the scene CRS and origin from the raster/grid center.
3. For existing georeferenced scenes, set `reprojection=True` only when the raster CRS differs from scene CRS; an incorrect CRS choice causes overlap and placement failures.
4. If origin exists but CRS is unset or inconsistent, fix the geoscene before trying DEM query, basemap, `MESH`, `DEM` on existing mesh, or clipped `DEM_RAW`.

## Nodata, Fill, and DEM Spikes

Symptoms:

- DEM displacement has spikes, holes, pits, or extreme values.
- Terrain imports but height scale is wildly wrong.
- DEM raw point cloud has missing areas or bad faces.

Causes:

- DEM contains nodata values such as `-9999` or a large sentinel.
- Nodata metadata was not read because GDAL/GeoTIFF tags are unavailable.
- Signed int16 DEM was loaded directly as a displacement texture.
- `MESH` ASCII mode kept nodata values in faces.

Recovery:

1. Inspect metadata with `scripts/inspect_georaster.py`; if it cannot report nodata, use a GIS tool or GDAL externally to inspect band nodata.
2. For `importgis.georaster(importMode='DEM')`, retry with `fillNodata=True` when nodata exists and holes should be interpolated.
3. Prefer 32-bit float GeoTIFF for DEM displacement; BlenderGIS rewrites signed int16 to `_bgis.tif` to avoid Blender texture interpretation issues.
4. For ASCII grids with nodata, choose `importMode='CLOUD'` if you want nodata skipped. If you need faces, preprocess/fill nodata before import or accept that `MESH` will include nodata heights.
5. Validate `demInterpolation`: enable for smoother terrain, disable for exact cell stepping.

## DEM Too Large / Step Choices

Symptoms:

- Blender hangs or becomes unresponsive.
- Import creates an enormous mesh or memory usage spikes.
- Web DEM query cancels `Too large extent`.

Recovery:

1. For raw vertices (`DEM_RAW`) or ASCII imports, estimate vertices: approximately `ceil(width/step) * ceil(height/step)`. Faces are almost the same count when `buildFaces=True`.
2. Increase `step` for large datasets. Example: `step=10` keeps about 1% of pixels.
3. Prefer `importMode='DEM'` with `subdivision='subsurf'` for visual terrain instead of `DEM_RAW` when exact sample vertices are not required.
4. Use `clip=True` only with a valid georeferenced target mesh and only when the clipped extent genuinely reduces size.
5. For `importgis.dem_query`, reduce the selected mesh/top-view extent below the 1,000,000-unit guard before retrying.

## Background Image Mode Fails

Symptoms:

- `Raster reprojection is not possible in background mode`
- `Cannot apply a rotation in background image mode`
- `Background image needs equal pixel size in map units in both x ans y axis`

Recovery:

- Use `PLANE` instead of `BKG` when reprojection, rotation, or unequal pixel sizes are involved.
- If you must use `BKG`, create a north-up, square-pixel raster in the scene CRS before importing.
- Confirm pixel sizes/rotation with `scripts/inspect_georaster.py`.

## Non-overlap in MESH / DEM-on-Mesh / Clip

Symptoms:

- `Non overlap data`
- `There isn't georef mesh to apply on`
- `No working extent`

Recovery:

1. Ensure the scene is fully georeferenced and the target mesh exists.
2. Confirm `objectsLst` points to the intended mesh index; Blender's object list order can change.
3. Verify the target mesh bbox and raster bbox are in the same CRS. Use `reprojection=True` and correct `rastCRS` only if they differ.
4. If clipping, choose a mesh whose bbox overlaps the DEM in the DEM CRS after reprojection.
5. If no mesh target exists, use `PLANE` or non-mesh `DEM` first.

## OpenTopography API-Key Failure

Symptoms:

- `Please register to opentopography.org and request for an API key` before any network delay.
- DEM query dialog shows an `Api Key` field when the selected server URL contains `opentopography`.

Explanation:

- Built-in OpenTopography SRTM 30m/90m templates include `{API_KEY}`.
- BlenderGIS checks the preference `opentopography_api_key` before formatting/downloading the URL.
- Without a key, this is a credentials/configuration issue, not a service outage.

Recovery:

1. Register for an OpenTopography API key and paste it into BlenderGIS preferences under Remote datasource > OpenTopography Api Key.
2. Alternatively choose a DEM server template that does not require OpenTopography, such as a properly configured GMRT template, if suitable for the target area.
3. If a key is present but download fails, then troubleshoot network/service status, quota, bbox, and HTTP errors.

## SRTM Latitude Limits

Symptoms:

- `SRTM is not available beyond 60 degrees north`
- `SRTM is not available below 56 degrees south`

Cause:

- The selected DEM server string contains `SRTM`, and the WGS84 bbox falls outside SRTM coverage.

Recovery:

- Choose a non-SRTM DEM service covering the area.
- Reduce/recenter the query extent if it only slightly crosses the limit.
- Do not retry with the same SRTM server and same bbox; the operator will cancel deterministically.

## DEM Service / Network Failures

Symptoms:

- `Cannot reach OpenTopography web service, check logs for more infos`
- `Cannot reach SRTM web service provider, server can be down or overloaded. Please retry later`
- Downloaded `srtm.tif` is corrupt or not georeferenced.

Recovery:

1. Confirm scene bbox and service URL template placeholders (`{W}`, `{E}`, `{S}`, `{N}`, optional `{API_KEY}`).
2. Check API key/quota and service status in a browser if policy permits.
3. Retry later for server overload/timeouts.
4. If the service returns a non-GeoTIFF error body, delete the bad `srtm.tif` and retry after fixing credentials/URL.
5. For reproducible offline work, download a DEM manually from a trusted source and import it with `importgis.georaster(importMode='DEM')`.

## Basemap Service, Network, or Cache Failures

Symptoms:

- Basemap remains gray/pink/red or empty.
- Header progress stays on downloading/building mosaic.
- Tile service HTTP errors, invalid tile data, or cache corruption.
- `Please define a valid cache folder path in addon's preferences` or `The selected cache folder has no write access`.

Recovery:

1. Confirm `cacheFolder` exists and is writable. BlenderGIS stores tile cache `.gpkg` files there.
2. If the scene CRS differs from selected grid CRS, install/enable GDAL or choose a grid matching the scene/source to avoid raster reprojection.
3. Try a conservative public source/layer such as `OSM` / `MAPNIK` / `WM` to separate service-specific issues from add-on configuration.
4. Delete the affected `{source}_{layer}_{grid}.gpkg` cache file if cached tiles are corrupt or stale. Tiles older than 90 days are already treated as missing, but corrupt fresh rows may persist.
5. Check network/proxy/firewall and service usage terms. Some services rate-limit, block referers/user agents, or change URL templates.
6. If the current mosaic is valid but not exported, press `E` in the map viewer to make a real textured mesh; otherwise the background mosaic is a temporary viewer artifact.

## Basemap Search Fails

Symptoms:

- `view3d.map_search` returns cancelled, map-start reports `No location found`, or origin does not move.

Recovery:

1. Check network access to Nominatim and whether a result exists for the query.
2. Try a more specific query string.
3. If scene georef is broken, repair it first.
4. Be aware that Nominatim is a public service with usage policies/rate limits; avoid scripted high-volume queries.

## Cache Privacy and Cleanup

- Basemap cache files store downloaded map tiles for viewed areas. They can reveal approximate places inspected.
- DEM downloads may write `srtm.tif` next to the `.blend` file or in Blender's temp directory.
- Clean up cache `.gpkg` files and temporary DEMs if privacy or disk usage matters.
- Do not include API keys in public skill files, screenshots, logs, or shared `.blend` metadata.

## Error-to-Recovery Matrix

| Message / symptom | Likely cause | First recovery |
| --- | --- | --- |
| `Unable to read georef infos...` | Missing world file/GeoTIFF tags | Run inspector; add world file or use GDAL/GeoTIFF. |
| `Unsupported format` | Bad/unsupported image header | Convert to GeoTIFF/PNG/JPEG + world file. |
| `No image engine available` | GDAL/ImageIO/Pillow missing or forced engine unavailable | Set image engine `AUTO`; install a supported image backend. |
| `Please install gdal...` | Raster/tile reprojection needed | Install GDAL or choose matching CRS/grid/no-reprojection workflow. |
| `Scene georef is broken...` | Inconsistent CRS/origin state | Route to georeferencing sub-skill. |
| `Non overlap data` | Wrong CRS, origin, target mesh, or extent | Verify bboxes and reprojection choice. |
| `Too large extent` | Web DEM bbox too wide/high | Reduce selected mesh/top-view extent. |
| OpenTopography API-key message | Missing credentials | Set `opentopography_api_key` or choose another DEM service. |
| SRTM latitude messages | Outside SRTM coverage | Choose non-SRTM DEM service. |
| Gray/pink/red basemap | missing/corrupt/service-failed tiles | Check cache folder/network; delete bad cache; try another source. |

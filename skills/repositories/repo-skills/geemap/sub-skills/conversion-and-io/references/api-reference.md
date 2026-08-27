# API reference: conversion and I/O

This reference lists the verified geemap entry points most relevant to
conversion, exports, and format movement. Prefer these module-qualified names
when ambiguity exists.

## Conversion APIs (`geemap.conversion`)

| Function | Signature summary | Use and cautions |
|---|---|---|
| `js_to_python` | `(in_file, out_file=None, use_qgis=True, github_repo=None, show_map=True, import_geemap=False, Map="m") -> str | None` | Converts one Earth Engine JavaScript file to Python. `use_qgis` and `import_geemap` cannot both be true. Writes `out_file` and returns generated code. |
| `js_snippet_to_py` | `(in_js_snippet, add_new_cell=True, import_ee=True, import_geemap=False, show_map=True, Map="m") -> list[str] | None` | Converts a JavaScript snippet. Use `add_new_cell=False` outside an interactive notebook to avoid mutating notebook state. |
| `js_to_python_dir` | `(in_dir, out_dir=None, use_qgis=True, github_repo=None, import_geemap=False, Map="m") -> None` | Recursively converts `*.js` files to `*_geemap.py` files. Use explicit `out_dir` for clean generated output. |
| `get_js_examples` | `(out_dir=None) -> str` | Returns package example JS directory or copies examples to `out_dir`. When copying, pass a `pathlib.Path`. |
| `get_nb_template` | `(download_latest=False, out_file=None) -> pathlib.Path` | Returns packaged template or copies/downloads it. `download_latest=True` contacts GitHub. |
| `py_to_ipynb` | `(in_file, template_file=None, out_file=None, github_username=None, github_repo=None, Map="m") -> None` | Converts one Earth Engine Python script to notebook via `ipynb-py-convert`; optional dependency required. |
| `py_to_ipynb_dir` | `(in_dir, template_file=None, out_dir=None, github_username=None, github_repo=None, Map="m") -> None` | Recursively converts `*_geemap.py` files to notebooks. |
| `execute_notebook` | `(in_file) -> None` | Executes a notebook in place via `jupyter nbconvert --execute`; may contact EE and run arbitrary notebook code. |

## Image and raster export APIs (`geemap.common`, top-level aliases where present)

| Function | Signature summary | Use and cautions |
|---|---|---|
| `ee_export_image` | `(ee_object, filename, scale=None, crs=None, crs_transform=None, region=None, dimensions=None, file_per_band=False, format="ZIPPED_GEO_TIFF", unzip=True, unmask_value=None, timeout=300, proxies=None, verbose=True) -> None` | Immediate local download of one `ee.Image`; `filename` must end with `.tif`. Formats: `ZIPPED_GEO_TIFF`, `GEO_TIFF`, `NPY`. |
| `ee_export_image_collection` | `(ee_object, out_dir, scale=None, crs=None, crs_transform=None, region=None, dimensions=None, file_per_band=False, format="ZIPPED_GEO_TIFF", unmask_value=None, filenames=None, timeout=300, proxies=None, verbose=True)` | Downloads each image in an `ee.ImageCollection`; counts images with `getInfo()`. Use small collections. |
| `ee_export_image_to_drive` | `(image, description="myExportImageTask", folder=None, fileNamePrefix=None, dimensions=None, region=None, scale=None, crs=None, crsTransform=None, maxPixels=None, shardSize=None, fileDimensions=None, skipEmptyTiles=None, fileFormat=None, formatOptions=None, **kwargs)` | Starts an EE batch image export to Drive. |
| `ee_export_image_to_asset` | `(image, description="myExportImageTask", assetId=None, pyramidingPolicy=None, dimensions=None, region=None, scale=None, crs=None, crsTransform=None, maxPixels=None, **kwargs)` | Starts image export to an EE Asset. Short asset IDs may be expanded under the authenticated user/project. |
| `ee_export_image_to_cloud_storage` | `(image, description="myExportImageTask", bucket=None, fileNamePrefix=None, dimensions=None, region=None, scale=None, crs=None, crsTransform=None, maxPixels=None, shardSize=None, fileDimensions=None, skipEmptyTiles=None, fileFormat=None, formatOptions=None, **kwargs)` | Starts image export to Cloud Storage; requires bucket permissions. |
| `ee_export_image_collection_to_drive` | `(collection, ...)` | Starts batch export tasks for collection images to Drive. |
| `ee_export_image_collection_to_asset` | `(collection, ...)` | Starts batch export tasks for collection images to EE Assets. |
| `ee_export_image_collection_to_cloud_storage` | `(collection, ...)` | Starts batch export tasks for collection images to Cloud Storage. |
| `ee_export_map_to_cloud_storage` | `(image, description="myExportMapTask", bucket=None, fileFormat=None, path=None, writePublicTiles=None, maxZoom=None, scale=None, minZoom=None, region=None, skipEmptyTiles=None, mapsApiKey=None, **kwargs)` | Starts export of map tiles to Cloud Storage. |

## Vector and table export APIs

| Function | Signature summary | Use and cautions |
|---|---|---|
| `ee_export_vector` | `(ee_object, filename, selectors=None, verbose=True, keep_zip=False, timeout=300, proxies=None)` | Immediate local download of an `ee.FeatureCollection` to `csv`, `geojson`, `json`, `kml`, `kmz`, or `shp`. Selectors must be a list of valid properties. |
| `ee_export_vector_to_drive` | `(collection, description="myExportTableTask", folder=None, fileNamePrefix=None, fileFormat="csv", selectors=None, maxVertices=None, **kwargs)` | Starts table export to Drive. Formats: `CSV`, `GeoJSON`, `KML`, `KMZ`, `SHP`, `TFRecord`. |
| `ee_export_vector_to_asset` | `(collection, description="myExportTableTask", assetId=None, maxVertices=None, **kwargs)` | Starts table export to EE Asset. |
| `ee_export_vector_to_cloud_storage` | `(collection, description="myExportTableTask", bucket=None, fileNamePrefix=None, fileFormat="csv", selectors=None, maxVertices=None, **kwargs)` | Starts table export to Cloud Storage. |
| `ee_export_vector_to_feature_view` | `(collection, description="myExportTableTask", assetId=None, ingestionTimeParameters=None, **kwargs)` | Starts FeatureView export. |
| `ee_export_video_to_drive` | `(collection, description="myExportVideoTask", folder=None, fileNamePrefix=None, framesPerSecond=None, dimensions=None, region=None, scale=None, crs=None, crsTransform=None, maxPixels=None, maxFrames=None, **kwargs)` | Starts RGB `ee.ImageCollection` video export to Drive. For timelapse design, route to the timelapse sub-skill. |
| `ee_export_video_to_cloud_storage` | `(collection, description="myExportVideoTask", bucket=None, fileNamePrefix=None, framesPerSecond=None, dimensions=None, region=None, scale=None, crs=None, crsTransform=None, maxPixels=None, maxFrames=None, **kwargs)` | Starts RGB `ee.ImageCollection` video export to Cloud Storage. |

## Local/EE data format helpers

| Function | Signature summary | Use and cautions |
|---|---|---|
| `csv_to_geojson` | `(in_csv, out_geojson=None, latitude="latitude", longitude="longitude", encoding="utf-8")` | Converts point CSV to GeoJSON; returns a GeoJSON object if `out_geojson=None`. |
| `csv_to_shp` | `(in_csv, out_shp, latitude="latitude", longitude="longitude", encoding="utf-8")` | Converts point CSV to shapefile and writes a WGS84 `.prj`. Requires `pyshp`. |
| `csv_to_ee` | `(in_csv, latitude="latitude", longitude="longitude", encoding="utf-8", geodesic=True)` | Converts point CSV to GeoJSON and then to an EE object via `coreutils.geojson_to_ee`. |
| `df_to_geojson` | `(df, out_geojson=None, latitude="latitude", longitude="longitude", encoding="utf-8")` | Converts a pandas DataFrame with lon/lat columns to GeoJSON. Requires `geojson`. |
| `shp_to_geojson` | `(in_shp, filename=None, **kwargs)` | Converts shapefile to GeoJSON; reprojects to EPSG:4326 with `geopandas` when needed. |
| `shp_to_ee` | `(in_shp, **kwargs)` | Converts an EPSG:4326 shapefile to an EE object. Top-level `geemap.shp_to_ee` is present. |
| `coreutils.geojson_to_ee` | `(geo_json, geodesic=False, encoding="utf-8") -> ee.Geometry | ee.FeatureCollection` | Verified GeoJSON-to-EE helper. Use this instead of missing top-level `geemap.geojson_to_ee`. |
| `ee_to_geojson` | `(ee_object, filename=None, indent=2, **kwargs)` | Converts small EE geometry/feature/collection objects using `.getInfo()`. |
| `ee_to_numpy` | `(ee_object, region=None, scale=None, bands=None, **kwargs)` | Computes pixels and returns a stacked NumPy array. Bound region/scale/bands to avoid oversized requests. |
| `ee_to_xarray` | `(dataset, drop_variables=None, io_chunks=None, n_images=-1, ..., crs=None, scale=None, projection=None, geometry=None, ee_initialize=True, project=None, opt_url=None, **kwargs)` | Wraps `xee` and xarray. Requires `xee`; legacy grid parameters may require `shapely`; initialization may require a project. |
| `numpy_to_ee` | `(np_array, crs=None, transform=None, transformWkt=None, band_names=None)` | Converts small NumPy arrays to an EE image. |
| `netcdf_to_ee` | `(nc_file, var_names, band_names=None, lon="lon", lat="lat", decimal=2)` | Converts a NetCDF variable to EE image data; optional scientific stack may be required. |

## Statistics helpers

| Function | Signature summary | Use and cautions |
|---|---|---|
| `zonal_stats` | `(in_value_raster, in_zone_vector, out_file_path=None, stat_type="MEAN", scale=None, crs=None, tile_scale=1.0, return_fc=False, verbose=True, timeout=300, proxies=None, **kwargs)` | Reduces image values by feature zones and either returns a FeatureCollection or exports a vector file. Allowed stats include `COUNT`, `MEAN`, `MAXIMUM`, `MEDIAN`, `MINIMUM`, `MODE`, `STD`, `MIN_MAX`, `SUM`, `VARIANCE`, `HIST`, `FIXED_HIST`, and combined count/mean reducers. |
| `zonal_stats_by_group` | `(in_value_raster, in_zone_vector, out_file_path=None, stat_type="SUM", decimal_places=0, denominator=1.0, scale=None, crs=None, crs_transform=None, best_effort=True, max_pixels=1e7, tile_scale=1.0, return_fc=False, ...)` | Summarizes integer grouped rasters by zones. Use when classes/categories must be summarized. |

## COG, STAC, and titiler helpers

| Function | Signature summary | Use and cautions |
|---|---|---|
| `cog_tile` | `(url, bands=None, titiler_endpoint=None, timeout=300, proxies=None, **kwargs)` | Returns a COG tile URL. Converts `palette`/`colormap` to `colormap_name`, discovers bands/stats through titiler, and may default to bands `[1,2,3]`. |
| `cog_bounds`, `cog_center`, `cog_bands`, `cog_stats`, `cog_info`, `cog_pixel_value` | COG metadata helpers | Network-bound titiler calls. Use before adding layers or diagnosing band/rescale choices. |
| `stac_tile` | `(url=None, collection=None, item=None, assets=None, bands=None, titiler_endpoint=None, timeout=300, **kwargs)` | Returns a STAC tile URL. If `collection` is provided and endpoint is absent, uses Planetary Computer. |
| `stac_bounds`, `stac_center`, `stac_bands`, `stac_stats`, `stac_info`, `stac_assets`, `stac_pixel_value` | STAC metadata helpers | Network-bound titiler/Planetary Computer calls. Validate `collection`, `item`, `assets`, and endpoint. |
| `load_GeoTIFF`, `load_GeoTIFFs` | `load_GeoTIFF(URL)`, `load_GeoTIFFs(URLs)` | Loads GeoTIFF URLs or `gs://` paths into EE images. GCS URLs must end in `.tif`. |

## Data catalog helpers

| Function | Signature summary | Use and cautions |
|---|---|---|
| `search_ee_data` | `(keywords, regex=False, source="ee", types=None, keys=["id", "provider", "tags", "title"])` | Searches EE/community catalog JSON over HTTP. Use `types=["image_collection"]` or similar for narrower results. |
| `ee_data_html`, `ee_data_thumbnail` | metadata/HTML helpers | Build display snippets and thumbnails; may require network and `beautifulsoup4`. |
| `geemap.datasets.DATA` | dot-notation catalog box | Useful for interactive exploration, but construction may fetch catalog data. Prefer explicit asset IDs in scripts. |

## OSM helpers (`geemap.osm`)

All OSM helpers wrap `osmnx` and usually require `geopandas` and online OSM or
Nominatim services.

| Input family | GeoDataFrame | Shapefile | GeoJSON |
|---|---|---|---|
| address | `osm_gdf_from_address(address, tags, dist=1000)` | `osm_shp_from_address(address, tags, filepath, dist=1000)` | `osm_geojson_from_address(address, tags, filepath=None, dist=1000)` |
| place | `osm_gdf_from_place(query, tags, which_result=None)` | `osm_shp_from_place(query, tags, filepath, which_result=None)` | `osm_geojson_from_place(query, tags, filepath=None, which_result=None)` |
| point | `osm_gdf_from_point(center_point, tags, dist=1000)` | `osm_shp_from_point(center_point, tags, filepath, dist=1000)` | `osm_geojson_from_point(center_point, tags, filepath=None, dist=1000)` |
| polygon | `osm_gdf_from_polygon(polygon, tags)` | `osm_shp_from_polygon(polygon, tags, filepath)` | `osm_geojson_from_polygon(polygon, tags, filepath=None)` |
| bbox | `osm_gdf_from_bbox(north, south, east, west, tags)` | `osm_shp_from_bbox(north, south, east, west, tags, filepath)` | `osm_geojson_from_bbox(north, south, east, west, tags, filepath=None)` |
| geocode | `osm_gdf_from_geocode(query, which_result=None, by_osmid=False)` | `osm_shp_from_geocode(query, filepath, which_result=None, by_osmid=False)` | `osm_geojson_from_geocode(query, filepath=None, which_result=None, by_osmid=False)` |
| XML | `osm_gdf_from_xml(filepath, polygon=None, tags=None)` | use GeoDataFrame `.to_file` | use GeoDataFrame `.to_file(..., driver="GeoJSON")` |

`osm_tags_list()` opens the OSM Map Features page in a browser; for automated
workflows, state the required tags instead of opening a browser.

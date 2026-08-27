# Geospatial utility API reference

Verified from installed `segment-geospatial` 1.4.1.

## File, download, and checkpoint helpers

```python
common.download_file(url=None, output=None, quiet=False, proxy=None, speed=None,
                     use_cookies=True, verify=True, id=None, fuzzy=False,
                     resume=False, unzip=True, overwrite=False, subfolder=False)
common.download_checkpoint(model_type="vit_h", checkpoint_dir=None, hq=False)
common.temp_file_path(extension)
common.check_file_path(file_path, make_dirs=True)
```

`download_file` supports normal URLs and Google Drive-style links. It can unzip
archives, resume, and skip existing files unless `overwrite=True`.

## Raster creation and CRS helpers

```python
common.tms_to_geotiff(output, bbox, zoom=None, resolution=None,
                      source="OpenStreetMap", crs="EPSG:3857", to_cog=False,
                      return_image=False, overwrite=False, quiet=False, **kwargs)
common.image_to_cog(source, dst_path=None, profile="deflate", **kwargs)
common.reproject(image, output, dst_crs="EPSG:4326", resampling="nearest",
                 to_cog=True, **kwargs)
common.get_profile(src_fp)
common.get_crs(src_fp)
common.get_features(src_fp, bidx=1)
```

## Image preparation

```python
common.prepare_image_for_sam(image, bands=None, channel_axis=-1)
common.read_image_for_sam(source, bands=None)
common.geotiff_to_jpg(geotiff_path, output_path=None, bands=None)
common.geotiff_to_jpg_batch(input_folder, output_folder, bands=None)
```

`prepare_image_for_sam` and `read_image_for_sam` are the key helpers for
multi-band RGB selection and uint8 conversion.

## Coordinate conversion

```python
common.transform_coords(x, y, src_crs, dst_crs, **kwargs)
common.vector_to_geojson(filename, output=None, **kwargs)
common.get_vector_crs(filename, **kwargs)
common.geojson_to_coords(geojson, src_crs, dst_crs)
common.coords_to_xy(src_fp, coords, coord_crs="epsg:4326",
                    return_out_of_bounds=False, **kwargs)
common.bbox_to_xy(src_fp, coords, coord_crs="epsg:4326", **kwargs)
common.geojson_to_xy(src_fp, geojson, coord_crs="epsg:4326", **kwargs)
common.rowcol_to_xy(src_fp, rows, cols, boxes=True, zs=None, offset="center",
                    output=None, dst_crs="EPSG:4326", **kwargs)
```

Use CRS conversion helpers before prompt prediction when user-provided prompts
are geospatial rather than pixel-based.

## Raster/vector outputs

```python
common.raster_to_vector(source, output, simplify_tolerance=None, dst_crs=None, **kwargs)
common.raster_to_gpkg(tiff_path, output, simplify_tolerance=None, **kwargs)
common.raster_to_shp(tiff_path, output, simplify_tolerance=None, **kwargs)
common.raster_to_geojson(tiff_path, output, simplify_tolerance=None, **kwargs)
common.write_features(gdf, dst_fp)
common.write_raster(dst_fp, dst_arr, profile, width, height, transform, crs)
```

## Tiling, array, and region helpers

```python
common.split_raster(filename, out_dir, tile_size=256, overlap=0)
common.merge_rasters(input_dir, output, input_pattern="*.tif",
                     output_format="GTiff", output_nodata=None,
                     output_options=["COMPRESS=DEFLATE"])
common.region_groups(image, connectivity=1, min_size=10, max_size=None,
                     threshold=None, properties=None, intensity_image=None,
                     out_csv=None, out_vector=None, out_image=None, **kwargs)
common.calculate_sample_grid(raster_h, raster_w, sample_h, sample_w, bound)
common.read_block(src, x, y, height, width, nodata=0, **kwargs)
common.write_block(dst, raster, y, x, height, width, bounds=None)
```

## Geometry cleanup and visualization

```python
common.regularize(data, output_path=None, parallel_threshold=1.0,
                  target_crs=None, simplify=True, simplify_tolerance=0.5,
                  allow_45_degree=True, diagonal_threshold_reduction=15,
                  allow_circles=True, circle_threshold=0.9, num_cores=1,
                  include_metadata=False, **kwargs)
common.smooth_vector(vector_data, output_path=None, segment_length=None,
                     smooth_iterations=3, num_cores=0, merge_collection=True,
                     merge_field=None, merge_multipolygons=True,
                     preserve_area=True, area_tolerance=0.01, **kwargs)
common.show_image(source, figsize=(12, 10), cmap=None, axis="off", fig_args={},
                  show_args={}, **kwargs)
common.overlay_images(image1, image2, alpha=0.5, backend="matplotlib", ...)
```

## Device helpers

```python
common.choose_device(empty_cache=True, quiet=True) -> str
common.get_device() -> torch.device
```

Use these for user-facing device selection, but still run a direct torch CUDA
allocation when SAM3 runtime readiness matters.

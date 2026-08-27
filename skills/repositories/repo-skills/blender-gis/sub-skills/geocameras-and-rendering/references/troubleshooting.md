# Geocameras and Rendering Troubleshooting

Use this matrix when BlenderGIS camera operators cancel, produce shifted outputs, or cannot be validated. Cross-cutting add-on install issues belong to the root troubleshooting reference; CRS/origin repair belongs to [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md).

## Quick diagnosis table

| Symptom or report | Likely source | Recovery |
| --- | --- | --- |
| `The scene must be georeferenced.` or `Scene isn't georef` | Scene lacks valid CRS and projected origin. | Route to [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md). Set a valid CRS and projected origin, then rerun the camera operator. |
| `Can't find GPS longitude or latitude.` | One selected photo lacks required GPS EXIF tags. | Preflight with `scripts/read_exif_gps.py`; remove or externally geotag failing files. |
| `Invalid format ...` | Input file is not detected as JPEG or TIFF by BlenderGIS. | Convert to JPEG/TIFF while preserving EXIF, or exclude it. |
| `Unable to open file. Checks logs for more infos.` | EXIF/TIFF/JPEG parser could not open the file. | Confirm file exists, is readable, is not corrupt, and can be opened by an image tool; then rerun preflight. |
| `Reprojection error. Check logs for more infos.` | GPS WGS84 coordinate could not be transformed to the scene CRS. | Validate the scene CRS and projection dependencies in the CRS sub-skill; test the lon/lat separately. |
| `No valid camera` | No camera has BlenderGIS geophoto metadata. | Create geophoto cameras first, or restore the `background`, `imageWidth`, and `imageHeight` camera-data custom properties. |
| `Wrong context` | `camera.geophotos_setactive` was run outside a 3D View. | Run from a 3D View area or use a context override that provides `space_data.type == 'VIEW_3D'`. |
| `Pre-selection is incorrect` | `camera.georender` selection is not exactly one mesh or one mesh plus one camera. | Switch to Object Mode and select exactly the required object set. |
| `This camera has not map resolution property` | Selected existing camera was not created by `camera.georender`, or lost `mapRes`. | Create a new georender camera from one mesh, or add/restore the camera-data `mapRes` custom property before updating. |
| Render georeferences with half-pixel shift concern | Misread world-file fifth/sixth lines as outer corner. | World files store upper-left pixel center; expect `xmin + origin + res/2` and `ymax + origin - res/2`. |

## Scene not georeferenced

Both camera placement and map render workflows require `GeoScene.isGeoref` to be true. That means:

- the scene has a valid CRS custom property (`SRID`), and
- the scene has projected origin custom properties (`crs x`, `crs y`).

Geophotos cancel in `invoke` before the file browser proceeds if this is false. Georender cancels during execution. Do not work around this by manually adding camera objects unless the task explicitly avoids georeferenced output; the output positions and world-file coordinates depend on the scene origin.

Recovery:

1. Route to [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md).
2. Fix any broken partial state, such as origin without CRS or invalid CRS.
3. Confirm projected origin is initialized.
4. Retry `camera.geophotos` or `camera.georender`.

## Missing GPS tags in a photo set

`camera.geophotos` requires all selected files to have latitude and longitude tags. It stops at the first file missing required GPS tags, so one bad photo can cancel a batch.

Preflight:

```bash
python ../scripts/read_exif_gps.py --json photo_a.jpg photo_b.jpg photo_c.jpg
```

From the root of the generated BlenderGIS skill tree, use:

```bash
python sub-skills/geocameras-and-rendering/scripts/read_exif_gps.py --json photo_a.jpg photo_b.jpg
```

Required tags for the BlenderGIS operator:

```text
GPSLatitude
GPSLatitudeRef
GPSLongitude
GPSLongitudeRef
```

Recovery options:

- Remove failing photos from the batch.
- Add/repair GPS EXIF with external image metadata tools, then rerun preflight.
- If only positions are needed and GPS is absent, do not use `camera.geophotos`; manually place objects or use another data source.

BlenderGIS reads EXIF here; it does not write or repair EXIF GPS tags.

## Invalid image format

The geophoto operator accepts only files detected as `JPEG` or `TIFF`. Its file browser filter includes `.jpg`, `.jpeg`, `.tif`, and `.tiff`, but extension alone is not enough: the file header must be recognized.

Recovery:

1. Confirm the file is a real JPEG/TIFF and not a renamed PNG/HEIC/raw file.
2. Convert unsupported files to JPEG/TIFF with metadata preserved.
3. Re-run `scripts/read_exif_gps.py` and ensure GPS still exists after conversion.
4. Select only valid JPEG/TIFF files in `camera.geophotos`.

## Reprojection failure from GPS to scene CRS

`camera.geophotos` reads photo GPS as WGS84 lon/lat and calls a reprojection from `EPSG:4326` to the current scene CRS. It cancels on projection exceptions.

Common causes:

- invalid or unsupported scene CRS string;
- missing optional projection backend for a CRS pair that cannot use the built-in path;
- coordinate values outside expected bounds;
- broken scene georef state where CRS and origin are inconsistent.

Recovery:

1. Use the EXIF helper to record the decimal lon/lat for the failing photo.
2. Route to [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md) and validate the scene CRS.
3. Test a single point transform from WGS84 to the scene CRS if a transform helper is available.
4. If the CRS requires `pyproj` or GDAL and that dependency is unavailable, enable the dependency or choose a supported CRS.
5. Retry with one photo first before processing the full batch.

## No valid camera for `camera.geophotos_setactive`

A camera is considered a valid geophoto camera only when it is a Blender camera object and its camera data block has the `background` custom property. The switch operator also expects `imageWidth` and `imageHeight` to set render resolution.

Recovery:

- Create cameras with `camera.geophotos` instead of generic Blender camera tools.
- If a camera was duplicated manually, copy these camera data custom properties from the original:

  ```text
  background
  imageWidth
  imageHeight
  orientation
  ```

- Confirm the photo path in `background` is still readable by Blender.

## Wrong context for geophoto switching

`camera.geophotos_setactive` checks `context.space_data.type`. It cancels outside the 3D View, including many text-editor or background execution contexts.

Recovery:

- Run the operator from the 3D View UI.
- If scripting, use a 3D View context override rather than a bare text-editor context.
- Avoid treating this operator as a headless batch command; it manipulates camera background display in a viewport-oriented context.

## Invalid selection for georender

`camera.georender` requires Object Mode and a strict selection:

- one selected mesh to create a camera; or
- one selected mesh plus one selected camera to update an existing georender camera.

It cancels if there are zero selected objects, more than two selected objects, non-mesh selected objects, two meshes, two cameras, curves without mesh conversion, or any other type combination.

Recovery:

1. Switch to Object Mode.
2. Deselect all.
3. Select exactly the mesh target.
4. Run `camera.georender` to create a fresh camera.
5. For updates, select exactly the target mesh and the existing georender camera.

If the target is a curve, point cloud, raster plane wrapper, or collection, convert or choose the actual mesh object first.

## Missing `mapRes` on an existing camera

When updating an existing camera, `camera.georender` reads `cam['mapRes']` on the first execution and writes it on redo. A normal Blender camera does not have this property.

Preferred recovery:

1. Select only the mesh.
2. Run `camera.georender` to create a new georender camera.
3. Use that camera for future updates.

Manual recovery when you intentionally want to reuse a camera:

```python
import bpy
cam_obj = bpy.data.objects['Your camera object name']
cam_obj.data['mapRes'] = 5.0  # map units per pixel
```

Then select the mesh and camera and rerun `camera.georender`. Confirm that the camera is orthographic and that the generated `.wld` text block matches expected values.

## World-file pixel-size expectations

The georender world file is based on target pixel size and selected mesh extent, not on arbitrary render settings edited later. If you change render resolution manually after running `camera.georender`, the saved world file may no longer match the rendered image.

Expected values:

```text
line 1: target_res
line 2: 0
line 3: 0
line 4: -target_res
line 5: scene_crsx + bbox_xmin + target_res / 2
line 6: scene_crsy + bbox_ymax - target_res / 2
```

Important details:

- Lines 5 and 6 are the center of the upper-left pixel, not the outer map corner.
- Line 4 is negative because image row coordinates increase downward.
- Render width/height are truncated with `int(dim / target_res)`.
- If target resolution does not divide the mesh extent exactly, the render dimensions may cover slightly less than the full continuous extent implied by the mesh dimensions. Use a pixel size that divides the extent, or explicitly accept truncation.
- If render dimensions become `0`, lower `target_res` or use a larger mesh extent.

## Background image missing after switching geophoto

If `camera.geophotos_setactive` selects a camera but no background appears:

1. Confirm the file path in camera data `background` exists and is readable.
2. Confirm the image can be loaded into Blender.
3. Check camera data `show_background_images` is enabled.
4. Check the active background image slot has `show_background_image = True` and `alpha = 1`.
5. Re-run `camera.geophotos_setactive` from a 3D View after restoring `background`.

## Orientation looks wrong

The geophoto camera workflow reads EXIF `Orientation` and adjusts camera Y rotation only for values `8`, `6`, and `3`. This is display-oriented handling and is noted as not fully tested in the source comments.

Recovery:

- Use the camera target empty to manually orient `TARGET_CAMERA` outputs.
- Confirm the image viewer and Blender agree on the EXIF orientation.
- Do not treat geophoto orientation as calibrated exterior orientation for photogrammetry.

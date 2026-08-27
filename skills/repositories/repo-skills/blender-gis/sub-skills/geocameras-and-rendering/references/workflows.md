# Geocameras and Rendering Workflows

These workflows cover BlenderGIS camera tasks without requiring access to the original repository. Operator details are in [operator-reference.md](operator-reference.md), and failure recovery is in [troubleshooting.md](troubleshooting.md).

## Workflow: preflight a photo set before `camera.geophotos`

Use this when a photo batch may contain non-image files, missing GPS tags, or inconsistent EXIF.

1. Run the bundled helper on every candidate photo:

   ```bash
   python sub-skills/geocameras-and-rendering/scripts/read_exif_gps.py IMG_0001.jpg IMG_0002.jpg
   ```

   Or request JSON for automation:

   ```bash
   python sub-skills/geocameras-and-rendering/scripts/read_exif_gps.py --json IMG_0001.jpg IMG_0002.jpg
   ```

2. Require every file to report:

   - `gps_present: true` in JSON, or a normal text report with latitude and longitude;
   - a supported image type (`JPEG` or `TIFF` for the BlenderGIS operator);
   - no parse errors.

3. Triage failures before opening Blender:

   - Missing GPS tags: remove the file from the geophoto batch, choose `EMPTY`/`CURSOR` only for files that still have GPS, or geotag the photo with external tooling. BlenderGIS does not write or repair EXIF GPS tags.
   - Invalid image format: convert to JPEG/TIFF while preserving EXIF, then re-run preflight.
   - Corrupt EXIF or unreadable file: fix the source file outside Blender.

4. Decide the output mode:

   - `TARGET_CAMERA`: best default for geophoto review because it creates a camera plus a track target.
   - `CAMERA`: use when you only need camera objects.
   - `EMPTY`: use when you need position markers but not photo backgrounds.
   - `CURSOR`: use for one-off cursor placement from GPS coordinates.

5. Ensure the Blender scene is georeferenced before invoking BlenderGIS camera operators. If not, route to [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md).

## Workflow: create geophoto cameras from EXIF GPS photos

Goal: create camera objects positioned at photo GPS coordinates in the current scene CRS.

1. Preflight the photo set with [scripts/read_exif_gps.py](../scripts/read_exif_gps.py) as described above.
2. In Blender, enable BlenderGIS and verify the `GIS` menu exists in the 3D View.
3. Confirm the scene is georeferenced:

   - valid CRS (`SRID` scene custom property), and
   - projected origin (`crs x`, `crs y` scene custom properties).

   If those are missing or broken, use the CRS/origin workflow in [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md).

4. Open `GIS > Camera > Geophotos`.
5. Select the JPEG/TIFF files.
6. Choose `Action` (`exifMode`): normally `Target Camera`.
7. Execute.
8. Validate results:

   - Each valid photo produced one camera, target camera pair, empty, or cursor move according to `exifMode`.
   - Camera names are derived from photo basenames.
   - Camera data contains custom properties `background`, `imageWidth`, `imageHeight`, and `orientation`.
   - Object locations equal reprojected WGS84 GPS coordinates minus the scene projected origin.
   - If no camera was active before the run, the first created geophoto camera becomes the active scene camera.

### Notes and limitations

- Input GPS is assumed to be WGS84 longitude/latitude (`EPSG:4326`).
- Altitude is used as Z when `GPSAltitude` exists; otherwise Z is `0`.
- Missing `FocalLengthIn35mmFilm` falls back to a 35 mm lens.
- Orientation handling only adjusts for EXIF orientation `8`, `6`, and `3`; treat it as approximate camera display orientation.
- The operator stops on the first invalid file in the batch. Preflight first when mixed file quality is likely.

## Workflow: switch to a geophoto camera and display its background

Goal: make one geophoto camera active and show its source photo as the camera background.

1. Run this only from a 3D View area. The operator requires `context.space_data.type == 'VIEW_3D'`.
2. Ensure at least one scene camera has a `background` custom property on the camera data block. Cameras created by `camera.geophotos` have this property.
3. Open `GIS > Camera >` the geophoto switch/refresh entry, or call:

   ```python
   bpy.ops.camera.geophotos_setactive('EXEC_DEFAULT', camLst='PHOTO_BASENAME')
   ```

4. Pick the desired camera.
5. Validate results:

   - `scene.camera` is the chosen camera.
   - Render resolution matches the source photo dimensions.
   - The camera has background images enabled.
   - The source image is visible as the active camera background with alpha `1`.

### Recovering a manually edited camera

If a geophoto camera was duplicated or edited, preserve these camera data custom properties before using `camera.geophotos_setactive`:

```text
background: path to the source photo
imageWidth: integer width
imageHeight: integer height
orientation: EXIF orientation integer, usually 1
```

Only `background`, `imageWidth`, and `imageHeight` are required by the switch workflow.

## Workflow: create a georeferenced orthographic render camera

Goal: render a selected mesh as a map image and extract world-file text for georeferencing the render.

1. Prepare a georeferenced scene. Route CRS/origin setup to [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md).
2. Import or create the target mesh. Route raster/image import to [raster-dem-and-basemaps](../../raster-dem-and-basemaps/SKILL.md) and vector import to the vector sub-skill if needed.
3. Switch to Object Mode.
4. Select exactly one mesh object.
5. Open `GIS > Camera > Georender`.
6. Set:

   - `Camera name`: meaningful output camera name, e.g. `ortho_map_5m`.
   - `Pixel size` (`target_res`): map units per rendered pixel. If the scene CRS uses meters, `5` means 5 meters per pixel.
   - `Z loc. off.` (`zLocOffset`): extra camera height as percent of mesh Z dimension. Increase only if clipping occurs.

7. Execute.
8. Validate:

   - A camera with the chosen name is selected and active.
   - Camera type is orthographic and frames the selected mesh.
   - Camera data custom property `mapRes` equals `target_res`.
   - Render resolution is `int(mesh_width / target_res)` by `int(mesh_height / target_res)` at `100%`.
   - A Blender text block named `<camera name>.wld` contains six world-file lines.

9. Render the image using Blender's render workflow.
10. Save the render image and copy the `.wld` text block to a sidecar world file with the appropriate extension for your image format (`.wld`, `.jgw`, `.pgw`, `.tfw`, etc., depending on downstream software expectations).

## Workflow: update an existing georender camera

Use this when the target mesh extent or pixel size changed and the camera was originally created by `camera.georender`.

1. Select exactly two objects: the target mesh and the existing georender camera.
2. Confirm the camera data has custom property `mapRes`. If not, use the recovery in [troubleshooting.md](troubleshooting.md) or create a new georender camera from one selected mesh.
3. Run `GIS > Camera > Georender`.
4. On the first execution, the operator reads the existing `mapRes` into `target_res`.
5. In the redo panel, adjust `Pixel size`, `Camera name`, or `Z loc. off.` as needed.
6. Validate the updated render resolution and regenerated `<camera name>.wld` text block.

## Workflow: compute expected world-file values before or after georender

Use this difficult case for verification or when a downstream GIS tool reports a shifted render.

Inputs:

- selected mesh world-space extent in Blender scene units:

  ```text
  xmin, ymin, xmax, ymax
  ```

- scene projected origin:

  ```text
  crsx, crsy
  ```

- target pixel size:

  ```text
  target_res
  ```

Expected render resolution:

```text
resolution_x = int((xmax - xmin) / target_res)
resolution_y = int((ymax - ymin) / target_res)
```

Expected world-file lines:

```text
target_res
0
0
-target_res
crsx + xmin + target_res / 2
crsy + ymax - target_res / 2
```

Concrete example:

```text
mesh extent: xmin=100, ymin=200, xmax=1100, ymax=700
scene origin: crsx=500000, crsy=4600000
target_res: 5
```

Expected render size:

```text
resolution_x = int((1100 - 100) / 5) = 200
resolution_y = int((700 - 200) / 5) = 100
```

Expected world-file lines:

```text
5
0
0
-5
500102.5
4600697.5
```

Interpretation: the fifth and sixth lines are the projected coordinates of the center of the upper-left rendered pixel, not the outer corner of the mesh extent. The half-pixel offset is intentional.

## Workflow: decide where to route related tasks

- Need to set CRS, initialize origin, fix broken `SRID`/`crs x`/`crs y`, or understand reprojection failures? Route to [georeferencing-and-crs](../../georeferencing-and-crs/SKILL.md).
- Need to import a GeoTIFF, JPEG+world-file, DEM, or basemap before rendering? Route to [raster-dem-and-basemaps](../../raster-dem-and-basemaps/SKILL.md).
- Need to render an existing mesh with a world file? Stay in this sub-skill and use `camera.georender`.
- Need geotagged camera markers from photos? Stay in this sub-skill and use `camera.geophotos`.

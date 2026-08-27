# Geometry and visualization troubleshooting

Use this when box coordinates, point projections, or visualizer output look wrong.

## Box looks shifted or has the wrong vertical position

Likely cause:

- The box was constructed with the wrong `origin`.
- A gravity-center tensor was fed into a bottom-center constructor, or the reverse.
- `center_mode` does not match the box family when drawing on a point cloud.

What to check:

1. Compare `bottom_center` and `gravity_center` first.
2. Confirm whether the box class is LiDAR, Camera, or Depth.
3. Re-read the constructor defaults from [`geometry-api.md`](geometry-api.md).
4. Re-run [`scripts/inspect_geometry.py`](../scripts/inspect_geometry.py) and compare the origin-shift output.

## Yaw looks mirrored, wrapped, or off by 90 degrees

Likely cause:

- The wrong source/destination mode was used during conversion.
- `correct_yaw` was needed because the transform matrix rotates the heading.
- A camera box was interpreted like a LiDAR or Depth box.
- The angle is equivalent modulo `2π`, but it was compared without normalization.

What to check:

1. Verify the box family and the destination family.
2. Use `limit_period` before comparing angles.
3. Remember that camera yaw uses the y axis, while LiDAR and Depth yaw use the z axis.
4. If the box footprint is right but the facing is wrong, check whether the mode conversion should have used `correct_yaw=True`.

## Projection is empty, shifted, or clipped

Likely cause:

- The points or boxes are not in camera coordinates when a camera projection is used.
- The wrong metadata key was supplied for the projection path.
- The projection matrix shape is wrong.
- The points are behind the camera or have a non-positive depth.
- `img_size` filtered the projected box out of the image.

What to check:

1. Match the box class to the correct projection matrix key.
2. Confirm the matrix shape is 3x3, 3x4, or 4x4.
3. Confirm `points_cam2img(..., with_depth=True)` produces positive depth.
4. If `draw_proj_bboxes_3d` is used with `img_size`, try again without that filter.
5. Inspect the raw projected corners before assuming the visualizer is wrong.

## Point cloud visualizer shows nothing

Likely cause:

- The point cloud was not set before drawing boxes.
- The visualizer received the wrong point mode.
- The host has no GUI display, so live Open3D rendering cannot open a window.
- The requested scene was saved to disk, but the live window was not meant to persist.

What to check:

1. Call `set_points` before `draw_bboxes_3d`.
2. Pass the correct `pcd_mode` for LiDAR, Camera, or Depth.
3. On remote or headless hosts, rely on saved output instead of a live window.
4. If `draw_seg_mask` is used, remember that the helper offsets the new point cloud along x to avoid overlap.

## 2D image render looks wrong

Likely cause:

- The image was still in BGR order when `set_image` was called.
- The wrong projection matrix was used for the box class.
- The image file and metadata do not describe the same sample.

What to check:

1. Convert BGR images to RGB before calling `set_image`.
2. Verify the camera key and projection matrix from metadata.
3. Check that the box tensor and the image belong to the same sample.

## Saved files are missing

Likely cause:

- The save path was not writable.
- A live display was expected on a headless host.
- The caller never set an output path.

What to check:

1. Confirm the output directory exists and is writable.
2. Prefer saved files when display is unavailable.
3. Re-run the synthetic smoke check if you need a fast geometry-only sanity test.

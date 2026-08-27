# Visualization reference

Use this reference when you need to inspect, project, or save geometry artifacts without running a model.

## What the visualizer does

`Det3DLocalVisualizer` is the main 3D visualizer class. It can draw 2D image overlays, point clouds, projected 3D boxes, BEV boxes, and per-point semantic colors.

| Task | Helper | Input state required first | Notes |
| --- | --- | --- | --- |
| Project points onto an RGB image | `draw_points_on_image` | `set_image(rgb_image)` | The image must already be RGB. Use `points_cam2img` for the projection matrix. |
| Draw 3D boxes on a point cloud | `draw_bboxes_3d` | `set_points(points, pcd_mode=...)` | The visualizer converts boxes to Depth mode for Open3D display. |
| Draw projected 3D boxes on an image | `draw_proj_bboxes_3d` | `set_image(rgb_image)` | The helper selects the projection path from the box class. |
| Draw BEV boxes | `draw_bev_bboxes` | `set_bev_image()` or a custom BEV canvas | Useful for top-down inspection of yaw and footprint. |
| Colorize semantic points | `draw_seg_mask` | `set_points(points, pcd_mode=...)` | The helper expects point coordinates plus per-point colors. |
| Combine GT/pred samples | `add_datasample` | `data_input` + `Det3DDataSample` | Handles both 3D and 2D result drawing and backend output. |

## Drawing modes and their caveats

### `set_points`

- Accepts point arrays in LiDAR, Camera, or Depth mode.
- `pcd_mode=0` means LiDAR, `1` means Camera, and `2` means Depth.
- Non-Depth points are converted to Depth mode internally for Open3D display.
- `mode='xyz'` draws only coordinates.
- `mode='xyzrgb'` expects RGB values in columns 4-6 and normalizes them when needed.
- A coordinate frame is created automatically.

### `draw_bboxes_3d`

- Accepts any `BaseInstance3DBoxes` subclass.
- Internally converts boxes to Depth mode before drawing on the point cloud scene.
- `center_mode='lidar_bottom'` is the common case for LiDAR scenes.
- `center_mode='camera_bottom'` is the matching camera alternative.
- If the box sits at the wrong height, the most common cause is a center-mode mismatch.

### `draw_proj_bboxes_3d`

- Picks the projection helper from the box class:
  - LiDAR boxes -> `lidar2img`
  - Camera boxes -> `cam2img`
  - Depth boxes -> `depth2img`
- `input_meta` must contain the matching matrix.
- `img_size` filters boxes that fall too far outside the visible frame.
- The helper draws both the wireframe and the front face polygon.
- If nothing appears, check the box class, the matrix key, and whether the projected corners are in front of the camera.

### `draw_bev_bboxes`

- Uses `bboxes_3d.bev` and a simple top-down canvas.
- It is the fastest way to diagnose yaw and width/length swaps.
- A wrong-looking BEV footprint usually means the box mode or origin is wrong, not the drawing code.

### `draw_seg_mask`

- Expects an `Nx6` array: XYZ plus RGB.
- If a point cloud already exists, the helper offsets the new mask along the x-axis so the overlay does not collide with the original cloud.
- This is useful when comparing GT and prediction masks in the same scene.

## Saved output conventions

- `add_datasample(..., out_file=...)` writes the rendered image to the requested file name.
- If a 2D image is also produced, a sibling file with `_2d` in the name is written as well.
- `show=True` switches from pure file output to live display behavior.
- On headless or remote hosts, prefer saved files and avoid depending on live Open3D windows.
- The evaluation replay workflow usually stores the rendered geometry in a chosen output directory; inspect the saved files there instead of expecting a visible window.

## Image and projection checklist

1. Confirm the image is RGB before passing it to the visualizer.
2. Confirm the box class matches the projection matrix key.
3. Confirm the point or box tensor is already in the correct coordinate family.
4. Confirm the camera-depth sign conventions before comparing projections.
5. Confirm the output directory is writable when you expect saved files.

## Helpers that pair well with the visualizer

- [`references/geometry-api.md`](geometry-api.md) explains the box, point, and projection conventions behind each draw helper.
- [`references/troubleshooting.md`](troubleshooting.md) lists the common reasons a rendered scene looks shifted, clipped, or blank.
- [`scripts/inspect_geometry.py`](../scripts/inspect_geometry.py) runs a tiny smoke check on the same geometry rules used here.

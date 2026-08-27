# Nerfstudio data formats

## Dataset directory

A typical processed dataset contains an image directory and one or more `transforms*.json` files. Train commands usually pass the dataset directory:

```bash
ns-train nerfacto --data PROCESSED_DATA_DIR
```

## Coordinate conventions

- Camera/view space follows OpenGL/Blender conventions: +X right, +Y up, +Z points backward from the camera; -Z is the look direction.
- World space is oriented so +Z is up.
- COLMAP/OpenCV poses use a different convention; use Nerfstudio converters/dataparsers instead of manually flipping axes unless you know the frame convention.
- Pixel coordinates are treated as pixel centers.

## `transforms*.json` fields

Top-level intrinsics may apply to every frame:

```json
{
  "camera_model": "OPENCV",
  "fl_x": 1072.0,
  "fl_y": 1068.0,
  "cx": 1504.0,
  "cy": 1000.0,
  "w": 3008,
  "h": 2000,
  "frames": []
}
```

Each frame needs at least:

```json
{
  "file_path": "images/frame_00001.jpg",
  "transform_matrix": [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]
  ]
}
```

Per-frame intrinsics are allowed, but if one frame provides a per-frame intrinsic key such as `fl_x`, every frame should provide it consistently.

## Optional depth and masks

- `depth_file_path` can be added per frame for depth-supervised methods such as depth-nerfacto. Depth values are expected in millimeters by default.
- `mask_path` can be added per frame to ignore regions. Masks should be one-channel black/white images at the RGB image resolution. If masks are used, all frames should have masks.

## Split lists

Optional top-level lists `train_filenames`, `val_filenames`, and `test_filenames` define explicit splits. Paths should match frame `file_path` values after normalization. If lists are absent, the dataparser creates splits using its configured eval mode.

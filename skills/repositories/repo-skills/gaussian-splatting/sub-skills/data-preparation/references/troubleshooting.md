# Data Preparation Troubleshooting

## `Could not recognize scene type!`

The loader did not find either `sparse/` or `transforms_train.json` under the source path.

Fix:

- For COLMAP data, verify `sparse/0` and an image directory exist.
- For Blender/NeRF synthetic data, verify `transforms_train.json` and `transforms_test.json` exist.
- Run `scripts/validate_scene_layout.py --scene-root <scene>` before retrying training.

## Unsupported COLMAP Camera Model

Symptom: `Colmap camera model not handled: only undistorted datasets (PINHOLE or SIMPLE_PINHOLE cameras) supported!`

Cause: the source contains distorted camera models such as `OPENCV`.

Fix: run the conversion/undistortion workflow so the final `sparse/0` model uses `PINHOLE` or `SIMPLE_PINHOLE`.

## Images Directory Missing

If COLMAP files exist but image loading fails, check the `--images` value. The default is `images`, but evaluation datasets often use `images_2` or `images_4`. Run:

```bash
python validate_scene_layout.py --scene-root <scene> --images images_4
```

## Depth Regularization Fails on `depth_params.json`

For real COLMAP scenes with `-d/--depths`, the loader requires `sparse/0/depth_params.json`. Generate it with the bundled depth-scale helper after per-image depth PNGs exist:

```bash
python make_depth_scale.py --base-dir <scene> --depths-dir <scene>/<depth-folder>
```

If many entries get scale `0`, COLMAP points or depth maps may not overlap enough for reliable scale fitting.

## Depth PNG Missing or Corrupted

The loader maps image names to depth files using the image stem. For an image `frame_0001.jpg`, the depth PNG should be named `frame_0001.png` inside the depth folder. Check that PNGs are readable and grayscale or single-channel compatible.

## COLMAP Command Fails

Common causes:

- `colmap` is not on PATH or `--colmap_executable` points to the wrong executable.
- GPU SIFT fails; retry conversion with `--no_gpu`.
- Input images are not under `<scene>/input`.
- The scene directory is not writable.

COLMAP conversion is external and mutating. Do not run it automatically without confirming the user wants files created.

## ImageMagick Resize Fails

`--resize` needs a `magick` executable. If it is unavailable, omit `--resize` and train using the default `images` folder, or install ImageMagick and rerun conversion with `--magick_executable` if needed.

## Blender JSON Paths Fail

Blender/NeRF synthetic frame paths are read from `file_path` in the JSON and `.png` is assumed by default. Verify the referenced images exist relative to the scene root and use the expected extension.

## Blender Synthetic Scene Fails With a PIL `Cannot handle this data type` Error

Symptom: training on a Blender/NeRF synthetic scene crashes while building the scene with a `TypeError` from `PIL.Image.fromarray`, often mentioning `Cannot handle this data type: (1, 1, 3), |i1`.

Cause: the repo's synthetic-scene loader creates an intermediate signed-byte RGB array, which some newer Pillow versions reject.

Recovery:

- Use a Pillow version compatible with the repo's Blender loader path.
- If the issue appears in a fresh environment, reinstall a compatible Pillow release and rerun the training smoke.
- If the user only needs COLMAP scenes, route them to the COLMAP layout path and avoid the synthetic loader.

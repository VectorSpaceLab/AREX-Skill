# Data Formats and Layouts

## When To Read

Read this before training, rendering pretrained models with a source override, or debugging `Could not recognize scene type!`, COLMAP camera errors, or missing depth files.

## COLMAP Scene Layout

The Python loader recognizes a COLMAP scene when the source directory contains `sparse/`. The expected training layout is:

```text
<scene>/
  images/
    <image files>
  sparse/
    0/
      cameras.bin or cameras.txt
      images.bin or images.txt
      points3D.bin or points3D.txt or points3D.ply
```

Important rules:

- The `images/` directory can be overridden with `--images` / `-i`, for example `-i images_4` for resized MipNeRF360 images.
- The loader supports undistorted `PINHOLE` and `SIMPLE_PINHOLE` camera models. If raw COLMAP output uses an OPENCV distortion model, run the conversion workflow to create undistorted output.
- On first read, if `points3D.ply` is missing but binary/text points exist, the loader creates it from the COLMAP points.
- With `--eval`, LLFF-style holdout is used; paths containing `360` use holdout 8. If no holdout is used, a `sparse/0/test.txt` split can be read.

## Blender / NeRF Synthetic Layout

The loader recognizes a Blender/NeRF synthetic scene when the source directory contains `transforms_train.json`:

```text
<scene>/
  transforms_train.json
  transforms_test.json
  <frame image files referenced by the JSON>
```

Rules:

- The JSON needs `camera_angle_x` and `frames` entries with `file_path` and `transform_matrix` fields.
- If `--eval` is not set, train and test frames are merged into training and no test set is used.
- Alpha images are composited over black by default or white with `--white_background`.

## Depth Regularization Layout

Training accepts depth maps with `--depths` / `-d` pointing to a folder relative to the scene root. For real COLMAP scenes, the loader also needs:

```text
<scene>/
  <depths-folder>/
    <image-name>.png
  sparse/0/depth_params.json
```

Use the bundled `scripts/make_depth_scale.py` to create `depth_params.json` after depth PNGs exist. For synthetic data, depth maps can be produced directly and do not need the same scale estimation.

Training only applies depth regularization when `depth_l1_weight(iteration) > 0` and the camera's depth is reliable. The default depth loss weight decays from `1.0` to `0.01` over the configured iterations.

## Trained Model Output Layout

A successful training run writes a model directory like:

```text
<model>/
  cfg_args
  cameras.json
  input.ply
  exposure.json
  point_cloud/
    iteration_<N>/
      point_cloud.ply
  chkpnt<N>.pth            # only when checkpoint iterations are requested
```

`render.py` reads `cfg_args` from the model directory and merges command-line overrides. If `cfg_args` is missing, provide explicit source/model options where possible.

## Render/Metric Output Layout

`render.py` writes renders and ground truth images under the model directory:

```text
<model>/
  train/ours_<iteration>/renders/*.png
  train/ours_<iteration>/gt/*.png
  test/ours_<iteration>/renders/*.png
  test/ours_<iteration>/gt/*.png
```

`metrics.py` looks under `test/` and writes:

```text
<model>/results.json
<model>/per_view.json
```

Use the rendering-evaluation validator when diagnosing this output layout.

# Conversion Workflows

## When To Read

Read this when a user has raw images, distorted COLMAP output, missing resized image folders, or asks how to prepare a scene before `train.py -s`.

## Validate First

Before starting long external commands, run the bundled layout checker:

```bash
python validate_scene_layout.py --scene-root <scene> --images images
```

Use `--depths <folder>` when planning depth regularization, and `--model-root <model>` when checking a trained model directory.

## Raw Images to Gaussian-Splatting COLMAP Layout

Put raw images in:

```text
<scene>/input/<image files>
```

Then run the repository's conversion workflow shape:

```bash
python convert.py -s <scene> [--resize]
```

Equivalent option details:

- `--source_path` / `-s`: scene location containing `input/`.
- `--camera`: early COLMAP matching camera model, default `OPENCV`.
- `--no_gpu`: tell COLMAP SIFT extraction/matching not to use GPU.
- `--resize`: create `images_2`, `images_4`, and `images_8` with ImageMagick.
- `--colmap_executable`: path/name of COLMAP executable if not on PATH.
- `--magick_executable`: path/name of ImageMagick executable if not on PATH.

The converter runs COLMAP feature extraction, matching, mapping, and image undistortion. It mutates the scene directory by creating `distorted/`, `sparse/`, `images/`, and optional resized image folders.

## Existing Distorted COLMAP Output

If COLMAP matching already exists in:

```text
<scene>/distorted/database.db
<scene>/distorted/sparse/0/<COLMAP files>
<scene>/input/<image files>
```

skip matching and run only undistortion/resizing:

```bash
python convert.py -s <scene> --skip_matching [--resize]
```

## Resized Image Folders

The conversion workflow can create:

```text
images_2/  # 50%
images_4/  # 25%
images_8/  # 12.5%
```

Select one during training with `--images` / `-i`, for example:

```bash
python train.py -s <scene> -i images_4 --eval --disable_viewer
```

## Depth Regularization Preparation

For real-world COLMAP scenes:

1. Generate per-image inverse-depth PNGs with a depth model selected by the user.
2. Put them in a folder such as `<scene>/depths_any/`.
3. Generate the scale/offset file:

```bash
python make_depth_scale.py --base-dir <scene> --depths-dir <scene>/depths_any --model-type bin
```

Then train with:

```bash
python train.py -s <scene> -d depths_any --disable_viewer
```

## Safety Notes

- COLMAP and ImageMagick commands can be long-running and write many files. Do not run them as a hidden smoke check.
- If input paths contain spaces, quote them in shell commands.
- If GPU COLMAP is unreliable, use `--no_gpu` for conversion; this does not remove the CUDA requirement for training/rendering.

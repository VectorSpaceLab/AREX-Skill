# Data preparation troubleshooting

## `transforms*.json` missing or invalid

Run the bundled validator. Fix JSON syntax, ensure `frames` is a non-empty list, and confirm each frame has a `file_path` and a 4x4 `transform_matrix`.

## Image paths do not resolve

Paths are normally relative to the directory containing the relevant `transforms*.json`. If the validator reports missing images, either move/copy the images into the expected relative layout or update `file_path` values consistently. Avoid absolute paths when the dataset must be portable.

## Train/eval split lists are inconsistent

If `train_filenames`, `val_filenames`, or `test_filenames` are present, every listed filename should match a frame file path. Use `nerfstudio-data --eval-mode filename` when training with filename split lists.

## COLMAP/FFmpeg failures

- Missing command: install and verify `colmap -h` and `ffmpeg -version`.
- Few registered images: improve overlap, blur, exposure, and viewpoint coverage; remove duplicates and low-quality frames.
- Existing sparse model path: use skip-COLMAP only when the sparse model is complete and matches the image paths.

## Device capture issues

- Polycam raw export must contain the expected keyframes/camera files; older app exports may not include corrected images.
- Record3D pose/image filenames must be numeric and complete.
- Metashape/RealityCapture/ODM modes need exported pose files in the format expected by that mode.
- Aria processing needs additional Project Aria dependencies and is not part of a minimal install.

## Depth or mask failures

Depth paths must exist for every frame that declares them. Masks should be one-channel black/white images at the same resolution as RGB and should be provided for every frame when mask training is intended.

# Data Formats

## Purpose

Use this before configuring `data_path.py`, choosing demo inputs, or validating
paired training data.

## Training data_path schema

`data_path.py` defines a `DATA_PATH` dictionary with these keys:

- `videomatte240k`
- `photomatte13k`
- `distinction`
- `adobe`
- `backgrounds`

Each foreground dataset entry has:

- `train.fgr`
- `train.pha`
- `valid.fgr`
- `valid.pha`

`backgrounds` has:

- `train`
- `valid`

The file is meant to be edited for the local dataset layout. Placeholder strings
such as `PATH_TO_IMAGES_DIR` must be replaced before training.

## Foreground / alpha directories

- `ImagesDataset` recursively reads `*.jpg` and `*.png` files.
- The foreground and alpha trees should stay structurally aligned.
- The paired training code expects matching pairs and uses equal-length checks in
  the training loaders.

## Inference inputs

- Image inference consumes a source image directory and a background image
  directory.
- Video inference consumes a source video and a background image or video.
- Webcam inference captures the background frame interactively from the camera
  stream.

## Benchmark layout

The evaluation script expects a benchmark tree with these subdirectories:

- `pha/`
- `fgr/`
- `trimap/`

Results are read from `pha/` and `fgr/` under the result directory.

## Output layout

Depending on the CLI and output type, the repo writes:

- `com/`
- `pha/`
- `fgr/`
- `err/`
- `ref/`

Image output directories contain per-example files; video output may be a single
MP4 per output type.

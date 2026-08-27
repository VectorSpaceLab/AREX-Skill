# Prediction Workflows

## Purpose

Use this reference for Luminoth inference, the demo web server, and the public
Python API.

## Image prediction CLI

Basic command:

```bash
lumi predict ./image.jpg
```

Useful flags:

- `--checkpoint`: checkpoint id or alias to load.
- `--config`: config file to load instead of a checkpoint.
- `--override`: dot-notation config override.
- `--output`: JSON lines output path. Use `-` for stdout.
- `--save-media-to`: output directory for annotated media.
- `--min-prob`: minimum probability threshold for drawn boxes.
- `--max-detections`: cap the number of detections.
- `--only-class`: keep only these classes.
- `--ignore-class`: drop these classes.
- `--debug`: extra logging.

### Default checkpoint behavior

If neither `--checkpoint` nor `--config` is provided, the CLI falls back to the
`accurate` checkpoint alias.

### What image prediction writes

- JSON lines are written only for image inputs.
- Each JSON object contains the source file path and the list of detected
  objects.
- Annotated media is written only if `--save-media-to` is set.

## Video prediction CLI

Basic command:

```bash
lumi predict ./video.mp4 --save-media-to ./preds
```

Important behavior:

- Supported video extensions include `mov`, `mp4`, and `avi`.
- Video output is saved as `.mp4`.
- If you do not pass `--save-media-to`, the command does not emit JSON output
  for videos.
- FFmpeg must be available if you want to write the annotated video file.

## Mixed directory jobs

If a directory contains both images and videos, the CLI will process both kinds
of files that it recognizes. Use the bundled checker first:

```bash
python scripts/check_prediction_inputs.py ./media --save-media-to ./preds --output ./preds/objects.json
```

The checker reports:

- recognized image and video files,
- ignored file suffixes,
- `--only-class` / `--ignore-class` conflicts,
- and whether FFmpeg is available when video output is requested.

## Demo web server

Basic command:

```bash
lumi server web
```

The server exposes a demo page and a POST API at:

```text
/api/<model_name>/predict/
```

The API expects an uploaded image in the `image` form field. A `total` query
parameter can limit the number of returned objects.

### Example use

- GET requests return a 400 error telling you to use POST.
- Missing image uploads return a 400 error.
- Incompatible file types also return a 400 error.

## Python API

The public Python route is meant for programmatic inference and visualization.
Read `references/api-reference.md` for signatures and return shapes.

## What to read next

- `references/api-reference.md` for `Detector`, `read_image`, and
  `vis_objects`.
- `references/troubleshooting.md` for missing checkpoint, ffmpeg, and CLI
  misuse errors.
- `scripts/check_prediction_inputs.py` for a safe preflight.

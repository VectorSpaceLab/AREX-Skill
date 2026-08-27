# Inference workflows

## Main function

The bundled concrete detection entrypoint is `runtime/detect.py`. Run it through `scripts/run_detection.py` so the working directory and `PYTHONPATH` point at the packaged runtime mirror:

```bash
python sub-skills/inference/scripts/run_detection.py --dry-run -- --weights weights.pt --source images/ --output inference/output --save-txt
```

The detection function centers on:

- `detect(save_img=False)`

It consumes the parsed CLI options and handles:

- source classification,
- model loading,
- NMS,
- class filtering,
- optional text output,
- rendered image or video output,
- optional augmented inference.

## Important inputs

- `--weights` for the checkpoint.
- `--source` for the input media.
- `--output` for the output directory.
- `--img-size` for inference sizing.
- `--conf-thres` and `--iou-thres` for prediction filtering.
- `--device` for CPU or GPU selection.
- `--view-img`, `--save-txt`, `--classes`, `--agnostic-nms`, `--augment`, and `--update` for behavior changes.

## Source types

The loader can work with:

- a single file,
- a directory of images or videos,
- a glob pattern,
- a text file that lists sources,
- a webcam index such as `0`,
- RTSP or HTTP streams.

## Output behavior

- The output directory is created or replaced before the run.
- Images and videos are saved when rendering is enabled.
- Text output uses normalized XYWH labels.
- The runtime prints detection counts and timing information per source item.

## Secondary classifier path

There is a second-stage classifier branch in the code, but it is disabled by default. Treat it as a dormant maintenance detail unless you are explicitly working on classifier integration.

## Prediction-time decisions

- `augment` increases compute but can help some accuracy-sensitive runs.
- `classes` filters detections by id.
- `agnostic_nms` changes class handling during suppression.
- `update` mutates checkpoint files by stripping optimizer state after the run.

## Inference checklist

- The runtime bundle is complete: `python scripts/check_runtime_bundle.py`.
- The source is readable by OpenCV or the file loader.
- The checkpoint is accessible.
- The output directory is expendable.
- `view_img` is only used in an environment that can open GUI windows.

Use `scripts/prepare_inference_run.py` for a safe plan check, then use `scripts/run_detection.py --dry-run -- ...` to preview the concrete bundled `runtime/detect.py` command before removing `--dry-run`.

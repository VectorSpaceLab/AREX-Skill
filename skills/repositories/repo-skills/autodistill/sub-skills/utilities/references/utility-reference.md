# Utility Reference

Read this for Autodistill 0.1.29 helper signatures, side effects, and safe usage boundaries.

## `load_image`

```text
load_image(image: Any, return_format="cv2") -> Any
```

Accepted `return_format` values:

- `"PIL"` -> returns a Pillow `Image`;
- `"cv2"` -> returns a BGR NumPy array suitable for OpenCV-style plugins;
- `"numpy"` -> returns a NumPy array.

Accepted inputs:

- `PIL.Image.Image`;
- NumPy arrays, including cv2 images;
- local file paths;
- HTTP/HTTPS URLs.

Invalid return formats raise `ValueError("return_format must be one of ...")`. Invalid paths/URIs raise `ValueError("<input> is not a valid file path or URI")`.

## `split_data`

```text
split_data(base_dir, split_ratio=0.8, record_confidence=False)
```

`split_data` expects a detection dataset output directory with intermediate `images/`, `annotations/`, and `data.yaml`. It shuffles image stems, creates `train/images`, `train/labels`, `valid/images`, `valid/labels`, moves images/labels, optionally moves `confidence-*` files, and rewrites `data.yaml`.

Side effects:

- normalizes duplicate dots in image filenames;
- converts `.png` and `.jpeg` files in the intermediate output folder to `.jpg` and removes the originals;
- moves files out of intermediate `images/` and `annotations/` directories;
- writes absolute train/val paths in `data.yaml`.

Use [dataset labeling data formats](../../dataset-labeling/references/data-formats.md) for output validation.

## `split_video_frames`

```text
split_video_frames(video_path: str, output_dir: str, stride: int) -> None
```

The helper lists video files with extensions `mov`, `mp4`, `MOV`, `MP4` and writes frames through `supervision.ImageSink`. Verify behavior on a tiny video before large runs. In this source snapshot, inspect carefully if using it as-is: the loop variable for each found file and the `source_path` argument should be validated for your workflow.

## `sync_with_roboflow`

```text
sync_with_roboflow(workspace_id, workspace_url, project_id, batch_id, model)
```

This helper logs into Roboflow, queries a batch, downloads source images, calls `model.label(...)`, and uploads annotations. It needs network, Roboflow credentials, workspace/project access, and permission to write a local working directory. Do not run it for a dry run.

## `plot`

```text
plot(image: numpy.ndarray, detections, classes: List[str], raw=False)
```

If `detections.mask` is present, the function uses `supervision.MaskAnnotator`; otherwise it uses `supervision.BoxAnnotator`. It also adds labels using class ids and confidences. With `raw=True`, it returns the annotated image array. With `raw=False`, it plots interactively through supervision.

## `compare`

```text
compare(models: list, images: List[str])
```

Runs each model's `predict(image)`, plots each result through `plot(..., raw=True)`, and displays a grid. Use this only after model plugins and image paths are verified. It can be slow or download-heavy if the models are heavyweight plugins.

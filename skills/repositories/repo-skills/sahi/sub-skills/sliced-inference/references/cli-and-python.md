# CLI and Python workflows for SAHI prediction

This reference is the command/API construction sheet for SAHI inference. It assumes SAHI is installed and importable. Real detectors also require their own optional framework packages and local weights or a preloaded model; use `../../model-integrations/SKILL.md` for that setup.

## Which entry point should you use?

| Task | Python entry point | CLI entry point | Notes |
| --- | --- | --- | --- |
| One image, full-image inference | `sahi.predict.get_prediction` | `sahi predict --no_sliced_prediction` | Fastest path when objects are not tiny relative to the image. |
| One image, tiled inference | `sahi.predict.get_sliced_prediction` | `sahi predict` on a single image | Default sliced mode also performs a standard full-image pass unless disabled. |
| Folder/file-list/video with exports | `sahi.predict.predict` | `sahi predict` | Creates run directories for visuals, crops, pickles, or COCO result JSON when requested. |
| Interactive FiftyOne review | `sahi.predict.predict_fiftyone` | `sahi predict-fiftyone` | Requires optional `fiftyone`; launches an app and keeps the process alive. |
| Detector-native batch call | `detection_model.perform_batch_inference` | Not exposed directly | Used internally by `get_sliced_prediction(batch_size=...)`; useful for advanced custom loops. |

## Model object pattern

Use `AutoDetectionModel.from_pretrained(...)` to construct a `DetectionModel`, then pass it to prediction APIs. The verified public signature is:

```python
from sahi import AutoDetectionModel

detection_model = AutoDetectionModel.from_pretrained(
    model_type="ultralytics",        # see model-integrations for supported backends
    model_path="weights.pt",         # local weights or backend-specific identifier
    model=None,                       # optional preloaded model object
    config_path=None,                 # framework-specific config when needed
    device="cpu",                    # for example: "cpu", "cuda:0", "mps"
    mask_threshold=0.5,
    confidence_threshold=0.25,
    category_mapping=None,            # e.g. {"0": "vehicle"}
    category_remapping=None,
    load_at_init=True,
    image_size=None,
    # backend-specific kwargs go here
)
```

Prediction construction is the same for all supported backends after the model object exists. Do not claim a backend was verified merely because this generic pattern is valid.

## Standard prediction on one image

```python
from sahi.predict import get_prediction

result = get_prediction(
    image="images/frame_001.jpg",        # path, PIL.Image, or numpy array
    detection_model=detection_model,
    verbose=1,
    exclude_classes_by_name=None,
    exclude_classes_by_id=None,
    confidence_threshold=None,            # temporary override; model threshold is restored
)

print(len(result.object_prediction_list))
for pred in result.object_prediction_list:
    print(pred.category.name, pred.score.value, pred.bbox.to_xyxy())
```

Use this for normal image sizes, baseline comparisons, or when sliced inference duplicates outweigh recall benefits.

## Sliced prediction on one image

```python
from sahi.predict import get_sliced_prediction

progress_events = []

def on_progress(current_slices: int, total_slices: int) -> None:
    progress_events.append((current_slices, total_slices))

result = get_sliced_prediction(
    image="images/large_frame.jpg",
    detection_model=detection_model,
    slice_height=512,
    slice_width=512,
    overlap_height_ratio=0.2,
    overlap_width_ratio=0.2,
    perform_standard_pred=True,           # default: append a full-image pass when there is more than one slice
    postprocess_type="GREEDYNMM",
    postprocess_match_metric="IOS",
    postprocess_match_threshold=0.5,
    postprocess_class_agnostic=False,
    exclude_classes_by_name=None,
    exclude_classes_by_id=None,
    progress_bar=False,
    progress_callback=on_progress,
    batch_size=1,
    confidence_threshold=None,            # temporary override; model threshold is restored
)

result.export_visuals(export_dir="runs/manual")
```

Important behavior:

- With `perform_standard_pred=True`, SAHI adds standard full-image predictions after slice predictions and then postprocesses the combined list. This improves large-object recall when tiling splits large objects.
- `progress_callback` is called after each processed slice batch, with cumulative processed slices and total slices. When `batch_size > 1`, callback jumps can be larger than one.
- `batch_size` groups slice inference calls. It can improve throughput for backends with native batching; base models without native batching still use the same grouped result API.
- `confidence_threshold` on `get_prediction` and `get_sliced_prediction` is a per-call temporary override; the model's original threshold is restored afterward.

## High-level Python folder/video prediction

`predict(...)` owns iteration over a single image path, an image folder, a video path, or COCO-json-driven image list. It can instantiate a model from `model_type`/paths or use a prebuilt `detection_model`.

```python
from sahi.predict import predict

summary = predict(
    model_type="ultralytics",
    model_path="weights.pt",
    model_config_path=None,
    model_confidence_threshold=0.25,
    model_device="cpu",
    image_size=640,
    source="images/",                    # image file, folder, or video file
    no_standard_prediction=False,
    no_sliced_prediction=False,
    slice_height=512,
    slice_width=512,
    overlap_height_ratio=0.2,
    overlap_width_ratio=0.2,
    postprocess_type="GREEDYNMM",
    postprocess_match_metric="IOS",
    postprocess_match_threshold=0.5,
    postprocess_class_agnostic=False,
    novisual=False,
    export_pickle=True,
    export_crop=True,
    dataset_json_path=None,
    project="runs/predict",
    name="exp",
    visual_bbox_thickness=None,
    visual_text_size=None,
    visual_text_thickness=None,
    visual_hide_labels=False,
    visual_hide_conf=False,
    visual_export_format="png",          # `png` or `jpg` are the documented choices
    return_dict=True,
    progress_bar=True,
    batch_size=2,
)
print(summary["export_dir"])
```

`predict(...)` creates no output directory when all export routes are disabled (`novisual=True`, `export_pickle=False`, `export_crop=False`, and no `dataset_json_path`). Set `return_dict=True` when downstream code needs the run directory.

## Low-level detector batch API

For custom loops outside SAHI's slicer, call the model batch API directly and then convert raw predictions into SAHI result objects:

```python
import numpy as np

images = [np.zeros((512, 512, 3), dtype=np.uint8) for _ in range(4)]

detection_model.perform_batch_inference(images)
detection_model.convert_original_predictions(
    shift_amount=[[0, 0]] * len(images),
    full_shape=[[img.shape[0], img.shape[1]] for img in images],
)

for preds in detection_model.object_prediction_list_per_image:
    print(len(preds))
```

Use `object_prediction_list_per_image` for batch results. `object_prediction_list` is a single-image convenience accessor for the first image's predictions.

## CLI command construction

The CLI is backed by Python function names. Use underscores in flag names, as shown below.

### Default standard+sliced prediction

```bash
sahi predict \
  --model_type ultralytics \
  --model_path weights.pt \
  --source images/ \
  --slice_height 512 \
  --slice_width 512 \
  --overlap_height_ratio 0.2 \
  --overlap_width_ratio 0.2 \
  --model_confidence_threshold 0.25 \
  --progress_bar \
  --batch_size 2
```

### Standard-only baseline

```bash
sahi predict \
  --model_type ultralytics \
  --model_path weights.pt \
  --source images/frame_001.jpg \
  --no_sliced_prediction \
  --novisual
```

### Sliced-only run for small-object recall

```bash
sahi predict \
  --model_type ultralytics \
  --model_path weights.pt \
  --source images/ \
  --no_standard_prediction \
  --slice_height 640 \
  --slice_width 640 \
  --overlap_height_ratio 0.25 \
  --overlap_width_ratio 0.25
```

### Folder prediction with COCO result JSON, crops, pickles, and visuals

```bash
sahi predict \
  --model_type ultralytics \
  --model_path weights.pt \
  --source images/ \
  --dataset_json_path annotations.json \
  --project runs/predict \
  --name exp \
  --export_pickle \
  --export_crop \
  --visual_export_format jpg
```

With `--dataset_json_path`, predictions are written as COCO result JSON under the run directory. Use `../../dataset-tools/SKILL.md` for evaluation and dataset conversion after this file exists.

### Video inference

```bash
sahi predict \
  --model_type ultralytics \
  --model_path weights.pt \
  --source video.mp4 \
  --slice_height 512 \
  --slice_width 512 \
  --frame_skip_interval 3
```

Add `--view_video` only when a GUI display is available. The viewer accepts `D`/`A` for +/-100 frames, `G`/`F` for +/-20 frames, and `Esc` to exit. In headless sessions, prefer exported visuals/video or `--novisual`.

### FiftyOne prediction

```bash
sahi predict-fiftyone \
  --model_type ultralytics \
  --model_path weights.pt \
  --image_dir images/ \
  --dataset_json_path annotations.json \
  --slice_height 256 \
  --slice_width 256
```

This route requires `fiftyone`, creates a FiftyOne dataset from the COCO file, adds predictions, launches the app, runs detection evaluation, and keeps the session alive for interactive inspection.

## Output routing

| Option | Where output goes | Notes |
| --- | --- | --- |
| default visuals | `project/name/visuals/` | Disabled by `novisual` / `--novisual`. |
| `export_crop=True` / `--export_crop` | `project/name/crops/` | Crops every predicted object using the visual export format. |
| `export_pickle=True` / `--export_pickle` | `project/name/pickles/` | Stores Python prediction lists; use only in trusted Python environments. |
| `dataset_json_path=...` / `--dataset_json_path ...` | `project/name/result.json` | COCO result JSON for later evaluation. Video input with COCO JSON is unsupported. |
| video with visuals enabled | video file in the run directory | Uses OpenCV video writer; codec availability is environment-dependent. |
| `PredictionResult.export_visuals(...)` | caller-provided directory | One-image API helper; current public method exports PNG visuals. |

## Result conversion routing

For quick checks, use:

```python
result.to_coco_annotations()
result.to_coco_predictions(image_id=1)
result.to_imantics_annotations()
# result.to_fiftyone_detections() requires optional fiftyone
```

For detailed coordinate conventions, mask behavior, and conversion troubleshooting, route to `../../annotations-and-results/SKILL.md`.

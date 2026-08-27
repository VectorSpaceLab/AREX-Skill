# Inference API reference

Use this reference when command templates are not enough and the task needs direct access to MMYOLO/MMDetection objects, predictions, visualizers, LabelMe output, or large-image merging.

## Minimal detector API

```python
from mmdet.apis import init_detector, inference_detector
from mmyolo.utils import register_all_modules

register_all_modules(init_default_scope=True)

config_file = "model_config.py"
checkpoint_file = "checkpoint.pth"
model = init_detector(config_file, checkpoint_file, device="cpu")
result = inference_detector(model, "image.jpg")

pred = result.pred_instances
boxes = pred.bboxes      # tensor shaped (N, 4) for horizontal boxes, sometimes (N, 5) for rotated boxes
scores = pred.scores    # tensor shaped (N,)
labels = pred.labels    # tensor shaped (N,)
```

`inference_detector` returns an MMDetection `DetDataSample`. For normal detection, the predictions live in `result.pred_instances`, an `InstanceData` container with tensor fields such as `bboxes`, `scores`, and `labels`.

Convert predictions for downstream code only after moving tensors to CPU:

```python
keep = pred.scores > 0.3
filtered = pred[keep]
boxes_np = filtered.bboxes.cpu().numpy()
scores_np = filtered.scores.cpu().numpy()
labels_np = filtered.labels.cpu().numpy()
```

## Class-name filtering

Dataset classes usually come from the checkpoint/config metadata:

```python
classes = tuple(model.dataset_meta.get("classes", ()))
name_to_id = {name: idx for idx, name in enumerate(classes)}
selected_names = ["cat", "dog"]
missing = [name for name in selected_names if name not in name_to_id]
if missing:
    raise ValueError(f"Unknown class names: {missing}; available classes: {classes}")

selected_ids = {name_to_id[name] for name in selected_names}
keep_by_name = [int(label) in selected_ids for label in pred.labels.cpu()]
filtered = pred[keep_by_name]
```

For rendered visualizations, assign the filtered instances back to a copied result before drawing:

```python
result_for_draw = result.clone()
result_for_draw.pred_instances = filtered
```

Image-demo-style `--class-name` filtering is primarily used for LabelMe shape export. Use the manual filter above when the user specifically wants class-filtered rendered images.

## Visualizer API

```python
import mmcv
from mmyolo.registry import VISUALIZERS

img = mmcv.imread("image.jpg")
img = mmcv.imconvert(img, "bgr", "rgb")

visualizer = VISUALIZERS.build(model.cfg.visualizer)
visualizer.dataset_meta = model.dataset_meta
visualizer.add_datasample(
    "image.jpg",
    img,
    data_sample=result,
    draw_gt=False,
    show=False,
    wait_time=0,
    out_file="output/image.jpg",
    pred_score_thr=0.3,
)
```

`pred_score_thr` controls which predicted boxes are drawn. If `show=True`, avoid setting an output file and ensure the host has a display.

## `get_file_list` utility facts

Installed API fact:

```text
mmyolo.utils.misc.get_file_list(source_root: str) -> (list, dict)
```

Behavior to preserve in wrappers/templates:

- Directories are scanned recursively for supported image extensions.
- URLs beginning with `http:/` or `https:/` are downloaded to the current working directory and then returned as a one-file list.
- Single image paths are accepted when their suffix is a supported image extension.
- Unsupported paths print a message and return an empty file list.
- The second return value is a dict with `is_dir`, `is_url`, and `is_file` booleans.

Always check for an empty file list before calling `ProgressBar` or inference.

## LabelMe export API

Installed API fact:

```text
mmyolo.utils.labelme_utils.LabelmeFormat(classes: tuple)
```

Usage:

```python
from mmyolo.utils.labelme_utils import LabelmeFormat

writer = LabelmeFormat(classes=tuple(model.dataset_meta["classes"]))
filtered = result.pred_instances[result.pred_instances.scores > 0.3]
writer(
    pred_instances=filtered,
    metainfo=result.metainfo,
    output_path="output/image.json",
    selected_classes=["cat"],  # or None to keep all predicted classes
)
```

Output structure:

- `version`: fixed LabelMe version string used by the MMYOLO helper.
- `flags`: empty object.
- `imagePath`: runtime image path from prediction metadata.
- `imageData`: null.
- `imageHeight` / `imageWidth`: original image shape from metadata.
- `shapes`: one rectangle per kept prediction, with `label`, two corner `points`, `group_id: null`, `shape_type: rectangle`, and empty `flags`.

If `selected_classes` is not `None`, shapes whose class label is not in that list are skipped.

## TTA config modification

Image inference with TTA modifies the config before model construction:

```python
from mmengine.config import Config, ConfigDict

cfg = Config.fromfile("model_config.py")
if "tta_model" not in cfg or "tta_pipeline" not in cfg:
    raise KeyError("TTA requires both tta_model and tta_pipeline in the config")

cfg.model = ConfigDict(**cfg.tta_model, module=cfg.model)
test_data_cfg = cfg.test_dataloader.dataset
while "dataset" in test_data_cfg:
    test_data_cfg = test_data_cfg["dataset"]
if "batch_shapes_cfg" in test_data_cfg:
    test_data_cfg.batch_shapes_cfg = None
test_data_cfg.pipeline = cfg.tta_pipeline

model = init_detector(cfg, "checkpoint.pth", device="cpu", cfg_options={})
```

Use this only for configs that explicitly define TTA fields.

## Deploy-mode switch for PyTorch inference

Installed API fact:

```text
mmyolo.utils.switch_to_deploy(model)
```

This iterates through model modules and switches MMYOLO `RepVGGBlock` modules into deploy mode. It is for the in-memory PyTorch model, not for running exported ONNX/TensorRT/MMDeploy artifacts.

```python
from mmyolo.utils import switch_to_deploy

model = init_detector(cfg, checkpoint, device="cpu", cfg_options={})
switch_to_deploy(model)
```

## Video API pattern

Video frame inference must use an ndarray-aware test pipeline:

```python
import cv2
import mmcv
from mmcv.transforms import Compose
from mmdet.apis import init_detector, inference_detector
from mmyolo.registry import VISUALIZERS

model = init_detector("model_config.py", "checkpoint.pth", device="cpu")
model.cfg.test_dataloader.dataset.pipeline[0].type = "mmdet.LoadImageFromNDArray"
test_pipeline = Compose(model.cfg.test_dataloader.dataset.pipeline)
visualizer = VISUALIZERS.build(model.cfg.visualizer)
visualizer.dataset_meta = model.dataset_meta

reader = mmcv.VideoReader("input.mp4")
writer = cv2.VideoWriter("output.mp4", cv2.VideoWriter_fourcc(*"mp4v"), reader.fps, (reader.width, reader.height))
for frame in reader:
    result = inference_detector(model, frame, test_pipeline=test_pipeline)
    visualizer.add_datasample("video", frame, data_sample=result, draw_gt=False, show=False, pred_score_thr=0.3)
    writer.write(visualizer.get_image())
writer.release()
```

## Large-image merge API

Installed API fact:

```text
mmyolo.utils.large_image.merge_results_by_nms(
    results: List[DetDataSample],
    offsets: Sequence[Tuple[int, int]],
    src_image_shape: Tuple[int, int],
    nms_cfg: dict,
) -> DetDataSample
```

Use it after patch inference. The function shifts patch predictions by offsets, runs batched NMS grouped by labels, and returns a cloned `DetDataSample` with merged `pred_instances`.

```python
merged = merge_results_by_nms(
    results=patch_results,
    offsets=starting_pixels,
    src_image_shape=(height, width),
    nms_cfg={"type": "nms", "iou_threshold": 0.25},
)
```

The merge path requires `sahi` for coordinate shifting helpers. Validate that the number of patch results equals the number of offsets.

## Feature-map target-layer access

MMYOLO's feature-map and CAM recipes resolve layer strings against the built model. Prefer explicit validation over blind `eval` in new code:

```python
def resolve_layer(root, dotted):
    obj = root
    for part in dotted.split("."):
        if "[" in part and part.endswith("]"):
            name, index = part[:-1].split("[")
            obj = getattr(obj, name)[int(index)]
        else:
            obj = getattr(obj, part)
    return obj

layer = resolve_layer(model, "neck.out_layers[1]")
```

Common valid starting points are `backbone` and `neck`, but the exact layer tree depends on the chosen config/model family. Preview the model before a long visualization run.

# Inference Workflows

Detectron2 inference has two common paths: `DefaultPredictor` for simple single-image demos, and direct model calls when you need batching, custom preprocessing, custom outputs, or strict control over checkpoint loading.

## DefaultPredictor Single-Image Inference

`DefaultPredictor(cfg)` is convenient but eager:

1. Clones the config.
2. Builds a model with `build_model(cfg)`.
3. Puts the model in eval mode.
4. Loads `cfg.MODEL.WEIGHTS` through `DetectionCheckpointer`.
5. Creates a resize transform from `cfg.INPUT.MIN_SIZE_TEST` and `cfg.INPUT.MAX_SIZE_TEST`.
6. Expects one OpenCV-style BGR `numpy.ndarray` with shape `(H, W, 3)`.
7. Returns one prediction dictionary, not a batch list.

Minimal pattern:

```python
import cv2
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor

cfg = get_cfg()
cfg.merge_from_file("config.yaml")
cfg.MODEL.WEIGHTS = "model_final.pth"
cfg.MODEL.DEVICE = "cpu"  # or "cuda" when CUDA is available and intended
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
cfg.freeze()

image_bgr = cv2.imread("input.jpg")
predictor = DefaultPredictor(cfg)
outputs = predictor(image_bgr)
```

Use this path when the task is a quick local image demo and the config is a Yacs `CfgNode`. Avoid it when validation must not download weights: construction loads `cfg.MODEL.WEIGHTS`, including URLs and `detectron2://` model-zoo weights.

## CPU-Only No-Download Planning Recipe

For a CPU-only inference recipe that must not download during validation:

1. Load and mutate the config only.
2. Set `cfg.MODEL.DEVICE = "cpu"` before any model or predictor is constructed.
3. Set thresholds on all relevant heads.
4. Leave `cfg.MODEL.WEIGHTS` empty or point it to a verified local file for validation.
5. Print or inspect the planned command/API call; do not instantiate `DefaultPredictor` until weights are available.

Example planning-only config snippet:

```python
from detectron2.config import get_cfg
from detectron2 import model_zoo

cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
cfg.MODEL.DEVICE = "cpu"
cfg.MODEL.WEIGHTS = ""  # no checkpoint load during planning
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = 0.5
```

If the user wants a runnable command, build it with `scripts/demo_command_builder.py` and require explicit local weights or an explicit decision to allow downloads.

## Direct Model Inference

Use direct calls when you need batches, custom resizing, intermediate control, or a non-demo loop. Builtin Detectron2 models accept `list[dict]`; for inference the standard required key is `"image"`, with optional `"height"` and `"width"` to request output resizing back to the original image dimensions.

```python
import torch
from detectron2.checkpoint import DetectionCheckpointer
from detectron2.modeling import build_model

model = build_model(cfg)
model.eval()
DetectionCheckpointer(model).load(cfg.MODEL.WEIGHTS)

image = torch.as_tensor(image_chw_float32)  # shape C,H,W; channel order follows cfg.INPUT.FORMAT
inputs = [{"image": image, "height": original_height, "width": original_width}]
with torch.no_grad():
    outputs = model(inputs)[0]
```

Important details:

- The model handles pixel normalization from `cfg.MODEL.PIXEL_MEAN` and `cfg.MODEL.PIXEL_STD` internally.
- `"height"` and `"width"` are output-size hints, not necessarily the tensor size after resizing.
- Put the config device and tensor device in agreement before calling the model.
- Call `model.eval()` and wrap inference in `torch.no_grad()`.
- For training-mode loss dictionaries, route to the training/evaluation sub-skill.

## Demo-Style Image, Video, and Webcam Modes

The upstream demo exposes these concepts:

- `--input IMG [IMG ...]`: process one or more images, or one glob pattern.
- `--webcam`: read frames from webcam index 0.
- `--video-input VIDEO`: read frames from a video file.
- `--output PATH`: save image outputs to a file/directory or video output to a file; without output the demo opens OpenCV windows.
- `--confidence-threshold FLOAT`: sets common builtin test thresholds.
- `--opts KEY VALUE ...`: applies config overrides such as `MODEL.DEVICE cpu` and `MODEL.WEIGHTS path_or_uri`.

This checkout's original demo imports a missing `vision.fair.detectron2.demo.predictor` module, so do not depend on the original script. Use `scripts/demo_command_builder.py` to validate mutually exclusive modes and produce a command shape a user can adapt to an installed Detectron2 demo or their own wrapper.

## Visualization Pattern

The visualization pattern from the reference demo is:

```python
from detectron2.data import MetadataCatalog
from detectron2.utils.visualizer import ColorMode, Visualizer

metadata = MetadataCatalog.get(cfg.DATASETS.TEST[0]) if len(cfg.DATASETS.TEST) else None
image_rgb = image_bgr[:, :, ::-1]
visualizer = Visualizer(image_rgb, metadata, instance_mode=ColorMode.IMAGE)

if "instances" in outputs:
    vis = visualizer.draw_instance_predictions(outputs["instances"].to("cpu"))
elif "sem_seg" in outputs:
    vis = visualizer.draw_sem_seg(outputs["sem_seg"].argmax(dim=0).to("cpu"))
elif "panoptic_seg" in outputs:
    panoptic_seg, segments_info = outputs["panoptic_seg"]
    vis = visualizer.draw_panoptic_seg_predictions(panoptic_seg.to("cpu"), segments_info)

vis.save("output.png")
# or: image_rgb = vis.get_image()
```

`Visualizer` expects RGB images. OpenCV `cv2.imread` and `cv2.VideoCapture` return BGR frames, so convert before drawing and convert back only if writing through OpenCV.

## Confidence Thresholds

For common builtin configs, set all threshold fields that may exist in the selected architecture:

```python
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold
cfg.MODEL.RETINANET.SCORE_THRESH_TEST = threshold
cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = threshold
```

If predictions are empty, lower thresholds only after confirming weights, class count, image format, and device are correct. Empty predictions can be valid on images without target objects.

# GroundingDINO Inference API Reference

This reference captures the public single-image inference APIs from `groundingdino.util.inference`. It is self-contained for future agents; do not reopen repository demo files for these signatures.

## Prompt Normalization

`preprocess_caption(caption: str) -> str`

- Lowercases the caption.
- Strips leading/trailing whitespace.
- Appends a final period if the caption does not already end with `.`.
- Use periods between categories: `person . bicycle . dog .`.

GroundingDINO scores boxes against text tokens. Category prompts without separators can merge phrases and make labels harder to interpret.

## Function API

| API | Signature | Use When | Returns |
| --- | --- | --- | --- |
| `load_model` | `load_model(model_config_path: str, model_checkpoint_path: str, device: str = 'cuda')` | You have a config file and checkpoint and want the raw model object. | A model in eval mode with checkpoint weights loaded. |
| `load_image` | `load_image(image_path: str) -> Tuple[numpy.ndarray, torch.Tensor]` | You need the original RGB image plus transformed tensor. | `image_source` RGB array and normalized/resized tensor. |
| `predict` | `predict(model, image: torch.Tensor, caption: str, box_threshold: float, text_threshold: float, device: str = 'cuda', remove_combined: bool = False) -> Tuple[torch.Tensor, torch.Tensor, List[str]]` | You need raw normalized boxes/logits/phrases and control over thresholds. | `boxes`, `logits`, `phrases`. Boxes are normalized `cxcywh`. |
| `annotate` | `annotate(image_source: numpy.ndarray, boxes: torch.Tensor, logits: torch.Tensor, phrases: List[str]) -> numpy.ndarray` | You want a visualization from function API outputs. | BGR image array with pixel-space `xyxy` boxes and labels drawn. |

### Function API Recipe

```python
import cv2
from groundingdino.util.inference import annotate, load_image, load_model, predict

model = load_model("/path/to/GroundingDINO_SwinT_OGC.py", "/path/to/groundingdino_swint_ogc.pth", device="cuda")
image_source, image = load_image("/path/to/image.jpg")
boxes, logits, phrases = predict(
    model=model,
    image=image,
    caption="chair . person . dog .",
    box_threshold=0.35,
    text_threshold=0.25,
    device="cuda",
)
annotated = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
cv2.imwrite("annotated_image.jpg", annotated)
```

## Model Wrapper API

Use `Model` when you want a reusable object and integration with `supervision.Detections`.

| API | Signature | Notes |
| --- | --- | --- |
| `Model.__init__` | `Model(model_config_path: str, model_checkpoint_path: str, device: str = 'cuda')` | Loads and stores the model on the selected device. |
| `predict_with_caption` | `predict_with_caption(self, image: numpy.ndarray, caption: str, box_threshold: float = 0.35, text_threshold: float = 0.25) -> Tuple[supervision.detection.core.Detections, List[str]]` | Input image is BGR, such as `cv2.imread` output. Returns detections and phrase labels. |
| `predict_with_classes` | `predict_with_classes(self, image: numpy.ndarray, classes: List[str], box_threshold: float, text_threshold: float) -> supervision.detection.core.Detections` | Builds caption from classes with `. ` separators and fills `detections.class_id`. |
| `preprocess_image` | `Model.preprocess_image(image_bgr: numpy.ndarray) -> torch.Tensor` | Converts BGR array to RGB PIL, resizes, tensors, and normalizes. |
| `post_process_result` | `Model.post_process_result(source_h: int, source_w: int, boxes: torch.Tensor, logits: torch.Tensor) -> supervision.detection.core.Detections` | Converts normalized `cxcywh` to pixel `xyxy` and stores confidence. |
| `phrases2classes` | `Model.phrases2classes(phrases: List[str], classes: List[str]) -> numpy.ndarray` | Assigns first class whose text appears in each phrase; unmatched phrases get `None`. |

### Wrapper Recipe

```python
import cv2
from groundingdino.util.inference import Model

model = Model("/path/to/GroundingDINO_SwinT_OGC.py", "/path/to/groundingdino_swint_ogc.pth", device="cpu")
image = cv2.imread("/path/to/image.jpg")
detections = model.predict_with_classes(
    image=image,
    classes=["cat", "dog"],
    box_threshold=0.35,
    text_threshold=0.25,
)
```

## Output Formats

- `predict` returns `boxes` as normalized center-format `cxcywh`: `[center_x, center_y, width, height]`, all scaled from `0` to `1` relative to image width/height.
- `annotate` and `Model.post_process_result` convert boxes to pixel `xyxy`: `[x_min, y_min, x_max, y_max]`.
- `logits` from `predict` are the maximum token similarity score per kept query after sigmoid.
- `phrases` are text tokens extracted from the prompt using `text_threshold`; they may be combined if the prompt lacks period separators.
- `predict_with_classes` uses substring matching from phrase to class name, so overlapping class names such as `cat` and `catfish` need careful class ordering or manual phrase review.

## Config And Checkpoint Compatibility

Common packaged configs include:

| Config | Backbone | Queries | Max text length | Text encoder |
| --- | --- | ---: | ---: | --- |
| `GroundingDINO_SwinT_OGC.py` | `swin_T_224_1k` | 900 | 256 | `bert-base-uncased` |
| `GroundingDINO_SwinB_cfg.py` | `swin_B_384_22k` | 900 | 256 | `bert-base-uncased` |

Use a checkpoint that matches the selected config/backbone. Mismatched config and checkpoint pairs can load partially, produce poor detections, or fail at runtime.

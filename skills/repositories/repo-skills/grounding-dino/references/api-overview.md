# API Overview

## Primary Modules

| Module | Use |
| --- | --- |
| `groundingdino.util.inference` | Main public inference functions and `Model` wrapper. |
| `groundingdino.models` | `build_model(args)` for config-driven model construction. |
| `groundingdino.util.slconfig` | `SLConfig.fromfile(...)` config loader for Python/YAML/JSON config files. |
| `groundingdino.datasets.transforms` | Image preprocessing transforms used by demos and APIs. |
| `groundingdino.datasets.cocogrounding_eval` | COCO evaluator wrapper and COCO-format conversion helpers. |
| `groundingdino.util.vl_utils` | Positive-map and category-caption helpers for text span/category mapping. |
| `groundingdino.util.box_ops` | Bounding-box conversion and IoU helpers. |

## Inference APIs

Detailed signatures and recipes live in `../sub-skills/inference/references/api-reference.md`.

Key functions:

- `preprocess_caption(caption: str) -> str`
- `load_model(model_config_path: str, model_checkpoint_path: str, device: str = "cuda")`
- `load_image(image_path: str) -> Tuple[np.ndarray, torch.Tensor]`
- `predict(model, image, caption, box_threshold, text_threshold, device="cuda", remove_combined=False)`
- `annotate(image_source, boxes, logits, phrases)`
- `Model(model_config_path, model_checkpoint_path, device="cuda")`

## Evaluation APIs

Detailed COCO evaluator behavior lives in `../sub-skills/evaluation/references/api-reference.md`.

Key objects:

- `CocoGroundingEvaluator(coco_gt, iou_types, useCats=True)`
- `convert_to_xywh(boxes)`
- Positive-map creation through `create_positive_map_from_span(tokenized, token_span, max_text_len=256)`
- Category caption construction through `build_captions_and_token_span(cat_list, force_lowercase)`

## Box And Image Contracts

- GroundingDINO prediction boxes are normalized `cxcywh` unless a reference says otherwise.
- Visualization and downstream segmentation usually need pixel `xyxy` boxes.
- FiftyOne dataset annotations expect relative `xywh` boxes.
- `load_image` returns an RGB NumPy source image plus a normalized Torch tensor.
- OpenCV inputs are BGR; PIL and Gradio images are usually RGB. Convert explicitly at integration boundaries.

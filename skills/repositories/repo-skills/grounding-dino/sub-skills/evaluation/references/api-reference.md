# Evaluation API Reference

## `CocoGroundingEvaluator`

```python
from groundingdino.datasets.cocogrounding_eval import CocoGroundingEvaluator

evaluator = CocoGroundingEvaluator(coco_gt, iou_types=("bbox",), useCats=True)
```

- `coco_gt`: a `pycocotools.coco.COCO` ground-truth object.
- `iou_types`: list or tuple of evaluation modes. The COCO benchmark workflow uses `("bbox",)`.
- `useCats`: passes category-aware matching into `COCOeval`; keep `True` for COCO object detection AP.

Lifecycle:

```python
evaluator.update({image_id: {"boxes": boxes_xyxy, "scores": scores, "labels": category_ids}})
evaluator.synchronize_between_processes()
evaluator.accumulate()
evaluator.summarize()
stats = evaluator.coco_eval["bbox"].stats.tolist()
```

Prediction contract for `bbox` evaluation:

| Key | Shape/type | Meaning |
| --- | --- | --- |
| `boxes` | `torch.Tensor[N, 4]` | Absolute pixel `xyxy` boxes before evaluator conversion. |
| `scores` | `torch.Tensor[N]` | Confidence per detection. |
| `labels` | `torch.Tensor[N]` or list-like | COCO `category_id` values, not contiguous class indexes unless the dataset uses contiguous IDs. |

`update()` converts each prediction into COCO result dictionaries, suppresses noisy `pycocotools` prints while loading detections, and stores per-image evaluation results. `summarize()` prints the familiar AP/AR table.

## `convert_to_xywh`

```python
from groundingdino.datasets.cocogrounding_eval import convert_to_xywh

boxes_xywh = convert_to_xywh(boxes_xyxy)
```

- Input: `torch.Tensor[N, 4]` in absolute `xmin, ymin, xmax, ymax` format.
- Output: `torch.Tensor[N, 4]` in absolute `xmin, ymin, width, height` format for COCO result JSON.
- Use it only after normalized model boxes have already been scaled to image pixels.

## COCO Dataset Wrapper Concept

The bundled helper implements a local `CocoDetection` wrapper around `torchvision.datasets.CocoDetection`:

- Reads `image_dir` and `anno_path` through the COCO API.
- Converts annotation boxes from COCO `xywh` to absolute `xyxy`.
- Clamps boxes to image width/height and filters invalid boxes.
- Returns a target dict with `image_id`, `boxes`, and `orig_size`.
- Applies the same evaluation transforms used by the demo workflow: resize to `800` with `max_size=1333`, tensor conversion, and ImageNet normalization.

The ground-truth boxes are mainly needed by the transforms/evaluator wiring; GroundingDINO predictions are generated from image pixels and the category caption.

## COCO Postprocessor Concept

GroundingDINO predicts boxes and token-level logits. The COCO evaluator needs category IDs, scores, and pixel boxes. The `PostProcessCocoGrounding` concept performs that bridge:

1. Read `categories[*].name` from the COCO annotation JSON.
2. Build a prompt such as `person . bicycle . car . ... .`.
3. Tokenize category spans using `build_captions_and_token_span` and `create_positive_map_from_span`.
4. Convert `pred_logits.sigmoid()` from token probabilities into category probabilities with a positive-map matrix multiply.
5. Select the top `num_select` query/category pairs.
6. Convert `pred_boxes` from normalized `cxcywh` to normalized `xyxy`, gather selected boxes, and scale by original image size.
7. Return dictionaries with `scores`, `labels`, and `boxes`.

The original demo hard-codes the official COCO category-id map. The bundled helper derives category IDs from the annotation JSON so mini-COCO subsets can run as smoke tests, while still requiring official COCO categories for benchmark-comparable AP.

## Supporting Package APIs

| API | Role in evaluation |
| --- | --- |
| `SLConfig.fromfile(config_file)` | Loads the model config and text encoder type. |
| `groundingdino.models.build_model(cfg)` | Builds the model architecture specified by the config. |
| `clean_state_dict(checkpoint["model"])` | Normalizes checkpoint key names before `load_state_dict`. |
| `get_tokenlizer.get_tokenlizer(cfg.text_encoder_type)` | Creates the tokenizer used for category text spans. |
| `build_captions_and_token_span(cat_list, force_lowercase=True)` | Builds normalized category caption text and span mapping. |
| `create_positive_map_from_span(tokenized, token_span)` | Builds the category-to-token positive map. |
| `box_ops.box_cxcywh_to_xyxy(boxes)` | Converts model boxes from center format to corner format. |
| `collate_fn` | Collates transformed images into the nested tensor format expected by the model. |

## Output Interpretation

`evaluator.coco_eval["bbox"].stats` follows standard COCO order. Important indexes:

| Index | Meaning |
| --- | --- |
| `0` | AP averaged over IoU `0.50:0.95`, all object sizes, max detections 100. |
| `1` | AP at IoU `0.50`. |
| `2` | AP at IoU `0.75`. |
| `3` | AP for small objects. |
| `4` | AP for medium objects. |
| `5` | AP for large objects. |

For GroundingDINO zero-shot COCO comparisons, cite index `0` as bbox AP unless the user explicitly asks for a different COCO metric.

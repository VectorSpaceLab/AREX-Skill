# Detection Helpers

This reference explains TorchVision detection helper concepts that interact with `torchvision.ops`. It is not a replacement for high-level model selection or training guidance.

## Outputs and postprocessing

Most TorchVision detection models return a list with one dictionary per input image during evaluation. Common keys are:

- `boxes`: float tensor `[num_detections, 4]` in `xyxy` image coordinates.
- `labels`: integer tensor `[num_detections]` with predicted class ids.
- `scores`: float tensor `[num_detections]` with confidence scores.
- `masks`: for instance segmentation, tensor `[num_detections, 1, H, W]` or postprocessed masks depending on model path.
- `keypoints`: for keypoint models, tensor `[num_detections, num_keypoints, 3]`.

Detection postprocessing commonly applies:

1. Decode box regressions against anchors/proposals.
2. Clip boxes to image size.
3. Remove background class or low-score candidates with `score_thresh`.
4. Remove invalid or very small boxes.
5. Apply `batched_nms` using class labels or feature levels as groups.
6. Truncate to `detections_per_img`.
7. Resize boxes/masks/keypoints back to original image sizes through the model transform.

If a user asks how to tune detection output count or filtering, look for model constructor options such as `box_score_thresh`, `box_nms_thresh`, `box_detections_per_img`, `rpn_score_thresh`, `rpn_nms_thresh`, `score_thresh`, `nms_thresh`, and `detections_per_img`. Route complete model construction and pretrained weights to `../models-and-weights/`.

## Boxes inside detection models

TorchVision detection internals use `xyxy` boxes for proposals, targets, and predictions. Training targets commonly require:

- `boxes`: float tensor `[N, 4]`, `xyxy`, valid coordinate order, within image bounds where practical.
- `labels`: int64 tensor `[N]`, with class ids expected by the model.
- Optional task-specific fields such as `masks`, `keypoints`, `area`, `iscrowd`, and `image_id`.

Transforms that update boxes or masks belong in `../transforms-and-tv-tensors/`. This skill only covers how those boxes are consumed by ops and detection helper code.

## ROI heads and proposal helpers

Two-stage models such as Faster R-CNN, Mask R-CNN, and Keypoint R-CNN use proposal and ROI helper components:

- Region Proposal Network (RPN) filters anchors using objectness scores, NMS, and pre/post-NMS top-k limits.
- `RoIHeads` pool proposal features, classify/refine boxes, apply score thresholding, class-wise NMS, and top-k truncation.
- `MultiScaleRoIAlign` maps proposals to FPN levels and returns fixed-size feature crops for box, mask, or keypoint heads.
- `BoxCoder` encodes/decodes box regression deltas against anchors or proposals; FCOS-style code uses `BoxLinearCoder`.

When debugging custom heads, check the shape boundary between helpers:

- Proposals: list of `[num_props_i, 4]` `xyxy` tensors, one per image.
- Image shapes: list of `(height, width)` tuples after model transforms.
- Feature maps: ordered mapping of `[N, C, H_l, W_l]` tensors with names matching the ROI pooler.
- Box logits/regression: model-specific tensors that are decoded before final NMS.

## One-stage models

RetinaNet, FCOS, SSD, and SSDLite do not use ROI pooling, but still rely on box coders/decoders, clipping, score thresholds, `batched_nms`, and `detections_per_img` truncation in postprocessing.

Common debugging checks:

- Anchor generator output count must align with head output locations.
- Classification scores are filtered before NMS, so a high `score_thresh` can yield empty predictions.
- `nms_thresh` governs overlap suppression after decoding boxes.
- `detections_per_img` caps the final returned detections.

## Choosing the right helper level

- Use raw `torchvision.ops` functions for standalone box normalization, NMS, IoU calculations, or ROI feature extraction.
- Use detection helper classes only when integrating custom backbones/heads with TorchVision detection architecture.
- Use model factory APIs and weights docs from `../models-and-weights/` for standard detection architectures.
- Use training reference guidance from `../training-references/` for COCO/VOC-style command recipes.

## Minimal postprocessing skeleton

```python
boxes = torchvision.ops.box_convert(boxes, in_fmt="xywh", out_fmt="xyxy")
boxes = torchvision.ops.clip_boxes_to_image(boxes, size=(height, width))
keep = torchvision.ops.remove_small_boxes(boxes, min_size=1.0)
boxes, scores, labels = boxes[keep], scores[keep], labels[keep]
keep = scores > score_thresh
boxes, scores, labels = boxes[keep], scores[keep], labels[keep]
keep = torchvision.ops.batched_nms(boxes, scores, labels, iou_threshold=nms_thresh)
keep = keep[:detections_per_img]
result = {"boxes": boxes[keep], "scores": scores[keep], "labels": labels[keep]}
```

For tests, assert shapes and coordinate validity rather than exact NMS ordering when equal scores or hardware-dependent ties are possible.

# Evaluation and Visualization

## Visualization helpers

Verified public helpers in `mrcnn.visualize` include:

- `display_instances(image, boxes, masks, class_ids, class_names, scores=None, title='', figsize=(16, 16), ax=None, show_mask=True, show_bbox=True, colors=None, captions=None)`
- `display_differences(image, gt_box, gt_class_id, gt_mask, pred_box, pred_class_id, pred_score, pred_mask, class_names, title='', ax=None, show_mask=True, show_box=True, iou_threshold=0.5, score_threshold=0.5)`
- `draw_rois(image, rois, refined_rois, mask, class_ids, class_names, limit=10)`
- `display_top_masks(image, mask, class_ids, class_names, limit=4)`
- `draw_boxes(image, boxes=None, refined_boxes=None, masks=None, captions=None, visibilities=None, title='', ax=None)`
- `display_weight_stats(model)`

Use these helpers for local inspection and notebook parity. Do not tell future agents to reopen the original notebooks.

## COCO-style evaluation flow

The COCO sample shows the reusable pattern:

1. Run `model.detect([image])`.
2. Convert predictions into COCO result records with `image_id`, `category_id`, `bbox`, `score`, and compressed `segmentation`.
3. Load results with pycocotools.
4. Run `COCOeval` for `bbox` or `segm` metrics.

Important conversion detail: COCO `bbox` uses `[x, y, width, height]`, while Mask_RCNN boxes are `[y1, x1, y2, x2]`.

## AP and recall utilities

`mrcnn.utils` provides:

- `compute_matches(gt_boxes, gt_class_ids, gt_masks, pred_boxes, pred_class_ids, pred_scores, pred_masks, iou_threshold=0.5, score_threshold=0.0)`
- `compute_ap(..., iou_threshold=0.5)`
- `compute_ap_range(..., iou_thresholds=None, verbose=1)`
- `compute_recall(pred_boxes, gt_boxes, iou)`

Use them when the task is a local metric check rather than full COCO benchmark execution.

## Nucleus RLE

The Nucleus sample encodes masks for competition submission. Reusable facts:

- Encode masks in column-major order after transposing `mask.T.flatten()`.
- RLE strings are space-separated start/length pairs.
- The submission helper sorts instances by score and removes overlaps before encoding.
- An empty mask set should still produce a valid image-id-only line.

The bundled `scripts/rle_tools.py` keeps this logic available without the sample notebook.

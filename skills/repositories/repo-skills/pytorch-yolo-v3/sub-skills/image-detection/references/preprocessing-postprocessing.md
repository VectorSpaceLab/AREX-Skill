# Preprocessing and Postprocessing APIs

## Purpose

Read this when a user asks how pytorch-yolo-v3 converts image files into tensors, transforms YOLO feature maps into boxes, filters predictions, applies class-wise NMS, loads class names, or interprets raw detection rows.

## Preprocessing API contracts

| API | Contract | Notes |
| --- | --- | --- |
| `letterbox_image(img, inp_dim)` | Resizes an OpenCV image array while preserving aspect ratio and pads with value `128` to `(width, height)` from `inp_dim`. | `img` is an HWC NumPy array. `inp_dim` is a two-item tuple such as `(416, 416)`. |
| `prep_image(img, inp_dim)` | Reads an image path with OpenCV, letterboxes to square `inp_dim`, converts BGR to RGB, transposes to CHW, scales to `[0, 1]`, adds batch dimension, and returns `(tensor, orig_im, dim)`. | Verified tiny-image behavior: a `24x32` image at `64` returns tensor shape `(1, 3, 64, 64)`, original shape `(24, 32, 3)`, and `dim == (32, 24)`. |
| `prep_image_pil(img, network_dim)` | Opens a path with PIL, converts to RGB, resizes directly to `network_dim`, creates a float tensor shaped `(1, 3, *network_dim)`, and returns `(tensor, orig_im, dim)`. | Unlike `prep_image`, this path performs direct PIL resizing rather than OpenCV letterboxing. |
| `inp_to_image(inp)` | Converts a tensor-like network input back to an HWC NumPy image array scaled to `0..255` and channel-reversed for OpenCV-style display/write use. | It squeezes batch dimension and moves CPU tensors to NumPy. |

Practical implications:

- `prep_image` is the detector path used by image inference.
- OpenCV reads images as BGR; the network tensor is RGB after `[:,:,::-1]` channel reversal.
- `dim` is `(width, height)`, not `(height, width)`. Use this when mapping detections back to the original image.
- If `cv2.imread` returns `None`, `prep_image` will fail when it tries to access `orig_im.shape`; treat this as an image path, extension, permission, or codec problem.

## Postprocessing API contracts

| API | Contract | Notes |
| --- | --- | --- |
| `predict_transform(prediction, inp_dim, anchors, num_classes, CUDA=True)` | Reshapes a YOLO feature map into rows of box predictions, scales anchors by stride, applies sigmoid to center/object/class scores, adds grid offsets, exponentiates width/height, and scales box coordinates by stride. | Pass `CUDA=False` for CPU tensors. Route anchor/cfg internals to [../../model-and-config/SKILL.md](../../model-and-config/SKILL.md). |
| `write_results(prediction, confidence, num_classes, nms=True, nms_conf=0.4)` | Filters object confidence, converts center-width-height boxes to corner coordinates, selects the maximum class score/class id, applies class-wise NMS when enabled, and returns detection rows. | Returns integer `0` when no predictions survive. A synthetic one-box check returns tensor shape `(1, 8)`. |
| `load_classes(namesfile)` | Reads class names from a newline-delimited names file and drops the final empty split element. | The bundled COCO names evidence has 80 names, from `person` through `toothbrush`. |
| `bbox_iou(box1, box2)` | Computes pairwise IoU for boxes in corner format `[x1, y1, x2, y2]`. | Synthetic overlapping/non-overlapping boxes produce finite IoU values. |

## Detection row format

`write_results` returns one row per retained detection with eight columns:

```text
[batch_id, x1, y1, x2, y2, object_confidence, class_confidence, class_id]
```

After model inference, the detector rescales `x1`, `y1`, `x2`, `y2` from the letterboxed network square back onto the original image dimensions, clamps coordinates inside the original image, maps `class_id` through the loaded class-name list, and draws boxes/labels on the original image arrays.

## Classes, cfg, and weights alignment

- The default class count is `80`.
- The default names list contains 80 COCO class names.
- The default cfg has three YOLO heads with `classes=80` and shared COCO anchors.
- A cfg/classes/weights mismatch can produce shape errors, wrong labels, missing detections, or failed weight loading. Route model-file compatibility and cfg edits to [../../model-and-config/SKILL.md](../../model-and-config/SKILL.md).

## Safe validation

Use the bundled smoke helper for a no-weight check of the preprocessing/postprocessing path:

```bash
python scripts/check_image_pipeline.py --reso 64
```

Expected pass signals include:

- `prep_image` reports a `(1, 3, 64, 64)` tensor for the generated tiny image.
- `bbox_iou` reports finite IoU values.
- `write_results` reports output shape `(1, 8)`.
- The final line says no weights, downloads, CUDA, GUI, or sample images were required.

To validate the user's checkout modules instead of the bundled fallback implementations:

```bash
python scripts/check_image_pipeline.py --repo-root <repo-root> --reso 64
```

# Data Formats

## Purpose

Read this when preparing images, prompt arrays, mask outputs, automatic mask annotations, or SA-1B-style JSON for Segment Anything workflows.

## Images

- `SamPredictor.set_image` expects an `H x W x 3` NumPy array with `uint8` values in `[0, 255]`.
- Pass `image_format="RGB"` for RGB arrays and `image_format="BGR"` for images loaded by OpenCV without conversion.
- Automatic mask generation also expects an RGB `H x W x 3` NumPy array when using the Python API.
- The bundled AMG CLI reads images with OpenCV and converts BGR to RGB internally.

## Prompted Segmentation Inputs

| Input | Shape | Meaning |
| --- | --- | --- |
| `point_coords` | `N x 2` NumPy array | Pixel coordinates in `(x, y)` order in the original image frame. |
| `point_labels` | length `N` NumPy array | `1` for foreground points, `0` for background points. |
| `box` | length 4 NumPy array | Box prompt in `XYXY` order. |
| `mask_input` | `1 x 256 x 256` NumPy array | Low-resolution logits from a previous prediction iteration. |

If `point_coords` is supplied, `point_labels` must also be supplied. Coordinates and boxes are transformed internally after `set_image`.

## Prompted Segmentation Outputs

`SamPredictor.predict(...)` returns `(masks, scores, low_res_masks)`:

- `masks`: `C x H x W`, where `C` is usually 3 with `multimask_output=True` and 1 with `False`.
- `scores`: length `C`, predicted mask quality scores.
- `low_res_masks`: `C x 256 x 256`, logits suitable for iterative refinement via `mask_input=low_res_masks[index:index+1]`.

## Automatic Mask Annotation Records

`SamAutomaticMaskGenerator.generate(image)` returns a list of dictionaries. Each record contains:

| Key | Meaning |
| --- | --- |
| `segmentation` | Binary mask, uncompressed RLE, or COCO RLE depending on `output_mode`. |
| `bbox` | Bounding box around the mask in `XYWH` format. |
| `area` | Mask area in pixels. |
| `predicted_iou` | Model-predicted mask quality score. |
| `point_coords` | Point prompt used to generate the mask. |
| `stability_score` | Stability under mask-threshold perturbation. |
| `crop_box` | Crop used to generate the mask in `XYWH` format. |

`output_mode="coco_rle"` requires `pycocotools`. `output_mode="binary_mask"` can consume large memory for high-resolution images or many masks.

## SA-1B-Style JSON

Dataset-style mask JSON stores one image record and many annotations:

```json
{
  "image": {
    "image_id": 1,
    "width": 1024,
    "height": 768,
    "file_name": "example.jpg"
  },
  "annotations": [
    {
      "id": 0,
      "segmentation": {},
      "bbox": [x, y, w, h],
      "area": 1234,
      "predicted_iou": 0.95,
      "stability_score": 0.97,
      "crop_box": [x, y, w, h],
      "point_coords": [[x, y]]
    }
  ]
}
```

Use `pycocotools.mask.decode(annotation["segmentation"])` to decode COCO RLE masks.

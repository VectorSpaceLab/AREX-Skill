# AMG Troubleshooting

## `ModuleNotFoundError: No module named 'cv2'`

The bundled CLI uses OpenCV for reading images, RGB conversion, and PNG writing. Install `opencv-python` in the active environment. `min_mask_region_area > 0` also needs OpenCV because SAM removes small holes/islands with connected-components operations.

## `ModuleNotFoundError: No module named 'pycocotools'`

`--convert-to-rle` maps to `output_mode="coco_rle"`, which imports `pycocotools`. Install `pycocotools`, or omit `--convert-to-rle` and write binary PNG masks plus `metadata.csv` instead.

## Checkpoint and `--model-type` Mismatch

Use the model type that matches the checkpoint filename:

- `sam_vit_h_4b8939.pth`: `--model-type vit_h` or `default`
- `sam_vit_l_0b3195.pth`: `--model-type vit_l`
- `sam_vit_b_01ec64.pth`: `--model-type vit_b`

A mismatch can surface as missing or unexpected state-dict keys, tensor shape errors, or poor outputs.

## CUDA Is Selected by Default

The original AMG command defaults to CUDA. The bundled CLI keeps that behavior for compatibility. If CUDA is unavailable, use:

```bash
--device cpu
```

If CUDA exists but runs out of memory, reduce `--points-per-batch`, lower `--points-per-side`, remove crop layers, use `--convert-to-rle`, or use a smaller model/checkpoint pair.

## GPU OOM or Host Memory Blowups

Common causes:

- Large images create large image embeddings and large full-resolution masks.
- `points_per_side` scales quadratically.
- `points_per_batch` raises peak model inference memory.
- `crop_n_layers` multiplies the number of crops and prompt grids.
- `output_mode="binary_mask"` materializes one full `H x W` boolean array per mask.

Fast mitigations:

```bash
--points-per-batch 8 --points-per-side 24 --crop-n-layers 0 --convert-to-rle
```

For slow but reliable execution, also use `--device cpu`.

## Empty or Too Few Masks

Likely causes:

- The input image could not be loaded or was not a supported image file.
- `pred_iou_thresh` or `stability_score_thresh` is too strict for the image.
- `points_per_side` is too low for small objects.
- No crop layers are used for many small objects.

Try:

```bash
--pred-iou-thresh 0.80 --stability-score-thresh 0.90 --points-per-side 48 --crop-n-layers 1
```

Then back off if noisy or duplicate masks appear.

## Unreadable Input Images

The CLI reports unreadable images and skips them. Confirm the file extension, file permissions, and that OpenCV can decode the image. For folder input, only common image extensions are scanned.

## Output Already Exists

For binary PNG output, each image creates an output subfolder. For COCO RLE, each image creates one JSON file. If a destination already exists, rerun with `--overwrite` only when replacing it is intended.

## `min_mask_region_area` Has No Effect or Fails

`min_mask_region_area=0` disables postprocessing. Any value greater than zero requires OpenCV and removes both small disconnected islands and small holes before a final NMS pass.

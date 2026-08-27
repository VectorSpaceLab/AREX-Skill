# Data Formats

## Inputs

The image directory should contain ordinary image files such as `.jpg`, `.jpeg`, `.png`, `.bmp`, or `.webp`. The helper validates that at least one supported image file is present before loading the model.

Provide a local GroundingDINO config and checkpoint. The helper does not download model weights, configs, datasets, or image assets.

## Prompt format

Use an open-vocabulary caption that names the target concepts. For multi-class pseudo-labeling, separate categories with periods:

```text
bus . car . traffic light .
```

Comma-separated text can work, but period-separated categories usually produce cleaner phrase boundaries for downstream review.

## Prediction tensors

`groundingdino.util.inference.predict` returns:

| Value | Format | Meaning |
| --- | --- | --- |
| `boxes` | normalized `cxcywh` tensor | Center x, center y, width, height relative to image size. |
| `logits` | confidence tensor | One confidence score per retained detection. |
| `phrases` | list of strings | Decoded text phrase for each detection. |

The pseudo-label helper converts each normalized `cxcywh` box to normalized top-left `xywh` before creating a FiftyOne detection.

## FiftyOne detection field

Each sample receives a `detections` field containing `fo.Detections`. Each detection stores:

| Field | Format | Meaning |
| --- | --- | --- |
| `label` | string | GroundingDINO decoded phrase, such as `car` or `traffic light`. |
| `bounding_box` | relative `[x, y, width, height]` | Top-left `xywh` values normalized to image width/height, as expected by FiftyOne. |
| `confidence` | float | GroundingDINO score used for review and filtering. |

Do not multiply these relative boxes by image width/height before assigning them to FiftyOne. FiftyOne handles the conversion needed when exporting to COCO.

## COCO export

When `--export-coco` is set, the helper exports a `fo.types.COCODetectionDataset` to:

```text
output-dir/coco_dataset/
```

The exported dataset contains copied/exported images and COCO detection annotations generated from the `detections` field. COCO uses top-left `xywh` boxes in image coordinates in its JSON annotation records; FiftyOne performs this conversion from its stored relative boxes during export.

## Annotated image review

When `--draw-labels` is set, the helper renders review images to:

```text
output-dir/images_with_bounding_boxes/
```

Use these images to tune prompts and thresholds before trusting the exported COCO labels for training or downstream curation.

## Subsampling

`--subsample N` labels a smaller cloned view of the dataset. Use it for quick checks, especially before enabling COCO export on large folders. If `N` is greater than or equal to the number of discovered images, the full dataset is used.

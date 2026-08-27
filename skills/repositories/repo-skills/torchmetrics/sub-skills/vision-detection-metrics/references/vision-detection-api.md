# Vision Detection Metrics API

This reference groups the TorchMetrics vision and detection APIs by input contract so future agents can choose the right metric quickly.

## 1) Full-reference image quality

Use these when you already have a prediction image and a target image.

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| Peak signal-to-noise ratio | `PeakSignalNoiseRatio` / `peak_signal_noise_ratio` | `preds`, `target` with matching shape, usually `(N, C, H, W)` | `data_range` required, `base`, `reduction`, `dim` | Scalar or per-sample tensor | Pass `data_range` explicitly; tuple values clamp inputs and define the range. If `dim` is set, `reduction` should usually stay at the default. |
| Structural similarity | `StructuralSimilarityIndexMeasure` / `structural_similarity_index_measure` | Matching `preds`, `target` images in `(N, C, H, W)` or `(N, C, D, H, W)` | `gaussian_kernel`, `sigma`, `kernel_size`, `data_range`, `k1`, `k2`, `return_full_image`, `return_contrast_sensitivity` | Scalar or per-sample tensor | Use explicit `data_range` for stable behavior; `return_full_image` and `return_contrast_sensitivity` are mutually exclusive. |
| Multi-scale SSIM | `MultiScaleStructuralSimilarityIndexMeasure` / `multiscale_structural_similarity_index_measure` | Same as SSIM | Same family as SSIM plus `betas`, `normalize` | Scalar or per-sample tensor | Use a larger spatial size than SSIM because it pools across scales. |
| Spectral angle mapper | `SpectralAngleMapper` / `spectral_angle_mapper` | Matching `(N, C, H, W)` tensors | `reduction` | Scalar or per-sample tensor | Requires channel dimension > 1. |
| Spatial correlation coefficient | `SpatialCorrelationCoefficient` / `spatial_correlation_coefficient` | Matching `(N, C, H, W)` or `(N, H, W)` tensors | `high_pass_filter`, `window_size` | Scalar tensor | Useful for spatial structure checks. |
| Universal image quality index | `UniversalImageQualityIndex` / `universal_image_quality_index` | Matching `(N, C, H, W)` tensors | `kernel_size`, `sigma`, `reduction` | Scalar or per-sample tensor | `kernel_size` and `sigma` are 2-tuples for the 2D path. |
| Visual information fidelity | `VisualInformationFidelity` / `visual_information_fidelity` | Matching `(N, C, H, W)` tensors with height and width at least 41 | `sigma_n_sq`, `reduction` | Scalar or per-sample tensor | Tiny crops will fail because the metric needs a large enough receptive field. |
| Total variation | `TotalVariation` / `total_variation` | A single image batch `(N, C, H, W)` | `reduction` | Scalar or per-sample tensor | No target tensor is needed. |

## 2) Multispectral and pan-sharpening metrics

Use these when the task is remote sensing, fusion, or multispectral comparison.

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| Quality with no reference | `QualityWithNoReference` / `quality_with_no_reference` | `preds` high-res multispectral tensor plus a target dict with `ms`, `pan`, and optional `pan_lr` | `alpha`, `beta`, `norm_order`, `window_size`, `reduction` | Scalar or per-sample tensor | `ms` and `pan` must have compatible batch/channel sizes and the high-res sizes must be multiples of the low-res sizes. If `pan_lr` is omitted, the metric synthesizes it and may need torchvision. |
| Spatial distortion index | `SpatialDistortionIndex` / `spatial_distortion_index` | `preds`, `ms`, `pan`, optional `pan_lr` | `norm_order`, `window_size`, `reduction` | Scalar or per-sample tensor | Same spatial-multiple rules as QNR; if `pan_lr` is absent, torchvision is used for degradation and resize. |
| Spectral distortion index | `SpectralDistortionIndex` / `spectral_distortion_index` | Matching multispectral tensors `(N, C, H, W)` | `p`, `reduction` | Scalar or per-sample tensor | `preds` and `target` must share dtype and batch/channel sizes. |
| Error relative global dimensionless synthesis | `ErrorRelativeGlobalDimensionlessSynthesis` / `error_relative_global_dimensionless_synthesis` | Matching `(N, C, H, W)` tensors | `ratio`, `reduction` | Scalar or per-sample tensor | Used for pan-sharpening accuracy. |
| Relative average spectral error | `RelativeAverageSpectralError` / `relative_average_spectral_error` | Matching `(N, C, H, W)` tensors | `window_size` | Scalar tensor | The sliding window must be positive and smaller than the image dimensions. |
| Root mean squared error using sliding window | `RootMeanSquaredErrorUsingSlidingWindow` / `root_mean_squared_error_using_sliding_window` | Matching `(N, C, H, W)` tensors | `window_size` | Scalar tensor | Good for local similarity checks. |

## 3) Segmentation metrics

Use these when the output is a semantic class map or one-hot segmentation mask.

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| Dice score | `DiceScore` / `dice_score` | `preds`, `target` in one-hot, index, or mixed form | `num_classes`, `include_background`, `average`, `aggregation_level`, `input_format` | Scalar or class vector | `input_format="mixed"` is valid when one tensor has a class channel and the other is index-based. `include_background=False` removes class 0 from the output. |
| Generalized Dice score | `GeneralizedDiceScore` / `generalized_dice_score` | Same tensor forms as Dice | `num_classes`, `include_background`, `per_class`, `weight_type`, `input_format` | Scalar or class vector | Weight type controls class balancing. |
| Mean IoU | `MeanIoU` / `mean_iou` | Same tensor forms as Dice | `num_classes`, `include_background`, `per_class`, `input_format` | Scalar or class vector | `num_classes` is required for index input. Classes absent from both prediction and target return `-1` in per-class mode. |
| Hausdorff distance | `HausdorffDistance` / `hausdorff_distance` | Same tensor forms as Dice | `num_classes`, `include_background`, `distance_metric`, `spacing`, `directed`, `input_format` | Scalar tensor | `spacing` may be a list or tensor; `directed=True` computes the directed form. |

### Segmentation input reminders

- One-hot tensors should be shaped like `(N, C, ...)`.
- Index tensors should be shaped like `(N, ...)`.
- Mixed inputs are valid when exactly one tensor has the extra class dimension.
- `num_classes` is required for index mode and often helpful when a class is missing from a batch.

## 4) Detection and instance segmentation metrics

Use these when the input is a list of per-image prediction dictionaries and target dictionaries.

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| Mean average precision | `MeanAveragePrecision` / `mean_average_precision` | `preds` and `target` as `list[dict]` | `box_format`, `iou_type`, `iou_thresholds`, `rec_thresholds`, `max_detection_thresholds`, `class_metrics`, `extended_summary`, `average`, `backend` | Dict of tensors | `preds` must include `boxes`, `scores`, and `labels`. Targets need `boxes` and `labels`, plus optional `masks`, `iscrowd`, and `area`. For `iou_type=("bbox", "segm")`, keys are prefixed with `bbox_` and `segm_`. |
| IoU | `IntersectionOverUnion` / `intersection_over_union` | `list[dict]` with `boxes` and `labels` | `box_format`, `iou_threshold`, `class_metrics`, `respect_labels` | Dict of tensors | Scores are not required here. |
| CIoU | `CompleteIntersectionOverUnion` / `complete_intersection_over_union` | Same as IoU | `box_format`, `iou_threshold`, `class_metrics`, `respect_labels` | Dict of tensors | Same list-of-dicts contract as IoU. |
| DIoU | `DistanceIntersectionOverUnion` / `distance_intersection_over_union` | Same as IoU | `box_format`, `iou_threshold`, `class_metrics`, `respect_labels` | Dict of tensors | Same list-of-dicts contract as IoU. |
| GIoU | `GeneralizedIntersectionOverUnion` / `generalized_intersection_over_union` | Same as IoU | `box_format`, `iou_threshold`, `class_metrics`, `respect_labels` | Dict of tensors | Same list-of-dicts contract as IoU. |

### Detection input reminders

- `box_format` can be `xyxy`, `xywh`, or `cxcywh`.
- `masks` must be boolean tensors shaped `(num_boxes, H, W)` when `iou_type` includes `segm`.
- `scores` are required for mAP predictions but not for the IoU family.
- `max_detection_thresholds` must have length 3 when you override it.
- `backend` for mAP is either `pycocotools` or `faster_coco_eval`.

## 5) Panoptic metrics

Use these when each pixel carries both a category id and an instance id.

| Metric | Class / functional | Core inputs | Key args | Output | Notes |
| --- | --- | --- | --- | --- | --- |
| Panoptic quality | `PanopticQuality` / `panoptic_quality` | `preds` and `target` tensors shaped `(B, *spatial_dims, 2)` | `things`, `stuffs`, `allow_unknown_preds_category`, `return_sq_and_rq`, `return_per_class` | Scalar, vector, or stacked tensor | `things` and `stuffs` must be disjoint. Unknown target categories are ignored; unknown predicted categories can be ignored or rejected. |
| Modified panoptic quality | `ModifiedPanopticQuality` / `modified_panoptic_quality` | Same as PQ | `things`, `stuffs`, `allow_unknown_preds_category` | Scalar tensor | Uses the modified stuff-class formulation from the seamless scene segmentation setting. |

## 6) When to choose module vs functional

- Use the functional call when you need a one-shot, stateless result.
- Use the metric class when you need to accumulate batches or keep an ongoing score.
- If the task is mostly about `update`, `compute`, `reset`, or distributed state handling, route to the core API skill instead of expanding this one.

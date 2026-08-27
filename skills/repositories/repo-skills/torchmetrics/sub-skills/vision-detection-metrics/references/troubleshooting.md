# Troubleshooting

## Image quality and multispectral metrics

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PSNR` complains about `data_range` or gives an unexpected scale | The metric needs an explicit range, especially when your tensors are normalized | Pass `data_range=1.0` for normalized images or a tuple if you want clamping and an explicit range. |
| `SSIM` or `MS-SSIM` raises a kernel-size or dimension error | The tensors are not `(N, C, H, W)` / `(N, C, D, H, W)` or the default kernel is too large for the image | Keep the batch/channel axes in place, use odd positive kernel sizes, and use a larger spatial size for MS-SSIM. |
| `VIF` fails on small crops | The metric expects at least `41 x 41` pixels | Resize or crop to a larger patch before running the metric. |
| `SAM` says the channel dimension must be larger than 1 | Single-channel inputs are not valid for spectral angle comparisons | Use multispectral inputs with `C > 1` or choose a different image-quality metric. |
| `SCC` or `QNR` fails when `pan_lr` is omitted | The degraded panchromatic path needs torchvision | Install torchvision or supply `pan_lr` explicitly. |
| `QNR` / `SDI` says the multispectral and panchromatic shapes are incompatible | High-res tensors are not integer multiples of the low-res tensors | Make `preds` and `pan` the same spatial size and ensure that size is a multiple of `ms`. |
| `SCC` or `QNR` looks noisy after a dtype change | The metrics expect matching dtypes between paired inputs | Cast all paired tensors to the same floating dtype before calling the metric. |

## Segmentation metrics

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `DiceScore` or `MeanIoU` complains about `num_classes` in index mode | Index input needs the class count to build one-hot encodings | Pass `num_classes` explicitly. |
| Mixed segmentation input fails | The class and index tensors do not differ by exactly one channel dimension | Make one tensor `(N, C, ...)` and the other `(N, ...)`, or convert both to the same representation. |
| Background handling changes the output length | `include_background=False` removes class 0 from the result | Adjust downstream expectations so class vectors are one shorter. |
| `MeanIoU` returns `-1` for some classes | Those classes are absent from both prediction and target | That value means "no valid data for this class", not a numerical failure. |
| `DiceScore` or `MeanIoU` rejects `aggregation_level` or `mixed` | The installed wheel exposes a slimmer segmentation signature than the source branch | Fall back to the conservative one-hot or index path; the bundled smoke script already does this. |
| `HausdorffDistance` errors on `spacing` or `directed` | The argument type or list length is wrong | Pass `spacing` as a list or tensor with the correct spatial length, and keep `directed` boolean. |
| `HausdorffDistance` complains about the distance engine | The scipy engine is unavailable in that environment | Install scipy, or use the pytorch engine path where supported. |

## Detection and instance segmentation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MeanAveragePrecision` says `preds` or `target` is not a sequence | The metric expects a list of per-image dictionaries | Wrap each image sample in its own dict and pass a list. |
| `MeanAveragePrecision` says a dict is missing `scores` | Predictions for mAP need per-box scores | Add `scores` to every prediction dict. Targets do not need scores. |
| `MeanAveragePrecision` says `boxes` or `masks` have the wrong type | The values are not tensors | Use tensor values for every box, score, label, and mask. |
| `MeanAveragePrecision` rejects a mask | The mask tensor is not boolean or the shape does not match the box count | Use `(num_boxes, H, W)` boolean masks. |
| `MeanAveragePrecision` with tuple `iou_type` does not expose `map` | The metric prefixes keys when both bbox and segm are requested | Check `bbox_map` and `segm_map` instead. |
| `MeanAveragePrecision` complains about `box_format` | The boxes are in the wrong coordinate convention | Match `box_format` to the actual tensor layout. |
| `MeanAveragePrecision` needs a backend package | Neither COCO backend is installed | Install `pycocotools` or `faster_coco_eval`, and keep torchvision available. |
| `MeanAveragePrecision` errors on `max_detection_thresholds` | The list length is invalid | Use exactly three integers. |
| `IntersectionOverUnion` or its CIoU/DIoU/GIoU variants give a low score when boxes overlap | Labels are being respected, so cross-label matches are ignored | Set `respect_labels=False` only when that is truly the intended comparison. |
| `IntersectionOverUnion` mentions scores, but you only care about overlap | You picked the wrong metric family | Use the IoU family for label-aware overlap; use mAP when you need ranked detections and scores. |

## Panoptic metrics

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PanopticQuality` says the final dimension is wrong | The input is not shaped `(B, *spatial_dims, 2)` | Store category id and instance id in the last dimension. |
| `PanopticQuality` rejects category sets | `things` and `stuffs` overlap or contain non-integers | Keep the category sets disjoint and integer-only. |
| `PanopticQuality` fails on unknown predicted categories | The predicted category id is outside the declared sets | Either fix the labels or set `allow_unknown_preds_category=True` if that is the intended behavior. |
| `ModifiedPanopticQuality` looks different from `PanopticQuality` | The metric is intentionally using a different stuff-class rule | That difference is expected; choose the metric that matches the evaluation protocol. |

## Precision and device issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PSNR` fails on half precision CPU | The CPU path does not fully support the needed log operations | Keep the CPU smoke in float32 or move the metric to CUDA. |
| A metric works on CPU but not on CUDA | One of the inputs or the metric state stayed on the wrong device | Move every tensor and the metric instance to the same device before updating. |
| A metric imports but an optional branch fails later | The package was installed without an optional backend | Check the exact branch you are using and install the missing optional dependency instead of assuming the base package is enough. |

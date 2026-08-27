# Evaluation and Analysis

## Evaluator Config Patterns

MMDetection 3.x uses `val_evaluator` and `test_evaluator` metric configs. Keep evaluator annotations aligned with the validation/test dataset annotation file.

COCO bbox and mask metrics:

```python
val_evaluator = dict(
    type='CocoMetric',
    ann_file=data_root + 'annotations/instances_val.json',
    metric=['bbox', 'segm'],
    format_only=False)
test_evaluator = val_evaluator
```

COCO format-only submission or prediction export:

```python
test_evaluator = dict(
    type='CocoMetric',
    ann_file=data_root + 'annotations/image_info_test.json',
    metric=['bbox', 'segm'],
    format_only=True,
    outfile_prefix='work_dirs/my_exp/test')
```

VOC metrics:

```python
val_evaluator = dict(type='VOCMetric', metric='mAP', iou_thrs=0.5, eval_mode='11points')
```

Cityscapes instance segmentation metrics:

```python
val_evaluator = dict(
    type='CityScapesMetric',
    outfile_prefix='work_dirs/cityscapes/val',
    seg_prefix=data_root + 'gtFine/val')
```

Cityscapes official evaluation requires the `cityscapesscripts` package.

## Metric Selection

| Metric class | Typical dataset | Key options | Reads |
| --- | --- | --- | --- |
| `CocoMetric` | COCO-style detection/instance segmentation | `metric='bbox'`, `['bbox', 'segm']`, `classwise=True`, `format_only=True`, `outfile_prefix=...` | COCO JSON annotations or dataset-converted ground truth. |
| `VOCMetric` | Pascal VOC or VOC-like detection | `metric='mAP'` or `recall`, `iou_thrs`, `eval_mode='11points'` or `'area'` | Dataset-provided GT instances. |
| `CityScapesMetric` | Cityscapes instance segmentation | `outfile_prefix`, `seg_prefix`, `format_only` | Cityscapes mask directories and official scripts. |
| `CocoPanopticMetric` | COCO panoptic | panoptic annotation and segmentation prefixes | Panoptic JSON plus PNG segment maps. |
| `LVISMetric`, `OpenImagesMetric`, task-specific metrics | Matching specialized datasets | Dataset-specific options | Matching annotation schema. |

`CocoMetric` valid metric names are `bbox`, `segm`, `proposal`, and `proposal_fast`. `format_only=True` requires `outfile_prefix` and writes JSON-like result files without computing AP.

## Reading COCO Outputs

Common COCO result keys:

- `bbox_mAP`: mean AP averaged over IoU thresholds 0.50:0.95.
- `bbox_mAP_50` and `bbox_mAP_75`: AP at fixed IoU thresholds.
- `bbox_mAP_s`, `bbox_mAP_m`, `bbox_mAP_l`: AP by object scale.
- `segm_*`: same family for instance masks.
- `AR@100`, `AR@300`, `AR@1000`: average recall at proposal counts when proposal metrics are enabled.

Interpretation tips:

- `bbox_mAP_50` can look healthy while `bbox_mAP` is low when boxes are roughly localized but imprecise.
- Missing or wrong class order can depress all per-class AP even if boxes look visually correct.
- Mask AP requires valid segmentation annotations and `LoadAnnotations(with_mask=True)` for training.
- Use `classwise=True` to expose categories that fail due to naming, id mapping, imbalance, or annotation quality.

## Dataset Browsing

Use dataset browsing after changing annotation paths, metainfo, or transforms. MMDetection provides a native source-checkout analysis utility named `browse_dataset.py`; treat it as an optional native candidate when the user is already working inside an MMDetection checkout. Without that checkout, reproduce the same checks by building the dataset from the config and visualizing a few samples with the user's own plotting stack.

Useful native options to look for:

- `--skip-type TYPE ...`: bypass selected transforms when debugging raw annotations versus augmented samples.
- `--output-dir DIR --not-show`: save visualization in headless environments.
- `--show-interval SEC`: slow down GUI display if display is enabled.

Expected findings:

- Wrong `data_root` or `data_prefix` usually fails before drawing images.
- Class order/palette issues appear as wrong labels or colors.
- Transform problems appear as shifted boxes/masks after resize, crop, flip, or packing.

## Analysis Tools

Many analysis tools require a source checkout, full dataset, trained checkpoint, or produced result file. Treat them as optional native candidates when those assets exist, not as runtime dependencies of this skill and not as mandatory for a tiny validation pass.

| Native tool name | Purpose | Inputs |
| --- | --- | --- |
| `browse_dataset.py` | Visualize loaded dataset and transforms | Config; optional output dir. |
| `coco_error_analysis.py` | Per-category COCO bbox/segm error plots | COCO result JSON and annotation JSON. |
| `confusion_matrix.py` | Category confusion from predictions | Config, prediction outputs, score/TP thresholds. |
| `analyze_results.py` | Compare good/bad prediction examples | Config, prediction pickle/result file, optional top-k. |
| `eval_metric.py` | Evaluate saved results with config evaluator | Config and result file compatible with evaluator. |
| `test_robustness.py` | Benchmark corruptions and severities | Config, checkpoint, optional corruption/severity choices. |
| `robustness_eval.py` | Summarize robustness outputs | Results from robustness testing. |

## Robustness Benchmarking

The robustness workflow evaluates object detection/instance segmentation under image corruptions. It may require `imagecorruptions`, a real checkpoint, substantial compute, and MMDetection's native analysis utility named `test_robustness.py` when the user is already working inside a source checkout.

Treat robustness execution as an optional native verification candidate rather than a runtime dependency of this skill. When the native utility is available, inspect its `--help` output first, then pass a config, checkpoint, selected corruptions, selected severities, and an output pickle path. Use severity `0` for clean data and `1` to `5` for increasing corruption strength. Robustness results can vary slightly because corruptions may be stochastic.

## Tiny Metric Smoke Checks

Before a long run:

1. Confirm the validation annotation path exists and is the same file referenced by `val_evaluator.ann_file`.
2. Run dataset browsing on a tiny output directory or a reduced config where possible.
3. If a saved prediction/result file exists, evaluate it with the config evaluator rather than rerunning inference.
4. Use `format_only=True` only for submission/export; it does not prove metric quality.
5. For no-annotation test manifests, expect formatted JSON outputs, not AP/AR metrics.

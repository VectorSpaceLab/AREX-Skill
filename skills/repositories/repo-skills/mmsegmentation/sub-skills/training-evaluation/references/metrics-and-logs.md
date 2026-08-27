# Metrics and Logs

Use this reference to explain MMSegmentation evaluation outputs, saved predictions, JSON logs, and lightweight analysis tooling. Runnable examples use bundled skill scripts so the generated skill remains self-contained.

## Evaluator Placement

Validation and testing are MMEngine loop workflows:

- Training-time validation requires `val_dataloader`, `val_evaluator`, and `val_cfg`.
- Standalone testing requires `test_dataloader`, `test_evaluator`, and `test_cfg`.
- `Runner.from_cfg(cfg)` builds the loops from those config sections when `runner.val()` or `runner.test()` is called.

Typical segmentation evaluator config:

```python
val_evaluator = dict(type='IoUMetric', iou_metrics=['mIoU'])
test_evaluator = val_evaluator
```

## IoUMetric

Installed signature:

```text
IoUMetric(ignore_index=255, iou_metrics=['mIoU'], nan_to_num=None, beta=1, collect_device='cpu', output_dir=None, format_only=False, prefix=None, **kwargs)
```

Core behavior:

- `process(data_batch, data_samples)` reads `pred_sem_seg.data` and, unless `format_only=True`, compares it with `gt_sem_seg.data` while ignoring `ignore_index`.
- `compute_metrics(results)` returns dataset-level summary metrics and logs a per-class table.
- Supported `iou_metrics` are `mIoU`, `mDice`, and `mFscore`.
- Returned summary keys can include `aAcc`, `mIoU`, `mAcc`, `mDice`, `mFscore`, `mPrecision`, and `mRecall` depending on requested metrics.
- `nan_to_num` replaces NaN metric values after computation.
- `collect_device` must be suitable for distributed result collection, usually `cpu` unless the user needs GPU collection.
- `prefix` disambiguates metric names when multiple evaluators emit similar keys.

Saved output behavior:

- If `output_dir` is set, each predicted segmentation mask is saved as `<image-basename>.png`.
- If the data sample has `reduce_zero_label=True`, the saved mask is incremented by one to match official ADE-style index ranges.
- If `format_only=True`, no ground-truth metric is computed and the internal results list remains empty; use this for hidden-test or submission formatting.

Useful wrapper overrides:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --out work_dirs/format_results
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --cfg-options test_evaluator.iou_metrics="['mIoU','mDice','mFscore']"
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --format-only --out work_dirs/format_results
```

## DepthMetric

Installed signature:

```text
DepthMetric(depth_metrics=None, min_depth_eval=0.0, max_depth_eval=inf, crop_type=None, depth_scale_factor=1.0, collect_device='cpu', output_dir=None, format_only=False, prefix=None, **kwargs)
```

Core behavior:

- `depth_metrics=None` enables all built-in depth metrics: `d1`, `d2`, `d3`, `abs_rel`, `sq_rel`, `rmse`, `rmse_log`, `log10`, and `silog`.
- `process(data_batch, data_samples)` reads `pred_depth_map.data` and, unless `format_only=True`, compares it with `gt_depth_map.data` under the evaluation mask.
- The evaluation mask keeps depths between `min_depth_eval` and `max_depth_eval`; `crop_type='nyu_crop'` applies the NYU crop region.
- If `output_dir` is set, predictions are saved as 16-bit PNG files after multiplying by `depth_scale_factor`.
- If `format_only=True`, no metric is computed and only output files are saved.

Useful wrapper overrides:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --cfg-options test_evaluator.depth_metrics="['rmse','abs_rel']"
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --cfg-options test_evaluator.min_depth_eval=0.001 test_evaluator.max_depth_eval=80
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --format-only --out work_dirs/depth_results
```

## CityscapesMetric

Cityscapes-style evaluation wraps the external `cityscapesscripts` package. It is useful for official Cityscapes evaluation and submission formatting.

Important behavior:

- `output_dir` is required.
- If `format_only=True`, `keep_results=True` is required; otherwise construction raises an assertion.
- Predictions are converted from train IDs to label IDs before saving.
- If `format_only=False`, ground-truth filenames are converted from `labelTrainIds.png` to `labelIds.png` and evaluated with `cityscapesscripts`.
- If `keep_results=False`, temporary output files are removed when the metric object is destroyed.

Useful wrapper overrides:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --cfg-options test_evaluator.type=CityscapesMetric test_evaluator.output_dir=work_dirs/cityscapes_eval
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --format-only --keep-results --cfg-options test_evaluator.type=CityscapesMetric test_evaluator.output_dir=work_dirs/cityscapes_submit
```

If `cityscapesscripts` is not installed, choose `IoUMetric` for ordinary validation or install the optional dependency before Cityscapes official evaluation.

## Log Files

MMEngine logger hooks write JSON-line logs under the run's `work_dir` when configured. MMSegmentation's upstream analysis tool reads one JSON object per line and groups records by `step`. Validation records may not include a nonzero `step`, so parsers commonly reuse the previous step value.

Use the bundled analyzer for safe summaries that do not import MMSegmentation:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/analyze_mmseg_log.py work_dirs/run/vis_data/scalars.json
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/analyze_mmseg_log.py log.json --keys loss mIoU mAcc aAcc
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/analyze_mmseg_log.py log.json --plot-out metrics.png --keys loss mIoU
```

The bundled analyzer:

- accepts MMEngine/MMSegmentation JSON-line logs;
- summarizes count, first step, last step, min, max, mean, and last value per key;
- can write a compact JSON summary with `--summary-out`;
- can plot selected keys with `--plot-out` when `matplotlib` is installed;
- remains fixture-friendly for tiny logs and does not require `seaborn`.

If the upstream analysis behavior fails because `seaborn` is missing, use the bundled analyzer or install the plotting dependency in an appropriate environment.

## Confusion Matrix and Benchmark Workflows

Confusion matrix generation requires saved prediction PNGs plus a matching test dataset config. The bundled wrapper can safely construct the prediction-saving command:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --out result/predictions
```

After predictions are created, a future agent can adapt the documented confusion-matrix algorithm: build the configured test dataset, read sorted prediction images, ignore `dataset.ignore_index`, handle `reduce_zero_label`, normalize the matrix per ground-truth class, and save `confusion_matrix.png`. Do not make this generated skill depend on the source repository analysis script at runtime.

Benchmarking runs many test batches after warmup and can be expensive. Treat throughput measurement as an explicit user request, not as a smoke test. If needed, mirror the benchmark algorithm with a bounded config/checkpoint and record the repeat count, warmup, device, and batch limit in the report.

## Metric Unit-Test Candidates

Safe native candidates for verification planning include:

- IoUMetric saved-output and `format_only` behavior from the repo's metric unit tests.
- DepthMetric saved-output and `format_only` behavior from the repo's metric unit tests.
- CityscapesMetric `format_only` plus `keep_results` assertion from the repo's metric unit tests.

These tests are source-evidence candidates; do not make the public skill depend on the test paths at runtime.

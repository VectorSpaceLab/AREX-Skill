# Evaluation, output prefixes, visualization hook, and TTA

MMDetection3D testing loads a config, merges `--cfg-options`, sets `cfg.load_from` to the checkpoint, optionally modifies the visualization hook or TTA model, builds a runner, and calls `runner.test()`. Evaluation behavior is therefore controlled mostly by the config's `test_evaluator` block.

## Test command flags

| Flag | Meaning | Guardrail |
| --- | --- | --- |
| `CONFIG CHECKPOINT` | Required positional config and checkpoint. | Checkpoint must match model/config classes and task. |
| `--work-dir DIR` | Directory for the file containing evaluation metrics and runtime logs. | Overrides config `work_dir`; otherwise default mirrors config basename. |
| `--cfg-options KEY=VALUE ...` | Merge nested config overrides before runner construction. | Quote values containing lists/tuples; no spaces around `=`. Prefer nested evaluator keys. |
| `--show` | Enable visualization hook `show=True`. | Documented for single-GPU debugging and should normally be paired with `--show-dir`. |
| `--show-dir DIR` | Save painted outputs under the test work directory's timestamped show directory. | Does not require a GUI, but still activates the visualization hook. |
| `--task TASK` | Visualization mode: `mono_det`, `multi-view_det`, `lidar_det`, `lidar_seg`, or `multi-modality_det`. | Required whenever `--show` or `--show-dir` is used. |
| `--score-thr FLOAT` | Visualization score threshold, default `0.1`. | Affects displayed predictions, not metric computation. |
| `--wait-time FLOAT` | Display interval when showing interactively, default `2`. | Mainly relevant with `--show`. |
| `--tta` | Enable test-time augmentation. | Only supported for 3D segmentation configs with `tta_model` and `tta_pipeline`. |
| `--ceph` | Replace local file backend with Ceph backend. | Only for deployments configured for Ceph storage. |
| `--launcher none|pytorch|slurm|mpi` | Distributed launcher mode. | Usually set by the shell launchers, not by hand. |

## Evaluator output keys

Pass these as `--cfg-options` entries. Exact availability depends on the active `test_evaluator` type, so inspect the selected config when possible.

| Dataset/task family | Common evaluator type | Output/format keys | Notes |
| --- | --- | --- | --- |
| KITTI lidar/mono/multimodal detection | `KittiMetric` | `test_evaluator.pklfile_prefix=...`, `test_evaluator.submission_prefix=...`, `test_evaluator.format_only=True` | `pklfile_prefix` saves pickle results; `submission_prefix` writes KITTI text submission files. If `format_only=True`, `submission_prefix` is required. |
| nuScenes detection, including vision-only variants | `NuScenesMetric` | `test_evaluator.jsonfile_prefix=...`, `test_evaluator.format_only=True` | Generates a directory containing nuScenes JSON such as `results_nusc.json`. If `format_only=True`, `jsonfile_prefix` is required. |
| Lyft detection | `LyftMetric` | `test_evaluator.jsonfile_prefix=...`, `test_evaluator.csv_savepath=...`, `test_evaluator.format_only=True` | CSV output requires `csv_savepath`; `format_only=True` also requires `csv_savepath`. |
| Waymo detection | `WaymoMetric` | `test_evaluator.result_prefix=...`, `test_evaluator.format_only=True`, plus existing `test_evaluator.waymo_bin_file=...` | v1.4.0 metric code uses `result_prefix` for generated Waymo-format results. Older examples may mention KITTI-style prefixes; prefer the metric field in the active config. |
| Indoor 3D detection | `IndoorMetric` | usually metric-only through config | Produces mAP-style metric dictionaries; benchmark formatting is dataset-specific. |
| LiDAR semantic segmentation | `SegMetric` | `test_evaluator.pklfile_prefix=...`, `test_evaluator.submission_prefix=...` | `submission_prefix` writes per-sample text submissions for supported segmentation benchmarks. |
| Instance/panoptic segmentation | `InstanceSegMetric`, `PanopticSegMetric` | metric-specific; panoptic also inherits segmentation output-prefix behavior where configured | Confirm config fields before passing format options. |

### Nested key rule

Because test-time overrides are merged into the config dictionary, evaluator fields usually need the `test_evaluator.` prefix:

```bash
--cfg-options test_evaluator.jsonfile_prefix=work_dirs/model/results_eval
```

A bare option such as `submission_prefix=...` creates or updates a top-level config key and usually does not change the evaluator. Use a bare key only when the current config explicitly consumes it.

## Visualization hook behavior

When `--show` or `--show-dir` is present, testing modifies `default_hooks.visualization`:

- `draw=True` is enabled.
- `show=True` and `wait_time` are set when `--show` is present.
- `test_out_dir` is set from `--show-dir` when provided.
- `vis_task` is set from `--task`; missing or invalid `--task` causes an assertion.
- `score_thr` is set from `--score-thr`.

The default runtime config includes a 3D visualization hook. Custom configs that remove it will fail with an error asking for `visualization=dict(type='VisualizationHook')`/`Det3DVisualizationHook` in default hooks. For saved outputs, prefer `--show-dir` with the task mode that matches the model:

- `lidar_det` for LiDAR 3D boxes.
- `lidar_seg` for point semantic segmentation.
- `mono_det` for monocular 3D detection.
- `multi-view_det` for camera-only multi-view detection.
- `multi-modality_det` for LiDAR+camera models.

## TTA behavior

`--tta` changes the test dataloader pipeline and wraps the model only if both config keys exist:

- `tta_pipeline`
- `tta_model`

In this release, the implementation comments restrict TTA to 3D segmentation. Segmentation base configs such as indoor/SemanticKITTI-style configs define `Seg3DTTAModel`; ordinary 3D detection configs do not. If a user asks for detection TTA, route to config customization rather than adding `--tta` blindly.

## Metric tests as behavior evidence

The repo's metric tests show the evaluator contract rather than full benchmark runs:

- KITTI metric tests require CUDA for rotate-IoU/3D AP paths and produce keys such as `pred_instances_3d/KITTI/Overall_3D_AP11_easy`.
- Indoor, semantic segmentation, instance segmentation, and panoptic tests use small synthetic predictions and verify that metric dictionaries are produced.
- These tests support command/evaluator guidance, but they do not replace full dataset validation.

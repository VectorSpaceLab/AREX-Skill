# Benchmark Dispatch, Metrics, and Search

## Dispatch map

The maintained evaluator chooses one branch in order. Use the exact dataset name
when possible; substring matches are intentionally documented because they affect
routing.

| Dataset selection | Dataset object | Benchmark object(s) | Printed outputs |
|---|---|---|---|
| name contains `OTB` | `OTBDataset` | `OPEBenchmark` | success and precision; OPE success AUC-like mean and precision at 20 pixels |
| name contains `DTB70` | `DTB70Dataset` | `OPEBenchmark` | success and precision |
| name contains `UAVDT` | `UAVDTDataset` | `OPEBenchmark` | success and precision |
| name contains `VisDrone` | `VisDroneDataset` | `OPEBenchmark` | success and precision |
| exactly `GOT-10k` | `got10k.experiments.ExperimentGOT10k` | wrapper report | AO, SR, speed |
| exactly `LaSOT` | `LaSOTDataset` | `OPEBenchmark` | success, precision, normalized precision |
| name contains `UAV` after UAVDT check | `UAVDataset` | `OPEBenchmark` | success and precision |
| name contains `NFS` | `NFSDataset` | `OPEBenchmark` | success and precision |
| in VOT2016–2019 | `VOTDataset` | `AccuracyRobustnessBenchmark` + `EAOBenchmark` | accuracy, robustness, lost number, EAO |
| exactly `VOT2018-LT` | `VOTLTDataset` | `F1Benchmark` | best-threshold precision, recall, F1 |

The implementation imports `OTBDataset`, `UAVDataset`, `LaSOTDataset`,
`VOTDataset`, `NFSDataset`, `VOTLTDataset`, and `DTB70Dataset` in the evaluator
module. It calls `UAVDTDataset` and `VisDroneDataset` without importing them in
the inspected snapshot. That is a real code-level blocker for those branches;
do not infer that a factory constructor proves `bin/eval.py` can run them.

The evaluator's VOT conditional includes VOT2017, while the test-side factory
recognizes only VOT2016, VOT2018, and VOT2019. VOT2017 therefore needs a
separate metadata/runtime path. TrackingNet is factory-recognized but has no
`bin/eval.py` branch. These are dispatch facts, not recommendations to patch
source blindly.

## OPE: success and precision

`OPEBenchmark.eval_success` computes an overlap success vector at IoU thresholds
`0.00, 0.05, ..., 1.00`. A ground-truth rectangle is considered valid when its
width and height are positive. The vector is divided by the full sequence frame
count. `show_result` reports the mean of this vector across sequences as
**Success**. In this implementation that mean is the discrete AUC-like score;
it is not a separately integrated continuous curve.

`eval_precision` computes Euclidean center error and evaluates thresholds
`0, 1, ..., 50` pixels. The printed **Precision** is the mean curve value at
index 20, i.e. the fraction at the 20-pixel threshold. It is not the average
center error.

`eval_norm_precision` normalizes center coordinates by ground-truth width and
height, evaluates thresholds `0.00, 0.01, ..., 0.50`, and prints index 20 only
when the LaSOT call supplies that curve: **Norm Precision** at normalized
threshold 0.20. OTB/DTB/UAV/NFS tables print zero in this column because the
standalone evaluator passes no normalized curve to `show_result`; do not read
that zero as a measured normalized score.

For LaSOT, the wrapper carries `absent` flags and the OPE benchmark filters
both ground truth and predictions to present-target frames. A missing or
misaligned prediction file can therefore change the array shape before metric
calculation; validate row counts first.

## VOT restart: accuracy, robustness, EAO

The result loader treats each VOT repetition as a trajectory containing boxes and
markers. The statistics helper counts marker `2` as a failure and computes
polygon/rectangle overlap through `vot_overlap`. Marker `0` denotes an unknown
or skipped frame; marker `1` denotes initialization.

`AccuracyRobustnessBenchmark` uses a ten-frame burn-in after initialization when
calculating per-frame accuracy. The displayed values are:

- **Accuracy**: mean of valid overlap values across sequence/repetition
  trajectories, with NaNs ignored.
- **Lost Number**: mean number of failure markers per video/repetition grouping.
- **Robustness**: the implementation's percentage-like failure rate, computed as
  mean failures divided by the evaluated length and multiplied by 100. It is
  therefore lower-is-better even though the label is “Robustness”.

`EAOBenchmark` fragments trajectories at failures after a five-frame skipping
offset, weights fragments by sequence/tag, and computes expected overlap. The
VOT version selects a benchmark-specific valid curve interval:

| Dataset | low | high | peak metadata |
|---|---:|---:|---:|
| VOT2016 | 108 | 371 | 168 |
| VOT2017/VOT2018 | 100 | 356 | 160 |
| VOT2019 | 46 | 291 | 128 |

The implementation averages expected overlap over the selected interval and
prints **EAO**. It does not use the `peak` field in the final calculation.
Higher accuracy and EAO are desirable; lower lost number and lower failure-rate
robustness are desirable. Never compare EAO across VOT versions without stating
the version-specific interval and result protocol.

## VOT long-term: F1

The long-term loader reads a trajectory, confidence values, and timing file.
It inserts a NaN confidence at frame zero after skipping the first confidence
line. `F1Benchmark` derives 100 score thresholds from finite confidence values,
computes precision and recall from overlap and target-visible frame count, and
reports the maximum F1 operating point per tracker. The printed columns are the
precision, recall, and F1 at the threshold with maximum mean F1.

Confidence is not optional for this branch. A trajectory-only result can appear
present but cannot produce a valid F1 curve. The stock test writer currently does
not append `outputs['best_score']` in its OPE loop, so its long-term confidence
file can be too short; fix the producer in a copied active runtime or stop at
layout validation.

## GOT-10k: AO, SR, speed

The embedded `ExperimentGOT10k` wrapper supports `val` and `test` subsets. For
validation it reads one or more `<sequence>_NNN.txt` records and optional
`<sequence>_time.txt`, discards the first frame when calculating IoU, filters by
visible `cover`, and reports:

- **AO**: mean IoU over valid evaluated frames;
- **SR**: fraction of evaluated IoUs strictly greater than 0.5;
- **speed_fps**: mean of `1 / time` over positive timing entries, or `-1` if
  no valid timing rows exist.

For the hidden-label test subset, `report()` packages results for submission and
cannot locally calculate AO/SR. Do not claim a test score from local files.

The test-side `bin/eval.py` constructs `ExperimentGOT10k` with its default
result parent, even after discovering trackers under `--tracker_path`. Confirm
where result files are actually located before using this branch.

## GOT-10k experiment wrappers

The bundled `got10k.experiments` package also contains OTB, VOT, LaSOT, NFS,
UAV123, DTB70, and TColor128 wrappers. These wrappers are reusable API evidence,
not proof that `bin/eval.py` dispatches them. Their common lifecycle is:

1. construct an experiment with dataset root, result directory, and report
   directory;
2. `run(tracker, visualize=False)` to produce records and timing files;
3. `report([tracker_name])` to compute/save performance;
4. optionally `show(...)` for GUI visualization.

The `ExperimentOTB` family reports success/precision curves and their summary
scores; `ExperimentVOT` supports supervised/unsupervised/realtime record
layouts, but its own docstring says evaluation is still under development in
this snapshot. Keep that API separate from the maintained `bin/eval.py` path.

## Hyperparameter search

`bin/hp_search.py` exposes:

| Flag | Default |
|---|---|
| `--snapshot` | `models/pretrained/nanotrackv2.pth` |
| `--dataset` | `VOT2018` |
| `--penalty-k` | `0.145, 0.148, 0.150, 0.152, 0.155` |
| `--lr` | `0.385, 0.390, 0.395, 0.400, 0.405, 0.410, 0.415, 0.420` |
| `--window-influence` | `0.462, 0.465, 0.468, 0.470, 0.472, 0.475` |
| `--search-region` | `255` |
| `--config` | `models/config/configv2.yaml` |

Values are comma-separated parser inputs. The default grid has
`5 * 8 * 6 * 1 = 240` combinations before videos, and the script shuffles
sequence and parameter order. Each trial mutates global `cfg.TRACK` fields and
names its result with `r<instance>_pk-..._wi-..._lr-...`.

Safe procedure:

1. resolve the extension and run one fixed tracker/evaluator case;
2. choose a validation split and a bounded video subset;
3. compute trial count and set a unique output root;
4. keep checkpoint, config family, dataset, and device fixed;
5. do not reuse stale `Occ` placeholders as completed results;
6. validate each completed trial before scoring;
7. select on validation metrics, then run one locked final configuration.

The inspected search script has a material defect: `run_tracker()` accepts
`img`/`gt` arguments but loops over an undefined `video` variable. It therefore
cannot be treated as a verified working search entry point without a copied
runtime fix. It also hard-codes `CUDA_VISIBLE_DEVICES="0"`, and its GOT-10k
branch depends on variables that are not populated by the broken call path.
Keep search planning and layout checks usable even when the historical script is
not launch-ready.

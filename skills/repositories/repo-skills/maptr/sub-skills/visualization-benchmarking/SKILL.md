---
name: visualization-benchmarking
description: "This skill guides an agent through MapTR prediction visualization,
  qualitative video assembly, inference timing, and log interpretation without
  overstating unavailable evidence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Visualization and benchmarking

Use this skill when a MapTR config and checkpoint should produce inspectable
prediction artifacts, when existing artifacts should be assembled into a
video, or when timing/log outputs need a cautious interpretation. Read the
linked references before running a command:

- [visualization procedure and artifact contract](references/visualization.md)
- [benchmark and log-analysis contract](references/benchmarking.md)
- [symptoms, recovery, and stop conditions](references/troubleshooting.md)

This skill routes data conversion, dataset layout, and annotation generation
to data-preparation. It routes model/config changes to model-configuration and
training or distributed evaluation launches to training-evaluation. It does not
train a model, download data or checkpoints, build the legacy CUDA extension,
or claim native execution when those prerequisites are absent.

## Fast routing

1. **Need rendered predictions?** First verify a compatible config, checkpoint,
   prepared test annotations, six camera image paths per sample, and the
   documented legacy runtime. Then use `tools/maptr/vis_pred.py`.
2. **Need a video from rendered samples?** Inspect the sample directories and
   required filenames. Prefer the safe local helper linked below; it sorts
   sample directories, validates images, rejects unsafe output names, and does
   not access the network.
3. **Need FPS?** Record GPU, batch size, number of camera views, precision,
   config, checkpoint, sample count, warm-up policy, software/extension state,
   and whether data loading is included. Compare only matched conditions.
4. **Need curves or iteration timing?** Use `analyze_logs.py` only with
   line-delimited JSON logs and state whether the first iteration of each epoch
   was excluded.

## Prediction visualization

Run commands from the project root and use an explicit threshold when a result
must be reproducible. The documented example is:

```bash
PYTHONPATH=. python tools/maptr/vis_pred.py \
  projects/configs/maptr/maptr_tiny_r50_24e.py path/to/checkpoint.pth \
  --score-thresh 0.3 --show-cam \
  --show-dir work_dirs/maptr_tiny/vis_pred \
  --gt-format fixed_num_pts
```

The positional arguments are `config` and `checkpoint`. Useful options are
`--score-thresh FLOAT`, `--show-cam`, `--show-dir DIR`, and one or more values
for `--gt-format`. In the checked source, the documentation says the default
threshold is 0.3 while the parser currently defaults to 0.4; pass the value
explicitly. The `--show-cam` flag is accepted, but the current implementation
copies camera images and builds `surroud_view.jpg` regardless of that flag.

With no `--show-dir`, the native default is
`work_dirs/<config-stem>/vis_pred`. Each sample is a child directory named from
the lidar filename. Typical outputs include `CAM_*.jpg`, the misspelled
`surroud_view.jpg`, `PRED_MAP_plot.png`, and a GT map image. The native script
also dumps a copy of the config into the visualization directory.

Choose GT representation deliberately:

- `fixed_num_pts`: resampled points used by the standard saved artifact
  `GT_fixednum_pts_MAP.png`; this is the safest choice for the native video
  layout.
- `polyline_pts`: original Shapely coordinates, saved as
  `GT_polyline_pts_MAP.png`; useful for inspecting annotation detail.
- `se_pts`: start/end point arrows. The parser accepts it, but this source
  revision does not save a separate `se_pts` image.
- `bbox`: an enclosing rectangle. The parser accepts it, but this source
  revision does not save a separate `bbox` image.

A visualization run is not evidence of model quality by itself. Preserve the
config, checkpoint identity, threshold, GT format, dataset split, and skipped
sample count beside any review. If the dataset, checkpoint, or required
extension is unavailable, stop after prerequisite reporting rather than
inventing images or metrics.

## Safe video assembly

The native command is:

```bash
python tools/maptr/generate_video.py path/to/vis_pred \
  --fps 10 --video-name demo --sample-name SAMPLE_VIS.jpg
```

It writes `<parent-of-vis_pred>/demo.mp4`, assumes six camera files plus
`PRED_MAP_plot.png` and `GT_fixednum_pts_MAP.png` in every sample directory,
and uses the `mp4v` codec at 1680x450. Its directory iteration is not sorted
and it can fail obscurely on missing or undecodable images. Use the bundled,
source-adapted helper for a safe fixture or an existing artifact set:

```bash
python <skill-root>/sub-skills/visualization-benchmarking/scripts/make_video.py \
  path/to/vis_pred --fps 10 --video-name demo --sample-name SAMPLE_VIS.jpg
python <skill-root>/sub-skills/visualization-benchmarking/scripts/make_video.py \
  --self-check
```

The helper ignores non-directory entries, sorts frame directory names, reports
and skips incomplete samples, generates the requested sample image (so a
pre-existing `SAMPLE_VIS.jpg` is not required), writes a fixed-size MP4, and
fails if no complete sample can be decoded. It refuses path traversal in
`--video-name` or `--sample-name`; add `--overwrite` to replace an existing
video. A successful fixture check must report two ordered frames and a video
path. Codec availability is still platform-dependent; a successful write does
not prove that every media player can decode the file.

## Timing and logs

The native benchmark contract and interpretation rules are in
[benchmarking.md](references/benchmarking.md). In short, `tools/maptr/benchmark.py`
requires a config, optionally loads a checkpoint, uses one GPU and batch size
one, synchronizes CUDA around model inference, warms up five iterations, and
prints periodic and overall `img / s`. It is not a video frame rate and does
not establish end-to-end latency. The sibling analysis benchmark has the same
core timing assumptions but no plugin import step.

Do not compare an FPS value across different GPU models, batch sizes, view
counts, precision modes, configs, checkpoints, warm-up/sample policies, or
extension builds. The README's published reference is specifically batch one
with six views on an RTX3090; it is context, not a result for another setup.
When logs or hardware metadata are missing, label the comparison **blocked**.

## Difficult synthetic cases

- **Mixed visualization names:** create `frame-b/` and `frame-a/` with the
  required images, add a non-directory and an incomplete child, and omit
  `SAMPLE_VIS.jpg`. Assert that the helper reports the incomplete child,
  writes the requested sample image, and reports `ORDER frame-a,frame-b`.
  Recovery is to repair or intentionally exclude the skipped child; never
  infer order from native `os.listdir` output.
- **Incompatible benchmark request:** if two proposed FPS values have
  different GPU or batch size and the logs/manifests are missing, assert
  `status: blocked` and produce no numeric comparison. Recovery is to provide
  matched manifests/logs or rerun both cases under one fixed protocol.

For JSON training logs:

```bash
python tools/analysis_tools/analyze_logs.py plot_curve run_a.json run_b.json \
  --keys mAP_0.25 --legend run-a run-b --out curves.png
python tools/analysis_tools/analyze_logs.py cal_train_time run.json
```

`plot_curve` supports `--mode train|eval`, `--interval`, `--backend`,
`--style`, and `--out`. `cal_train_time` excludes each epoch's first timing
value unless `--include-outliers` is supplied. Check that every log is
line-delimited JSON, ends in `.json`, contains epoch fields, and has the
requested metric before interpreting a plot. Missing logs, incompatible
metrics, or an unavailable display backend are stop conditions, not reasons to
fill in a fabricated curve.

## Completion gate

A safe handoff states the exact commands, artifact directory, threshold and GT
format, frame count/order, video codec/size/fps, benchmark conditions, log
files/metrics, and every skipped or unverified item. It must explicitly say
when model visualization or benchmark execution was deferred because data,
checkpoint, CUDA compatibility, or logs were not available.

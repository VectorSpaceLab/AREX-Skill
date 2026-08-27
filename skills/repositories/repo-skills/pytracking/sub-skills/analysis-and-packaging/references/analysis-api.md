# Analysis API and Result Shapes

This reference covers analysis of saved PyTracking results. It assumes tracker execution already produced result files. If results still need to be generated, route to `tracking-evaluation`.

## Core objects

PyTracking analysis functions usually consume two lists:

- `trackers`: created with `trackerlist(name, parameter_name, run_ids=None, display_name=None)` or individual `Tracker(name, parameter_name, run_id=None, display_name=None)` objects.
- `dataset`: created with `get_dataset(*aliases)`.

Useful dataset aliases verified for this repo include `otb`, `nfs`, `uav`, `tpl`, `tpl_nootb`, `vot`, `trackingnet`, `trackingnetvos`, `got10k_test`, `got10k_val`, `got10k_ltrval`, `got10kvos_val`, `lasot`, `lasot_train`, `lasot_extension_subset`, `lasotvos`, `oxuva_dev`, `oxuva_test`, `avist`, `dv2016_val`, `dv2017_val`, `dv2017_test_dev`, `dv2017_test_chal`, `yt2018_jjval`, `yt2018_valid_all`, `yt2019_test`, `yt2019_valid`, `yt2019_valid_all`, `yt2019_jjval`, `yt2019_jjval_all`, `lagot_sot_mode`, and `lagot`.

The tracker object supplies these analysis paths:

- `results_dir`: bounding-box result directory for one tracker/parameter/run.
- `segmentation_dir`: VOS mask result directory for one tracker/parameter/run.
- `name`, `parameter_name`, `run_id`, `display_name`: used in cache validation, merging, labels, and report keys.

## Bounding-box result file shape

Saved box results are text files with one row per frame:

```text
x, y, width, height
```

`x` and `y` are top-left coordinates. Width and height must be non-negative. The analysis loader accepts comma or tab delimiters. The first prediction is overwritten with the first ground-truth box before metric computation, matching the PyTracking analysis implementation.

Expected result paths are relative to each `Tracker.results_dir`:

```text
<sequence-name>.txt
<sequence-name>_object_presence_scores.txt   # optional for precision/recall/F1 analysis
<sequence-name>_time.txt                     # used by benchmark packaging, not by basic plots
```

When `run_id` is present, PyTracking conventionally places results under a run-suffixed parameter directory such as `parameter_000`, `parameter_001`, etc. Official package planning relies on that convention.

## Metric helpers

- `calc_err_center(pred_bb, anno_bb, normalized=False)`: center-distance error. With `normalized=True`, centers are normalized by annotation width/height.
- `calc_iou_overlap(pred_bb, anno_bb)`: IoU overlap for `[x, y, w, h]` boxes.
- `calc_seq_err_robust(pred_bb, anno_bb, dataset, target_visible=None)`: applies PyTracking's sequence-level validity rules, handles zero-size predictions by carrying forward previous boxes, handles selected length mismatches, and returns overlap error, center error, normalized center error, and a valid-frame mask.

Important validity behavior:

- NaNs in predictions or negative predicted sizes are fatal.
- NaNs in annotations are fatal except for UAV handling.
- Predictions shorter than annotations are padded with zeros for most datasets; longer predictions are truncated for most datasets.
- Invalid frames are excluded or marked depending on dataset and target visibility.

## Extracting cached evaluation data

`extract_results(trackers, dataset, report_name, skip_missing_seq=False, plot_bin_gap=0.05, exclude_invalid_frames=False, verbose=True)` computes standard single-object tracking curves and writes:

```text
<result_plot_path>/<report_name>/eval_data.pkl
```

The pickle contains:

- `sequences`: sequence names.
- `trackers`: dictionaries with tracker name, parameter, run id, and display name.
- `valid_sequence`: per-sequence validity flags.
- `ave_success_rate_plot_overlap`: success curves by sequence, tracker, threshold.
- `ave_success_rate_plot_center`: pixel precision curves.
- `ave_success_rate_plot_center_norm`: normalized precision curves.
- `avg_overlap_all`: per-sequence average overlap.
- `threshold_set_overlap`, `threshold_set_center`, `threshold_set_center_norm`.

`extract_results_prec_rec_f1(...)` additionally reads optional object-presence score files. If a score file is missing but the box result exists, it uses all-one scores. Its cache stores `raw_data` with precision/recall arrays, maximum F1, best threshold, and selected index per tracker key.

## Plotting and reports

Use these high-level functions for saved box results:

```python
from pytracking.evaluation import trackerlist, get_dataset
from pytracking.analysis.plot_results import (
    print_results,
    plot_results,
    print_per_sequence_results,
    print_results_per_attribute,
    plot_attributes_radar,
    plot_got_success,
)

trackers = trackerlist('dimp', 'dimp50', run_ids=[0, 1, 2, 3, 4], display_name='DiMP-50')
dataset = get_dataset('otb')

print_results(trackers, dataset, 'otb_dimp50', merge_results=True,
              plot_types=('success', 'prec', 'norm_prec'))
plot_results(trackers, dataset, 'otb_dimp50', merge_results=True,
             plot_types=('success', 'prec', 'norm_prec'), force_evaluation=False)
```

`plot_results(...)` saves PDFs such as `success_plot.pdf`, `precision_plot.pdf`, and `norm_precision_plot.pdf` under the configured plot-report directory. It also calls `plt.show()`, so in non-interactive sessions set a backend such as `Agg` before importing `matplotlib.pyplot` or plotting modules.

`print_results(...)` prints tables with AUC, OP50, OP75, precision, normalized precision, or F1 depending on `plot_types`.

`print_per_sequence_results(...)` can filter sequences with:

- `{'mode': 'ao_min', 'threshold': value}`
- `{'mode': 'ao_max', 'threshold': value}`
- `{'mode': 'delta_ao', 'threshold': value}`

`plot_got_success(trackers, report_name)` is for plotting downloaded official GOT-10k JSON reports. The tracker names in the experiment must match JSON report filenames located in the configured GOT report directory.

## Playback of saved boxes

`playback_results(trackers, sequence)` displays saved bounding boxes on the sequence frames. It requires GUI-capable OpenCV/Matplotlib and readable frame paths from the dataset object.

Controls:

- Space: pause/resume.
- Left/right arrows: step or change automatic playback speed.
- Escape or `q`: exit.

Do not use playback in headless automation unless a display backend is available.

## VOS evaluation

`evaluate_vos(trackers, dataset='yt2019_jjval', force=False)` evaluates indexed segmentation masks and prints J-Mean/J-Recall/J-Decay. It writes or reuses per-tracker CSVs in each tracker's `segmentation_dir`:

```text
<dataset>_global_results.csv
<dataset>_per-sequence_results.csv
```

Expected VOS result layout:

```text
<tracker.segmentation_dir>/
  <sequence-name>/
    <frame-name>.png
```

The frame names must match the dataset annotation mask names. Mask values encode object ids; background is object id 0 and is excluded from object scoring. The implementation evaluates the Jaccard region measure by default and has support utilities for DAVIS-style boundary F-measure, recall, decay, mean, and text bargraphs.

## Notebook-to-script translation

The repo includes analysis notebooks for regular benchmark results and AVisT-style analysis. When translating notebook workflows into scripts:

1. Move imports and tracker/dataset construction to the top.
2. Make `report_name`, tracker list, dataset alias, run ids, and plot types CLI arguments.
3. Set a headless-safe Matplotlib backend for batch runs.
4. Reuse `print_results(...)` or `plot_results(...)` rather than reimplementing metric loops.
5. Keep any download/unpack step separate and explicitly approved by the user.

## Raw model-zoo result context

The model-zoo raw bounding-box results use `[top_left_x, top_left_y, width, height]` rows. Reported benchmark numbers are averages over multiple stochastic runs for several datasets: five runs for OTB-100/NFS/UAV123/LaSOT/LaSOT extension, 15 runs for VOT2018, one run for TrackingNet server uploads, and three runs for GOT-10k protocol submissions. Use this context when deciding whether `merge_results=True` is valid.

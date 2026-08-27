# Datasets, Entry-Point Contracts, and Results

This reference preserves the maintained NanoTrack evaluation contracts without
requiring any external checkout. Paths below are contract-shaped examples, not
bundled assets. A compatible active runtime must provide the tracker package,
entry points, datasets, configs, checkpoints, and native build sources.

## Test-side entry-point contract

The maintained test entry point accepts these flags:

| Flag | Alias | Type/default | Contract |
|---|---|---|---|
| `--dataset` | none | string, `GOT-10k` | Exact dataset name; data root is fixed to `./datasets/<dataset>` relative to launch working directory. |
| `--tracker_name` | `-t` | string, `nanotrack` | Directory name written under the dataset result root and later selected by evaluator globbing. |
| `--config` | none | path, `./models/config/configv3.yaml` | Merged into the global NanoTrack config before model construction. |
| `--snapshot` | none | path, `models/pretrained/nanotrackv3.pth` | Loaded into `ModelBuilder`; stock control flow then moves the model to CUDA and evaluation mode. |
| `--save_path` | none | path, `./results` | Parent under which tracking outputs are written. |
| `--video` | none | string, empty | If non-empty, only the exactly named sequence is tracked. This does not make the evaluator partial-dataset aware. |
| `--vis` | none | boolean flag, false | Opens OpenCV windows while tracking; avoid on headless hosts. |
| `--gpu_id` | none | string, `not_set` | When set, assigned to `CUDA_VISIBLE_DEVICES` before model use. It does not check occupancy. |
| `--tracker_path` | `-p` | path, `./results` | Parent from which the evaluator reads results after testing. |
| `--num` | `-n` | integer, `4` | Requested evaluator worker-process count; capped to discovered tracker count. |
| `--show_video_level` | `-s` | boolean flag, false | Adds per-sequence tables where supported. |

The entry point calls evaluation after writing results. Two consequences matter:

1. `--save_path` and `--tracker_path` are independent. Their defaults coincide,
   but changing only one causes the evaluator to miss the new results or read
   stale results elsewhere.
2. A non-empty `--video` produces only one sequence, while the evaluation
   wrappers iterate the complete dataset metadata. Use it for tracking/debugging
   plus structural validation, not for an unqualified dataset score.

The script sets PyTorch CPU threads to one, but its tracker path still uses
unconditional CUDA. Route model/checkpoint/config/device work to **inference**.

## Evaluation-only entry-point contract

The standalone evaluator accepts:

| Flag | Alias | Type/default | Contract |
|---|---|---|---|
| `--tracker_path` | `-p` | path, `./results` | Parent containing `<dataset>/<tracker...>`. |
| `--dataset` | `-d` | string, `DTB70` | Selects dispatch by ordered string/exact-name checks. |
| `--num` | `-n` | integer, `4` | Pool size after `min(requested, discovered_trackers)`. Must remain positive. |
| `--tracker_name` | `-t` | string, `nanotrack` | Prefix used as `<tracker_name>*` under `<tracker_path>/<dataset>/`. |
| `--show_video_level` | `-s` | boolean flag, false | Requests per-video output from benchmark printers. |

Tracker discovery is equivalent to:

```text
<tracker_path>/<dataset>/<tracker_name>*
```

At least one matching tracker directory is required. Prefer a literal prefix
rather than relying on shell wildcard expansion; quote values if they contain
shell metacharacters. The evaluator takes the final path component as each
tracker name.

For every non-GOT dispatch branch, dataset metadata/images are resolved from
`./datasets/<dataset>` relative to the launch directory. The GOT-10k branch
also fixes its dataset root to `./datasets/GOT-10k`.

### GOT-10k path caveat

The GOT-10k evaluation branch constructs `ExperimentGOT10k` without forwarding
`--tracker_path`, so its embedded result directory remains the wrapper default
`results/GOT-10k`. A custom `--tracker_path` can satisfy initial tracker
discovery yet still be ignored by the report step. In a compatible active
runtime, either keep the default parent or patch the experiment construction to
pass the chosen result parent explicitly. Record which behavior was used.

## `DatasetFactory` contract

The test-side construction call is:

```python
DatasetFactory.create_dataset(
    name=dataset_name,
    dataset_root=dataset_root,
    load_img=False,
)
```

Required keyword arguments are `name`, `dataset_root`, and normally
`load_img=False`. Factory dispatch is ordered:

| Name test | Wrapper |
|---|---|
| contains `OTB` | `OTBDataset` |
| exactly `LaSOT` | `LaSOTDataset` |
| contains `UAV123` or `UAV20L` | `UAVDataset` |
| contains `NFS` | `NFSDataset` |
| exactly `VOT2016`, `VOT2018`, or `VOT2019` | `VOTDataset` |
| exactly `VOT2018-LT` | `VOTLTDataset` |
| exactly `TrackingNet` | `TrackingNetDataset` |
| exactly `GOT-10k` | `GOT10kDataset` |
| exactly `DTB70` | `DTB70Dataset` |
| exactly `UAVDT` | `UAVDTDataset` |
| exactly `VisDrone` | `VisDroneDataset` |

Unknown names raise an exception. `VOT2017` is not factory-dispatched even
though the evaluator has a VOT2017 branch. `TrackingNet` is factory-dispatched
but has no evaluator branch.

`load_img=False` means images are not retained as one in-memory list. It does
not eliminate image I/O: base video objects inspect the first image, and frame
iteration decodes images as needed.

## Dataset wrapper layouts

### Metadata-JSON wrappers

OTB, UAV123/UAV20L, LaSOT, NFS, VOT restart, VOT2018-LT, and TrackingNet expect
`<dataset_root>/<dataset_name>.json`. Their per-sequence records distill to:

- common: `video_dir`, `init_rect`, `img_names`, `gt_rect`;
- OTB/UAV: `attr`;
- LaSOT: `attr` and `absent` (only present-target frames contribute);
- VOT restart: `camera_motion`, `illum_change`, `motion_change`, `size_change`,
  and `occlusion` tag arrays.

Image names in metadata must resolve under the dataset root. The JSON is part of
the runtime dataset contract; raw images alone are insufficient for these
wrappers.

### Scanned-directory wrappers

| Dataset | Scanned annotation/images |
|---|---|
| DTB70 | `*/groundtruth_rect.txt` and sibling `img/*.jpg` |
| UAVDT | `*/*_gt.txt` and JPEGs in each annotation directory |
| VisDrone | sorted `annotations/*_s.txt` paired positionally with sorted `sequences/*`, whose JPEGs are frames |
| GOT-10k test-side | `val/*/*.txt`; sequence directory is the annotation parent and sibling `*.jpg` files are frames |

The VisDrone wrapper assumes sorted annotation and sequence lists align; verify
basenames/counts before a long run. Scanned wrappers use lexicographic frame
ordering, so zero-padded frame names are safest. Ground-truth row count must
match frame count even where the wrapper does not assert it early.

The embedded `got10k.datasets.GOT10k` wrapper is separate from the test-side
`toolkit.datasets.GOT10kDataset`. It expects:

```text
<root>/<subset>/list.txt
<root>/<subset>/<sequence>/*.jpg
<root>/<subset>/<sequence>/groundtruth.txt
```

where subset is `val` or `test` for experiment reporting. Validation metadata
also includes `meta_info.ini`, `cover.label`, `absence.label`, and
`cut_by_image.label` as required by the reporting path.

## Result layout by protocol

In all diagrams, `R` is the result parent, `D` the exact dataset name, `T` the
tracker directory, and `S` one sequence.

### OPE

```text
R/D/T/S.txt
```

Each line is one comma-separated finite `[x, y, width, height]` box. Stock result
production writes one row per frame and includes the initialization box in row
one. Width and height should be positive. OTB result loading has historical
lowercase filename fallbacks for a few sequences, but new outputs should use the
canonical sequence name exactly.

### VOT restart

```text
R/D/T/baseline/S/S_001.txt
```

Each frame row is either a four/eight-value box or a one-value protocol marker:

- `1`: initialize/reinitialize on this frame;
- `2`: tracking loss on this frame;
- `0`: skipped frame after a loss.

The maintained loop writes `2`, then four `0` rows, then `1` on the fifth frame
after loss if the sequence continues. It writes one repetition. The loader uses
all files only when exactly 15 repetition files match; otherwise it takes only
the first match. Avoid stray matching text files.

### VOT2018-LT

```text
R/D/T/longterm/S/S_001.txt
R/D/T/longterm/S/S_001_confidence.value
R/D/T/longterm/S/S_time.txt
```

Trajectory, confidence, and timing files must align one row per frame. The first
trajectory row is a one-value initialization marker (`1` in the test path; a
historical search path wrote `0`). The confidence file's first row is blank and
remaining rows are finite scores. Timing rows are positive seconds.

Important defect: the maintained test loop does not append per-frame
`best_score` values, so it can emit a one-line confidence file for a multi-frame
trajectory. That is structurally invalid for F1 evaluation. Do not claim a
successful long-term evaluation until confidence and trajectory counts match.

### GOT-10k

```text
R/GOT-10k/T/S/S_001.txt
R/GOT-10k/T/S/S_time.txt
```

Each trajectory row is a four-value box. The experiment wrapper permits up to
three repetitions named `_001`, `_002`, `_003`; its timing file stores one row
per frame and one comma-separated column per recorded repetition. The maintained
test path writes one repetition and one timing scalar per row.

Validation reporting computes overlap from frame 2 onward, checks each result
array shape against ground truth, filters frames with `cover > 0`, and derives
speed from finite positive timing entries. GOT-10k test ground truth is withheld;
test results are submission material, not locally scored validation results.

## Offline validator

The bundled checker validates names and result structure without importing any
tracker or benchmark package:

```bash
SKILL_DIR=/path/to/evaluation
python "$SKILL_DIR/scripts/check_result_layout.py" --help
python "$SKILL_DIR/scripts/check_result_layout.py" --list-datasets
python "$SKILL_DIR/scripts/check_result_layout.py" \
  --dataset GOT-10k --results-root ./results --tracker-name nanotrack \
  --sequence GOT-10k_Val_000001:120 --json
```

`--results-root` corresponds to `R`, not `R/D` or `R/D/T`.
`--tracker-name` is an exact directory name, not the evaluator's prefix glob.
Repeat `--sequence NAME[:FRAMES]` to require selected sequences and optional
row counts. Extra discovered sequences fail unless `--allow-extra-sequences` is
set.

Expected failures include unknown dataset names, missing tracker/sequence
folders, malformed or non-finite boxes, nonpositive dimensions, missing GOT
runtime files, invalid VOT markers/restart cadence, and VOT-LT confidence/time
count mismatch. A pass proves only structural coherence.

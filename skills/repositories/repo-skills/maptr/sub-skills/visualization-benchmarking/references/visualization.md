# Visualization reference

## Preconditions

`vis_pred.py` is a model-and-dataset execution tool, not a renderer that can
operate on an empty directory. Before invoking it, check all of the following:

- The config resolves its base configs and plugin package. The standard tiny
  camera config enables `plugin=True` and uses the repository's plugin path.
- The checkpoint matches the config's model and class setup. A checkpoint alone
  is not a substitute for the configured model or its pretrained backbone
  assets.
- The test annotation pickle, map annotation file where required, six camera
  image paths, and any CAN-bus metadata required by the selected dataset are
  prepared. Dataset layout and conversion belong to data-preparation.
- The installed runtime matches the documented legacy stack closely enough to
  import `mmcv`, `mmdet`, `mmdet3d`, the plugin, and the model's custom
  operations. The documented versions include Python 3.8, torch 1.9.1+cu111,
  mmcv-full 1.4.0, mmdet 2.14.0, mmseg 0.14.1, mmdetection3d 0.17.2, and
  Shapely 1.8.5.post1. A visible CUDA device does not prove that the matching
  legacy `nvcc`, `mmcv-full`, or GeometricKernelAttention build is usable.
- There is enough storage for copied camera images and high-DPI PNG maps. A
  normal run creates one child directory per usable test sample.

If any required item is absent, report the exact missing item and stop. Do not
replace a missing checkpoint with a random checkpoint or treat a config parse
as successful inference.

## Native command and arguments

From the project root:

```bash
PYTHONPATH=. python tools/maptr/vis_pred.py CONFIG CHECKPOINT \
  --score-thresh 0.30 \
  --show-cam \
  --show-dir work_dirs/experiment/vis_pred \
  --gt-format fixed_num_pts polyline_pts
```

The source parser defines:

| Argument | Contract | Practical rule |
|---|---|---|
| `CONFIG` | positional config file | Use the same config used to train/evaluate the checkpoint. |
| `CHECKPOINT` | positional checkpoint file | Check existence and compatibility before starting the dataset loop. |
| `--score-thresh` | floating prediction cutoff | Current code default is 0.4; the visualization doc says 0.3. Pass it explicitly. |
| `--show-cam` | boolean camera-display option | Accepted by the parser; current code still copies camera images and builds a surrounding view without checking it. |
| `--show-dir` | output directory | Defaults to `./work_dirs/<config stem>/vis_pred`; it is created and receives a config copy. |
| `--gt-format` | one or more strings | Accepted values are `se_pts`, `bbox`, `fixed_num_pts`, and `polyline_pts`. Unknown values raise `ValueError`. |

The source's help text calls the default GT format `fixed_num_pts`. The actual
saved filename behavior matters more than the parser's acceptance:

| Requested format | Source representation | Saved by this revision |
|---|---|---|
| `fixed_num_pts` | fixed-number sampled points | `GT_fixednum_pts_MAP.png` |
| `polyline_pts` | original polyline coordinates | `GT_polyline_pts_MAP.png` |
| `se_pts` | start/end points with arrows | drawn on a transient Matplotlib figure; no dedicated file is written |
| `bbox` | enclosing XY rectangle | drawn on a transient Matplotlib figure; no dedicated file is written |

Use `fixed_num_pts` when the downstream consumer expects the native video
contract. Use `polyline_pts` for a saved view of the original annotation. If a
review requires persistent `se_pts` or `bbox` images, treat that as an
implementation change and route it to model-configuration or a separately
reviewed visualization change; do not claim the native output contains them.

## Output layout and checks

The default output is conceptually:

```text
work_dirs/<config stem>/vis_pred/
├── <sample-id>/
│   ├── CAM_FRONT_LEFT.jpg
│   ├── CAM_FRONT.jpg
│   ├── CAM_FRONT_RIGHT.jpg
│   ├── CAM_BACK_LEFT.jpg
│   ├── CAM_BACK.jpg
│   ├── CAM_BACK_RIGHT.jpg
│   ├── surroud_view.jpg
│   ├── GT_fixednum_pts_MAP.png       # if fixed_num_pts was requested
│   ├── GT_polyline_pts_MAP.png       # if polyline_pts was requested
│   └── PRED_MAP_plot.png
└── <config filename>
```

The source derives `<sample-id>` from the basename of the lidar filename after
removing the `__LIDAR_TOP__` marker and extension. It copies camera images
from the dataset and produces map views over the configured point-cloud range.
The common tiny R50 config uses three map classes (`divider`, `ped_crossing`,
and `boundary`), 20 points per vector, and a `[-15, -30, -2, 15, 30, 2]`
point-cloud range; these are configuration facts, not universal assumptions.

Before video assembly, perform a file-level check for every selected sample:

```bash
find work_dirs/experiment/vis_pred -mindepth 1 -maxdepth 1 -type d -print | sort
find work_dirs/experiment/vis_pred/SAMPLE_ID -maxdepth 1 -type f -printf '%f\n' | sort
```

Require six camera JPEGs, `PRED_MAP_plot.png`, and
`GT_fixednum_pts_MAP.png` for the native video layout. If a sample has only
`GT_polyline_pts_MAP.png`, it may be useful for inspection but is not accepted
by the native video assembler or the bundled helper. Decode images rather than
checking names alone; a zero-byte image is not a visual artifact.

## Deferred execution policy

A generation request can still produce a useful handoff without running the
model. Record the intended command, resolved config/checkpoint paths, expected
outputs, and the precise gate that prevented execution. Typical gates are no
prepared annotations/images, no checkpoint, import failure from the legacy
stack, or an unbuilt custom operation. Do not report threshold effects, sample
counts, or qualitative performance unless a real run produced them.

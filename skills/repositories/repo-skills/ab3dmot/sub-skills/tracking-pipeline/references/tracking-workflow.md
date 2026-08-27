# AB3DMOT Tracking Workflow

This reference covers the runtime tracking path: build a `main.py` command, ensure the expected tracking inputs exist, run per-category tracking, and interpret the result folders. It intentionally does not cover raw data conversion or metric/visualization workflows.

## Before running tracking

AB3DMOT tracking expects to be run from the AB3DMOT repository root, because `main.py` reads relative paths such as `./configs/<dataset>.yml`, `./data/<dataset>/detection/...`, and `./results/<dataset>/...`.

Minimum prerequisites:

1. Python can import `AB3DMOT_libs` and the Xinshuo toolbox modules.
2. The selected dataset config exists under `configs/`.
3. Category-specific detection input folders exist under `./data/<dataset>/detection/`.
4. The corresponding tracking data root has calibration, ego-motion, and image folders:
   - KITTI: `./data/KITTI/tracking/training/...` for `val`, or `./data/KITTI/tracking/testing/...` for `test`.
   - nuScenes: `./data/nuScenes/nuKITTI/tracking/<split>/...` after conversion to the KITTI-like layout.

For data and detection preparation, use [../../data-conversion/SKILL.md](../../data-conversion/SKILL.md). For result evaluation and visualization after tracking, use [../../evaluation-visualization/SKILL.md](../../evaluation-visualization/SKILL.md).

## Build safe commands first

The bundled builder does not import AB3DMOT and does not run tracking. Use it to avoid accidental reliance on `main.py` defaults:

```bash
python sub-skills/tracking-pipeline/scripts/build_tracking_command.py \
  --dataset KITTI --split val --det_name pointrcnn
```

It prints:

- the explicit `python main.py ...` command;
- category-specific detection folders that must exist;
- category-specific result folder names;
- the combined result folder name that downstream evaluation/visualization expects.

Add `--format json` when another script needs machine-readable output.

## Primary CLI

`main.py` exposes exactly these command-line flags:

| Flag | Meaning | Practical guidance |
| --- | --- | --- |
| `--dataset` | Selects `configs/<dataset>.yml`; supported values are `KITTI` and `nuScenes`. | Always pass it explicitly. The parser default is `nuScenes`, while the quick KITTI demo expects `KITTI`. |
| `--split` | Overrides `cfg.split` after the YAML file is loaded. | Pass `val` or `test` for KITTI; pass `train`, `val`, or `test` for nuScenes when matching inputs exist. |
| `--det_name` | Overrides `cfg.det_name` after the YAML file is loaded. | Must match both a tuned tracker branch and the detection-folder prefix. |

Safe examples:

```bash
# KITTI validation with provided/documented PointRCNN detections.
python main.py --dataset KITTI --split val --det_name pointrcnn

# KITTI test with PointRCNN detections.
python main.py --dataset KITTI --split test --det_name pointrcnn

# nuScenes validation with Megvii or CenterPoint detections after nuScenes conversion.
python main.py --dataset nuScenes --split val --det_name megvii
python main.py --dataset nuScenes --split val --det_name centerpoint
```

Avoid running `python main.py` without flags unless you really intend to use the `nuScenes` config default.

## Supported tracking combinations

The docs and configs mention detector names, but actual tracking also depends on tuned branches in the tracker parameter table.

| Dataset | Splits for tracking | Tuned detector names | Categories looped by default |
| --- | --- | --- | --- |
| `KITTI` | `val`, `test` | `pointrcnn`, `pvrcnn` | `Car`, `Pedestrian`, `Cyclist` |
| `nuScenes` | `train`, `val`, `test` | `megvii`, `centerpoint` | `Car`, `Pedestrian`, `Bicycle`, `Motorcycle`, `Bus`, `Trailer`, `Truck` |

Notes:

- KITTI config comments list `pointrcnn` and `pvrcnn`; public tracking docs demonstrate `pointrcnn`.
- nuScenes config comments mention `centerpoint`, `megvii`, `mapillary`, and `pointpillar`, but the inspected tracker parameter table has tuned branches only for `centerpoint` and `megvii` plus a stale `deprecated` branch. Do not use `mapillary` or `pointpillar` directly without adding and verifying tracker parameters.
- KITTI has a stale train sequence list in a utility function, but the split dispatch for tracking accepts only `val` and `test`. Treat KITTI `train` tracking as unsupported unless the code is changed and verified.

## What `main.py` does

For a chosen dataset/split/detector:

1. Loads `configs/<dataset>.yml`.
2. Applies CLI overrides for `split` and `det_name`.
3. Opens a log under `<save_root>/log/`.
4. Initializes a global track-ID counter at `1` so categories do not reuse IDs.
5. Loops over `cfg.cat_list` and runs `main_per_cat(cfg, cat, log, ID_start)`.
6. For each category, loads detections from `./data/<dataset>/detection/<det_name>_<cat>_<split>/<seq>.txt`.
7. Initializes one `AB3DMOT` tracker per sequence/category.
8. Calls `tracker.track(dets_frame, frame, seq_name)` once per frame.
9. Saves per-frame tracking rows, MOT-evaluation rows, and affinity matrices.
10. After all categories finish, combines category-specific result folders into one all-category folder.

## Detection inputs consumed by tracking

For a category `cat`, `main_per_cat` constructs:

```text
result_sha = <det_name>_<cat>_<split>
det_root   = ./data/<dataset>/detection/<result_sha>
```

Each sequence file is expected at:

```text
./data/<dataset>/detection/<det_name>_<cat>_<split>/<seq>.txt
```

Rows are comma-separated numeric detections. Tracking consumes frame-specific data as:

- 3D box columns: `[h, w, l, x, y, z, theta]`;
- side information: `[alpha, type_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, score]`.

Detailed schema validation and conversion are owned by the data-conversion sub-skill.

## Result folders

The default `save_root` values are:

- KITTI: `./results/KITTI`
- nuScenes: `./results/nuScenes`

For each category, tracking writes:

```text
<save_root>/<det_name>_<cat>_<split>_H<num_hypo>/
  data_0/<seq>.txt                  # MOT evaluation format, one file per sequence
  trk_withid_0/<seq>/<frame>.txt    # per-frame detection-like rows with track ID
  affi/<seq>/<frame>.npy            # affinity matrices when non-empty
  affi_vis/<seq>/<frame>.txt        # text affinity for visual inspection when both axes are non-empty
  vis_debug/<seq>/...               # only when cfg.vis is true
```

After the category loop, `combine_trk_cat` writes the all-category result folder:

```text
<save_root>/<det_name>_<split>_H<num_hypo>/
  data_0/<seq>.txt
  trk_withid_0/<seq>/<frame>.txt
  combine_log.txt
```

Downstream evaluation, confidence thresholding, and visualization usually consume the combined result name, for example `pointrcnn_val_H1` or `megvii_val_H1`.

## Affinity outputs

`main.py` saves affinity after each `tracker.track` call when the affinity matrix has at least one row or column. With `cfg.affi_pro: true`, the tracker post-processes raw detection-to-track affinity into past-active-tracklet to current-active-tracklet affinity. On the first frame with one new detection and no previous active tracks, a normal processed affinity shape is `(0, 1)`.

## Native verification candidates

Safe candidates for this workflow:

```bash
python main.py --help
python sub-skills/tracking-pipeline/scripts/build_tracking_command.py --dataset KITTI --split val --det_name pointrcnn
python sub-skills/tracking-pipeline/scripts/smoke_track_synthetic.py
```

Full KITTI or nuScenes tracking commands are native candidates only when the corresponding full tracking data and category-specific detection folders are present.

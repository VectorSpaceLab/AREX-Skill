# Tracking Configuration Reference

AB3DMOT has one YAML config per dataset. `main.py` loads `configs/<dataset>.yml` based on `--dataset`, then overrides only `split` and `det_name` from the CLI.

## Default configs

### KITTI defaults

```yaml
save_root: ./results/KITTI
dataset: KITTI
split: val
det_name: pointrcnn
cat_list: [Car, Pedestrian, Cyclist]
score_threshold: -10000
num_hypo: 1
ego_com: true
vis: false
affi_pro: true
```

### nuScenes defaults

```yaml
save_root: ./results/nuScenes
dataset: nuScenes
split: val
det_name: megvii
cat_list: [Car, Pedestrian, Bicycle, Motorcycle, Bus, Trailer, Truck]
score_threshold: -10000
num_hypo: 1
ego_com: true
vis: false
affi_pro: true
```

## Field meanings

| Field | Used by | Meaning and pitfalls |
| --- | --- | --- |
| `save_root` | `main.py`, IO helpers | Root for logs, category result folders, combined result folders, affinity, and visualization-debug output. It is interpreted relative to the current shell when set to a relative path. |
| `dataset` | config selection, sequence utilities, tracker parameters | Must be `KITTI` or `nuScenes`. It controls category IDs, sequence lists, image sizes, data roots, and tracker parameter branches. |
| `split` | detection lookup, sequence list, result names | CLI `--split` overrides it. KITTI tracking is practical for `val` and `test`; nuScenes tracking supports `train`, `val`, and `test` when inputs exist. |
| `det_name` | detection lookup, tracker parameter branches, result names | CLI `--det_name` overrides it. It must match both detection-folder prefixes and tuned tracker branches. |
| `cat_list` | category loop | `main.py` loops all categories and carries a global track-ID counter across them. Category names must match tracker parameter branches and detection-folder suffixes. |
| `score_threshold` | result saving | Filters rows written to `data_0` evaluation files. The default `-10000` means effectively no filtering during tracking. Confidence thresholding is usually done after tracking by the evaluation/visualization workflow. |
| `num_hypo` | result subfolders and tracker initialization | Public configs use `1`, creating `data_0` and `trk_withid_0`. Values above `1` require multi-hypothesis tracker support and must be reverified before use. |
| `ego_com` | `AB3DMOT` model | Enables ego-motion compensation before association. It improves tracking when calibration and OXTS/ego poses exist. Disable for synthetic/in-memory smoke tests without ego data. |
| `vis` | `AB3DMOT` model | Enables debug visualization inside the tracker loop. It is slow and requires image files, calibration, OpenCV, and writable debug directories. It is not the same as post-processing visualization. |
| `affi_pro` | `AB3DMOT` model | Converts raw detection-to-track affinity into past-active-output by current-active-output affinity. Keep true when consuming saved affinity as tracklet-to-tracklet confidence. |

## CLI override behavior

`main.py` has parser defaults:

```text
--dataset nuScenes
--split ""
--det_name ""
```

Then it loads the selected YAML file and applies:

```python
if args.split is not '': cfg.split = args.split
if args.det_name is not '': cfg.det_name = args.det_name
```

Consequences:

- Always pass `--dataset` explicitly. The parser default is `nuScenes`, not KITTI.
- If `--split` or `--det_name` is omitted, the YAML default is used.
- CLI cannot override `save_root`, `cat_list`, `score_threshold`, `num_hypo`, `ego_com`, `vis`, or `affi_pro`; edit the config or construct a config object in direct API code.
- Newer Python versions can warn about `is not ''`; treat it as a syntax warning unless it becomes an error in the runtime.

## Detector and category compatibility

Use [../scripts/build_tracking_command.py](../scripts/build_tracking_command.py) to validate common combinations without importing the repository.

| Dataset | Recommended detector names | Category list |
| --- | --- | --- |
| `KITTI` | `pointrcnn`; `pvrcnn` if matching detection folders exist | `Car`, `Pedestrian`, `Cyclist` |
| `nuScenes` | `megvii`, `centerpoint` | `Car`, `Pedestrian`, `Bicycle`, `Motorcycle`, `Bus`, `Trailer`, `Truck` |

Do not rely on detector names that appear only in comments. For example, nuScenes config comments mention `mapillary` and `pointpillar`, but the tracker parameter table does not include tuned branches for those detector names in the inspected code.

## Result naming formulas

With `num_hypo: 1`, per-category result folder:

```text
<save_root>/<det_name>_<cat>_<split>_H1/
```

Combined all-category result folder:

```text
<save_root>/<det_name>_<split>_H1/
```

The combined folder is produced only after every configured category loop finishes and `combine_trk_cat` succeeds. Evaluation and visualization typically use the combined result SHA, such as `pointrcnn_val_H1` or `megvii_val_H1`.

## Working-directory pitfalls

AB3DMOT uses relative paths in the CLI path:

- `./configs/<dataset>.yml`
- `./data/<dataset>/detection/...`
- `./results/<dataset>/...`

Run command-level tracking from the AB3DMOT repository root, or change the working directory and path arguments deliberately in custom wrappers. The bundled command builder prints `python main.py ...` rather than an absolute path for this reason.

## Practical config edits

Common safe edits:

- Set `score_threshold` above `-10000` only when you intentionally want `data_0` outputs filtered during tracking.
- Set `ego_com: false` for direct synthetic tests or streams without ego poses.
- Keep `vis: false` for throughput; use post-processing visualization after tracking instead.
- Keep `affi_pro: true` unless downstream code expects raw detection-to-track affinity.

Edits that require re-verification:

- Adding a new detector name.
- Adding or removing categories.
- Changing `num_hypo` above `1`.
- Running KITTI `train` through `main.py`.
- Replacing dataset roots or sequence lists.

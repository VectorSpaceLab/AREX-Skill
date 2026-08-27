# Dataset Aliases and Result Layout

## When to read

Read this before any dataset or experiment run. PyTracking uses short dataset aliases, local path fields, and tracker-specific result directories; wrong aliases or unset paths are common failure sources.

## Dataset aliases verified from the registry

The evaluation registry accepts these aliases:

```text
avist, dv2016_val, dv2017_test_chal, dv2017_test_dev, dv2017_val,
got10k_ltrval, got10k_test, got10k_val, got10kvos_val,
lagot, lagot_sot_mode, lasot, lasot_train, lasot_extension_subset, lasotvos,
nfs, otb, oxuva_dev, oxuva_test, tpl, tpl_nootb,
trackingnet, trackingnetvos, uav, vot,
yt2018_jjval, yt2018_valid_all, yt2019_test, yt2019_valid,
yt2019_valid_all, yt2019_jjval, yt2019_jjval_all
```

Use the helper to list aliases in the current skill copy:

```bash
python scripts/build_tracking_command.py --list-datasets
```

## Local configuration fields

PyTracking creates a user-local `pytracking/evaluation/local.py` from `pytracking.evaluation.environment.create_default_local_file()`. The file defines a `local_env_settings()` function returning an object with fields such as:

| Field | Purpose |
| --- | --- |
| `results_path` | Where tracking bounding-box result text files are written. |
| `segmentation_path` | Where segmentation masks/results are written for VOS-capable trackers. |
| `network_path` | Directory containing pretrained tracker network checkpoints. |
| `result_plot_path` | Plot/report output directory. |
| `otb_path`, `nfs_path`, `uav_path`, `tpl_path`, `vot_path` | Dataset roots for common short-term tracking datasets. |
| `got10k_path`, `lasot_path`, `lasot_extension_subset_path`, `trackingnet_path`, `oxuva_path`, `davis_dir`, `youtubevos_dir` | Dataset roots for GOT-10k, LaSOT, TrackingNet, OxUvA, DAVIS, and YouTube-VOS families. |
| `got_packed_results_path`, `got_reports_path`, `tn_packed_results_path` | Packaging/report output locations used by result utility workflows. |

The environment module will generate a default file and then raise an error if `local.py` is missing. Treat that as a setup action, not a tracker bug.

## Result path conventions

`Tracker(name, parameter_name, run_id=None)` derives paths from the local environment:

- No run id: `<results_path>/<tracker>/<parameter>/`
- With run id: `<results_path>/<tracker>/<parameter>_<run_id:03d>/`
- Segmentation paths mirror the same tracker/parameter layout under `segmentation_path`.

Sequence result files are written by the running/evaluation code with names derived from sequence names. Packaging helpers for GOT-10k and TrackingNet expect this layout; route packaging tasks to the `analysis-and-packaging` sub-skill.

## Tracker and parameter name discipline

Do not use display names such as `DiMP-50` as module names. Use source module names:

| Display family | Typical tracker name | Example parameter names |
| --- | --- | --- |
| ATOM | `atom` | `default`, `default_vot`, `multiscale_no_iounet`, `atom_prob_ml`, `atom_gmm_sampl` |
| DiMP / PrDiMP / SuperDiMP | `dimp` | `dimp18`, `dimp50`, `prdimp18`, `prdimp50`, `super_dimp`, VOT variants |
| SuperDiMPSimple | `dimp_simple` | `super_dimp_simple` |
| ECO | `eco` | `default`, `mobile3` |
| KeepTrack | `keep_track` | `default`, `default_fast` |
| KYS | `kys` | `default`, `default_vot` |
| LWL | `lwl` | `lwl_ytvos`, `lwl_boxinit` |
| RTS | `rts` | `rts50` |
| TaMOs | `tamos` | `tamos_resnet50`, `tamos_swin_base` |
| ToMP | `tomp` | `tomp50`, `tomp101` |

See the root tracker/model catalog for a broader catalog and checkpoint notes.

## Dataset run triage

- If an alias is unknown, check spelling against the registry list before editing code.
- If a sequence name fails, try a sequence index only after confirming the dataset root points to the expected benchmark layout.
- If no result files appear, check `results_path`, write permission, `run_id`, and whether the command targeted a single sequence or full dataset.
- For VOS aliases, also check `segmentation_path` and mask/annotation availability.
- For large datasets, start with a single known-short sequence and `threads=0` before parallel full evaluation.

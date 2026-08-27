# Configuration Reference

## When to read

Read this before choosing or generating a YAML config for a run.

## Inheritance model

`mast3r_slam.config.load_config(path)` loads YAML, then recursively merges a
parent file named by `inherit` before applying child overrides. Child values
replace parent scalars and recursively merge dictionaries.

## Bundled templates

Use `scripts/write_config_templates.py` to write these templates into a working
configuration directory:

| Template | Purpose |
| --- | --- |
| `base.yaml` | Default interactive/runtime config without calibration. |
| `calib.yaml` | Inherits base; enables calibration and dataset subsampling of 2. |
| `eval_calib.yaml` | Inherits base; enables calibration, single-threaded headless-style behavior, and subsampling of 2. |
| `eval_no_calib.yaml` | Inherits base; disables calibration, uses single-threaded evaluation mode, and subsampling of 2. |
| `eth3d.yaml` | Inherits `eval_calib`; sets dataset subsample to 1, disables center-principal-point adjustment, and relaxes relocalization strictness. |
| `intrinsics.yaml` | Example camera model with width, height, and calibration vector. |

## High-impact keys

| Key path | Typical values | Runtime effect |
| --- | --- | --- |
| `use_calib` | `False` or `True` | Toggles calibrated projection/ray logic and requires available intrinsics. |
| `single_thread` | `False` or `True` | Evaluation configs use true so backend and relocalization waits are deterministic. |
| `dataset.subsample` | `1` or `2` | Drops frames before processing; evaluation configs often use 2. |
| `dataset.img_downsample` | `1` | Downsamples pointmap tensors after MASt3R inference. |
| `dataset.center_principle_point` | `True` or `False` | Controls OpenCV optimal camera matrix center behavior. |
| `tracking.min_match_frac` | `0.05` | Too few matches triggers relocalization instead of pose update. |
| `tracking.match_frac_thresh` | `0.333` | Lower match/unique fraction creates a new keyframe. |
| `tracking.filtering_mode` | `weighted_pointmap`, `recent`, `first`, `best_score`, `weighted_spherical`, `indep_conf` | Controls pointmap update strategy. |
| `local_opt.use_cuda` | `True` | Backend optimization expects CUDA kernels for selected runtime. |
| `retrieval.k` | `3` | Number of retrieval candidates considered for loop closure/relocalization. |
| `reloc.strict` | `True` or `False` | ETH3D relaxes this to improve long-loop behavior. |

## Calibration file shape

A calibration YAML has:

```yaml
width: 640
height: 480
calibration: [fx, fy, cx, cy, k1, k2, p1, p2, k3]
```

The distortion tail can be omitted when only `[fx, fy, cx, cy]` is known. A
runtime `--calib` argument forces `config["use_calib"] = True` and sets the
loaded dataset to use the provided intrinsics.

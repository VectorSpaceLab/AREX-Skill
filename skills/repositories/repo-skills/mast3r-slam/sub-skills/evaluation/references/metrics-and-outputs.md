# Metrics and Outputs

## When to read

Read this when locating trajectory outputs, point clouds, keyframes, or `evo_ape`
metric inputs.

## Runtime outputs

For dataset/video/folder inputs with `save_results=True`, MASt3R-SLAM writes
under `logs/` or `logs/<save-as>/`:

- `<sequence>.txt`: trajectory rows in TUM format-ish order: timestamp, xyz,
  quaternion.
- `<sequence>.ply`: dense point-cloud reconstruction.
- `keyframes/<sequence>/<timestamp>.png`: saved keyframe images.

The sequence name is normally `dataset.dataset_path.stem`. For official suite
scripts, the trajectory path is:

```text
logs/<suite>/<calib-or-no_calib>/<sequence>/<sequence>.txt
```

ETH3D uses:

```text
logs/eth3d/<sequence>/<sequence>.txt
```

## Metric command shape

All upstream scripts use `evo_ape` with the `tum` format and alignment/scale:

```bash
evo_ape tum <groundtruth.txt> <trajectory.txt> -as
```

Groundtruth paths differ by suite:

| Suite | Groundtruth path |
| --- | --- |
| TUM | `<dataset-sequence>/groundtruth.txt` |
| 7-Scenes | `groundtruths/7-scenes/<sequence>.txt` |
| EuRoC | `groundtruths/euroc/<sequence>.txt` |
| ETH3D | `<dataset-sequence>/groundtruth.txt` |

## Metric-only workflow

If trajectories already exist, do not rerun SLAM. Use:

```bash
python sub-skills/evaluation/scripts/plan_evaluation.py --suite tum --metric-only
```

Review the printed `evo_ape` commands and run only the ones whose input files
exist.

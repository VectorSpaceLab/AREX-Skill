# Metrics workflows

These are the noninteractive APE/RPE recipes distilled from the original demo scripts. They are intended to be copied directly into a shell or Python session. Create the output directory once before commands that write under `out/`:

```bash
mkdir -p out
```

## 1. Fast APE on timestamped trajectories

Use this when you already have paired TUM, EuRoC, or bag-based trajectories and want a standard APE score.

```bash
evo_ape tum reference.tum estimate.tum --align --save_results out/ape.zip
```

Expected behavior:

- The output title says `APE w.r.t. translation part (m)`.
- The metric report prints `max`, `mean`, `median`, `min`, `rmse`, `sse`, and `std`.
- The zip file is written after evaluation.

If the timestamps are slightly misaligned, add the sync flags:

```bash
evo_ape tum reference.tum estimate.tum --align --t_offset -0.2 --t_max_diff 0.05 --save_results out/ape.zip
```

## 2. APE on KITTI pose files

Use this when both inputs are KITTI pose files and you want either alignment or scale correction.

```bash
evo_ape kitti reference.txt estimate.txt --align --save_results out/kitti_ape.zip
```

For monocular or scale-drifted estimates:

```bash
evo_ape kitti reference.txt estimate.txt --correct_scale --save_results out/kitti_ape_scaled.zip
```

If you want a 2D visualization, add `--project_to_plane xz` or another plane and optionally `--save_plot out/kitti_ape.pdf`.

## 3. Relative pose error on frames, meters, or angles

Use this when you want drift between pairs of poses.

```bash
evo_rpe kitti reference.txt estimate.txt -d 10 -u m --save_results out/kitti_rpe.zip
```

For frame-based spacing:

```bash
evo_rpe tum reference.tum estimate.tum -d 1 -u f --save_results out/tum_rpe.zip
```

For angle-based pair spacing:

```bash
evo_rpe tum reference.tum estimate.tum -d 5 -u d --save_results out/tum_rpe_angle.zip
```

Pair-selection options:

- `--all_pairs` searches all valid pairs instead of consecutive pairs.
- `--pairs_from_reference` chooses the candidate pairs from the reference trajectory.
- `-t/--delta_tol` controls the relative tolerance for all-pairs matching.

## 4. EuRoC and bag-based routes

Use these when the timestamps are already embedded in the data source or when you need topic-based association.

```bash
evo_ape euroc data.csv estimate.tum --align --save_results out/euroc_ape.zip
```

```bash
evo_ape bag example.bag /reference /estimate --save_results out/bag_ape.zip
```

```bash
evo_rpe bag2 example.mcap /reference /estimate -d 1 -u f --save_results out/bag2_rpe.zip
```

`bag2` and `mcap` are the same route.

If association fails, tune the timestamp window first:

- widen `--t_max_diff`
- correct the sign or magnitude of `--t_offset`
- crop with `--t_start` / `--t_end` when the input contains unrelated spans

## 5. Origin alignment versus Umeyama alignment

Pick one of these patterns:

```bash
evo_ape tum reference.tum estimate.tum --align
```

```bash
evo_ape tum reference.tum estimate.tum --align_origin
```

Do not combine them. `--align` is Umeyama alignment; `--align_origin` only moves the starting pose to the reference origin.

## 6. Result zip and plot validation

If you want both a plot and a saved result, use both flags:

```bash
evo_rpe tum reference.tum estimate.tum -d 1 -u f --plot --save_plot out/rpe.pdf --save_results out/rpe.zip
```

Validation steps:

1. Check that the CLI prints a metric title and statistics.
2. Check that the zip file exists.
3. Re-load the zip with `load_res_file(..., load_trajectories=True)` if trajectory backups were saved.
4. If you only need the aggregate values, the zip must still contain `info.json`, `stats.json`, and the `.npy` arrays.

## 7. Rerun logging

If the optional dependency is installed, add `--rerun`:

```bash
evo_ape tum reference.tum estimate.tum --rerun --rerun_rec_id eval-01
```

This sends the trajectories, error scalars, and statistics to the Rerun viewer.

## 8. Bundled smoke helper

Run the in-tree synthetic smoke helper when you want a fixture-free sanity check, from an environment where the `evo` package is importable:

```bash
python scripts/metric_smoke.py
```

It builds tiny trajectories in memory, exercises APE and RPE, and validates that saved result zips round-trip correctly.

## 9. Minimal Python API recipe

```python
from copy import deepcopy

from evo.core.metrics import PoseRelation, Unit
from evo.main_ape import ape
from evo.main_rpe import rpe
from evo.tools import file_interface

ape_res = ape(deepcopy(traj_ref), deepcopy(traj_est), PoseRelation.translation_part, align=True)
rpe_res = rpe(deepcopy(traj_ref), deepcopy(traj_est), PoseRelation.translation_part, delta=1, delta_unit=Unit.frames)

file_interface.save_res_file("ape.zip", ape_res)
file_interface.save_res_file("rpe.zip", rpe_res)
```

Use the Python API when you want to control copying, titles, result storage, or custom batching.

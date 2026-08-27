# Trajectory workflows

These recipes were distilled from the repo's demo scripts and source loaders. They are written to be copy-pasted without needing the original checkout.

Create a scratch directory for outputs first:

```bash
mkdir -p out
```

## 1. Inspect a TUM trajectory

```bash
evo_traj tum path/to/traj.tum --full_check
```

Use this when you want trajectory summary stats and validation details.

## 2. Sync and align TUM trajectories

```bash
evo_traj tum reference.tum estimate.tum --ref reference.tum --sync --align -p --plot_mode xyz
```

Useful flags:
- `--align` for Umeyama alignment
- `--align_origin` when you only want the estimate's origin moved to the reference origin
- `--t_offset` and `--t_max_diff` when the timestamps are close but not identical

## 3. Export trajectories to another format

```bash
evo_traj tum reference.tum estimate.tum --ref reference.tum --align --save_as_tum --save_as_kitti
```

For ROS bag or bag2 export, add the relevant `--save_as_bag` or `--save_as_bag2` flag after you have loaded valid trajectories.

## 4. Use the bundled converters instead of hand-editing files

### KITTI poses + timestamps -> TUM

```bash
python scripts/kitti_timestamps_to_tum.py path/to/poses.txt path/to/timestamps.txt out/traj.tum
```

### Scale timestamps in a TUM file

```bash
python scripts/scale_tum_timestamps.py path/to/input.tum 0.5 out/scaled.tum
```

## 5. Check for duplicate timestamps

```bash
python scripts/check_duplicate_timestamps.py path/to/traj.tum
```

Use this before sync-heavy workflows when a trajectory seems to produce strange association results.

## 6. Run the trajectory I/O smoke helper

```bash
python scripts/trajectory_io_smoke.py
```

This synthetic helper creates tiny trajectories and transform files in a temporary directory, then round-trips them through evo's public I/O helpers.

## 7. Bag and MCAP route examples

```bash
evo_traj bag example.bag groundtruth estimate --ref groundtruth --sync
```

```bash
evo_traj bag2 example.mcap /tf:map.base_link --all_topics
```

Use the supported topic names from the bag contents, or `--all_topics` / `--all_channels` when you want every supported topic.

## 8. Why the original demos are not bundled verbatim

The repo's demo shell scripts are interactive and assume the source-tree layout. This sub-skill replaces them with noninteractive recipes and safe bundled helpers that work from an installed environment.

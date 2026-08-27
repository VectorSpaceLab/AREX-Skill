# Stamped trajectories and APE/RPE

## `StampedSE3`

The trajectory helper is defined in `pypose/metric/ape_rpe.py`:

```python
StampedSE3(timestamps=None, poses_SE3=None, dtype=torch.float64)
```

`poses_SE3` is required, nonempty, and must represent one unbatched trajectory
(`lshape` has one dimension). It is converted to `dtype`, whose default is
`torch.float64`. `timestamps=None` creates `0, 1, ..., N-1` as float64 on the
pose device. Otherwise timestamps are converted to float64 and moved to the
pose device. Timestamps must be one-dimensional, the same length as poses, and
nondecreasing. Use an explicit timestamp vector for real sensor times.

Useful operations and properties:

- `traj[index]` returns a new `StampedSE3` subset; list/tensor indices are the
  safe way to select several poses.
- `reduce_to_ids(ids)` mutates the trajectory in place.
- `align(trans)` mutates poses by a supplied SE3 or Sim3 transform.
- `translation()` and `rotation()` expose pose translation/rotation components.
- `first_pose`, `num_poses`, `dtype`, `device`, and
  `accumulated_distances` support evaluation bookkeeping.
- `type(dtype)`, `cuda()`, and `cpu()` mutate the stored pose dtype/device.

Use LieTensor comparison (`pp.testing.assert_close`) for poses. A trajectory is
not a generic batched tensor: construct one `StampedSE3` per sequence.

## Association and alignment

`matching_time_indices(stamps_1, stamps_2, max_diff=0.01, offset_2=0.0)` picks,
for every stamp in `stamps_1`, the nearest stamp in `stamps_2 + offset_2` and
keeps pairs whose absolute difference is strictly less than `max_diff`. It
returns two Python index lists. The implementation currently performs
`stamps_2 += offset_2`, so protect a caller-owned timestamp tensor by passing a
clone when a nonzero offset is used:

```python
ids1, ids2 = matching_time_indices(ref_t, est_t.clone(),
                                   max_diff=0.01, offset_2=offset)
```

The nearest-neighbor matching is not a one-to-one assignment solver; repeated
nearest matches can occur when timestamps are dense or duplicated. Check the
returned indices and match count for applications that require bijection.

`associate_traj(rtraj, etraj, max_diff=0.01, offset_2=0.0, threshold=0.3)`
chooses the shorter and longer timestamp sequence, associates them, subsets both
trajectories, and returns `(rtraj_aligned, etraj_aligned)`. This return order is
what the implementation does even though older docstrings list the outputs in a
confusing order. It raises if there are no matches and warns if the number of
matches is below `threshold * len(shorter_trajectory)`. `max_diff` is strict and
is in seconds; `offset_2` shifts the second timestamp vector. Avoid mutating the
original timestamp tensor before later metrics by cloning it or reconstructing
trajectories.

Alignment is optional in `metric.ape` and `metric.rpe`:

- `align=True` estimates a Sim3 using `svdstf` (or SE3 when `scale=False`) from
  the first `nposes` associated translations and applies it to the estimate.
- `scale=True` enables similarity-scale correction.
- `origin=True` aligns the estimate's first pose to the reference first pose.
- These options alter the estimated trajectory before errors are computed; state
  them in a report and never compare scores with different alignment settings as
  if they were equivalent.

## Error APIs and result statistics

The public metric surface is function-based:

```python
pp.metric.ape(rstamp, rpose, estamp, epose, ...)
pp.metric.rpe(rstamp, rpose, estamp, epose, ...)
```

There are no `APE` or `RPE` classes in this API. The implementation also defines
`StampedSE3`, `matching_time_indices`, `associate_traj`, `compute_error`,
`pairs_by_frames`, `pairs_by_dist`, and `pair_id` in
`pypose.metric.ape_rpe`; import those helpers from that module only when a
workflow explicitly needs them.

`compute_error(rtraj, etraj, output='translation', mtype='ape', otype='All')`
accepts `mtype='ape'` or `'rpe'` and `output` in:

- `'translation'`: translational Euclidean error;
- `'rotation'`: Frobenius norm of rotation-matrix error;
- `'pose'`: Frobenius norm of homogeneous pose-matrix error;
- `'radian'` / `'degree'`: norm of the relative rotation logarithm in radians or
  degrees.

For APE translation, the implementation computes `etraj.translation() -
rtraj.translation()`. For other APE outputs it uses `etraj.Inv() @ rtraj`. For
RPE it expects relative pose trajectories and uses `rtraj.Inv() @ etraj` for the
matrix error. The statistic selector is case-sensitive:
`'All'`, `'Max'`, `'Min'`, `'Mean'`, `'Median'`, `'RMSE'`, `'SSE'`, or `'STD'`.
`otype='All'` returns a dictionary of statistics; any single selector returns a
scalar tensor. The source's internal condition populates every dictionary key
when `'All'` is selected, so rely on the documented return shape, not on a
partial dictionary for an individual selector.

## APE

`metric.ape` first constructs and associates `StampedSE3` trajectories. Important
parameters include:

```python
pp.metric.ape(
    rstamp, rpose, estamp, epose,
    etype='translation', diff=0.01, offset=0.0,
    align=False, scale=False, nposes=-1, origin=False,
    thresh=0.3, otype='All')
```

`diff` is the timestamp matching tolerance and `thresh` controls the low-match
warning. Use `etype` to select the error output and `otype` to select the returned
statistic. APE is an absolute, same-time pose error after association and optional
alignment.

## RPE and pair selection

`metric.rpe` has the same association/alignment controls and additionally chooses
relative pairs:

```python
pp.metric.rpe(
    rstamp, rpose, estamp, epose,
    etype='translation', diff=0.01, offset=0.0,
    associate='frame', delta=1.0, rtol=0.1, all=False,
    rpair=False, thresh=0.3, otype='All')
```

`associate='frame'` uses `pairs_by_frames`; `delta` is converted to an integer
frame gap and must be at least one. `associate='distance'` uses
`pairs_by_dist`; `delta` is a path-length step in translation units and `rtol`
becomes the tolerance (`delta * rtol`) in all-pairs mode. `all=True` asks for all
qualifying pairs; otherwise a sparser sequence of pairs is returned. By default
`rpair=False`, so the estimate trajectory selects pairs; `rpair=True` uses the
reference trajectory's pair indices. If no pair is produced, `pair_id` raises a
`ValueError` and the caller should reduce `delta` or relax `rtol`.

RPE is computed from relative motions, so a common global rigid offset should
cancel even though APE can remain nonzero. Use identity/same-trajectory tests to
check zero RPE and a known constant incremental translation to test nonzero
relative error. Do not confuse frame `delta` with seconds or distance `delta`
with a frame count.

## Evidence

- `pypose/metric/ape_rpe.py`
- `pypose/metric/__init__.py`
- `docs/source/metric.rst`
- `tests/function/test_metric.py`

# Matching, grouping, and threshold evaluation

## Single-image matching

```python
matching(y_true, y_pred, thresh=.5, criterion='iou', report_matches=False)
```

Inputs must have equal shape and integer, non-negative labels. Positive IDs need
not be consecutive: matching sequentially relabels them internally and reports
the original IDs. Criteria are `iou` (intersection/union), `iot`
(intersection/true area), and `iop` (intersection/predicted area). An optimal
one-to-one assignment prefers pairs whose score is at least `thresh`, then uses
score as a tie-breaker. A pair is a TP iff its score is `>= thresh`.

The `Matching` named tuple fields are `criterion`, `thresh`, `fp`, `tp`, `fn`,
`precision`, `recall`, `accuracy`, `f1`, `n_true`, `n_pred`,
`mean_true_score`, `mean_matched_score`, and `panoptic_quality`. This version
returns zero for the four detection metrics when `tp == 0`. `accuracy` is
`tp/(tp+fp+fn)` and `f1` is `2*tp/(2*tp+fp+fn)`. `mean_true_score` divides the
accepted-match score sum by all true objects; `mean_matched_score` divides by
TP; panoptic quality uses denominator `tp+fp/2+fn/2`.

With `report_matches=True`, `matched_pairs` and `matched_scores` include every
assigned pair, including below-threshold pairs; `matched_tps` contains the
zero-based positions of accepted pairs. Use `matched_tps` for TP overlays. A
threshold sequence returns a tuple of `Matching` objects; `None` means zero.

## Dataset and grouping

`matching_dataset(y_true,y_pred,thresh=.5,criterion='iou',by_image=False,
show_progress=True,parallel=False)` requires equal-length sequences and returns
a `DatasetMatching` named tuple for a scalar threshold, or a tuple for a
threshold sequence. `by_image=False` aggregates TP/FP/FN and matched scores
before recomputing metrics; `by_image=True` averages per-image metrics.
`matching_dataset_lazy` consumes an iterable of pairs and has the same contract.
Use `show_progress=False` for logs/smoke tests; `parallel=True` uses a thread
pool and should be avoided when deterministic ordering or shared state matters.

`group_matching_labels(ys,thresh=1e-10,criterion='iou')` requires at least two
same-shaped 2D/3D images, copies them to an `int32` output, and greedily matches
consecutive frames. Matched objects inherit the previous group ID; unmatched
objects receive increasing new IDs. It is identity propagation, not global
tracking or geometric registration.

## NMS and threshold concepts

`prob_thresh` filters candidate centers; `nms_thresh` controls overlap between
candidate polygons/polyhedra. Dense NMS uses strict `prob > prob_thresh`, while
3D `polyhedron_to_label` uses inclusive `prob >= thr`. `b` excludes border
candidates in dense NMS; for grid predictions, its coordinates are sampled-grid
coordinates. NMS overlap is intersection divided by the smaller object area or
volume, not union IoU. Record criterion, thresholds, grid, border, candidate
count, survivor count, and backend with every comparison.

```python
optimize_threshold(Y, Yhat, model, nms_thresh, measure='accuracy',
                   iou_threshs=[.3,.5,.7], bracket=None, tol=1e-2,
                   maxiter=20, verbose=1)
```

This utility holds `nms_thresh` fixed and golden-section searches `prob_thresh`.
`Y` is a sequence of ground-truth label images; `Yhat` is a sequence of
`(prob,dist)` predictions; the model's private
`_instances_from_prediction` creates instances. It returns
`(best_prob_thresh,best_measure)`. The default bracket is
`(max_probability/2,max_probability)`; use a bounded explicit bracket and
`verbose=0` for repeatable affordable tuning. The higher-level model
`optimize_thresholds` loops candidate NMS thresholds and belongs to the model
workflow, not this utility sub-skill.

## Evidence and verification

The native candidates are `tests/test_matching.py::test_matching` and
`::test_grouping`, `tests/test_utils.py::test_valid_inds`, the CPU/grid tests in
`tests/test_stardist2D.py` and `tests/test_stardist3D.py`, NMS tests in
`tests/test_nms2D.py` and `tests/test_nms3D.py`, and RGBA assertions in
`tests/test_plot.py`. Use them as evidence; do not copy tests into the runtime
skill.

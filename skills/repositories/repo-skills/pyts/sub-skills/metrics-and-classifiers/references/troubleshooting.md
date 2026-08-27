# Metrics and Classifier Troubleshooting

## scikit-learn compatibility break

**Symptoms**
- `dtw` fails with `TypeError: check_array() got an unexpected keyword argument 'force_all_finite'`.

**Likely causes**
- The installed scikit-learn is too new for the current pyts snapshot.

**What to do next**
1. Use a tested scikit-learn version such as `1.5.2` for this snapshot.
2. Re-run `python -m pip check` and the metrics smoke script after changing the
   dependency.
3. Record the compatible version in the generated skill's troubleshooting
   notes.

## DTW region and shape errors

**Symptoms**
- `dtw` or the lower-bound helpers reject a region array or the input shapes.

**Likely causes**
- The region shape does not match the pair of series.
- `boss` was called on 2D data instead of a 1D pair of equal shape.

**What to do next**
1. Use `sakoe_chiba_band` or `itakura_parallelogram` to build the region.
2. Confirm that `boss(x, y)` receives two one-dimensional arrays.
3. Match the region shape to the lengths of the two series before retrying.

## `show_options` confusion

**Symptoms**
- `show_options` appears to print nothing in a smoke script.

**Likely causes**
- `disp=True` is still in effect, or the caller is not inspecting the returned
  string.

**What to do next**
- Call `show_options(method, disp=False)` and print or log the returned text.

## Slow classifiers or first-run delays

**Symptoms**
- `KNeighborsClassifier(metric='dtw')`, `TSBF`, or `LearningShapelets` is slow.
- The first call takes longer than the rest.

**Likely causes**
- DTW is computationally heavier than Euclidean distance.
- Numba or optimization code may have a first-run compilation cost.
- `LearningShapelets` and some tree/ensemble classifiers are heavier by design.

**What to do next**
1. Use tiny subsets when you just need a smoke test.
2. Treat `LearningShapelets` as an advanced workflow rather than a quick check.
3. If the metric path is the issue, simplify to the raw `KNeighborsClassifier(metric='dtw')` baseline first.

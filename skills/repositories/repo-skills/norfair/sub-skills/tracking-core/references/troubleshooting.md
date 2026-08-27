# Troubleshooting

Use these checks before changing the tracker design.

## Import and install problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: filterpy` while importing `norfair` or `norfair.filter` | Core tracking dependencies are missing | Install the package with its tracking dependencies, or repair the environment before retrying. |
| Optional drawing/video imports fail | OpenCV is missing | Do not use the video/drawing workflows in this sub-skill unless the optional video dependency is installed. Route drawing/video work to [video-visualization](../../video-visualization/). |
| `ImportError` when calling `Video` or drawing helpers | OpenCV is not present | This sub-skill only covers core tracking. Install the video extra or route the task elsewhere. |
| `pip install` changed the wrong environment | You are using a different Python runtime than the one running the task | Use the same Python for installation and smoke checks; verify with `python -c "import sys, norfair; print(sys.version); print(norfair.__version__)"`. |

## Invalid point shapes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError` from `validate_points` | Rank > 2 input was passed as detection points | Reshape to `(n_points, n_dimensions)` or use a rank-1 single-point array. |
| `AttributeError` while constructing `Detection` | A plain list was passed instead of a NumPy array | Convert detector outputs with `np.asarray(...)` before building `Detection`. |
| Tracker or distance crashes with shape mismatches | Different detections use incompatible point counts or dimensionality | Keep a consistent point layout within each tracker stream or per label. |
| `iou` assertion error | Box points are not in `xyxy` form after flattening | Pass box corners in a consistent order such as `[[x_min, y_min], [x_max, y_max]]`. |

## Bad distance configuration

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Invalid distance ...` | Unsupported distance name | Use a built-in name from [API reference](api-reference.md#distance-helpers) or pass a callable.
| Custom `VectorizedDistance` object does not work with `Tracker` | `Tracker` only accepts a string or a callable; it wraps callables as scalar distances | Use a built-in name, a scalar callable, or another design that stays inside the accepted tracker signature. |
| Tracker warnings about scalar distance speed | A custom callable was used | This is not an error; switch to a built-in vectorized metric if speed matters. |
| No matches even though objects are close | `distance_threshold` is too small or the wrong metric was chosen | Start with a higher threshold, then narrow it down after checking the output. |
| Unwanted long-range matches | `distance_threshold` is too large | Lower the threshold or switch to a more selective metric. |

## NaN distance failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Received nan values from distance function` | The custom distance returned `NaN` for one or more candidate/object pairs | Return a finite float instead. Use `np.inf` to mean “do not match”. |

Checklist:

- Guard divisions and normalizations.
- Check for empty embeddings or missing data.
- Make the distance function total for all label-compatible candidate/object pairs.

## Label mismatch problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Objects from different classes are being associated | Labels are missing or inconsistent | Set `Detection.label` consistently for every class you want separated. |
| Mixed labeled/unlabeled detections behave oddly | Some detections have labels and others do not | Either label everything or label nothing for that tracker stream. |
| ReID fails to recover across classes | ReID still respects labels through the matching pipeline | Keep the same label for the same semantic class across the entire recovery sequence. |

Notes:

- Scalar distances skip label mismatches directly.
- Vectorized distances still apply label gating, so labels should be consistent regardless of distance family.

## Lifecycle counter issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tracks appear too late | `initialization_delay` is too high | Lower it. |
| Tracks vanish too early | `hit_counter_max` is too low | Raise it. |
| One-point tracks flicker | `pointwise_hit_counter_max` is too low or the detector skips too many frames | Raise the counter or reduce frame skipping. |
| Tracker seems to lag after skipped frames | `period` does not match the skip interval | Pass the correct `period` on detection frames and still call `update()` on skipped frames. |
| `current_object_count` drops to zero but `total_object_count` stays high | Objects were created and then expired | This is expected. `total_object_count` counts initialized objects ever created. |

## ReID recovery pitfalls

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Occluded object never comes back | `reid_distance_function` is missing or `reid_hit_counter_max` is not set | Enable both the distance function and the ReID lifetime. |
| ReID never merges a recovered candidate | `reid_distance_threshold` is too strict or appearance embeddings are too weak | Loosen the threshold or improve the embedding signal. |
| ReID keeps returning the wrong identity | Spatial and appearance cues disagree | Increase appearance quality, lower the spatial threshold, or add label filtering. |
| ReID candidate disappears before merging | `initialization_delay=0` or the candidate never becomes a matched initializing object | Use a positive initialization delay for recovery workflows. |
| `last_detection.embedding` is missing | Embeddings were never attached to detections | Store the appearance cue on each `Detection` or use `past_detections` to recover a previous embedding. |

Practical ReID checklist:

1. Keep the same `label` for the full object class.
2. Attach a stable appearance cue to `Detection.embedding`.
3. Set `past_detections_length > 0`.
4. Set `reid_hit_counter_max` high enough for the expected occlusion length.
5. Start with a conservative `reid_distance_threshold` and widen only if needed.

## Cutout and debug helper issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `get_cutout` returns an empty crop | The points are outside the image or the min/max box collapses | Clip or validate the points before cropping. |
| `print_objects_as_table` crashes on `None` | At least one object has no numeric `last_distance` yet | Call it after a successful match or print object fields manually. |

## Coordinate transformation issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `get_estimate(absolute=True)` raises | No coordinate transformation was provided to the tracker | Only request absolute estimates after passing `coord_transformations=` to `update()`. |
| Update with camera motion fails when no detections were produced | `coord_transformations` was passed together with `detections=None` | Pass `detections=[]` on that frame so the tracker can still apply the transformation. |

## If you still cannot recover

- Verify that detector outputs are already converted to `Detection`.
- Verify that all detections in the same tracker stream use the same point ordering.
- Verify that the distance function returns a finite scalar for every comparable pair.
- Verify that the labels, thresholds, and `period` values match the real frame cadence.
- If the issue is about drawing, video output, or evaluation metrics, route out of this sub-skill to the linked specialized sub-skills.

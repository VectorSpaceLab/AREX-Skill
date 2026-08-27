# Skeleton data troubleshooting

Use [the data-preparation router](../SKILL.md) to choose scope, then
[data-formats.md](data-formats.md) for schema and
[transforms.md](transforms.md) for pipeline semantics. Each recovery action
below is read-only until the user explicitly chooses how to regenerate or
rewrite source data.

## Validator errors

- **Missing or non-object `info`, `annotations`, or `category_id`:** inspect
  the named file and top-level type. A sample needs all three keys; do not
  paper over a missing label with a guessed class. Use `-1` only for an
  intentionally unlabeled sample.
- **Bad resolution or counts:** use positive finite `[width,height]`, a
  positive integer `num_frame`, and a positive integer `num_keypoints`. A
  builder that emitted `num_keypoints: -1` had no usable detections; regenerate
  or exclude it rather than letting NumPy allocate an invalid shape.
- **Unsupported, duplicate, or empty channels:** channel names must be unique
  and drawn from `x`, `y`, `score`, and `visibility`; the point row length must
  equal the channel count. For the documented 2-D normalization and camera
  augmentation, require `x` and `y`, and for visibility masking provide
  `score` or `visibility`.
- **Keypoint count mismatch:** identify the exact annotation index and frame.
  Fix the producer or split the sample by a genuinely different skeleton
  layout; do not truncate or pad points silently.
- **Non-finite values:** replace NaN/Infinity at the producer boundary with a
  documented missing-joint policy, preferably zero plus a score/visibility of
  zero. Do not rely on JSON parsers accepting non-standard numeric literals.
- **Out-of-range or duplicate slots:** frame indices are zero-based and below
  `num_frame`; effective person slots are non-negative and below configured
  `num_track`. Duplicate frame/person records would overwrite in the loader,
  so resolve them by choosing a source record or changing the tracking policy.

## Categories

A category mapping has ordered `categories` and filename-keyed `annotations`.
The mapping key should match `info.video_name`; if it is absent, the validator
tries the input filename and its stem. A mapping ID must be an integer in the
category list and agree with the sample. A missing mapping is not automatically
an error: the documented video builder writes `category_id: -1`. If a sample
has a non-negative label but no mapping, verify whether the sample was labeled
independently; supply a mapping for cross-checking or omit the mapping file.
Do not turn `-1` into a training class—recognition loss expects valid class
indices.

## Loader and pipeline failures

- **`KeyError` during load:** run the validator first; the loader directly
  indexes required keys and does not provide schema diagnostics.
- **Broadcast/transpose error:** compare `len(keypoint_channels)` with every
  keypoint row and `num_keypoints` with every annotation. The source rows are
  `(V,C)`, the loader result is `(C,V,T,M)`, and the recognition permutation is
  `(C,T,V,M)`.
- **Wrong number of persons:** `person_id` takes precedence over `id` unless
  null. Configure `num_track` for the model and validate with the same bound.
  The loader silently ignores positive slots at or above `num_track`; treat
  that as a data-loss risk, not a feature.
- **Missing joints look nonzero:** sparse unannotated slots are initialized to
  zero. Run `mask_by_visibility` when score/visibility zero means missing, and
  verify that normalization does not make empty coordinates look like valid
  centered coordinates.
- **Temporal size is unexpected:** `pad_zero` only pads; `random_crop` only
  crops sequences longer than the target; `temporal_repeat` reflects short
  sequences. Apply them before transposing, and remember random stages are
  stochastic.
- **Camera augmentation raises `NotImplementedError`:** its source contract
  requires `keypoint_channels[0:2] == ['x','y']`. Reorder channels at the data
  producer or omit this augmentation; do not blindly swap tensor axes.
- **`to_tuple` loses metadata:** place all metadata-dependent stages first and
  ensure the requested keys exist. The recognition default is
  `[data, category_id]`; analysis configs may intentionally choose `[data,
  mask]`.

## Boundary and environment cases

- **Raw video or no skeleton JSON:** stop here and route extraction to
  `pose-estimation`. The detector/HRNet path is optional and its runtime is not
  proven by this core data skill.
- **ST-GCN graph/model mismatch:** route to the [recognition sub-skill](../../recognition/SKILL.md).
  This skill can report `V` and `C`, but it does not choose `openpose`,
  `coco`, or `ntu-rgb+d`, and it must not silently reshape a 17/18/25-joint
  sample.
- **No data directory or mixed files:** point `SkeletonLoader.data_dir` at a
  directory containing the intended JSON samples. The bundled validator
  ignores non-JSON directory entries; keep unrelated JSON files out or validate
  them separately.
- **Detector-produced JSON has no detections:** the build processor can emit
  `num_keypoints: -1`; this is an explicit unverified/invalid handoff for
  recognition. Re-run extraction with the optional dependency gate, or remove
  the sample after recording the failure.

## Safe recovery sequence

1. Copy or version the input outside the runtime skill tree if a repair is
   authorized; never let the validator mutate it.
2. Run the validator on the original file or directory, optionally with
   `--category-annotations` and the intended `--num-track`.
3. Fix the upstream producer or mapping, then rerun validation and compare
   counts/labels.
4. Load one sample and inspect each pipeline boundary using the axis recipe in
   [transforms.md](transforms.md).
5. Only then hand the validated channel/joint/time/person contract to the
   [recognition sub-skill](../../recognition/SKILL.md) for graph/model and CLI
   configuration.

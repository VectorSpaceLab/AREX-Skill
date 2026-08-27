---
name: data-preparation
description: "It prepares, validates, loads, normalizes, transforms, inspects,
  and customizes MMSkeleton skeleton datasets while preserving loader and
  tensor-axis contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMSkeleton data preparation

Use this skill when the input is already skeleton data, or when a pose
extraction result must be checked before recognition. It covers the JSON
annotation contract, category labels, the `SkeletonLoader`/`DataPipeline`
boundary, and the transforms exposed as `datasets.skeleton.*`.

## Route first

- Read [data-formats.md](references/data-formats.md) before authoring or
  loading JSON. Run the bundled [validator](scripts/validate_skeleton_json.py)
  on a file or directory before training or evaluation.
- Read [transforms.md](references/transforms.md) when selecting normalization,
  masking, temporal sampling, axis permutation, or tuple conversion. Preserve
  the distinction between annotation keypoint lists and model tensors.
- Read [troubleshooting.md](references/troubleshooting.md) when validation,
  loading, or a pipeline stage fails.
- Route ST-GCN graph/model construction, checkpoint use, and recognition train
  or test commands to the `recognition` sub-skill. Route raw-video detector
  extraction, MMDetection, or HRNet work to the `pose-estimation` sub-skill;
  hand its produced JSON back here for validation. This skill does not claim
  detector execution.

## Operating procedure

1. Treat each JSON object as one sample. Check `info`, `annotations`, and
   `category_id`, then check every annotation's frame, effective person slot,
   channel count, and finite numeric value. Use `--num-track` when the target
   loader configuration has a known person-slot limit.
2. Configure `SkeletonLoader` with the JSON directory, `num_track`, and (only
   when it exactly matches the file) `num_keypoints`. The loader allocates
   `(C, V, T, M)` float32 data and fills sparse `(channel, joint, frame,
   person)` locations with zeros. It uses `person_id` when present and falls
   back to `id` when `person_id` is null; avoid relying on the loader's silent
   dropping of out-of-range records.
3. Apply transforms in a deliberate order: resolution normalization, optional
   visibility masking, temporal sizing/augmentation, then the explicit axis
   permutation expected by the model and `to_tuple`. The common ST-GCN path
   changes `(C,V,T,M)` to `(C,T,V,M)` and batching adds `N`, yielding
   `(N,C,T,V,M)`.
4. For a custom feeder, keep the same boundary: a data source used by
   `DataPipeline` should return a mutable sample dictionary with `data` and
   `category_id`, and pipeline stages should finish with the tuple expected by
   the consumer. A feeder that bypasses `DataPipeline` must document and return
   the consumer's exact tensor/label contract rather than guessing axes.
5. Inspect masks and channel statistics with the dataset-analysis pipeline
   only after the sample shape and visibility semantics are known. Do not use
   an unknown graph layout or silently pad a joint-count mismatch; route those
   model decisions to the `recognition` sub-skill.

## Fast checks

```text
python scripts/validate_skeleton_json.py --help
python scripts/validate_skeleton_json.py --input path/to/sample.json
python scripts/validate_skeleton_json.py --input path/to/dataset --category-annotations path/to/categories.json --num-track 2
```

The validator is read-only, reports file and annotation locations, accepts a
missing category mapping only when the sample label is `-1`, and exits nonzero
for malformed or unsafe data. Its exact checks and category matching rules are
in [data-formats.md](references/data-formats.md).

## Internal references

- [Data formats and loader contract](references/data-formats.md)
- [Transforms and axis recipes](references/transforms.md)
- [Troubleshooting and recovery](references/troubleshooting.md)
- [Read-only JSON validator](scripts/validate_skeleton_json.py)

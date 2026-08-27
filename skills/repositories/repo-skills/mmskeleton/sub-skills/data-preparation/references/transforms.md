# Skeleton transforms and axis recipes

Start at [the data-preparation router](../SKILL.md). The data structure and
category rules are in [data-formats.md](data-formats.md); failure recovery is
in [troubleshooting.md](troubleshooting.md). These names are the registered
`datasets.skeleton.*` stages used by a `DataPipeline`.

## Recommended ordering

A safe recognition-oriented sequence is:

1. Load JSON into `(C,V,T,M)` with `SkeletonLoader`.
2. Normalize coordinates by the declared resolution, or use explicit channel
   statistics with a mask-aware variant.
3. Mask missing joints from score/visibility if the data carries that signal.
4. Make the temporal length deterministic (`pad_zero` then `random_crop`, or
   `temporal_repeat` when reflected repetition is intended).
5. Apply training-only augmentation such as `simulate_camera_moving`.
6. Transpose to `(C,T,V,M)` with `[0,2,1,3]` for the standard ST-GCN path.
7. Convert to `(data, category_id)` with `to_tuple`.

Do not normalize before identifying channel names, do not apply random
augmentation to an evaluation pipeline unless reproducibility is intended,
and do not transpose twice. The model-side graph/layout and `in_channels`
choice belongs to the [recognition sub-skill](../../recognition/SKILL.md).

## Coordinate and mask stages

### `normalize_by_resolution`

For each channel named `x`, replace `x` with `x / resolution[0] - 0.5`; for
`y`, use `y / resolution[1] - 0.5`. Other channels, including `score` and
`visibility`, are unchanged. This stage mutates `data['data']` and expects
resolution order `[width, height]`, not `[height, width]`.

### `get_mask` and `mask`

`get_mask(data, mask_channel, mask_threshold=0)` stores a one-channel boolean
mask where the selected channel is greater than the threshold. `mask(data)`
multiplies all data channels by that mask. This is useful for analysis or for a
pipeline that wants to retain the mask as a second tuple item.

### `mask_by_visibility`

For every channel named `score` or `visibility`, values equal to zero mark
missing points; the corresponding locations in the other channels are set to
zero. It acts on the loaded tensor and does not produce a separate mask. Use a
single, well-defined visibility signal when possible, and inspect the result
when a sample has both `score` and `visibility` channels.

### `normalize` and `normalize_with_mask`

`normalize(data, mean, std)` broadcasts the supplied per-channel statistics
across all remaining axes: `(C,V,T,M)` or the same number of dimensions after
a deliberate permutation. Supply one mean and standard deviation per channel
and never use a zero standard deviation. `normalize_with_mask` first makes a
mask from the selected channel, normalizes, then zeros masked positions. The
statistics must match the channel order in the JSON; the documented Kinetics
recipe uses `[x, y, score]` statistics, while a custom channel order needs
custom statistics.

## Temporal transforms

All temporal helpers operate on axis 2 while the data is in loader layout
`(C,V,T,M)`. Apply them before the standard `[0,2,1,3]` permutation.

### `temporal_repeat(data, size, random_crop=False)`

- If `T >= size`, it takes the first `size` frames, or a random contiguous
  window when `random_crop=True`.
- If `T < size`, it builds a reflected index sequence (forward frames followed
  by the interior in reverse), tiles it, and truncates to `size`.
- It does not create new pose values; it reuses frames. For a one-frame input,
  the source implementation cannot construct its reflected period safely, so
  prefer `pad_zero` or reject that case before calling it.

Use this when repeated motion is preferable to stationary zero padding. Keep
`size` positive and make the choice deterministic for evaluation.

### `pad_zero(data, size)`

If `T < size`, allocate a zero-filled tensor of the same dtype and copy the
sequence into its first `T` slots. If `T >= size`, it leaves the sequence
unchanged; it is not a crop. Follow it with `random_crop` or an explicit crop
when a fixed length is required.

### `random_crop(data, size)`

If `T > size`, select a random contiguous window of length `size`; otherwise
leave the sequence unchanged. It can therefore return a shorter-than-requested
sequence when used without `pad_zero`. Seed the Python random generator in the
caller when reproducibility matters.

### `simulate_camera_moving`

This training augmentation requires the first two channels to be exactly
`x` and `y`, applies a smooth random affine motion over time, and changes only
those coordinate channels. It is safest after coordinate normalization and
before axis permutation. It is not a substitute for raw-video camera
calibration.

## Axis and tuple transforms

### `transpose(data, order, key='data')`

This calls the array transpose with the supplied permutation. For a loader
sample, `order=[0,2,1,3]` means `(C,V,T,M) -> (C,T,V,M)`. Confirm the current
shape before applying another permutation; an already batched tensor has an
additional leading `N` and requires a different operation.

### `to_tuple(data, keys=['data', 'category_id'])`

Returns a tuple in the requested key order. The default is exactly
`(data['data'], data['category_id'])`, which is what the recognition processor
consumes. For dataset analysis, a config may select `[data, mask]` instead.
Do not call it before stages that need the metadata dictionary.

## Inspecting a pipeline

For a new dataset, inspect one sample after each conceptual boundary:

- before loading: annotation `(V,C)` rows and category label;
- after loading: finite `(C,V,T,M)` tensor and sparse zero locations;
- after normalization/masking: coordinate range and invalid-joint zeros;
- after temporal processing: exact `T` and whether repetition or padding was
  intended;
- after transpose: `(C,T,V,M)` and channel count;
- after tuple conversion: label dtype/range and consumer compatibility.

If any observation disagrees with the model's expected `(N,C,T,V,M)`, stop and
route the graph/joint-count decision to the [recognition sub-skill](../../recognition/SKILL.md)
rather than inserting a silent reshape.

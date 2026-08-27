# Skeleton JSON and loader contract

Return to [the data-preparation router](../SKILL.md) for scope and routing. Use
[transforms.md](transforms.md) after the sample has passed these checks, and use
[troubleshooting.md](troubleshooting.md) for recovery. The executable
[validator](../scripts/validate_skeleton_json.py) implements the strict,
read-only checks described here.

## Sample JSON

A sample is a JSON object with these top-level keys:

- `info`: metadata for the sequence.
- `annotations`: a list of sparse person detections/poses.
- `category_id`: an integer class index, or `-1` when no category is known.

The required `info` members are:

| Member | Contract |
|---|---|
| `resolution` | Two finite positive numbers `[width, height]`; x is divided by width and y by height. |
| `num_frame` | Positive integer number of valid frame slots. Valid frame indices are `0` through `num_frame - 1`. |
| `num_keypoints` | Positive integer joint count. Every annotation must contain exactly this many joints. |
| `keypoint_channels` | Non-empty list of unique supported names: `x`, `y`, `score`, and/or `visibility`. `x` and `y` are required for the documented 2-D normalization path. |

`version` and `video_name` are useful metadata and are preserved by the
loader, but are not needed to allocate its tensor. If present, `version` should
be a string and `video_name` should be a string. Do not use a negative
`num_keypoints`: a no-detection builder output with `-1` cannot be loaded
safely.

Each annotation must contain:

```json
{
  "frame_index": 0,
  "id": 0,
  "person_id": null,
  "keypoints": [[x, y, score], [x, y, score]]
}
```

`frame_index` and `id` are non-negative integers. `person_id` is either null
or a non-negative integer. The effective person slot is `person_id` when it is
not null, otherwise `id`. `keypoints` is a list of exactly `num_keypoints`
points; each point has exactly one finite numeric value per channel, in the
same order as `info.keypoint_channels`. Coordinates are not forced into the
image rectangle because detector and tracking pipelines can produce boundary
or slightly out-of-frame values; they must still be finite.

If a known loader setting has `num_track=M`, every effective person slot must
be in `[0, M)`. Without that setting, the validator checks non-negative person
indices but cannot invent an upper bound. The loader's own condition only
checks the upper bound and can therefore mis-handle negative indices as Python
negative array indices; reject negative values before loading. Duplicate
`(frame_index, effective person slot)` records are rejected because the loader
would silently overwrite one with the other.

## Source lists versus model tensors

The JSON representation is annotation-oriented: one annotation contains a
`(V, C)` list, where each joint is a row and each row follows the named channel
order. It is **not** a flattened model tensor and it does not include empty
frames/persons explicitly.

`SkeletonLoader` reads one JSON sample and allocates zero-filled float32 data
with shape `(C, V, T, M)`:

- `C = len(keypoint_channels)`;
- `V = info.num_keypoints` unless an explicit loader override is supplied;
- `T = info.num_frame`;
- `M = num_track`.

For each annotation it transposes the point list from `(V, C)` to `(C, V)`
and writes it into its frame/person slot. Missing detections remain zero.
The loader returns the original sample dictionary with the generated `data`
member, so metadata and `category_id` remain available to pipeline stages.
An override of `num_keypoints` must exactly agree with annotation lengths; it
is not a safe resize operation.

The standard ST-GCN configuration applies `transpose(order=[0, 2, 1, 3])`,
which changes the per-sample layout to `(C, T, V, M)`. The model receives a
batch `(N, C, T, V, M)`. Keep `V` aligned with the selected graph layout and
`C` aligned with the model's `in_channels`; graph and model selection belongs
to the `recognition` sub-skill, not to this validator.

## Categories

An optional category-annotation file has this shape:

```json
{
  "categories": ["skateboarding", "clean_and_jerk", "ta_chi"],
  "annotations": {
    "clip.mp4": {"category_id": 0}
  }
}
```

`categories` is an ordered list, so valid IDs are `0` through
`len(categories)-1`. The per-file mapping uses the source `video_name` when
available; the validator also tries the input filename and its `.json`-free
stem. If a mapping entry exists, its ID must equal the sample's
`category_id`. If no mapping entry exists, the documented build behavior is
`category_id: -1`; the validator accepts that missing-category state and
rejects a positive label that contradicts it. If no category file is supplied,
any non-negative sample label is structurally valid but cannot be cross-checked.

The category file itself is checked for a list of string categories, an object
of annotations, integer IDs, and IDs within the category list. This catches a
bad mapping before it can contaminate a directory run.

## Custom feeder boundary

A custom skeleton source can replace the default source through the normal
configuration object-resolution mechanism. Preserve these observable
contracts:

1. `__len__` returns the number of samples.
2. `__getitem__` returns a sample dictionary when it is wrapped by
   `DataPipeline`; it must provide `data` and `category_id` before a final
   `to_tuple` stage.
3. The final pipeline output is `(data, category_id)` by default, or an
   explicitly documented tuple selected with `to_tuple(keys=[...])`.
4. `data` must have the axes and channel count expected by the downstream
   model. A custom annotation format may be parsed at this boundary, but it
   must not quietly change `(C,V,T,M)` or the post-transpose
   `(C,T,V,M)` contract.

If the requested feeder needs ST-GCN graph/model or recognition CLI changes,
route the model-side work to the `recognition` sub-skill. If it starts from raw
video or detector output, route extraction to the `pose-estimation` sub-skill,
then validate the resulting JSON here.

## Validator behavior

The validator takes `--input FILE_OR_DIRECTORY`, optionally
`--category-annotations FILE`, and optionally `--num-track M`. A directory
run checks sorted `.json` files without modifying them. It emits actionable
errors with the file and annotation index, returns zero only when all checked
samples and the optional category mapping are valid, and never rewrites JSON.

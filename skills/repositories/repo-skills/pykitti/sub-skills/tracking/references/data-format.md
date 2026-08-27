# KITTI tracking label data format

## File layout and row schema

The tracking label/detection files are frame-indexed text files. The source
parser treats the **first token as the frame index** (`DataFrame.index`) and
maps the remaining tokens to `KittiTrackingLabels.columns`:

```text
id class truncated occluded alpha x1 y1 x2 y2 xd yd zd x y z roty score
```

The fields are:

| Field | Meaning | Typical representation |
|---|---|---|
| `id` | track or detection identity | integer before normalization |
| `class` | object category | string |
| `truncated` | truncation amount/flag | numeric |
| `occluded` | occlusion level | integer-like |
| `alpha` | observation angle | numeric |
| `x1 y1 x2 y2` | image bounding-box corners | pixel coordinates |
| `xd yd zd` | object dimensions | dataset-provided 3-D values |
| `x y z` | object location | dataset-provided 3-D values |
| `roty` | object rotation around vertical axis | numeric |
| `score` | optional detector confidence | numeric, detection files only |

Consequently:

- A ground-truth **label** row has **17 total tokens**: frame index plus the
  first 16 payload fields through `roty`. After `index_col=0`, pandas sees 16
  columns and the source assigns `columns[:16]` (no `score`).
- A **detection** row has **18 total tokens**: frame index plus all 17 payload
  fields, including `score`. After `index_col=0`, pandas sees 17 columns and
  the source assigns all 17 names.

The parser uses `sep=' '` and `skip_blank_lines=True`. Keep one row per object,
retain the frame token even when it is zero, and ensure every numeric field is
parseable. The parser does not robustly validate a malformed row before column
assignment; a wrong token count can fail in pandas or later property access.

The source declares these class names:

```text
Car Van Truck Pedestrian Person_sitting Cyclist Tram Misc DontCare
```

`class` is not normalized. `remove_dontcare=True` removes only rows whose value
is exactly `DontCare`; spelling or casing variants remain. Truncation and
occlusion thresholds are currently commented out, so those fields are retained
but not filtered.

## DataFrame input contract

A DataFrame input is already expected to have:

- its frame number in the index;
- an `id` column;
- a `class` column;
- the numeric/label columns needed by any property to be used.

Use the canonical names above. A minimal full label frame has the 16 columns
through `roty`; a detection frame can add `score`. The constructor does not
insert a frame column, infer missing names, or fill missing values. It may
coerce NumPy `float64` columns to `float32` and `int64` columns to `int32`.

The constructor normalizes IDs after filtering. It maps unique source IDs in
first-seen order to `0, 1, ..., n-1`; this is not the same as preserving the
KITTI source ID. If the default filter removes every row, ID normalization
cannot compute a maximum and construction fails. Make empty/all-`DontCare`
inputs an explicit preflight case rather than expecting an empty result.

## Output shape and coordinate semantics

`labels.bbox` selects the columns `id, x1, y1, x2, y2`, then passes them to
`to_array_list`, which sorts by normalized ID and removes `id` from a
multi-column result. Therefore each object row has four values, not five:

- with `bbox_with_size=True` (default): `[x1, y1, x2 - x1, y2 - y1]`;
- with `bbox_with_size=False`: `[x1, y1, x2, y2]`.

For equal object counts in all contiguous frames, the usual numeric shape is
`(n_frames, n_objects, 4)`. The source comment says the size conversion still
needs fixing, but this subtraction behavior is what 0.3.1 performs. It does
not clip boxes, reorder axes, or validate positive width/height.

`labels.cls` and `labels.occlusion` similarly remove the temporary ID during
conversion. Their common shape is `(n_frames, n_objects, 1)` and values are
sorted by normalized ID. `labels.presence` is different: it is a boolean matrix
of shape `(max_frame_index + 1, max_objects)`, with true at each observed
`[frame, normalized_id]` location. A missing frame is all false when the
presence matrix can be constructed.

`labels.id` is currently unsafe: it passes a Series to `to_array_list`, whose
`by_id=True` path accesses `.columns`; pandas Series has no `.columns`. Probe
before use and prefer the normalized IDs visible through `presence`/other
sorted outputs or a separately prepared DataFrame. `labels.num_objects` is
also version-sensitive because its implementation calls legacy pandas
`Series.append` and `as_matrix`; it is not a guaranteed pandas 3 API.

## Missing frame indexes and reappearance

`to_array_list` assumes non-negative, zero-based frame indexes. If `length` is
omitted, it chooses `max(index) + 1`. If `length` is supplied, it creates that
many slots and leaves unobserved positions as `np.empty(0)`. A slot index at or
after `length` raises `IndexError`.

That representation becomes a compatibility hazard when converted with
`np.asarray`: if some frames are empty or object counts differ, current NumPy
can reject the ragged list with `ValueError: setting an array element with a
sequence`. Do not promise padded dense arrays for missing indexes; preflight
continuity and catch the conversion error. `split_on_reappear=True` can itself
create different per-frame object counts, making this issue more likely.

For label objects, splitting examines each normalized ID's frame presence. A
gap larger than one causes rows after the gap to receive a new normalized ID.
The implementation assumes frame-sorted rows and uses pandas label slicing
internally; unusual or duplicated indexes should be treated as unsupported.

# Tracking API reference

This reference records the observable label API in `pykitti==0.3.1`. The
package is old relative to current pandas/NumPy releases, so the compatibility
limits below are part of the contract rather than implementation trivia.

## Public entry points

```python
from pykitti.tracking import KittiTrackingLabels, to_array_list

KittiTrackingLabels(
    path_or_df,
    bbox_with_size=True,
    remove_dontcare=True,
    split_on_reappear=True,
)
to_array_list(df, length=None, by_id=True)
```

`KittiTrackingLabels` accepts either a path or a pandas `DataFrame`:

- For a path, it checks `os.path.exists`, then calls `pandas.read_csv` with
  `sep=' '`, `header=None`, `index_col=0`, and `skip_blank_lines=True`.
  The first token on each line becomes the DataFrame index (the frame number).
- For a DataFrame, the existing index is treated as the frame number and the
  existing column names are used as-is. Supply the names required by the
  selected properties; the constructor does not rename arbitrary columns.
- The source first assigns the DataFrame reference, but its default
  `remove_dontcare=True` row filter creates a derived frame. Do not rely on
  the caller's DataFrame being normalized in place. With filtering disabled,
  the later ID replacement can mutate the supplied frame on versions where
  pandas preserves the reference.

The constructor performs type conversions when a column has exactly the
expected NumPy float or integer dtype, removes `DontCare` rows when requested,
normalizes IDs, and optionally splits an ID when it reappears after a gap.
It does not validate every required column up front.

## Label and detection columns

`KittiTrackingLabels.columns` contains the 16 payload names:

| Position after frame index | Name | Meaning |
|---:|---|---|
| 0 | `id` | source track/detection identity |
| 1 | `class` | KITTI object class string |
| 2 | `truncated` | truncation fraction/flag from the label |
| 3 | `occluded` | occlusion level |
| 4 | `alpha` | observation angle |
| 5--8 | `x1`, `y1`, `x2`, `y2` | image bounding-box corners |
| 9--11 | `xd`, `yd`, `zd` | 3-D dimensions as supplied by KITTI |
| 12--14 | `x`, `y`, `z` | 3-D location as supplied by KITTI |
| 15 | `roty` | object yaw as supplied by KITTI |
| 16 | `score` | optional detector confidence |

The source uses the first whitespace-separated token as the frame index, so a
normal **label** line has 17 total tokens: frame plus the 16 payload values
through `roty`, with no `score`. A **detection** line has 18 total tokens:
frame plus all 17 payload names, including `score`. After `index_col=0`, the
label DataFrame has 16 columns and the detection DataFrame has 17 columns; the
code assigns the corresponding prefix of `columns`. Do not add a fake score to
a label file or assume the score is exposed by a dedicated property.

The declared class vocabulary is:

```text
Car Van Truck Pedestrian Person_sitting Cyclist Tram Misc DontCare
```

`remove_dontcare=True` is the default and removes rows whose `class` is exactly
`"DontCare"`. It does not remove truncated or occluded objects: the source's
threshold variables are unused. `remove_dontcare=False` retains such rows and
they participate in ID normalization and all array outputs.

## Normalization and frame metadata

After filtering, IDs are remapped in first-seen order to contiguous zero-based
IDs. For example, source IDs `[42, 7]` become `[0, 1]`; the original values are
not retained in the public `id` column. The input must contain at least one
usable row and an `id` column. An all-`DontCare` file with the default filter
reaches `max()` on an empty ID array and fails instead of producing an empty
label object.

The public metadata is:

| Attribute | Behavior |
|---|---|
| `ids` | list of normalized IDs; reappearing tracks can add IDs |
| `max_objects` | number of IDs after optional splitting |
| `index` | unique frame index values from the filtered DataFrame, in pandas' observed order |
| `len(labels)` | `last_index - first_index + 1`; it is not necessarily the number of unique index values |

For ordinary use, sort the DataFrame by a non-negative, zero-based frame index
before constructing the object. The implementation assumes this convention;
it does not normalize a nonzero starting frame or validate sortedness.

With `split_on_reappear=True`, the implementation looks for gaps larger than
one between rows of one normalized ID and assigns later segments new IDs. The
result is observable through `ids`, `max_objects`, `presence`, and the internal
normalized `id` column. It is safest when rows are sorted by frame and there is
at most one record for an identity in a frame. Set it to `False` when source IDs
must be preserved as one identity across a temporary absence (noting that IDs
are still renumbered).

## Array properties

All properties below use `to_array_list` unless noted. With a normal contiguous
zero-based index and the same number of records in each frame, they return a
NumPy array whose leading dimension is `max(frame index) + 1`; an empty frame is
represented by an empty array in the source's internal list.

- `bbox`: selects `id, x1, y1, x2, y2`, then removes `id` while grouping by ID.
  With the default `bbox_with_size=True`, it mutates the selected copy so the
  four values are `[x1, y1, x2 - x1, y2 - y1]` (top-left plus width/height),
  despite the source TODO comment saying this should be fixed. With
  `bbox_with_size=False`, the values are `[x1, y1, x2, y2]`. The usual shape
  is `[frame, object, 4]`.
- `presence`: a boolean array of shape `(max(frame index) + 1,
  max_objects)`. `presence[frame, normalized_id]` is true for each row. It
  uses frame numbers directly, so a missing frame is an all-false row and a
  DataFrame starting at frame 5 produces five leading rows. It is not shaped
  from `len(labels)` when the first index is nonzero.
- `cls`: per-frame object class values, usually shape `[frame, object, 1]`
  and `dtype=object`, sorted by normalized ID.
- `occlusion`: per-frame `occluded` values, usually `[frame, object, 1]`,
  sorted by normalized ID.
- `id`: intended to return per-frame ID values, but in 0.3.1 it passes a
  pandas `Series` to `to_array_list`, which immediately accesses `.columns`.
  On the verified pandas 3 environment this raises `AttributeError`. Do not
  claim this property is usable without a compatibility probe.
- `num_objects`: intended to return a count per frame, padded for absent
  indexes. It calls the removed pandas `Series.append` and then the removed
  `as_matrix` API. On pandas 3 it fails at `append`; even on older pandas,
  verify behavior rather than treating it as guaranteed.

## `to_array_list` details

`to_array_list` expects a DataFrame with a frame index. Its index is assumed to
be non-negative, zero-based, and contiguous unless the caller supplies a
suitable `length`. For each unique index `i`, it selects `df.loc[i]` and stores
that row group at list position `i`. Positions with no input rows are initially
created as `np.empty(0)`.

When `by_id=True` (the default), an `id` column is required. For a multi-column
DataFrame, rows are grouped with `id` as a temporary index, sorted by ID, and
the ID column is omitted from the returned values. If `id` is the only column,
the function disables ID sorting/removal and retains the ID values. A
single-row group is handled as a Series; a multi-row group is handled as a
DataFrame. The output is finally passed to `np.asarray`.

That final conversion is important: with current NumPy, missing frame indexes
or different object counts per frame can make the list ragged and raise a
`ValueError` instead of returning an object array. An explicit `length` only
controls the list length; it does not pad each frame to a common object count
and does not eliminate this ragged-array risk. Preflight index continuity and
per-frame row counts, or catch and handle this failure outside pykitti.

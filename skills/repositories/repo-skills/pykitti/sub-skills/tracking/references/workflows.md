# Tracking workflows

## 1. Preflight a local label file

Acquire and unpack KITTI data outside the runtime skill. The bundled downloader
is intentionally not part of this skill because it downloads large archives,
invokes external tools, changes directories, and overwrites extraction targets.
For a local training label file, validate the path and a few row invariants
before constructing the parser:

```python
from pathlib import Path

path = Path(label_path)
if not path.is_file():
    raise FileNotFoundError(path)

rows = [line.split() for line in path.read_text().splitlines() if line.strip()]
if not rows:
    raise ValueError("label file is empty")
if any(len(row) not in (17, 18) for row in rows):
    raise ValueError("expected frame + 16 label fields, or frame + 17 detection fields")
frames = [int(row[0]) for row in rows]
if min(frames) < 0 or frames != sorted(frames):
    raise ValueError("use non-negative frame-sorted rows for pykitti tracking labels")
```

The parser itself uses the first token as the index. A label row has 17 tokens
and a detection row has 18; see [data format](data-format.md). Validate frame
and row counts before relying on a dense per-frame array.

## 2. Parse labels and inspect safe outputs

```python
from pykitti.tracking import KittiTrackingLabels

labels = KittiTrackingLabels(
    str(path),
    bbox_with_size=True,
    remove_dontcare=True,
    split_on_reappear=True,
)

print("frame span", labels.index[0], labels.index[-1], "length", len(labels))
print("normalized IDs", labels.ids, "object capacity", labels.max_objects)
boxes = labels.bbox       # typically (frames, objects, 4)
classes = labels.cls       # typically (frames, objects, 1), object dtype
occ = labels.occlusion     # typically (frames, objects, 1)
present = labels.presence  # (max_frame + 1, max_objects), bool
```

The default box rows are `[x1, y1, width, height]`, where width and height
are computed by subtracting the top-left corner from the lower-right corner.
Use `bbox_with_size=False` to retain `[x1, y1, x2, y2]`. The ID is used for
sorting but is not included in the multi-column `bbox`, `cls`, or `occlusion`
array rows.

Do not use `labels.id` or `labels.num_objects` without a live compatibility
probe. In this release `id` passes a Series into a DataFrame-only path, while
`num_objects` uses removed pandas methods on current pandas. If per-frame IDs
or counts are required, derive them from a validated copy of the normalized
DataFrame in a compatibility layer and keep that workaround outside this
skill's claimed API.

## 3. Use a prepared DataFrame

A DataFrame is useful for filtering or deterministic tests. Put frame numbers
in the index and use the canonical columns:

```python
import pandas as pd
from pykitti.tracking import KittiTrackingLabels

frame_df = pd.DataFrame(
    [
        [42, "Car", 0.0, 0, 0.0, 10, 20, 30, 40, 1.5, 1.6, 3.7, 1, 2, 15, 0.1],
    ],
    columns=KittiTrackingLabels.columns[:-1],  # label fields through roty
    index=[0],
)
labels = KittiTrackingLabels(frame_df, split_on_reappear=False)
```

The constructor does not add missing names or a frame column. It can coerce
float64/int64 columns to float32/int32 and remaps source IDs. If the input
contains `DontCare`, default filtering returns a derived filtered DataFrame;
still treat the caller's input as immutable and pass a copy when experimenting.

## 4. Convert a frame-indexed DataFrame directly

Use `to_array_list` when the desired columns are already selected:

```python
import pandas as pd
from pykitti.tracking import to_array_list

df = pd.DataFrame(
    {"id": [2, 1, 1, 2], "value": [20, 10, 11, 21]},
    index=[0, 0, 1, 1],
)
values = to_array_list(df)  # sorted by id; ID column omitted from each row
assert values.shape == (2, 2, 1)
```

For each frame, rows are sorted by `id` when `by_id=True`. Use `by_id=False`
only when no ID sorting/removal is desired; the function still expects a
DataFrame. `length=3` creates slots for frames 0, 1, and 2, but it does not
pad object rows and does not guarantee a dense NumPy result. Current NumPy may
raise on the final `np.asarray` when one of those slots is empty or object
counts differ. Validate the result or catch this known compatibility failure.

## 5. Handle track reappearance deliberately

A track present at frames 0 and 2 with no row at frame 1 is considered
non-contiguous by the default split pass:

```python
labels = KittiTrackingLabels(frame_df, split_on_reappear=True)
```

Use `split_on_reappear=False` when a temporary absence must retain one logical
source ID. Either choice still applies zero-based ID normalization. For
reproducible splitting, sort by frame and keep at most one row per source ID
per frame; duplicated or unsorted indexes interact poorly with the source's
pandas label slicing.

## 6. Treat the `tracking` class as a diagnostic-only surface

The source's tracking constructor discovers only these files under the exact
root passed to it:

```text
<base_path>/image_02/<sequence>/*.png
<base_path>/image_03/<sequence>/*.png
<base_path>/velodyne/<sequence>/*.bin
```

It stores `base_path`, `sequence`, `frames`, and `imtype` (default `png`),
then prints `files <count>` during construction. It does not load label files,
calibration, or timestamps. `cam2`, `cam3`, and `velo` properties are lazy
iterators; `get_cam2`, `get_cam3`, and `get_velo` are indexed readers. The
`gray` property and `get_gray` refer to absent `cam0`/`cam1` attributes, and
`len(dataset)` refers to an uninitialized `timestamps` attribute. Supplying
`frames` reaches absent `cam0_files`/`cam1_files` in `_get_file_lists`.

Use this class only to reproduce or diagnose an existing, deliberately patched
checkout. For actual tracking labels, construct `KittiTrackingLabels` directly
and keep sensor streams in a sibling raw/odometry workflow where applicable.

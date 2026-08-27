---
name: tracking
description: "Parse KITTI tracking labels with pykitti==0.3.1 and assess its
  incomplete tracking loader conservatively."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# KITTI tracking labels

Use this sub-skill primarily for the two usable label utilities in
`pykitti==0.3.1`: `KittiTrackingLabels` and `to_array_list`. They parse local
KITTI tracking/detection records into per-frame arrays; they do not acquire a
dataset and do not repair malformed data.

## Route and boundary

- Use `KittiTrackingLabels(path_or_df, bbox_with_size=True,
  remove_dontcare=True, split_on_reappear=True)` for a label/detection text
  file or a prepared pandas `DataFrame`.
- Use `to_array_list(df, length=None, by_id=True)` for a frame-indexed
  `DataFrame`. Its index is the frame number, not a column.
- Treat `pykitti.tracking(base_path, sequence, **kwargs)` as an incomplete,
  legacy sensor-loader skeleton, not as a verified tracking dataset loader.
  It has no initialized timestamps, prints a file count, and its frame
  sub-selection references missing `cam0_files`/`cam1_files` attributes. See
  [API reference](references/api-reference.md) and
  [troubleshooting](references/troubleshooting.md).
- Use [raw-data](../raw-data/SKILL.md) for raw drives and
  [odometry](../odometry/SKILL.md) for odometry sequences. Read the shared
  [root troubleshooting guide](../../references/troubleshooting.md) for
  installation and package-wide issues.

## Minimal safe route

```python
from pykitti.tracking import KittiTrackingLabels, to_array_list

labels = KittiTrackingLabels(
    "/data/kitti/tracking/training/label_02/0000.txt",
    remove_dontcare=True,
    split_on_reappear=True,
)
print(labels.ids, labels.index, len(labels))
boxes = labels.bbox                 # [frame, object, x1, y1, w, h] by default
classes = labels.cls                # [frame, object, 1] object arrays
visible = labels.presence            # [frame, normalized-id] bool array
```

The text schema, count rules, ID normalization, shape semantics, DataFrame
contract, and current compatibility limits are in the bundled references. Run
the deterministic fixture smoke before using a real file:

```bash
python scripts/labels_fixture_smoke.py --help
python scripts/labels_fixture_smoke.py
```

The normal package import reaches `tracking.py`, which imports `cv2`
eagerly; install a compatible OpenCV package when `import pykitti` or this
module import fails with `ModuleNotFoundError: cv2`. The smoke script performs
only local in-memory checks and has no network or GUI behavior.

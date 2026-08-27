# Detection And Zones Workflows

Use these recipes as operating patterns. They avoid model-download code; plug in the caller's already-prepared model result or callback.

## Normalize model output to `sv.Detections`

### Decision tree

1. If the model already returns `sv.Detections`, use it directly after checking required fields for the downstream operation.
2. If the result is from a supported framework, use the matching `sv.Detections.from_*` adapter.
3. If the result is from a VLM, use `sv.Detections.from_vlm(...)` and provide the image resolution explicitly.
4. If no adapter matches, construct `sv.Detections` manually from aligned NumPy arrays and add metadata in `detections.data`.

### Adapter normalization skeleton

```python
import supervision as sv

# result is produced elsewhere.
detections = sv.Detections.from_ultralytics(result)

# Framework adapters often add class names when the raw result exposes them.
class_names = detections.get_data("class_name")
```

Common replacements:

```python
detections = sv.Detections.from_inference(result)
detections = sv.Detections.from_inference(result, compact_masks=True)
detections = sv.Detections.from_transformers(result, id2label=id2label)
detections = sv.Detections.from_vlm(
    sv.VLM.GOOGLE_GEMINI_2_0,
    response_text,
    resolution_wh=(image_width, image_height),
    classes=["person", "car"],
)
```

Use `from_lmm` only to maintain older code; new code should use `from_vlm`.

## Construct `Detections` manually

Use manual construction when the model output is already in arrays or when writing synthetic tests.

```python
import numpy as np
import supervision as sv
from supervision.config import CLASS_NAME_DATA_FIELD

xyxy = np.array(
    [
        [10.0, 20.0, 110.0, 160.0],
        [200.0, 80.0, 260.0, 180.0],
    ],
    dtype=np.float32,
)
confidence = np.array([0.92, 0.65], dtype=np.float32)
class_id = np.array([0, 2], dtype=int)

# Every data value must align with len(xyxy).
detections = sv.Detections(
    xyxy=xyxy,
    confidence=confidence,
    class_id=class_id,
    data={CLASS_NAME_DATA_FIELD: np.array(["person", "car"])},
)
```

Manual OBB detections need both `xyxy` envelopes and the oriented corners:

```python
import numpy as np
import supervision as sv
from supervision.config import ORIENTED_BOX_COORDINATES

corners = np.array(
    [
        [[20.0, 20.0], [80.0, 15.0], [85.0, 45.0], [25.0, 50.0]],
    ],
    dtype=np.float32,
)
xyxy = sv.xyxyxyxy_to_xyxy(corners)

detections = sv.Detections(
    xyxy=xyxy,
    confidence=np.array([0.9], dtype=np.float32),
    class_id=np.array([1]),
    data={ORIENTED_BOX_COORDINATES: corners},
)
```

## Filter detections

Always filter the `Detections` object, not individual arrays, so `mask`, `tracker_id`, `data`, and `metadata` stay aligned.

```python
# By one class.
people = detections[detections.class_id == 0]

# By multiple classes.
vehicle_ids = np.array([2, 3, 5, 7])
vehicles = detections[np.isin(detections.class_id, vehicle_ids)]

# By confidence.
high_confidence = detections[detections.confidence > 0.7]

# By area. With masks, this is mask area; with OBB, OBB area; otherwise box area.
large_objects = detections[detections.area > 1_000]

# By explicit axis-aligned dimensions.
width = detections.xyxy[:, 2] - detections.xyxy[:, 0]
height = detections.xyxy[:, 3] - detections.xyxy[:, 1]
wide_objects = detections[(width > 200) & (height > 80)]

# Combine masks.
selected = detections[(detections.confidence > 0.7) & np.isin(detections.class_id, [0, 2])]
```

Guard optional fields first when writing reusable utilities:

```python
if detections.confidence is None:
    raise ValueError("This filter needs detections.confidence.")
filtered = detections[detections.confidence >= min_confidence]
```

## Remove or merge duplicate detections

Use the `Detections` methods unless you need a low-level utility function.

```python
# Hard suppression: keep the highest-confidence detection in each overlap group.
detections = detections.with_nms(threshold=0.5)

# Class-agnostic suppression when class IDs are unavailable or intentionally ignored.
detections = detections.with_nms(threshold=0.5, class_agnostic=True)

# Soft-NMS: keeps all detections by default and decays confidence.
detections = detections.with_soft_nms(sigma=0.5)

# Soft-NMS plus real filtering.
detections = detections.with_soft_nms(sigma=0.5, score_threshold=0.25)

# Non-maximum merge: merge overlapping detections into representative boxes/masks/OBBs.
detections = detections.with_nmm(threshold=0.5)
```

Dispatch order for `with_nms` and `with_nmm` is masks first, then OBB corners under `ORIENTED_BOX_COORDINATES`, then axis-aligned `xyxy`. Soft-NMS uses masks when present and otherwise uses `xyxy`.

## Work with CompactMask

Use compact masks for many sparse segmentation masks on high-resolution images or for tiled inference where dense mask stacks are too large.

### Ingest dense or COCO RLE masks

```python
from supervision.detection.compact_mask import CompactMask

compact = CompactMask.from_dense(
    masks=dense_bool_masks,
    xyxy=detections.xyxy,
    image_shape=(image_height, image_width),
)
detections = sv.Detections(
    xyxy=detections.xyxy,
    mask=compact,
    confidence=detections.confidence,
    class_id=detections.class_id,
)
```

```python
compact = CompactMask.from_coco_rle(
    rles=coco_rle_payloads,
    xyxy=xyxy,
    image_shape=(image_height, image_width),
)
```

### Convert an existing dense-mask detections object

```python
compact_detections = dense_detections.to_compact_masks()
```

`to_compact_masks()` preserves all mask pixels by using full-image crops. If you need tight crops later, call `compact_detections.mask.repack()` and accept that trimming is based on currently true pixels.

### Use compact masks safely

```python
if isinstance(detections.mask, sv.CompactMask):
    one_full_mask = detections.mask[0]
    all_full_masks = detections.mask.to_dense()
    crop_only = detections.mask.crop(0)
```

Do not call arbitrary ndarray methods directly on `CompactMask`; materialize with `to_dense()` first.

## Polygon zone occupancy

`PolygonZone` answers: which detections are currently inside this polygon according to configured anchor points?

```python
import numpy as np
import supervision as sv

polygon = np.array([[0, 0], [300, 0], [300, 200], [0, 200]])
zone = sv.PolygonZone(
    polygon=polygon,
    triggering_anchors=[sv.Position.BOTTOM_CENTER],
)

in_zone = zone.trigger(detections)
detections_in_zone = detections[in_zone]
current_count = zone.current_count
```

Multiple anchors default to "all anchors must be inside". Switch to "any anchor" mode for more permissive occupancy:

```python
zone = sv.PolygonZone(
    polygon=polygon,
    triggering_anchors=[sv.Position.TOP_LEFT, sv.Position.BOTTOM_RIGHT],
    require_all_anchors=False,
)
```

For one-time entry counts with a polygon, maintain state outside the zone:

```python
seen_tracker_ids: set[int] = set()
inside = zone.trigger(detections)
inside_detections = detections[inside]

if inside_detections.tracker_id is not None:
    new_ids = set(map(int, inside_detections.tracker_id)) - seen_tracker_ids
    seen_tracker_ids.update(new_ids)
    new_entries_this_frame = len(new_ids)
else:
    new_entries_this_frame = 0
```

If the task is line crossing rather than current occupancy, use `LineZone`.

## Line crossing counts

`LineZone` uses persistent `tracker_id` values across frames. Without tracker IDs it warns and returns all-False crossing arrays.

```python
import supervision as sv

line = sv.LineZone(
    start=sv.Point(0, 200),
    end=sv.Point(800, 200),
    minimum_crossing_threshold=1,
)

for detections in detections_by_frame:
    if detections.tracker_id is None:
        # Run a tracker first or route to tracking-keypoints for tracker setup.
        continue

    crossed_in, crossed_out = line.trigger(detections)
    just_crossed_in = detections[crossed_in]
    just_crossed_out = detections[crossed_out]

in_total = line.in_count
out_total = line.out_count
per_class = line.in_count_per_class
```

Use `minimum_crossing_threshold > 1` when unstable boxes linger around the line and you need multiple frames on the new side before counting.

## Smooth tracked detections

`DetectionsSmoother` averages boxes over a per-track window. It requires `tracker_id` and is not for segmentation masks.

```python
smoother = sv.DetectionsSmoother(length=5)

for detections in detections_by_frame:
    if detections.tracker_id is not None:
        detections = smoother.update_with_detections(detections)
```

Reset between independent streams:

```python
smoother.reset()
```

## Detect small objects with tiled inference

Wrap the caller's existing model inference in a callback that consumes only the tile passed by `InferenceSlicer` and returns tile-local `Detections`.

```python
import numpy as np
import supervision as sv

# model_predict is provided by the caller and must run on image_slice, not the full image.
def callback(image_slice: np.ndarray) -> sv.Detections:
    raw_result = model_predict(image_slice)
    return sv.Detections.from_ultralytics(raw_result)

slicer = sv.InferenceSlicer(
    callback=callback,
    slice_wh=(640, 640),
    overlap_wh=(100, 100),
    overlap_filter=sv.OverlapFilter.NON_MAX_SUPPRESSION,
    iou_threshold=0.5,
    thread_workers=1,
)

detections = slicer(image)
```

Tune `overlap_wh` in pixels. Increase overlap when objects lie near tile boundaries; decrease it for speed. `overlap_wh` must be smaller than `slice_wh` in both dimensions.

### Batch callback mode

Use batch mode when the model is faster on batches. The callback signature changes.

```python
def batch_callback(tiles: list[np.ndarray]) -> list[sv.Detections]:
    raw_results = model_predict_batch(tiles)
    return [sv.Detections.from_inference(result) for result in raw_results]

slicer = sv.InferenceSlicer(
    callback=batch_callback,
    slice_wh=640,
    overlap_wh=100,
    batch_size=8,
    thread_workers=1,
)
```

For GPU models, prefer `batch_size > 1` with `thread_workers=1` rather than many concurrent single-image calls.

### Segmentation and compact masks in the slicer

```python
slicer = sv.InferenceSlicer(
    callback=segmentation_callback,
    slice_wh=640,
    overlap_wh=100,
    compact_masks=True,
)
detections = slicer(image)

if isinstance(detections.mask, sv.CompactMask):
    detections.mask = detections.mask.repack()
```

With `compact_masks=True`, dense tile masks returned by the callback are converted to `CompactMask` before moving/merging. Tile crops span the whole tile; call `repack()` after merging if tight crops matter.

### GeoTIFF/windowed raster lane

If `rasterio` is installed, pass an open rasterio-style dataset to the slicer. The callback receives HWC NumPy tiles; select bands and convert dtype/channels for the model inside the callback.

```python
slicer = sv.InferenceSlicer(callback=callback, slice_wh=1024, overlap_wh=128)

with open_windowed_raster_somehow() as dataset:
    detections = slicer(dataset)
```

The dataset CRS must be projected when present. Geographic CRSs are rejected because the slicer operates in pixel space.

## Save detections to CSV or JSON

Filter before saving if the output should contain only selected classes or confidence ranges.

```python
with sv.CSVSink("detections.csv") as sink:
    for frame_index, detections in enumerate(detections_by_frame):
        selected = detections[detections.confidence > 0.5]
        sink.append(selected, custom_data={"frame_index": frame_index})
```

```python
with sv.JSONSink("detections.json") as sink:
    for frame_index, detections in enumerate(detections_by_frame):
        sink.append(detections, custom_data={"frame_index": frame_index})
```

`detections.data` fields and `custom_data` keys are written into rows. Values with length equal to `len(detections)` are sliced per row; scalars and length-mismatched arrays/lists are broadcast.

## Preserve class names and custom data through filtering/export

```python
from supervision.config import CLASS_NAME_DATA_FIELD

if detections.get_data(CLASS_NAME_DATA_FIELD) is None:
    detections[CLASS_NAME_DATA_FIELD] = np.array(
        [id_to_name[int(class_id)] for class_id in detections.class_id]
    )

selected = detections[detections.confidence >= 0.75]

with sv.JSONSink("selected.json") as sink:
    sink.append(selected, custom_data={"source": "camera-1"})
```

The assignment must happen before filtering when the names are aligned with the original detection order, or after filtering when the names are computed from filtered `class_id`.

## Convert box, mask, and polygon formats

Use public utilities when an adapter or downstream tool expects another shape.

```python
xyxy = sv.xywh_to_xyxy(xywh)
xywh = sv.xyxy_to_xywh(xyxy)
mask = sv.polygon_to_mask(polygon, resolution_wh=(width, height))
boxes = sv.mask_to_xyxy(masks)
polygons = sv.mask_to_polygons(mask)
rle = sv.mask_to_rle(mask, compressed=True)
mask = sv.rle_to_mask(rle, resolution_wh=(width, height))
```

For NumPy slicing/crop bounds, prefer `sv.mask_to_roi(mask)` because it returns exclusive ROI bounds; `mask_to_xyxy` follows Supervision's inclusive max-coordinate convention.

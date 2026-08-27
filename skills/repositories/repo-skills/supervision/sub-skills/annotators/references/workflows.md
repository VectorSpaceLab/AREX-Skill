# Annotator workflows

Use these recipes for high-level image and video visualization. For `Detections`
creation, filtering, model adapters, zones, and sinks, use
[detection-and-zones](../../detection-and-zones/SKILL.md). For image/video I/O
and low-level primitives, use [media-utils](../../media-utils/SKILL.md).

## Compose box, mask, and label annotators

Prefer a copy when the original frame must survive. Chain annotators by passing
one result into the next annotator.

```python
import numpy as np
import supervision as sv

scene = np.zeros((480, 640, 3), dtype=np.uint8)  # BGR NumPy scene
detections = sv.Detections(
    xyxy=np.array([[50, 60, 200, 220]], dtype=np.float32),
    confidence=np.array([0.92], dtype=np.float32),
    class_id=np.array([0]),
    data={"class_name": np.array(["person"])},
)

annotated = scene.copy()
annotated = sv.BoxAnnotator().annotate(scene=annotated, detections=detections)
annotated = sv.LabelAnnotator().annotate(scene=annotated, detections=detections)
```

If the model provides masks aligned to the frame, add the mask before labels so
labels stay readable:

```python
mask_annotator = sv.MaskAnnotator(opacity=0.45)
label_annotator = sv.LabelAnnotator(text_position=sv.Position.CENTER_OF_MASS)

annotated = mask_annotator.annotate(scene=scene.copy(), detections=detections)
annotated = label_annotator.annotate(scene=annotated, detections=detections)
```

## Build robust labels

When `labels` is omitted, label annotators choose `detections["class_name"]` /
`detections.data["class_name"]` first, then `class_id`, then detection indices.
For user-facing confidence labels, build an explicit list and keep it length
aligned with `detections`.

```python
class_names = detections.data.get("class_name")
if class_names is None:
    class_names = np.array([str(class_id) for class_id in detections.class_id])

labels = [
    f"{class_name} {confidence:.2f}"
    for class_name, confidence in zip(class_names, detections.confidence)
]

annotated = sv.LabelAnnotator(max_line_length=24).annotate(
    scene=scene.copy(),
    detections=detections,
    labels=labels,
)
```

Use `RichLabelAnnotator` when text includes Unicode or a custom font is needed:

```python
annotated = sv.RichLabelAnnotator(
    font_path="font.ttf",
    font_size=16,
    text_padding=8,
).annotate(scene=scene.copy(), detections=detections, labels=labels)
```

If the font file cannot be loaded, `RichLabelAnnotator` falls back to the PIL
default font and logs a warning; it does not raise for a missing font path.

## Use custom color lookup arrays

`custom_color_lookup` overrides the annotator's configured lookup for a single
call. It maps each detection index to a palette index.

```python
lookup = np.array([1, 0, 1, 2], dtype=int)
assert len(lookup) == len(detections)

annotated = sv.BoxAnnotator(
    color=sv.ColorPalette.DEFAULT,
    color_lookup=sv.ColorLookup.INDEX,
).annotate(
    scene=scene.copy(),
    detections=detections,
    custom_color_lookup=lookup,
)
```

Use this when the visual grouping is not exactly class, detection index, or
track id. If you choose `ColorLookup.CLASS`, detections must have `class_id`; if
you choose `ColorLookup.TRACK`, detections must have `tracker_id`.

## Annotate video frames

Keep stateless annotators outside the frame loop. Stateful annotators such as
`TraceAnnotator` and `HeatMapAnnotator` also belong outside the loop so they can
accumulate state across frames; call `reset()` before reusing them for a new
video or independent stream.

```python
import supervision as sv

box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()
trace_annotator = sv.TraceAnnotator(position=sv.Position.BOTTOM_CENTER)
heat_annotator = sv.HeatMapAnnotator()

for frame in frames:  # frame is a BGR np.ndarray
    detections = make_detections(frame)  # route adapter details elsewhere
    detections = update_tracker(detections)  # must fill tracker_id for traces

    annotated = frame.copy()
    annotated = heat_annotator.annotate(scene=annotated, detections=detections)
    annotated = trace_annotator.annotate(scene=annotated, detections=detections)
    annotated = box_annotator.annotate(scene=annotated, detections=detections)
    annotated = label_annotator.annotate(scene=annotated, detections=detections)
    write_frame(annotated)
```

Order matters: broad translucent overlays first, then traces/shapes, then text.

## Draw zone overlays after triggering zones

Zone predicates and counting are owned by
[detection-and-zones](../../detection-and-zones/SKILL.md); drawing the current
state is handled here.

```python
polygon = np.array([[20, 20], [220, 20], [220, 180], [20, 180]])
zone = sv.PolygonZone(polygon=polygon)
zone_annotator = sv.PolygonZoneAnnotator(zone=zone, opacity=0.25)
box_annotator = sv.BoxAnnotator()

mask = zone.trigger(detections)
zone_detections = detections[mask]

annotated = frame.copy()
annotated = zone_annotator.annotate(scene=annotated)
annotated = box_annotator.annotate(scene=annotated, detections=zone_detections)
```

For line zones, run tracking first so `LineZone.trigger` has `tracker_id`, then
draw the line and counts:

```python
line_zone = sv.LineZone(start=sv.Point(50, 300), end=sv.Point(590, 300))
line_annotator = sv.LineZoneAnnotator(text_orient_to_line=True)

crossed_in, crossed_out = line_zone.trigger(detections_with_tracker_ids)
annotated = line_annotator.annotate(frame=frame.copy(), line_counter=line_zone)
```

For multiple line zones with class counts:

```python
annotated = sv.LineZoneAnnotatorMulticlass().annotate(
    frame=frame.copy(),
    line_zones=[line_zone_a, line_zone_b],
    line_zone_labels=["Gate A:", "Gate B:"],
)
```

## Compare predictions and ground truth visually

`ComparisonAnnotator` fills areas that appear only in the first detections, only
in the second detections, or in both. It automatically prefers oriented boxes,
then masks, then axis-aligned boxes depending on available data.

```python
annotated = sv.ComparisonAnnotator(
    label_1="prediction",
    label_2="ground truth",
    label_overlap="overlap",
    opacity=0.6,
).annotate(
    scene=scene.copy(),
    detections_1=predictions,
    detections_2=ground_truth,
)
```

For quantitative metrics, route to [metrics](../../metrics/SKILL.md).

## Add bars, crops, icons, blur, or pixelation

```python
annotated = sv.PercentageBarAnnotator().annotate(
    scene=scene.copy(),
    detections=detections,
)

risk_scores = np.array([0.15, 0.82], dtype=float)
annotated = sv.PercentageBarAnnotator(position=sv.Position.BOTTOM_CENTER).annotate(
    scene=annotated,
    detections=detections,
    custom_values=risk_scores,
)
```

For privacy:

```python
annotated = sv.BlurAnnotator(kernel_size=31).annotate(
    scene=scene.copy(),
    detections=face_detections,
)
# or
annotated = sv.PixelateAnnotator(pixel_size=16).annotate(
    scene=scene.copy(),
    detections=face_detections,
)
```

For thumbnails or callouts:

```python
annotated = sv.CropAnnotator(
    position=sv.Position.BOTTOM_RIGHT,
    scale_factor=1.5,
).annotate(scene=scene.copy(), detections=detections)
```

For icons, pass one path for all detections or a list with exactly one path per
detection. Empty strings are valid no-op entries.

```python
icon_paths = ["car.png" for _ in detections]
annotated = sv.IconAnnotator(icon_resolution_wh=(32, 32)).annotate(
    scene=scene.copy(),
    detections=detections,
    icon_path=icon_paths,
)
```

## Use PIL scenes intentionally

Most detection annotators accept a PIL image and return a PIL image. Internally,
PIL RGB data is converted to the BGR drawing convention and pasted back.

```python
from PIL import Image
import supervision as sv

image = Image.new("RGB", (640, 480), color="white")
annotated_image = sv.LabelAnnotator().annotate(
    scene=image.copy(),
    detections=detections,
)
```

Do not pass PIL images to zone annotators; convert to NumPy or route through
media-utils conversion guidance first.

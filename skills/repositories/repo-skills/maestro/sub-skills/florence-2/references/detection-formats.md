# Florence-2 detection formats

Maestro's Florence-2 object-detection adapter converts COCO-style boxes to a text prefix/suffix pair for VLM training and can parse Florence-compatible generated text back into arrays.

## Prefix

```text
<OD>
```

`detections_to_prefix_formatter(...)` always returns `<OD>`. Pass this as the inference prefix for object detection:

```python
generated_text = predict(model=model, processor=processor, image=image, prefix="<OD>")
```

## Suffix grammar

Each detection is concatenated with no separator:

```text
class<loc_xmin><loc_ymin><loc_xmax><loc_ymax>
```

Example with two boxes:

```text
cat<loc_250><loc_250><loc_500><loc_500>dog<loc_0><loc_0><loc_1000><loc_1000>
```

Rules:

- Coordinates are normalized integers in the `0..1000` range.
- Coordinate order is `xmin`, `ymin`, `xmax`, `ymax`.
- Source boxes are pixel-space `xyxy` arrays relative to `resolution_wh=(width, height)`.
- Formatting divides x coordinates by width and y coordinates by height, multiplies by `1000`, rounds to integers, and emits `<loc_N>` tokens.
- Parsing divides by `1000` and scales back to pixel coordinates using the same `(width, height)`.
- The parser recognizes class labels made of word characters and spaces. If your class labels contain punctuation such as hyphens or slashes, map them to Florence-safe labels before formatting and map them back after parsing.

## Format detections for COCO-to-VLM training

```python
import numpy as np
from maestro.trainer.models.florence_2.detection import (
    detections_to_prefix_formatter,
    detections_to_suffix_formatter,
)

xyxy = np.array([[50, 50, 100, 100], [0, 0, 200, 200]], dtype=np.float32)
class_id = np.array([0, 1], dtype=np.int32)
classes = ["cat", "dog"]
resolution_wh = (200, 200)

prefix = detections_to_prefix_formatter(xyxy, class_id, classes, resolution_wh)
suffix = detections_to_suffix_formatter(xyxy, class_id, classes, resolution_wh)

assert prefix == "<OD>"
assert suffix == "cat<loc_250><loc_250><loc_500><loc_500>dog<loc_0><loc_0><loc_1000><loc_1000>"
```

The training API wires these callbacks automatically for COCO datasets. If constructing `create_data_loaders(...)` yourself, pass both Florence formatter callbacks; otherwise COCO loading raises a formatter error.

## Parse generated suffix text

```python
from maestro.trainer.models.florence_2.detection import result_to_detections_formatter

boxes, class_ids = result_to_detections_formatter(
    text="cat<loc_250><loc_250><loc_500><loc_500>dog<loc_0><loc_0><loc_1000><loc_1000>",
    resolution_wh=(200, 200),
    classes=["cat", "dog"],
)

# boxes is float32 pixel-space xyxy:
# [[50, 50, 100, 100], [0, 0, 200, 200]]
# class_ids is int32: [0, 1]
```

Parsing behavior to remember:

- Empty text returns empty arrays with shapes `(0, 4)` and `(0,)`.
- Malformed fragments are ignored rather than raising.
- When `classes` is provided, unknown class labels are skipped.
- When `classes=None`, all parsed boxes are returned and every class id is `-1`.
- Invalid class ids during formatting raise an index error because the formatter indexes `classes[class_id[i]]`.
- Coordinates are not semantically validated by the parser beyond matching digits. Keep generated/evaluated coordinates inside `0..1000` and ensure `xmin <= xmax`, `ymin <= ymax` before downstream use.

## Convert parsed output to visualization or metrics

For deterministic Maestro metrics, keep using pixel-space `xyxy` arrays and class ids:

```python
import numpy as np
import supervision as sv

confidence = np.ones_like(class_ids, dtype=np.float32)
detections = sv.Detections(xyxy=boxes, class_id=class_ids, confidence=confidence)
```

For model evaluation, Maestro's Florence trainer parses both generated suffixes and reference suffixes with `result_to_detections_formatter(...)` when the selected metric is `mean_average_precision`.

Metric names and plotting outputs are owned by [datasets-and-metrics](../../datasets-and-metrics/references/metrics-and-utilities.md).

## Safe smoke test

From the generated Maestro skill tree:

```bash
python sub-skills/florence-2/scripts/smoke_florence_detection_format.py --json
```

The script checks:

1. `<OD>` prefix generation.
2. Deterministic suffix formatting for two boxes.
3. Round-trip parsing back to pixel-space boxes and class ids.
4. Unknown-class filtering.
5. Malformed-text empty output behavior.
6. `classes=None` default class id behavior.

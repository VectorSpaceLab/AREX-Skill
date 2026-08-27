# Verified API Reference

These signatures were inspected from the installed package for this skill's
source snapshot. They are internal implementation facts, not a promise that
future labelme releases keep the same module names.

## Qt-free codec

```python
from labelme._label_file import Annotation
from labelme._label_file import read_label_file, write_label_file

read_label_file(filename: str) -> Annotation
write_label_file(
    filename: str,
    annotation: Annotation,
    *,
    image_height: int | None,
    image_width: int | None,
    save_image_data: bool,
) -> None
```

`Annotation` is a frozen dataclass with `image_path`, decoded `image_data`
(bytes), `shapes`, `flags`, and `other_data`. `image_data` is populated from
embedded `imageData` or the external `imagePath` during a read. Read/write
failures are wrapped in `LabelFileReadError` or `LabelFileWriteError`.

## Shape model

```python
from labelme._shape import Shape

Shape(
    label: str | None = None,
    group_id: int | None = None,
    shape_type: ShapeType = "polygon",
    flags: dict[str, bool] | None = None,
    description: str | None = None,
    mask: numpy.ndarray | None = None,
    points: numpy.ndarray = ...,
    point_labels: numpy.ndarray = ...,
    other_data: dict = ...,
    closed: bool = False,
    visible: bool = True,
)
```

`ShapeType` values are `polygon`, `rectangle`, `oriented_rectangle`, `point`,
`line`, `circle`, `linestrip`, `points`, and `mask`. `Shape` normalizes points to
float arrays and rejects unknown shape types. `can_add_point()` is true only for
polygon and linestrip; point, points, and mask Shapes do not expose draggable
vertices.

## Scope boundary

AI automation and Config File APIs are intentionally not repeated here. Route
those tasks to the sibling
[`ai-assisted-annotation`](../../ai-assisted-annotation/SKILL.md) and
[`cli-and-config`](../../cli-and-config/SKILL.md) sub-skills so this reference stays
focused on Annotation Files and Shapes.

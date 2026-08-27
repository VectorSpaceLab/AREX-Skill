---
name: layout-objects
description: "Routes LayoutParser coordinate primitives, layout containers,
  shape operations, and layout-analysis helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Layout Objects

Use this sub-skill for geometry-heavy LayoutParser tasks: coordinate
conversion, padding, containment, serialization, sorting, and lightweight line
or category grouping.

## What belongs here

- `Interval`, `Rectangle`, `Quadrilateral`, `TextBlock`, and `Layout`
- relative/absolute coordinate transforms
- `pad`, `shift`, `scale`, `crop_image`
- `union`, `intersect`, `is_in`, `condition_on`, `relative_to`
- `to_dict`, `from_dict`, `to_dataframe`, `get_homogeneous_blocks`
- `generalized_connected_component_analysis_1d`
- `simple_line_detection`
- `group_textblocks_based_on_category`

## What does not belong here

- JSON/CSV/PDF loading and export: use `layout-io`
- `draw_box` / `draw_text`: use `visualization`
- OCR response parsing: use `ocr`
- `lp://` model catalogs or model inference: use `layout-models`

## Read these files

- `references/guide.md` for the class, operation overview, and troubleshooting notes
- `../layout-io/SKILL.md` when the task starts with files or PDFs
- `../visualization/SKILL.md` when the task ends with rendering

## Fast path

1. Identify the shape type on each block.
2. Use the most specific conversion first (`Interval` ↔ `Rectangle` ↔
   `Quadrilateral`).
3. Use `Layout` batch methods for page-wide transforms.
4. Keep `TextBlock` wrappers when the block also carries text or ids.
5. Only approximate quadrilateral shape operations with `strict=False` when a
   bounding-box approximation is acceptable.

## Common user requests

- "Filter the left column"
- "Convert boxes to rectangles"
- "Union the regions"
- "Check whether a token is inside a page block"
- "Sort blocks by reading order"
- "Group the text blocks by line or category"
- "Round-trip a layout to dict or dataframe"

## Minimal smoke

Use the bundled root smoke script when you only need to confirm the geometry
layer and serialization basics:

```bash
python ../../scripts/smoke_layoutparser_core.py
```

## Failure clues

- `InvalidShapeError`: the chosen union/intersection is geometrically invalid.
- `NotSupportedShapeError`: the operation would create a polygonal result that
  LayoutParser cannot represent directly.
- `ValueError` from `Layout(...)`: the input is not an iterable of blocks or is
  already a `Layout` wrapper.
- `ValueError` from `TextBlock.to_interval()`: the axis is missing.

## Output discipline

When answering, give the exact class names and coordinate assumptions that the
future agent should use. If a block should be re-encoded as another shape,
state the destination shape explicitly so the user can follow the conversion.

# Layout Objects Guide

This guide covers the coordinate primitives and layout container that almost
all other LayoutParser workflows build on.

## Main classes

| Symbol | Purpose | Key behaviors |
| --- | --- | --- |
| `Interval` | One-dimensional span on the x or y axis | `put_on_canvas`, `condition_on`, `relative_to`, `is_in`, `pad`, `shift`, `scale`, `to_rectangle`, `to_quadrilateral` |
| `Rectangle` | Axis-aligned box | `coordinates`, `points`, `condition_on`, `relative_to`, `is_in`, `pad`, `shift`, `scale`, `to_interval`, `to_quadrilateral` |
| `Quadrilateral` | Four-point polygon-like block | `points`, `coordinates`, `area`, perspective-aware transforms, `pad`, `shift`, `scale`, `to_interval`, `to_rectangle` |
| `TextBlock` | Content + coordinate wrapper | Delegates geometry to the wrapped block and stores `text`, `id`, `type`, `parent`, `next`, `score` |
| `Layout` | Mutable sequence of layout blocks | Batch transforms, `filter_by`, `sort`, `to_dict`, `to_dataframe`, `get_texts`, `get_info`, `get_homogeneous_blocks` |

## Coordinate conversions

- `Interval` can be promoted to `Rectangle` or `Quadrilateral`.
- `Rectangle` can be downgraded to `Interval` on either axis.
- `Quadrilateral` stores 4 points and can be approximated as a rectangle via
  `to_rectangle()` when a downstream workflow only needs the bounding box.
- `TextBlock.to_interval()` needs `axis='x'` or `axis='y'` unless the wrapped
  block already is an `Interval`.

## Geometry and relations

| Method | Meaning |
| --- | --- |
| `condition_on(other)` | Convert relative coordinates into absolute coordinates under `other`. |
| `relative_to(other)` | Express the block relative to `other`. |
| `is_in(other, soft_margin={}, center=False)` | Check containment or center containment, optionally with relaxed margins. |
| `pad(left, right, top, bottom, safe_mode=True)` | Expand the block and clamp negatives when `safe_mode=True`. |
| `shift(shift_distance)` | Move the block by one scalar or x/y pair. |
| `scale(scale_factor)` | Scale the block by one scalar or x/y pair. |
| `crop_image(image)` | Crop an image array by the block geometry. |

Important behavior:

- `Quadrilateral` shape operations can raise `NotSupportedShapeError` when the
  result would be a polygon that LayoutParser does not model.
- `InvalidShapeError` is used for invalid unions, such as mixing interval axes.
- `strict=False` approximates problematic quadrilateral operations as rectangles.

## Layout batch behavior

- `Layout` is list-like and preserves `page_data`.
- Slices return another `Layout` with the same page data.
- `filter_by()` keeps elements that are inside another block.
- `sort()` can run in-place or return a new layout.
- `get_homogeneous_blocks()` promotes mixed shapes to the most compatible type.
- `to_dataframe()` is convenient for export, but it does not include
  `page_data`.

## Layout-analysis helpers

`layoutparser.tools` exposes three small but useful helpers:

- `generalized_connected_component_analysis_1d()` for generic 1D grouping
- `simple_line_detection()` for line clustering from text blocks
- `group_textblocks_based_on_category()` for grouping by `type`

These helpers are the easiest way to build reading-order or row-grouping logic
on top of `Layout`.

## Typical workflow

1. Build or load a `Layout`.
2. Filter by `Interval`/`Rectangle` to isolate page regions.
3. Sort the blocks and add ids if reading order matters.
4. Use `TextBlock` when you want geometry plus text/category metadata.
5. Convert to a dataframe or dict only after the layout is stable.

## Troubleshooting

- `Layout(l)` where `l` is already a `Layout` raises a shape-validation error;
  wrap it as `Layout([l])` if that is really what you want.
- `TextBlock.to_interval()` needs an axis argument for non-interval blocks.
- Invalid `axis` values and axis-mismatched unions raise explicit errors rather
  than silently coercing coordinates.
- If a transform looks wrong, inspect the underlying `.block` on a `TextBlock`.

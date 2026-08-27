# Annotator catalog

Supervision annotators are high-level renderers. Most consume a `scene` plus
`sv.Detections` and return the annotated scene. Use this catalog to choose a
class; use [workflows.md](workflows.md) for composition patterns and
[troubleshooting.md](troubleshooting.md) for failure modes.

## Shared calling contract

- **Scene:** usually `np.ndarray` with shape `(H, W, 3)`, dtype `uint8`, and BGR
  channel order. Most detection annotators also accept `PIL.Image.Image` and
  return the same type.
- **Mutation:** pass `scene.copy()` unless the caller explicitly wants to mutate
  the input frame. Annotators draw on the supplied object and return it or a
  same-type object containing the result.
- **Detections alignment:** `len(detections)`, `xyxy`, `class_id`,
  `confidence`, `tracker_id`, `mask`, and `detections.data[...]` arrays must all
  be aligned by detection index.
- **Color strategy:** annotators that accept `color_lookup` support
  `sv.ColorLookup.CLASS`, `sv.ColorLookup.INDEX`, and `sv.ColorLookup.TRACK`.
  `custom_color_lookup` overrides this per call and must be an integer NumPy
  array of length `len(detections)`.
- **Mask policy:** `MaskAnnotator`, `PolygonAnnotator`, and `HaloAnnotator`
  require `detections.mask`. `BackgroundOverlayAnnotator` can use masks when
  present but can fall back to boxes.

## Detection annotators

| Goal | Classes | Required data | Notes |
| --- | --- | --- | --- |
| Draw rectangular outlines | `BoxAnnotator`, `RoundBoxAnnotator`, `BoxCornerAnnotator` | `detections.xyxy`; usually `class_id` unless color lookup is changed | Use for standard object detection. `RoundBoxAnnotator` validates `roundness` in `(0, 1]`. |
| Draw non-rectangular outlines | `OrientedBoxAnnotator`, `PolygonAnnotator` | OBB data for oriented boxes; `detections.mask` for polygons | `OrientedBoxAnnotator` is a no-op if oriented-box coordinates are absent. `PolygonAnnotator` decodes dense masks or `CompactMask` crops. |
| Draw shape markers | `CircleAnnotator`, `EllipseAnnotator`, `DotAnnotator`, `TriangleAnnotator` | `xyxy` anchors; optional `Position` | Good for lighter overlays. `DotAnnotator` and `TriangleAnnotator` support outline styling. |
| Fill or shade detections | `ColorAnnotator`, `MaskAnnotator`, `HaloAnnotator`, `BackgroundOverlayAnnotator` | boxes for `ColorAnnotator`; masks for `MaskAnnotator`/`HaloAnnotator`; boxes or masks for background overlay | `MaskAnnotator` blends only the mask region of interest. All-false or absent masks leave the scene unchanged. |
| Blur, pixelate, or crop regions | `BlurAnnotator`, `PixelateAnnotator`, `CropAnnotator` | `xyxy` boxes | Degenerate boxes are skipped. `CropAnnotator` clips boxes crossing frame boundaries and samples crops from the original scene to avoid overlap aliasing. |
| Add text labels | `LabelAnnotator`, `RichLabelAnnotator` | one label per detection, or aligned `class_name`/`class_id` fallback | `LabelAnnotator` uses OpenCV text. `RichLabelAnnotator` uses PIL fonts and is better for Unicode/custom fonts. Both support `smart_position` and `max_line_length`. |
| Add icons | `IconAnnotator` | `xyxy`; `icon_path` string or one path per detection | Empty string draws nothing. Invalid icon paths raise `FileNotFoundError`; list length must match detections. Icons are cached by path and target resolution. |
| Draw confidence or custom bars | `PercentageBarAnnotator` | `detections.confidence` or `custom_values` | `custom_values` must be list/array of length `N`, values in `[0, 1]`. |
| Draw temporal trails | `TraceAnnotator` | `tracker_id` and `xyxy` anchors | Stateful; call `reset()` between independent streams. `smooth=True` uses spline smoothing when enough unique points exist and falls back safely for stationary objects. |
| Draw accumulated occupancy | `HeatMapAnnotator` | `xyxy` anchors | Stateful; reinitializes on resolution changes and supports `reset()`. Empty calls do not warn and leave the scene unchanged until heat exists. |
| Compare two detection sets | `ComparisonAnnotator` | two `Detections` objects | Chooses oriented boxes if both sides have OBB data, else masks if both sides have masks or one side is empty, else `xyxy` boxes. Optional labels explain colors. |

## Zone overlay annotators

Zone logic belongs to [detection-and-zones](../../detection-and-zones/SKILL.md);
this sub-skill owns the drawing part once zone state is available.

| Goal | Classes | Required state | Notes |
| --- | --- | --- | --- |
| Draw a polygon zone and count | `PolygonZoneAnnotator` | `PolygonZone.current_count`, normally updated by `zone.trigger(detections)` | `annotate(scene, label=None)` draws polygon lines, optional filled opacity, and count or custom label at the polygon center. |
| Draw a line-crossing zone | `LineZoneAnnotator` | `LineZone.in_count`/`out_count`, updated by `line_zone.trigger(detections)` | Can hide in/out counts, customize labels, draw text boxes, orient labels to the line, and move labels off center. |
| Draw per-class line counts | `LineZoneAnnotatorMulticlass` | one or more `LineZone` objects with class-aware counts | Renders a table. `line_zone_labels` length must match `line_zones`. Use `force_draw_class_ids=True` when class names are unavailable or ambiguous. |

## Keypoint annotators are adjacent, not owned here

For `sv.KeyPoints`, route primary guidance to
[tracking-keypoints](../../tracking-keypoints/SKILL.md). The following classes
share the high-level annotate pattern but consume `key_points` instead of
`detections`: `VertexAnnotator`, `EdgeAnnotator`, `VertexLabelAnnotator`,
`VertexEllipseAnnotator`, `VertexEllipseAreaAnnotator`,
`VertexEllipseOutlineAnnotator`, and `VertexEllipseHaloAnnotator`.

Keypoint-specific pitfalls include `visible` masks, 1-based skeleton edge
indices, per-class skeleton dictionaries, covariance data for vertex ellipses,
and label/color list lengths; keep those with the tracking-keypoints sub-skill.

## Choosing a color source

- Use `ColorLookup.CLASS` when every detection has `class_id` and the goal is
  stable color by category.
- Use `ColorLookup.INDEX` when `class_id` is absent, unknown, negative, or not
  meaningful for visualization.
- Use `ColorLookup.TRACK` when detections already carry `tracker_id`; pending
  tracker id `-1` is rendered with the pending-track color.
- Use `custom_color_lookup=np.array([...], dtype=int)` to group arbitrary
  detections into palette buckets. Its length must equal `len(detections)`.
- Hex color strings such as `"#010203"` are accepted by annotators that take
  `Color | ColorPalette | str`; alpha in hex input is parsed but annotator
  drawing uses RGB/BGR color channels.

For low-level palette construction or primitive drawing, route to
[media-utils](../../media-utils/SKILL.md).

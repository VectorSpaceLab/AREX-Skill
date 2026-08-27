---
name: annotators
description: "Operate supervision high-level visual annotators for images and videos."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Annotators

Use this sub-skill when a task asks to visualize `supervision` detections, masks,
tracks, heatmaps, labels, icons, zone overlays, or side-by-side detection
comparisons with high-level annotator classes.

## Route here for

- `BoxAnnotator`, `MaskAnnotator`, `LabelAnnotator`, `RichLabelAnnotator`,
  `TraceAnnotator`, `HeatMapAnnotator`, `ComparisonAnnotator`,
  `PercentageBarAnnotator`, `IconAnnotator`, `CropAnnotator`, and other
  `scene` + `Detections` annotators.
- `PolygonZoneAnnotator`, `LineZoneAnnotator`, and
  `LineZoneAnnotatorMulticlass` when the question is about drawing zone or line
  overlays after zone state has been computed.
- Label construction, `custom_color_lookup`, annotator color strategy,
  `scene.copy()` versus in-place mutation, and combining multiple annotators on
  an image or video frame.

## Route away

- Build, filter, convert, save, or adapt `Detections`: use
  [detection-and-zones](../detection-and-zones/SKILL.md).
- Low-level drawing primitives, `Color`, `ColorPalette`, image/video I/O,
  Pillow/OpenCV conversion, and backend diagnostics: use
  [media-utils](../media-utils/SKILL.md).
- `KeyPoints`, keypoint-specific annotators (`VertexAnnotator`,
  `EdgeAnnotator`, `VertexLabelAnnotator`, vertex ellipse annotators), tracker
  IDs, and deprecated keypoint/tracker paths: use
  [tracking-keypoints](../tracking-keypoints/SKILL.md). Keypoint annotators use
  the same `.annotate(scene, key_points)` shape, so cross-reference this skill
  for general composition style only.
- Metric interpretation or evaluation: use [metrics](../metrics/SKILL.md).

## Operating checklist

1. Verify the user already has a `scene` and the right container:
   `Detections` for detection annotators, `KeyPoints` for keypoint annotators,
   or zone objects for zone annotators. If not, route to the owner above.
2. Treat NumPy scenes as OpenCV-style images: `uint8`, shape `(H, W, 3)`, BGR
   channel order. PIL images are supported by most detection annotators and are
   converted internally, but zone annotators take NumPy arrays.
3. Preserve the input only when needed by passing `scene.copy()`. Annotators are
   designed to draw on the supplied scene and return the annotated result.
4. Pick an annotator family from
   [annotator-catalog.md](references/annotator-catalog.md), then apply a recipe
   from [workflows.md](references/workflows.md).
5. For visual/no-op/errors, consult
   [troubleshooting.md](references/troubleshooting.md) before changing the data
   pipeline.

## Required context to keep in answers

- `supervision` version target is `0.31.0.dev0` on Python `>=3.10`; base install
  is `pip install supervision`.
- Native OpenCV is optional. The documented fallback backend can render slightly
  different text, antialiasing, masks, or video behavior; use media-utils for
  backend-specific diagnosis.
- Do not recommend original repository docs, examples, tests, scripts, local
  checkout paths, or generated skill import steps as runtime dependencies.

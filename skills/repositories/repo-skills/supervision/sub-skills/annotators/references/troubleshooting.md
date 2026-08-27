# Annotator troubleshooting

Use this when a visualization is blank, colors are wrong, labels fail, masks are
misaligned, or output changes across environments. For container construction or
model adapters, route to [detection-and-zones](../../detection-and-zones/SKILL.md).
For low-level image I/O, color objects, and backend diagnostics, route to
[media-utils](../../media-utils/SKILL.md).

## Quick triage

1. Confirm `scene` is the expected type and order: NumPy BGR `uint8` array with
   shape `(H, W, 3)`, or a PIL image for annotators that support it.
2. Confirm `len(detections)` and all aligned fields have the same first-axis
   length. Check `xyxy`, `class_id`, `confidence`, `tracker_id`, masks, custom
   data arrays, labels, `custom_color_lookup`, icon paths, and custom values.
3. Confirm the chosen annotator has the required data: masks for mask/polygon/
   halo; tracker IDs for trace/line crossing; confidence or custom values for
   percentage bars; OBB data for oriented boxes.
4. Pass `scene.copy()` while debugging so prior drawing does not hide whether an
   annotator mutated the original.
5. Test `Detections.empty()` and one simple synthetic detection to separate data
   bugs from rendering/backend bugs.

## Scene type, channel order, and in-place behavior

**Symptom:** colors are swapped, image is black, output has unexpected type, or
original frame changed.

**Likely causes and repairs:**

- NumPy scenes should be BGR, not RGB. Images loaded by many PIL utilities are
  RGB; convert intentionally before using OpenCV-style drawing.
- Detection annotators usually accept `np.ndarray` or `PIL.Image.Image` and
  return the same type. Zone annotators take NumPy arrays.
- Annotators are designed to draw on the supplied scene. Use `scene.copy()` when
  preserving the input matters; assign the return value for chaining.
- Some operations create intermediate arrays internally, but do not rely on that
  as an immutability guarantee.
- Single-channel grayscale is only safe for specific operations that tests cover
  (for example pixelation); most colored overlays need 3-channel scenes.

## Mask annotator does nothing or draws in the wrong place

**Symptom:** `MaskAnnotator`, `PolygonAnnotator`, or `HaloAnnotator` returns an
unchanged scene, or masks appear shifted/cropped.

**Likely causes and repairs:**

- `detections.mask is None`: mask, polygon, and halo annotators are no-ops.
  Convert from a segmentation-capable model adapter or build masks in
  `Detections` first.
- Dense masks must be shape `(N, H, W)` where `(H, W)` exactly matches the scene
  height and width. Boolean and `uint8` masks both work when values represent
  foreground truth.
- `sv.CompactMask` is supported, but compact storage only represents pixels
  inside each detection's `xyxy` crop. If a dense mask contains foreground
  outside the declared box, the compact-mask path can legitimately omit it.
- All-false masks intentionally leave the scene unchanged and skip blending.
- Mask color resolution still runs through `class_id`, `tracker_id`, or a custom
  lookup. Missing `class_id` with `ColorLookup.CLASS` can raise before painting.
- `ComparisonAnnotator` requires mask shapes to match the scene when it uses
  mask mode; otherwise prefer boxes or repair the masks upstream.

## Labels are missing, wrong, or raise length errors

**Symptom:** labels are indices instead of class names, custom labels fail, or a
class-name array raises.

**Likely causes and repairs:**

- If `labels` is provided, it must contain exactly one string per detection.
- If `labels` is omitted, label annotators use `detections.data["class_name"]`
  first, then `class_id`, then stringified detection indices. A mismatched
  `class_name` or `class_id` array raises instead of silently truncating.
- Some adapters populate class names and some do not. If class names are missing,
  build a custom labels list from the model's mapping before annotation.
- `detections.confidence` can be `None`; guard before formatting confidence.
- Use `max_line_length` for wrapping long labels and `smart_position=True` when
  multiple labels overlap. Smart positioning spreads labels once per annotate
  call and clips them into the frame.
- Use `RichLabelAnnotator` for Unicode/custom font rendering. A bad `font_path`
  falls back to the PIL default font with a warning; it does not guarantee the
  requested glyph coverage.

## Color lookup failures

**Symptom:** errors mention resolving color by class/track, out-of-bounds
indices, or custom lookup length.

**Likely causes and repairs:**

- `ColorLookup.CLASS` requires `detections.class_id` and one value per
  detection. Switch to `ColorLookup.INDEX` if class ids are absent.
- `ColorLookup.TRACK` requires `detections.tracker_id`; run tracking first or
  switch lookup mode. Pending tracker id `-1` is treated specially for track
  coloring.
- `custom_color_lookup` must be a NumPy integer array with length
  `len(detections)`. Values select palette indices and may be reused to group
  multiple detections.
- Negative class ids can map deterministically through a palette, but often
  signal that the upstream adapter/class mapping should be checked.
- Hex color strings are accepted by annotator constructors that take color
  inputs; invalid hex formats raise.

## Trace and heatmap state surprises

**Symptom:** traces connect unrelated videos, heat accumulates from a prior run,
or `TraceAnnotator` raises about missing tracker IDs.

**Likely causes and repairs:**

- `TraceAnnotator` requires `detections.tracker_id`. Run a tracker first, then
  annotate. This is separate from detection construction; route tracker details
  to [tracking-keypoints](../../tracking-keypoints/SKILL.md).
- Call `TraceAnnotator.reset()` before reusing it for a new independent stream.
- `TraceAnnotator(smooth=True)` falls back safely when a tracker is stationary
  or has too few unique points; if the visual line is unexpected, compare with
  `smooth=False`.
- `HeatMapAnnotator` accumulates heat across frames and resets automatically
  when frame resolution changes. Call `reset()` to discard same-resolution
  history.
- Empty detection frames leave heat/trace output unchanged or no-op as designed;
  they should not produce runtime warnings.

## OpenCV fallback differences

**Symptom:** pixel-perfect assertions differ between machines, text/antialiasing
looks slightly different, or some video/media behavior changes.

**Likely causes and repairs:**

- Native OpenCV is optional. The base package can use a documented fallback
  backend. Drawing, antialiasing, text metrics, contour extraction, resize, and
  video helpers may have small visual or performance differences.
- For user workflows, prefer tolerance-based visual checks over exact pixel
  equality when backend is unknown.
- Install an OpenCV wheel only when the task requires native performance,
  codecs, GUI behavior, or exact OpenCV compatibility. Use media-utils for the
  backend choice and verification procedure.

## Text, icon, and file failures

**Symptom:** icon annotations raise, text boxes look wrong, or font rendering is
unexpected.

**Likely causes and repairs:**

- `IconAnnotator` needs `icon_path` as either a single path or a list matching
  `len(detections)`. A list-length mismatch raises `ValueError`.
- Empty icon path `""` means draw nothing for that detection.
- Invalid icon paths raise `FileNotFoundError` during image load. Verify the
  file exists and is a readable image with an alpha channel if transparency is
  needed.
- Icon images are cached by path and requested resolution; if a file is changed
  in-place during a long process, recreate the process or use a different path.
- `RichLabelAnnotator` missing font paths fall back to a default font. If a glyph
  is missing, choose a font file with the required glyphs.
- `LabelAnnotator` uses OpenCV-style text; it is fast but not a full Unicode
  text renderer.

## Empty or invalid geometry

**Symptom:** no output, clipped output, or ValueError for position/roundness.

**Likely causes and repairs:**

- Empty detections are expected to return the unchanged scene for most
  annotators.
- Zero-area or fully out-of-frame boxes are skipped by blur, pixelate, and crop
  annotators. Partially out-of-frame boxes are clipped.
- `BackgroundOverlayAnnotator` darkens/tints everything outside detections. A
  fully out-of-bounds detection can therefore leave the whole frame tinted.
- `OrientedBoxAnnotator` is a no-op if oriented-box coordinate data is absent.
- `PercentageBarAnnotator` requires `detections.confidence` or valid
  `custom_values`; custom values must be list/array, length `N`, and in `[0, 1]`.
- Unsupported `Position` values raise `ValueError` in label, crop, and
  percentage-bar placement helpers.
- `RoundBoxAnnotator` rejects invalid `roundness`; `BlurAnnotator` rejects
  `kernel_size < 1`; `PixelateAnnotator` rejects `pixel_size < 1`.

## Zone overlay counts look stale

**Symptom:** polygon or line overlay draws but count text is not updated.

**Likely causes and repairs:**

- Call `zone.trigger(detections)` or `line_zone.trigger(detections)` before the
  annotator for each frame.
- `PolygonZoneAnnotator` displays `zone.current_count` unless a custom `label`
  is passed.
- `LineZone` crossing counts require tracker IDs so the same object can be
  matched across frames. If `tracker_id` is missing, fix tracking before drawing.
- `LineZoneAnnotatorMulticlass` requires `line_zone_labels` length to match the
  number of zones. Set `force_draw_class_ids=True` when class names are not
  reliable.

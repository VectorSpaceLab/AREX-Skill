# Detection And Zones Troubleshooting

Use this page when detection code runs but shapes, metadata, optional dependencies, zones, masks, slicer behavior, or saved outputs are wrong.

## Optional model dependencies

**Symptom:** `ImportError`, model constructor failure, missing weights, or adapter code cannot import a framework.

**Likely cause:** Supervision adapters convert framework outputs; they do not install or run model frameworks.

**Fix:**

- Keep `supervision` installed separately from model libraries.
- Install the caller-selected model package only when that model is actually used.
- Do not add top-level imports for heavy optional frameworks in reusable utilities. Import them inside the model-specific function.
- For reference-only examples that require model downloads, preserve the adapter pattern but do not assume the model can be downloaded in the Researcher environment.

## Raw result shape mismatches

**Symptom:** Adapter raises a `ValueError`, fields are empty, masks disappear, or rows are misaligned.

**Checks:**

- `xyxy` must be a 2D `np.ndarray` with shape `(N, 4)`.
- `confidence`, `class_id`, and `tracker_id` must be `None` or 1D arrays with shape `(N,)`.
- Dense `mask` must be shape `(N, H, W)` and should be boolean.
- Every `detections.data` value must be a list or `np.ndarray` aligned with `N` on the first dimension.
- `Detections.from_transformers` needs recognized keys such as `boxes`, `masks`, `png_string`, `segments_info`, or `segmentation`.
- `Detections.from_inference` expects an image width/height and prediction entries with center `x`, `y`, `width`, `height`, class, class ID, and confidence fields.

**Fix:** Convert raw model output to these shapes before constructing `Detections`, or use the exact matching `from_*` adapter. If only some predictions include masks or tracker IDs in an Inference result, Supervision keeps all boxes but drops the partial optional field to preserve alignment.

## Missing `resolution_wh`

**Symptom:** VLM/TensorFlow/SAM3 adapters raise about missing or invalid resolution.

**Cause:** Some outputs are normalized or polygon-based and must be scaled into pixel coordinates.

**Fix:** Pass `(width, height)` with positive integer dimensions:

```python
detections = sv.Detections.from_tensorflow(result, resolution_wh=(width, height))
detections = sv.Detections.from_sam3(result, resolution_wh=(width, height))
detections = sv.Detections.from_vlm(vlm, result, resolution_wh=(width, height))
```

For Qwen2.5-VL, pass both `input_wh=(input_width, input_height)` and `resolution_wh=(output_width, output_height)`. Do not pass `(height, width)` by habit; the API name is `resolution_wh`.

## Missing or wrong `class_name` metadata

**Symptom:** Labels, CSV/JSON exports, or user code expect `detections["class_name"]`, but it is `None` or has the wrong length.

**Facts:**

- The canonical key is `CLASS_NAME_DATA_FIELD`, whose value is `"class_name"`.
- `from_inference` always returns `data["class_name"]`, including empty results.
- `from_ultralytics`, `from_transformers(..., id2label=...)`, `from_vlm(..., classes=...)`, and `from_easyocr` can populate names when the raw result contains enough label information.
- `Detections.empty()` alone does not guarantee a `class_name` field.

**Fix:** Add class names as an aligned array before downstream code needs them:

```python
from supervision.config import CLASS_NAME_DATA_FIELD

detections[CLASS_NAME_DATA_FIELD] = np.array(
    [id_to_name[int(class_id)] for class_id in detections.class_id]
)
```

Use the constant in library code so future key changes are centralized.

## Invalid boxes, masks, and OBB data

**Symptom:** Construction or area/NMS calls raise shape errors; `CENTER_OF_MASS` fails; NMS/NMM behaves like AABB instead of OBB.

**Fix checklist:**

- Convert boxes to `xyxy` shape `(N, 4)` and ensure `x_min <= x_max`, `y_min <= y_max` for meaningful area. Validation checks shape, not semantic validity of every coordinate.
- Convert masks to boolean dense `(N, H, W)` or a `CompactMask` with `len(mask) == N`.
- Use `sv.mask_to_roi(mask)` for exclusive NumPy slice bounds; `sv.mask_to_xyxy` returns inclusive `xyxy` boxes.
- Store oriented corners under `ORIENTED_BOX_COORDINATES`, shape `(N, 4, 2)`. Wrong shapes raise during OBB area/NMS/NMM paths.
- `detections.get_anchors_coordinates(sv.Position.CENTER_OF_MASS)` requires masks even if OBB data is present.
- `detections.area` prioritizes masks over OBB corners over AABB boxes. Use `detections.box_area` when only the axis-aligned box area is intended.

## CompactMask vs dense behavior

**Symptom:** Code calls ndarray-only methods on `CompactMask`, merged masks lose pixels, or memory use differs from expectations.

**Facts and fixes:**

- `CompactMask` supports `len`, indexing, slicing, `shape`, `area`, `sum`, `to_dense`, and `crop`, but it is not a full ndarray. Call `to_dense()` before arbitrary ndarray methods like `astype`, `reshape`, `ravel`, `any`, or `all`.
- Integer indexing (`compact[0]`) returns one full-frame dense mask. Slice/list/boolean indexing returns another `CompactMask`.
- `Detections.from_inference(result, compact_masks=True)` can crop native full-image COCO RLE masks to detector boxes; true pixels outside those boxes are silently dropped. Use the default dense path if exact out-of-box pixels matter.
- `Detections.to_compact_masks()` converts dense masks with full-image crops, preserving pixels but getting less crop-area memory savings. Call `repack()` to tighten crops around true pixels after merging or slicing.
- `Detections.merge` with mixed dense and compact masks returns `CompactMask`, but dense inputs are converted using detection boxes. Out-of-box true pixels in those dense masks can be dropped.
- All compact masks in a merge must share the same `image_shape`; dense masks mixed with compact masks must have the same `(H, W)` as the compact `image_shape`.

## NMS, Soft-NMS, and NMM failures

**Symptom:** `ValueError` about missing confidence or class IDs, no detections are dropped, or OBB duplicate handling is unexpected.

**Fix:**

- `with_nms`, `with_soft_nms`, and `with_nmm` require `detections.confidence`.
- They require `detections.class_id` unless called with `class_agnostic=True`.
- Soft-NMS does not drop detections unless `score_threshold` is set; by default it only decays confidence in the returned copy.
- `with_nms` and `with_nmm` use OBB geometry only when `data[ORIENTED_BOX_COORDINATES]` exists with shape `(N, 4, 2)`. Otherwise they fall back to `xyxy` envelopes.
- `with_soft_nms` has no OBB-specific branch; OBB detections use their `xyxy` envelopes.

## `LineZone` counts stay zero

**Symptom:** `line.trigger(detections)` returns all-False arrays and counts do not change.

**Likely causes and fixes:**

- `detections.tracker_id is None`: run a tracker first or provide stable tracker IDs. `LineZone` counts crossings across frames and cannot work from boxes alone.
- The same object does not keep the same tracker ID across frames: fix tracking before debugging the zone.
- `start` and `end` are identical: line magnitude is zero and initialization raises.
- Anchors straddle both sides of the line in one frame: the detection is skipped for that frame to avoid ambiguous direction.
- `minimum_crossing_threshold` is too high for the number of frames observed after crossing: lower it or process more frames.
- Class-specific counts use `class_id`; unclassified detections are counted under `None`. Class-name display relies on `data["class_name"]` when present.

## `PolygonZone` trigger surprises

**Symptom:** Objects partly overlapping a polygon do not trigger, objects on boundaries trigger, or multi-zone assignment looks surprising.

**Facts and fixes:**

- `PolygonZone` is anchor-based, not a geometric intersection or IoU test. It checks whether configured anchors land inside the polygon mask.
- Default anchor is `sv.Position.BOTTOM_CENTER` and default `require_all_anchors=True`.
- With multiple anchors and `require_all_anchors=True`, every configured anchor must be inside. Set `require_all_anchors=False` to trigger when any configured anchor is inside.
- Anchor coordinates are rounded to pixels; polygon-boundary anchors are included; out-of-bounds anchors are excluded.
- Anchors are computed from original detection boxes before zone clipping, so a straddling detection is not shifted into multiple non-overlapping zones by per-zone clipping.
- `PolygonZone` reports current occupancy per frame. If the task is "count once on first entry", combine it with external `tracker_id` state or use `LineZone` for crossing-style counts.

## `InferenceSlicer` overlap and callback problems

**Symptom:** Too many duplicates, missing boundary objects, warning about detections outside slice bounds, callback type errors, or unexpected sequential processing.

**Fix checklist:**

- `overlap_wh` is pixels, not a percentage, and must be smaller than `slice_wh` in both dimensions.
- The callback must run inference on the image slice passed to it. If it returns full-image coordinates or uses the original image, Supervision warns once that detections are outside slice bounds.
- For `batch_size=1`, callback signature is `np.ndarray -> sv.Detections`.
- For `batch_size > 1`, callback signature is `list[np.ndarray] -> list[sv.Detections]` with exactly one output per input tile. Non-list returns or length mismatches raise.
- Segmentation callbacks return tile-local masks. The slicer moves masks into full-image coordinates and needs full-image resolution internally; do not pre-shift tile detections yourself.
- If OBB detections appear and `thread_workers > 1`, remaining slices/batches run sequentially and warn once because common OBB inference backends are not thread-safe.
- Use `overlap_filter=sv.OverlapFilter.NONE` to diagnose raw tile outputs before NMS/NMM, then restore suppression or merging.
- With `compact_masks=True`, dense tile masks are converted to compact storage; call `detections.mask.repack()` after slicing if compact crops are too loose.

## GeoTIFF/windowed raster lane

**Symptom:** `rasterio` is missing, slicing a raster raises about CRS, or model input channels/dtype are wrong.

**Fix:**

- Install the GeoTIFF dependency lane only when needed.
- Pass an open rasterio-style dataset object, not a file path string, when using windowed reads.
- The dataset CRS must be projected when a CRS exists. Reproject geographic rasters before slicing.
- The slicer reads raster bands as `(bands, height, width)` and passes callback tiles as contiguous `(height, width, bands)`. Convert dtype, band order, scaling, and channel count inside the callback for the model.
- Single-band rasters become HWC tiles with one channel. Do not assume three channels.
- Raster reads are serialized internally; model callbacks may still run concurrently depending on `thread_workers` and OBB detection.

## CSV/JSON custom data serialization

**Symptom:** CSV columns differ from later appended data, JSON fails to serialize a custom object, arrays appear as whole lists instead of per-row values, or files are empty until close.

**Facts and fixes:**

- Use sinks as context managers so files are opened and closed correctly.
- CSV header is written on the first append from base columns plus sorted `detections.data` and `custom_data` keys. Later appends with different fields log a warning and write only the original header fields.
- `CSVSink` stringifies numeric fields; missing `class_id`, `confidence`, or `tracker_id` become empty strings.
- `JSONSink` writes the final JSON array on context exit. If inspecting the file before close, it may not be complete.
- In both sinks, `np.ndarray`, list, or tuple values with length equal to `len(detections)` are sliced per detection row; other values are broadcast to every row.
- JSON serialization converts NumPy scalars to Python numbers/booleans and NumPy arrays to lists. Non-NumPy custom objects must be converted to JSON-compatible values before `append`.
- Keep `detections.data` aligned. Do not store scalar custom fields in `detections.data`; use `custom_data` for broadcast scalar fields such as frame index, camera ID, or source name.

## Deprecated and boundary APIs

- Prefer `Detections.from_vlm` over deprecated `from_lmm` and prefer `sv.VLM` over deprecated `sv.LMM`.
- `LineZoneAnnotator`, `PolygonZoneAnnotator`, and other drawing choices are visualization concerns; route style and composition questions to annotators.
- Tracking setup and tracker deprecations belong to tracking-keypoints; this sub-skill only consumes `tracker_id` once present.
- Metrics, dataset conversion, and media/video helper issues belong to their respective sub-skills after detection objects are correctly formed.

# Detection And Zones API Reference

This reference covers detection-facing APIs in `supervision` 0.31.0.dev0. Import the public API as `import supervision as sv`; import constants from `supervision.config` when writing metadata keys.

## Package and install facts

| Need | Install | Notes |
| --- | --- | --- |
| Core detections, zones, slicer, sinks, compact masks | `pip install supervision` | Python >=3.10. Optional model libraries are not installed by Supervision. |
| Detection metrics | `pip install "supervision[metrics]"` | Metrics are outside this sub-skill; route evaluation to metrics. |
| GeoTIFF/windowed raster slicing | `pip install "supervision[geotiff]"` or install `rasterio` | Only needed when passing a rasterio-style dataset to `InferenceSlicer`. |
| Native OpenCV behavior | Install a compatible OpenCV wheel if the task needs native cv2 features | Base Supervision can run with its documented fallback; do not require native OpenCV for detection-only logic. |

## `sv.Detections` container

`sv.Detections` is the shared object for model adapters, zones, trackers, annotators, slicers, metrics, and sinks.

| Field | Required | Shape/type | Semantics |
| --- | --- | --- | --- |
| `xyxy` | Yes | `np.ndarray` shape `(N, 4)` | Axis-aligned boxes `[x_min, y_min, x_max, y_max]` in pixel coordinates. |
| `mask` | No | `None`, dense bool `np.ndarray` shape `(N, H, W)`, or `sv.CompactMask` | Instance segmentation masks aligned with `xyxy`. Dense non-bool masks warn and should be converted to bool. |
| `confidence` | No | `None` or `np.ndarray` shape `(N,)` | Detection scores. Required by NMS/NMM/Soft-NMS. |
| `class_id` | No | `None` or integer `np.ndarray` shape `(N,)` | Class IDs. Required by NMS/NMM/Soft-NMS unless `class_agnostic=True`. |
| `tracker_id` | No | `None` or integer `np.ndarray` shape `(N,)` | Track IDs. Required by `LineZone` crossing counts and `DetectionsSmoother`. |
| `data` | No | `dict[str, np.ndarray | list]`, first dimension or length `N` | Per-detection metadata such as class names or OBB corners. |
| `metadata` | No | `dict[str, object]` | Collection-level metadata, not per detection. |

### Important constants

| Constant | Value | Use |
| --- | --- | --- |
| `CLASS_NAME_DATA_FIELD` | `"class_name"` | Per-detection class labels in `detections.data`; most adapters that know names store here. |
| `ORIENTED_BOX_COORDINATES` | `"xyxyxyxy"` | Oriented bounding-box corners, shape `(N, 4, 2)`, ordered as four pixel-coordinate corners. Presence enables OBB-aware anchors, area, NMS, and NMM. |
| `AREA_DATA_FIELD` | `"area"` | Optional per-detection area metadata used by dataset/COCO lanes. |
| `COCO_RAW_SEGMENTATION` | `"coco_raw_segmentation"` | Optional raw COCO segmentation payload metadata. |

### Core methods and properties

| API | Returns | Use |
| --- | --- | --- |
| `sv.Detections.empty()` | Empty `Detections` with `(0, 4)` boxes and empty `confidence`/`class_id` arrays | Safe no-result sentinel. Adapter-specific empty outputs may additionally populate `data["class_name"]`. |
| `len(detections)`, `detections.is_empty()` | Count or boolean | Branching and assertions. |
| `detections[index]` / `detections.select(index)` | New `Detections` copy | Integer, slice, index list, or boolean mask selection preserving all aligned fields and `data`. |
| `detections["key"]` / `detections.get_data("key")` | Data value or `None` | Read per-detection metadata. |
| `detections["key"] = values` | Mutates `data` | Values must be list or `np.ndarray` aligned with length `N`. |
| `sv.Detections.merge(list_of_detections)` | Merged `Detections` | Requires all non-empty inputs to agree on optional field presence and `data` keys. Empty detections are ignored. |
| `detections.get_anchors_coordinates(sv.Position.*)` | `(N, 2)` coordinates | Anchor points for zones. Uses OBB corners when present except `CENTER_OF_MASS`, which requires masks. |
| `detections.area` | `(N,)` array | Mask pixel area if masks exist; else OBB area if OBB data exists; else axis-aligned box area. |
| `detections.box_area` | `(N,)` array | Axis-aligned `xyxy` box area only. |
| `detections.box_aspect_ratio` | `(N,)` float array | Width divided by height; zero-height boxes yield `nan`. |
| `detections.to_compact_masks()` | `Detections` or `self` | Converts dense masks to `CompactMask`; returns `self` when masks are already compact or absent. |
| `detections.with_nms(...)` | Filtered `Detections` | Hard non-max suppression using mask IoU, OBB IoU, or box IoU depending on available geometry. |
| `detections.with_soft_nms(...)` | `Detections` with decayed confidence, optionally filtered | Soft-NMS uses masks when present; otherwise axis-aligned boxes. OBBs fall back to `xyxy`. |
| `detections.with_nmm(...)` | Merged `Detections` | Non-maximum merging using mask, OBB, or box overlap. OBB groups keep winner orientation. |

## Model and VLM adapters

Adapters normalize raw framework outputs into `sv.Detections`. They do not run models, download weights, or install optional framework dependencies.

| Adapter | Raw input contract | Output notes |
| --- | --- | --- |
| `Detections.from_ultralytics(result)` | Ultralytics `Results` for detection, segmentation, tracking, or OBB | Populates `class_id`, `confidence`, optional `mask`, optional `tracker_id`, `data["class_name"]`; OBB results also populate `data[ORIENTED_BOX_COORDINATES]`. |
| `Detections.from_inference(result, *, compact_masks=False)` | Roboflow API / Inference package result dict or SDK object with `.dict()`/`.json()` | Parses center `x/y/width/height` predictions, class IDs/names, confidence, optional tracker IDs, polygon/RLE masks. Always returns `data["class_name"]` as a string array, even when empty. Mixed partial tracker IDs or masks are dropped to preserve alignment. |
| `Detections.from_transformers(transformers_results, id2label=None)` | Transformers post-processed dict or segmentation tensor containing `boxes`, `masks`, `png_string`, `segments_info`, or `segmentation` | Routes detection, semantic, instance, and panoptic result shapes. With `id2label`, populates `data["class_name"]`. Raises if no recognized keys are present. |
| `Detections.from_vlm(vlm, result, **kwargs)` | VLM response text/dict plus required geometry args | Parses supported VLM output formats; generally requires `resolution_wh=(width, height)`, and Qwen2.5-VL additionally requires `input_wh`. Optional `classes` maps labels to IDs and filters/aligns class names. |
| `Detections.from_lmm(...)` | Deprecated LMM alias | Present for compatibility but deprecated; use `from_vlm`. |
| `Detections.from_yolov5(result)` | YOLOv5 result with `.pred[0]` columns `xyxy, confidence, class_id` | Detection boxes only. |
| `Detections.from_yolo_nas(result)` | YOLO-NAS prediction object | Maps `bboxes_xyxy`, `confidence`, and labels. Empty predictions return `Detections.empty()`. |
| `Detections.from_tensorflow(result, resolution_wh)` | TensorFlow Hub dict with normalized `[ymin, xmin, ymax, xmax]` arrays | Requires positive `(width, height)` to denormalize into pixel `xyxy`; copies source boxes before scaling. |
| `Detections.from_deepsparse(result)` | DeepSparse result object | Maps boxes, scores, and labels. |
| `Detections.from_mmdetection(result)` | MMDetection outputs | Maps boxes/scores/classes, with optional masks when present. |
| `Detections.from_detectron2(result)` | Detectron2 result dict with `instances` | Maps `pred_boxes`, `scores`, optional `pred_masks`, and `pred_classes`. |
| `Detections.from_sam(result)` | SAM automatic mask result list | Sorts by area, accepts dense segmentations or COCO RLE dicts, returns boxes and masks. Mixed segmentation encodings raise. |
| `Detections.from_sam3(result, resolution_wh)` | SAM3 prompt result dict/object | Requires output resolution for polygon-to-mask conversion; class IDs are prompt indices. |
| `Detections.from_azure_analyze_image(result, class_map=None)` | Azure Analyze Image response | Maps objects/tags into detections; class map can filter/assign class IDs. |
| `Detections.from_paddledet(result)` | PaddleDet dict with `bbox` columns | Maps class, confidence, and box columns. |
| `Detections.from_easyocr(result)` | EasyOCR `detail=1` tuples | Stores OCR text in `data["class_name"]`; preserves quadrilateral corners in `data[ORIENTED_BOX_COORDINATES]`. `detail=0` text-only results cannot convert. |
| `Detections.from_ncnn(result)` | ncnn model-zoo detections with `rect`, `prob`, `label` | Maps `xywh` rectangles to `xyxy`. |

### Supported `sv.VLM` values

| VLM value | Result type | Required kwargs | Optional kwargs | Output geometry |
| --- | --- | --- | --- | --- |
| `sv.VLM.PALIGEMMA` / `"paligemma"` | `str` | `resolution_wh` | `classes` | Boxes. |
| `sv.VLM.FLORENCE_2` / `"florence_2"` | `dict` | `resolution_wh` | None | Boxes, and masks for supported segmentation tasks. |
| `sv.VLM.QWEN_2_5_VL` / `"qwen_2_5_vl"` | `str` | `input_wh`, `resolution_wh` | `classes` | Boxes. |
| `sv.VLM.QWEN_3_VL` / `"qwen_3_vl"` | `str` | `resolution_wh` | `classes` | Boxes. |
| `sv.VLM.DEEPSEEK_VL_2` / `"deepseek_vl_2"` | `str` | `resolution_wh` | `classes` | Boxes. |
| `sv.VLM.GOOGLE_GEMINI_2_0` / `"gemini_2_0"` | `str` | `resolution_wh` | `classes` | Boxes. |
| `sv.VLM.GOOGLE_GEMINI_2_5` / `"gemini_2_5"` | `str` | `resolution_wh` | `classes` | Boxes, confidence, and optional masks. |
| `sv.VLM.GOOGLE_GEMINI_3_5` / `"gemini_3_5"` | `str` | `resolution_wh` | `classes` | Boxes, confidence, and optional masks. |
| `sv.VLM.MOONDREAM` / `"moondream"` | `dict` | `resolution_wh` | None | Boxes. |

## Compact masks

`sv.CompactMask` stores each mask as crop-scoped run-length encoding. It is compatible with Supervision mask consumers but is not a general `np.ndarray` replacement.

| API | Returns | Use |
| --- | --- | --- |
| `sv.CompactMask.from_dense(masks, xyxy, image_shape)` | Compact mask stack | Convert dense `(N, H, W)` bool masks. Boxes are clipped to image bounds and use inclusive `xyxy` max coordinates. |
| `sv.CompactMask.from_coco_rle(rles, xyxy, image_shape)` | Compact mask stack | Convert full-frame COCO RLE dicts without materializing a dense stack. Every RLE `size` must match `image_shape`. |
| `compact.to_dense()` / `np.asarray(compact)` | Dense `(N, H, W)` bool array | Explicit materialization boundary. |
| `compact.crop(i)` | Dense `(crop_h, crop_w)` bool crop | Decode only one crop. |
| `compact[i]` | Dense `(H, W)` bool mask | Integer indexing materializes one full-frame mask. |
| `compact[slice_or_mask]` | `CompactMask` | Slice/list/boolean/fancy indexing keeps compact storage. |
| `compact.shape`, `compact.image_shape`, `compact.offsets`, `compact.bbox_xyxy`, `compact.dtype`, `compact.area` | Metadata arrays/properties | Introspection and alignment checks. |
| `compact.sum(axis=None)` | Pixel count(s) | Mask area-like computations. |
| `sv.CompactMask.merge(list_of_compact)` | Concatenated `CompactMask` | All inputs must share `image_shape`. |
| `compact.repack()` | Tight-crop `CompactMask` | Re-encode masks around true pixels after loose-crop operations. |
| `compact.with_offset(dx, dy, new_image_shape)` | Moved/clipped `CompactMask` | Shift masks into another canvas; fully out-of-frame masks become all-false crops. |
| `compact.resize(new_image_shape)` | Resized `CompactMask` | Nearest-neighbor style resize to a new full-image shape. |

Mask merge policy in `Detections.merge`:

| Inputs | Output mask type |
| --- | --- |
| All masks absent | `None` |
| All dense masks | Dense `np.ndarray` |
| All compact masks | `CompactMask` |
| Mixed dense and compact masks | `CompactMask`, after converting dense masks using their detection boxes |
| Some detections have masks and others do not | `ValueError` |

## Filtering, overlap, and detection utilities

### Methods on `Detections`

| API | Geometry dispatch | Notes |
| --- | --- | --- |
| `detections[mask]` | N/A | Preferred way to filter by class, confidence, area, zone trigger, or combined predicates. |
| `detections.with_nms(threshold=0.5, class_agnostic=False, overlap_metric=sv.OverlapMetric.IOU)` | Masks -> OBB corners -> `xyxy` boxes | Requires `confidence`; requires `class_id` unless class-agnostic. |
| `detections.with_soft_nms(sigma=0.5, class_agnostic=False, score_threshold=None)` | Masks -> `xyxy` boxes | Keeps all detections and decays confidence unless `score_threshold` is set. Requires positive `sigma`. |
| `detections.with_nmm(threshold=0.5, class_agnostic=False, overlap_metric=sv.OverlapMetric.IOU)` | Masks -> OBB corners -> `xyxy` boxes | Merges groups instead of dropping; output preserves winner metadata. |

### Enums

| Enum | Values | Use |
| --- | --- | --- |
| `sv.OverlapFilter` | `NONE`, `NON_MAX_SUPPRESSION`, `NON_MAX_MERGE` | `InferenceSlicer` overlap post-processing. String values are `"none"`, `"non_max_suppression"`, `"non_max_merge"`. |
| `sv.OverlapMetric` | `IOU`, `IOS` | Box/mask/OBB overlap metric. String input is normalized to uppercase. |
| `sv.Position` | `CENTER`, `CENTER_LEFT`, `CENTER_RIGHT`, `TOP_CENTER`, `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_CENTER`, `BOTTOM_RIGHT`, `CENTER_OF_MASS` | Anchor selection for zones and `get_anchors_coordinates`. `CENTER_OF_MASS` requires masks. |

### Public detection utilities

| Family | Public APIs | Typical use |
| --- | --- | --- |
| Boxes | `clip_boxes`, `pad_boxes`, `denormalize_boxes`, `move_boxes`, `scale_boxes`, `xyxyxyxy_to_xyxy` | Coordinate cleanup, moving tile-local detections into full-image coordinates, OBB envelopes. |
| Converters | `xyxy_to_polygons`, `polygon_to_mask`, `xywh_to_xyxy`, `xyxy_to_xywh`, `xcycwh_to_xyxy`, `xyxy_to_xcycarh`, `mask_to_xyxy`, `xyxy_to_mask`, `mask_to_polygons`, `is_compressed_rle`, `rle_to_mask`, `mask_to_rle`, `polygon_to_xyxy` | Format conversion among boxes, polygons, masks, RLE, and OBB-compatible forms. |
| IoU/NMS | `box_iou`, `box_iou_batch`, `box_iou_batch_with_jaccard`, `mask_iou_batch`, `box_non_max_suppression`, `box_soft_non_max_suppression`, `box_non_max_merge`, `mask_non_max_suppression`, `mask_soft_non_max_suppression`, `mask_non_max_merge`, `oriented_box_iou_batch`, `oriented_box_non_max_suppression`, `oriented_box_non_max_merge` | Low-level overlap and suppression/merge primitives. Prefer `Detections.with_*` unless building custom utilities. |
| Masks | `calculate_masks_centroids`, `contains_holes`, `contains_multiple_segments`, `filter_segments_by_distance`, `mask_to_roi`, `move_masks` | Mask cleanup, centroid anchors, ROI extraction, moving masks. |
| Polygons | `approximate_polygon`, `filter_polygons_by_area` | Simplify or filter polygon outputs. |
| VLM helpers | `edit_distance`, `fuzzy_match_index` | Fuzzy class-name matching around VLM outputs. |

## Zones and detection tools

| API | Signature essentials | Behavior |
| --- | --- | --- |
| `sv.PolygonZone(polygon, triggering_anchors=(sv.Position.BOTTOM_CENTER,), require_all_anchors=True)` | `polygon` is integer-like `(M, 2)` vertices | Builds a polygon mask sized from polygon max coordinates. `trigger(detections)` returns a boolean mask and updates `current_count`. It is anchor-based occupancy, not object identity tracking. |
| `PolygonZone.trigger(detections)` | returns `(N,)` bool array | Computes anchors from original detection boxes, rounds anchors to pixels, excludes out-of-bounds anchors, and includes polygon-boundary anchors. |
| `sv.LineZone(start, end, triggering_anchors=(four box corners), minimum_crossing_threshold=1)` | `start`/`end` are `sv.Point`; line magnitude must be nonzero | Counts objects crossing a line across frames. Requires `detections.tracker_id`. Returns `(crossed_in, crossed_out)` bool arrays. |
| `LineZone.in_count`, `out_count`, `in_count_per_class`, `out_count_per_class` | properties | Aggregate and per-class crossing counts. Unclassified detections are keyed by `None`. |
| `sv.DetectionsSmoother(length=5)` | tracker history window length | Smooths `xyxy` and confidence by `tracker_id`; not segmentation-compatible. Missing `tracker_id` warns and returns input unchanged. |
| `sv.InferenceSlicer(callback, slice_wh=640, overlap_wh=100, overlap_filter=sv.OverlapFilter.NON_MAX_SUPPRESSION, iou_threshold=0.5, overlap_metric=sv.OverlapMetric.IOU, thread_workers=1, compact_masks=False, batch_size=1)` | callback returns `Detections` for one tile, or `list[Detections]` for batch mode | Slices images or rasterio-style datasets, moves tile detections to full-image coordinates, merges, then applies overlap filtering. |
| `sv.CSVSink(file_name="output.csv")` | context manager; `append(detections, custom_data=None)` | Writes one row per detection. Base columns: `x_min`, `y_min`, `x_max`, `y_max`, `class_id`, `confidence`, `tracker_id`, plus sorted `detections.data` and `custom_data` keys. |
| `sv.JSONSink(file_name="output.json")` | context manager; `append(detections, custom_data=None)` | Accumulates rows and writes a JSON array on context exit. NumPy scalars/arrays are converted to JSON numbers/lists. |

Zone annotators (`PolygonZoneAnnotator`, `LineZoneAnnotator`, `LineZoneAnnotatorMulticlass`) draw zones and counts, but pure rendering/style questions should route to annotators.

# Slicing parameters and inference-mode choices

SAHI sliced inference works by splitting a large image into overlapping tiles, running the detector on each tile, shifting tile detections back into full-image coordinates, optionally adding a standard full-image prediction pass, and postprocessing overlapping predictions.

## Inference mode matrix

| Mode | Python setting | CLI setting | Use when | Trade-off |
| --- | --- | --- | --- | --- |
| Standard only | `get_prediction(...)` or `predict(no_sliced_prediction=True)` | `sahi predict --no_sliced_prediction` | Images are close to model input size, objects are large, or you need a fast baseline. | Small objects in very large images can be missed after resizing. |
| Sliced only | `get_sliced_prediction(..., perform_standard_pred=False)` or `predict(no_standard_prediction=True)` | `sahi predict --no_standard_prediction` | Target objects are small and full-image pass adds duplicates or cost. | Large objects split across tiles may be missed or fragmented. |
| Standard+sliced | `get_sliced_prediction(..., perform_standard_pred=True)` | default `sahi predict` | Mixed small and large objects; you want recall before speed. | Extra full-image inference plus final duplicate merging. |

`predict` rejects configurations where both `no_standard_prediction` and `no_sliced_prediction` are true.

## Core parameter reference

| Parameter | Default in low-level sliced API | Default in high-level `predict` | Guidance |
| --- | ---: | ---: | --- |
| `slice_height`, `slice_width` | `None` | `512` | For reproducible runs, specify both. Match the detector's training/input scale when possible, commonly 512-640 for YOLO-style models. |
| `auto_slice_resolution` | `True` | not exposed as a high-level CLI flag | Low-level `get_sliced_prediction` chooses tile geometry automatically only when explicit slice size is omitted. |
| `overlap_height_ratio`, `overlap_width_ratio` | `0.2` | `0.2` | Start with 0.2. Increase to 0.3-0.4 for missed boundary objects; decrease for speed or excessive duplicates. Must be less than 1.0 when explicit slice sizes are used. |
| `perform_standard_pred` | `True` | controlled by `no_standard_prediction=False` | Keep true unless all relevant objects are small or the full-image pass creates hard-to-merge duplicates. |
| `postprocess_type` | `GREEDYNMM` | `GREEDYNMM` | Other supported names are `NMM`, `NMS`, and `LSNMS`. See `../../postprocess-backends/SKILL.md` for algorithm/backend details. |
| `postprocess_match_metric` | `IOS` | `IOS` | `IOS` is aggressive for different-sized overlaps; `IOU` is more conservative and standard. |
| `postprocess_match_threshold` | `0.5` | `0.5` | Lower values merge more predictions; higher values keep more separate boxes. |
| `postprocess_class_agnostic` | `False` | `False` | Set true when duplicate boxes can receive inconsistent class ids and should still merge. |
| `batch_size` | `1` | `1` | Number of slices per batch. Must be at least 1. Larger values can improve GPU utilization for batch-capable backends. |
| `progress_bar` | `False` | `False` | Shows a tqdm slice progress bar. In CLI, use `--progress_bar`. |
| `progress_callback` | `None` | Python API only | Called after each processed slice batch with `(processed_slices, total_slices)`. |
| `merge_buffer_length` | `None` | not exposed in `predict` | Advanced low-memory path; periodically merges buffered slice predictions and can slightly affect AP. |
| `slice_export_prefix`, `slice_dir` | `None` | not exposed in `predict` | Debug tile generation by exporting the actual slices; avoid in production unless needed because it writes many files. |
| `exclude_classes_by_name`, `exclude_classes_by_id` | `None` | `None` | Filters predictions after model conversion. Ensure class names/ids match the detector mapping. |
| `confidence_threshold` | `None` | model-level threshold only | Low-level per-call override. The original model threshold is restored after the call. |
| `force_postprocess_type` | `False` | `False` | When false and model confidence threshold is below 0.1, SAHI switches to `NMS`/`IOU` to avoid box enlargement from merging. |

`predict_fiftyone` uses `slice_height=256` and `slice_width=256` by default, because it is oriented toward interactive dataset review.

## Choosing slice size

1. Start from the model's expected inference scale. If the detector was trained around 640-pixel images, try `slice_height=640` and `slice_width=640`; for memory-constrained runs, try 512.
2. Make slices large enough to contain complete objects plus context. If one object fills most of a tile, increase the tile size or keep standard prediction enabled.
3. Make slices small enough that tiny targets become visually meaningful after resizing. If standard prediction misses small objects, reduce tile size before increasing overlap.
4. For non-square images, it is still valid to use square tiles. Use rectangular tiles only when the scene geometry or detector training scale justifies it.

Approximate the number of tiles before running a large job:

```text
step_width  = slice_width  * (1 - overlap_width_ratio)
step_height = slice_height * (1 - overlap_height_ratio)
columns ≈ ceil((image_width  - slice_width)  / step_width)  + 1
rows    ≈ ceil((image_height - slice_height) / step_height) + 1
tiles   ≈ rows * columns
```

Higher overlap increases tile count quickly. Doubling `batch_size` does not reduce model work; it only changes how many slices are submitted per batch.

## Auto slice resolution behavior

When `get_sliced_prediction` receives no explicit `slice_height`/`slice_width` and `auto_slice_resolution=True`, SAHI chooses slicing parameters from image resolution and orientation:

| Image resolution class | Source behavior | Practical interpretation |
| --- | --- | --- |
| low | one full-image tile | Sliced path behaves close to standard prediction because the image is already small. |
| medium | orientation-aware 1x2, 2x1, or 1x1 style split with high overlap | Useful as a quick default, but not the most reproducible tuning choice. |
| high | orientation-aware split with more rows/columns and moderate overlap | Better for large images; explicit sizes are still preferred for experiments. |
| ultra-high | denser orientation-aware split | Watch tile count, memory, and duplicate handling. |

Use explicit slice dimensions for benchmarked or production runs. Use auto mode for quick exploratory calls when you do not yet know image scale.

## Standard+sliced aggregation details

For `get_sliced_prediction`:

1. SAHI slices the image and predicts each tile.
2. It shifts every tile prediction back to full-image coordinates.
3. If `perform_standard_pred=True` and there is more than one slice, it runs `get_prediction` on the full image and appends those predictions.
4. It postprocesses the combined list when more than one prediction remains.

This means duplicate tuning affects both tile duplicates and duplicates between the full-image pass and tile passes.

## Duplicate tuning quick recipes

| Symptom | First changes to try | Why |
| --- | --- | --- |
| Many duplicate boxes around one object | Lower `postprocess_match_threshold`; try `postprocess_match_metric="IOS"`; consider `postprocess_class_agnostic=True`. | More aggressive matching merges boxes from overlapping tiles. |
| Boxes become too large after merging | Try `postprocess_type="NMS"` and `postprocess_match_metric="IOU"`, or set `force_postprocess_type=False` with a sensible confidence threshold. | NMS suppresses instead of averaging/merging coordinates. |
| Boundary objects are missed | Increase overlap to 0.3 or 0.4; keep standard prediction enabled for large objects. | More overlap makes complete objects visible in at least one tile. |
| Run is too slow | Increase tile size, decrease overlap, disable standard prediction if safe, increase `batch_size` only if backend/hardware can use it. | Reduces tile count or improves submission efficiency. |
| Memory is too high | Reduce `batch_size`; consider `merge_buffer_length` for low-level calls. | Keeps fewer slice predictions/images live at once. |

For backend selection and exact NMS/NMM semantics, use `../../postprocess-backends/SKILL.md`.

## Export-related slicing choices

- Use `get_sliced_prediction(..., slice_export_prefix="case", slice_dir="debug_slices")` only to inspect generated tiles. This can produce many files.
- Use high-level `predict(..., export_crop=True, export_pickle=True, dataset_json_path="annotations.json")` or CLI equivalents when you need run artifacts. That path preserves folder structure under output subdirectories.
- Use `PredictionResult.export_visuals(...)` for one-off image visuals from low-level APIs.
- Use `../../annotations-and-results/SKILL.md` for detailed object conversion and coordinate-format questions.

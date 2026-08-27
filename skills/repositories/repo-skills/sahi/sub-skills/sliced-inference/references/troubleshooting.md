# Troubleshooting SAHI prediction workflows

Use this matrix for standard and sliced prediction failures before changing model code. For detector installation, model weights, API keys, or backend-specific constructor arguments, route to `../../model-integrations/SKILL.md`. For NMS/NMM implementation details, route to `../../postprocess-backends/SKILL.md`.

## Prediction setup failures

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `ImportError`, `ModuleNotFoundError`, or a message that backend packages are required | The selected `model_type` needs optional detector dependencies that are not installed. | Install/verify only the needed backend via `../../model-integrations/SKILL.md`. Then run a tiny import/model-load check before a full folder prediction. |
| `KeyError` or failure immediately after `AutoDetectionModel.from_pretrained(model_type=...)` | Wrong `model_type` string or alias. | Use a supported model type such as `ultralytics`, `rtdetr`, `mmdet`, `yolov5`, `detectron2`, `huggingface`, `huggingface_segmentation`, `torchvision`, `roboflow`, `yolo-world`, `yoloe`, or `hugging_face_universal_segmentation`. Route setup details to `../../model-integrations/SKILL.md`. |
| Model loads but predictions are empty | Confidence threshold too high, class filters exclude everything, category mapping/remapping mismatch, wrong image size, wrong weights, or the task needs sliced inference. | Lower `model_confidence_threshold` / per-call `confidence_threshold`, remove `exclude_classes_by_*`, print category names/ids, compare standard vs sliced modes, and test one known image before folder inference. |
| `No valid input given to predict function` and `predict(...)` returns `None` | `source` is missing, empty, or not a valid image/folder/video path for the current process. | Pass a single image file, image folder, or video file to `source` / `--source`. For FiftyOne use `image_dir` / `--image_dir`. |
| Prediction call tries to download or access credentials | Backend-specific model path or API-key behavior was chosen. | Replace with a local weights path or preloaded model object, or route to `../../model-integrations/SKILL.md` for explicit credential/network policy. This sub-skill's smoke script never downloads weights. |

## Slicing and aggregation failures

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `ValueError: Overlap ratio must be less than 1.0` | `overlap_height_ratio` or `overlap_width_ratio` is `>= 1.0` with explicit slice dimensions. | Use `0 <= overlap < 1`; start at `0.2`. If you need more boundary coverage, try `0.3` or `0.4`, not `1.0`. |
| `ValueError: Compute type is not auto and slice width and height are not provided.` | Low-level slicing was asked to avoid auto resolution but no explicit `slice_height`/`slice_width` was provided. | Provide both slice dimensions, or keep `auto_slice_resolution=True`. |
| `ValueError: batch_size must be >= 1` | `batch_size=0` or a negative value. | Set `batch_size=1` for safest behavior; increase only after the backend can handle batching. |
| Too many duplicate detections after slicing | Overlap is high, `postprocess_match_threshold` is too high, metric is too conservative, classes differ across duplicate boxes, or standard+sliced aggregation duplicates objects. | Lower `postprocess_match_threshold`, try `postprocess_match_metric="IOS"`, consider `postprocess_class_agnostic=True`, reduce overlap, or run sliced-only with `perform_standard_pred=False` / `--no_standard_prediction` to isolate the source. |
| Duplicate boxes are merged into boxes that are too large | Merge-style postprocess (`GREEDYNMM`/`NMM`) averages or combines overlapping coordinates, especially at low confidence. | Try `postprocess_type="NMS"` with `postprocess_match_metric="IOU"`. Keep confidence thresholds reasonable; by default very low model confidence can trigger an automatic NMS/IOU switch unless `force_postprocess_type=True`. |
| Boundary objects are cut or missed | Overlap too low, slices too small for object context, or standard prediction disabled for large objects. | Increase overlap, increase tile size, and compare with standard+sliced mode. Use tile export only for debugging when necessary. |
| Sliced inference is much slower than expected | Tile count exploded due to small slices/high overlap; standard pass is enabled; backend cannot use larger `batch_size`; visualization/export dominates runtime. | Estimate tile count, increase slice size, lower overlap, disable unneeded visuals/exports, and benchmark `batch_size` values on a short image subset. |
| Out-of-memory or process killed during sliced inference | Large tile batch, high-resolution images, many predictions retained before postprocess, or visualization/crop exports. | Lower `batch_size`, increase slice size or reduce overlap, disable `export_crop`/visuals, and consider low-level `merge_buffer_length` when retaining predictions is the bottleneck. |

## Postprocess option failures

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `postprocess_type should be one of ...` | Unsupported postprocess name or wrong case. | Use uppercase `GREEDYNMM`, `NMM`, `NMS`, or `LSNMS`. |
| Different results across `GREEDYNMM`, `NMM`, and `NMS` | These algorithms merge/suppress overlaps differently. | Treat this as expected. Choose based on duplicate behavior and route algorithm questions to `../../postprocess-backends/SKILL.md`. |
| Low confidence threshold unexpectedly changes postprocess to NMS/IOU | SAHI protects against box enlargement from merge operations when model confidence is below `0.1` and `force_postprocess_type=False`. | Either use a higher model confidence threshold, accept the NMS/IOU switch, or set `force_postprocess_type=True` only when you intentionally want the requested merge type. |

## Export and folder prediction issues

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| No run directory is created | All exports are disabled: `novisual=True`, `export_pickle=False`, `export_crop=False`, and no `dataset_json_path`. | Enable a needed export or set `return_dict=True` only when an export route exists. For low-level one-image APIs, call `result.export_visuals(...)` explicitly. |
| Expected COCO `result.json` is missing | `dataset_json_path` was not provided or source/dataset image mapping failed. | Pass `--dataset_json_path annotations.json` with `--source images/`; confirm COCO image file names resolve under the source folder. Use `../../dataset-tools/SKILL.md` for dataset validation. |
| COCO JSON with video raises an unsupported path | `dataset_json_path` is not implemented for video input. | Run video inference without dataset JSON, or extract frames and create an image dataset before COCO evaluation. |
| Crop export creates many files or is slow | `export_crop` writes one crop per prediction. Duplicate boxes multiply outputs. | Tune postprocess first, then enable crop export on a short subset before a full dataset. |
| Pickle export cannot be read elsewhere | Pickles are Python-specific and version/environment-sensitive. | Prefer COCO JSON for portable prediction exchange. Use pickles only in trusted Python workflows. |

## Video and visualization issues

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `--view_video` opens no window, hangs, or crashes | OpenCV GUI display is unavailable in the session. | Do not use `--view_video` in headless runs. Export video/visuals instead, or add `--novisual` for pure timing. |
| Video export fails with writer/codec errors | OpenCV could not create the output video writer for the input codec/container. | Try a common container/codec, shorten the clip, or run without visual export. If `view_video` is enough and GUI exists, use viewer-only debugging. |
| Video inference is too slow | Rendering/export and per-frame sliced inference are expensive. | Increase `frame_skip_interval`, disable `view_video`, use standard-only as a baseline, or tune slice count. |
| Visual labels clutter the image | Labels/confidences enabled by default in visual exports. | Use `visual_hide_labels=True`, `visual_hide_conf=True`, or CLI `--visual_hide_labels --visual_hide_conf`. Adjust `visual_bbox_thickness`, `visual_text_size`, and `visual_text_thickness` for readability. |

## Progress and batching expectations

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| Progress callback is not called once per image | `progress_callback` belongs to low-level sliced API and reports slice batches, not folder images. | For folder progress, rely on high-level tqdm output. For per-slice callback, call `get_sliced_prediction` directly. |
| Callback jumps by more than one | `batch_size > 1`; the callback receives cumulative processed slices after each batch. | Expect events like `(2, total)`, `(4, total)`, ... when `batch_size=2`. Assert only that the final event reaches total. |
| CLI needs custom progress callback | CLI exposes `--progress_bar` but not Python callback injection. | Use the Python API for callback integration with GUIs or logging. |
| `batch_size=4` changes performance but not expected counts | Backend batching changes throughput, not model semantics. Some backends fall back to sequential inference internally. | Compare serialized predictions for `batch_size=1` and the chosen batch size on a small fixture before scaling up. |

## Safe smoke validation

If the prediction path itself is suspect, run:

```bash
python scripts/sliced_prediction_smoke.py --mode both --slice-size 128 --batch-size 2
```

The script proves that SAHI's base prediction, slicing, shifting, postprocess invocation, batching, and progress callback plumbing can run without detector weights. Passing this smoke does not verify any optional real detector backend.

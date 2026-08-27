# Auto-labeling workflows

This reference summarizes how model-backed auto-labeling flows from the UI through the model manager into concrete YOLO and SAM-family models.

## UI-to-model-manager flow

The auto-labeling widget owns a `ModelManager` and connects UI controls to manager methods:

1. The model selector contains `No Model`, `...Load Custom Model`, then built-in and custom configs.
2. Selecting a built-in model emits the selected config path to `ModelManager.load_model()`.
3. Selecting `...Load Custom Model` opens a YAML file picker and emits that path to `ModelManager.load_custom_model()`.
4. `ModelManager.load_model()` starts a `QThread` and a generic worker for `_load_model()` so downloads and model initialization do not block the UI.
5. After a model loads, the manager emits model metadata, output modes, and selection/unselection signals. For `segment_anything`, it also emits the auto-segmentation-selected signal and requests next files for embedding preload.
6. Clicking Run, pressing Enter in the prompt box, or adding prompt marks calls `predict_shapes_threading(image, filename)`. Prediction also runs on a worker thread.
7. The manager emits an `AutoLabelingResult`; the parent labeling widget inserts the returned shapes into the annotation state.

Only result insertion belongs to broader annotation-data behavior. Model selection, prompts, inference threading, and result content belong here.

## Manager-level lifecycle details

`ModelManager` keeps separate state for model loading/downloading and model execution:

- A new load request is ignored while another model is being loaded.
- Loading a new model unloads the previous model and unselects auto-segmentation when appropriate.
- If a prediction is already running, a new prediction request tries to unload/stop the current model and waits briefly before deciding whether to skip the new request.
- Blocking `predict_shapes()` exists but UI code should prefer `predict_shapes_threading()`.
- `set_auto_labeling_marks()` only forwards marks when the loaded type is `segment_anything`.
- `set_text_prompt()`, `set_prompt_mode()`, and `set_confidence_threshold()` are forwarded only when the concrete model implements the method.

`AutoLabelingResult(shapes, replace=True)` means the caller should replace current shapes; `replace=False` means add/merge these results. YOLO models return `replace=True`. Segment Anything returns `replace=False` so prompted masks add to existing annotations.

## Prompt modes, marks, and output modes

Prompt marks use dictionaries with a `type` and `data`:

- Add point: `{"type": "point", "data": [x, y], "label": 1}`.
- Remove point: `{"type": "point", "data": [x, y], "label": 0}`.
- Rectangle: `{"type": "rectangle", "data": [x1, y1, x2, y2]}`.

The UI exposes Visual and Text prompt modes, but Text is meaningful only for SAM3. Non-SAM3 Segment Anything models are forced to Visual mode and the prompt-mode selector is disabled.

Segment Anything output modes:

- `polygon` (default): each retained contour becomes a closed polygon shape.
- `rectangle`: all retained contours are merged into one bounding rectangle shape.

YOLO output modes:

- `rectangle` only.

## YOLOv5 and YOLOv8 workflow

YOLO models use OpenCV DNN and a single model file. Both follow this high-level path:

1. Resolve `model_path` relative to the config directory, then under the AnyLabeling model cache.
2. Load with `cv2.dnn.readNet()`.
3. If the package build declares GPU preference, set OpenCV DNN CUDA backend and target. This is separate from ONNX Runtime providers used by SAM runners.
4. Convert the Qt image to an OpenCV RGB array.
5. Create a blob with scale `1/255`, configured `input_width` and `input_height`, no crop, and channel swap enabled.
6. Run the network forward pass.
7. Convert center-width-height boxes to image-space corners.
8. Apply thresholds and non-maximum suppression.
9. Emit rectangle `Shape` objects labeled from `classes`.

Differences:

- YOLOv5 reads output layers via `getUnconnectedOutLayersNames()` and uses objectness plus class-score filtering.
- YOLOv8 forwards once, transposes the first output, and filters by maximum class confidence.

If a detector loads but returns no rectangles, check the image content, class list length versus output width, `confidence_threshold`, `score_threshold`, `nms_threshold`, and whether the model export layout matches the expected YOLOv5 or YOLOv8 parser.

## SAM1 / MobileSAM workflow

SAM1 and MobileSAM use `SegmentAnythingONNX`:

1. The encoder session records its input name and dtype.
2. The image is resized with an affine transform to the model input size.
3. The encoder produces `image_embedding` plus `original_size` and `transform_matrix` metadata.
4. Points and rectangles are converted to SAM labels. Rectangles become two points with labels `2` and `3`.
5. The decoder returns masks, which are warped back to the original image size.
6. The wrapper uses the first/highest-quality mask candidate for post-processing.

SAM1/MobileSAM do not use text-only prompts. Without marks, the wrapper returns an empty `AutoLabelingResult` with `replace=False`.

## SAM2 ONNX workflow

SAM2 uses `SegmentAnything2ONNX`:

1. The image encoder preprocesses to CHW tensors and runs with available ONNX Runtime providers.
2. The encoder returns `high_res_feats_0`, `high_res_feats_1`, and `image_embedding` plus original image size.
3. The decoder sets the original image size before each prediction.
4. Points and rectangles are normalized to the encoder input size.
5. The decoder scores candidate masks, selects the best-scoring mask, resizes it back to original image size, and returns a single mask in a nested array shape.

SAM2 is detected by a decoder ONNX input named `high_res_feats_0` when the CoreML branch is not selected.

## SAM3 ONNX workflow

SAM3 uses `SegmentAnything3ONNX` and supports both visual prompts and text-only prompts.

### Model components

- Image encoder: current exports accept CHW `uint8` input and include normalization; older float exports receive normalized `float32` in `[-1, 1]`.
- Language encoder: tokenizes a text prompt and emits `language_mask`, `language_features`, and `language_embeds`. If the optional `osam` tokenizer import is unavailable, a zero-token fallback is used and language results may be meaningless.
- Decoder: consumes original image size, vision positional encodings, backbone FPN features, language tensors, and box prompt tensors. It returns ONNX outputs in the order boxes, scores, masks; the wrapper returns masks, scores, boxes for caller convenience.

### Text prompt behavior

SAM3 text mode is active only when the UI prompt mode is Text. In Text mode:

- Geometric prompt buttons are hidden.
- The text prompt is split on commas.
- Each non-empty term is handled as a separate class term.
- The image features are reused; `update_language()` re-runs only the language encoder for each term.
- Each detected object mask is post-processed individually.
- Result labels are the class terms themselves, such as `cat` or `bottle`.

In Visual mode:

- Points and rectangles are used as geometric prompts.
- The current text prompt is used as a single visual/language cue for SAM3 when present.
- Result labels are `AUTOLABEL_OBJECT`.

The confidence spin box controls SAM3 score filtering. Masks with `score <= confidence_threshold` are removed. If all masks are filtered out, the result is empty.

### SAM3 geometric prompts

SAM3 represents geometry as normalized box prompts:

- A rectangle becomes center x, center y, width, height normalized by original image width/height and sets `box_masks` false.
- A point becomes a tiny 1% box centered on the point and sets `box_masks` false.
- No geometry uses a dummy box and sets `box_masks` true, which enables text-only detection.

The SAM3 decoder accepts simplified ONNX graphs. Inputs removed by simplification are not forwarded; dummy language tensors are supplied when the decoder expects language inputs but no language encoder output is present.

## Segment Anything post-processing

The wrapper post-processes a 2-D mask to AnyLabeling shapes:

1. Strip extra dimensions until a 2-D mask remains.
2. Cast bool/float/uint8 masks to `float32`, threshold positive values to 255, then cast to `uint8`. This avoids NumPy 2.x bool-assignment failures.
3. Find external contours.
4. Approximate contours with a small epsilon.
5. Remove huge contours when multiple contours exist and a contour covers more than 90% of image area.
6. Remove very small contours when multiple contours exist and a contour area is below 20% of average contour area.
7. Emit polygons or one merged rectangle according to output mode.

Blank masks produce no shapes.

## Embedding cache and preload behavior

Segment Anything keeps a thread-safe LRU cache of image embeddings:

- Default cache size: 10 entries.
- Preloaded size: cache size minus 3.
- Cache key: filename passed to prediction/preload.
- Changing the text prompt clears the cache so SAM3 language-conditioned embeddings are not reused for stale prompts.
- `on_next_files_changed()` preloads embeddings for upcoming files only for `segment_anything` models.

If an image appears to use stale segmentation features, check whether the filename key is stable, whether text prompt changes are reaching `set_text_prompt()`, and whether a previous inference was interrupted by `unload()`.

## Optional real-inference playbook

Real inference is intentionally optional because model files can be large and network access may be unavailable.

1. Start with unit-level diagnostics and config checks. Do not download multi-GB models just to validate YAML.
2. For a minimal detector check, use a small YOLOv8n model archive when available.
3. For SAM-family checks, MobileSAM is much smaller than SAM3. SAM2 Hiera-Tiny is moderate. SAM3 ViT-H is large and should be downloaded only when SAM3 code paths, text prompts, or variant detection changed.
4. Place models in the standard AnyLabeling model cache under their catalog `name` and ensure each downloaded folder has a `config.yaml` plus the expected ONNX or CoreML files.
5. Use a representative image for text prompts. SAM3 text-only tests that ask for `truck` need an image that actually contains a truck; a generic sample image can make text-prompt assertions fail even when the pipeline is healthy.
6. Prefer tests that skip cleanly when files are absent. A missing optional model should be recorded as unavailable, not as a code failure.

Real-inference caveats:

- SAM3 models can be several gigabytes.
- Hugging Face downloads may require reliable network and enough disk space.
- ONNX Runtime provider selection for SAM runners is independent of the package's CPU/GPU wheel name.
- CoreML checks require macOS and `coremltools`; do not treat a Linux/Windows CoreML failure as evidence that ONNX SAM2 is broken.

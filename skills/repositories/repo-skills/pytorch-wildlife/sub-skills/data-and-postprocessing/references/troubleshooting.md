# Data and post-processing troubleshooting

## Import and dependency failures

- **Import fails before using data utilities:** the package imports many model
  families eagerly from its top-level model surface. Confirm the installation
  is the intended `PytorchWildlife` 1.3.0 distribution, inspect the first
  missing dependency in the traceback, and repair the isolated environment
  rather than copying files into the package. A broken optional model import
  can prevent access to unrelated utilities.
- **Legacy MegaDetector v5 import fails in a modern environment:** this path
  has compatibility sensitivity in newer Python/PyTorch/vision combinations.
  Confirm the selected v5 path and package versions, use a supported modern
  environment or an explicitly reviewed compatibility workaround, and record
  the workaround in the environment handoff. Do not publish private shim code
  or assume v5 weight downloads are available.
- **Weights unexpectedly download:** constructors with `pretrained=True` may
  fetch weights. Use `pretrained=False` or a verified local weight path for
  structural checks, and keep downloads out of tests that promise no network.

## Dataset and crop failures

- **No images found:** check that files use one of the case-insensitive
  extensions documented in `data-formats.md`. The folder loader walks nested
  directories but does not interpret class-folder labels.
- **Tensor shape or color is wrong:** folder loaders convert to RGB before
  transforms. Use a PIL image for `Classification_Inference_Transform`; use a
  CHW tensor or RGB array appropriate for `MegaDetector_v5_Transform`. Verify
  the batch dimension is added by the DataLoader/model path, not by the
  dataset item.
- **Classifier crop path missing:** `DetectionCrops` resolves `path_head /` 
  `img_id` only when `path_head` is given. Ensure detector ids are relative to
  that root, or use absolute ids intentionally. Every animal crop is selected
  by `class_id == animal_cls_id` (default `0`); non-animal detections are not
  passed to the classifier.
- **Boxes crop the wrong region:** detection boxes are image-space `xyxy`
  coordinates. Do not pass normalized `xywh` TimeLapse boxes to
  `DetectionCrops` without converting them back to pixel `xyxy` first.

## Serialization and paths

- **Wrong number of categories/confidences:** serializers assume parallel
  arrays. Reject or repair mismatched arrays before calling them; the bundled
  separation helper fails closed instead of truncating with `zip`.
- **Absolute paths leak into JSON:** use `exclude_file_path` with the exact
  native prefix or build relative ids at the result boundary. Inspect the
  emitted JSON before sharing it; the native option performs string-prefix
  replacement, not canonical path sanitization.
- **TimeLapse boxes are invalid:** supply one `normalized_coords` `xyxy` row
  per retained detection. The serializer converts it to normalized `xywh`.
  Empty frames use an empty-string maximum confidence by design.
- **Classification labels do not align:** plain classification serialization
  consumes classifier results in grouped order, while the classification
  TimeLapse serializer associates classifications by image. Preserve crop
  order and validate the output against detection count; do not infer a
  per-box mapping that the current function does not encode.
- **Separation copied the wrong image:** category `0` is positive only when
  confidence is strictly greater than the threshold. Empty/missing-category
  annotations are negative. Prefer the bundled helper for untrusted JSON:
  it validates relative non-traversing ids, checks containment and existence,
  preserves nested paths, copies rather than moves, rejects an output inside
  the source root, and refuses overwrite unless requested.

## Video and UI failures

- **Processed video will not play in a browser:** try a newer browser or an
  OpenCV build with `avc1`; retain `mp4v` as the fallback. Confirm the output
  file exists and that the codec is available in the installed OpenCV build.
- **Callback receives unexpected indexing:** `process_video` may stride frames
  to meet `target_fps`; `index` is the callback's sampled-frame counter. Do
  not use it as the original timestamp without tracking source FPS and stride.
- **Video upload or ZIP batch fails:** reduce fixture size, inspect free
  temporary disk, and test the local model/data path separately. Large uploads
  are a known Gradio/demo limitation, especially on Windows. Never solve this
  by exposing the app publicly or disabling file validation.
- **UI is reachable by others:** stop the process or bind it to loopback,
  keep `share=False`, and add authentication/reverse-proxy controls before
  remote use. A Gradio demo has no built-in user authentication boundary for
  research data.

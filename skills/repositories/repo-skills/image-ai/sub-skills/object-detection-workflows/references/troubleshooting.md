# Object Detection Troubleshooting

Use this guide for still-image detection failures. Route video/camera/callback failures to `video-detection-workflows`; route dataset/training/conversion issues to `custom-training-and-data`.

## Model and asset errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `invalid path, path not pointing to a valid file` or `invalid path, path not pointing to the weightfile` | `setModelPath()` was given a missing path. | Pass an existing `.pt` or `.pth` file. Do not rely on current working directory; resolve model paths explicitly. |
| TensorFlow `.h5` compatibility error | ImageAI 3.x uses the PyTorch backend. | Use ImageAI 3.x `.pt`/`.pth` weights, or intentionally use an older ImageAI 2.1.6-era environment for legacy `.h5` models. |
| `Invalid model file ... Please parse in a '.pt' and '.pth' model file.` | Model extension is not `.pt` or `.pth`. | Supply a PyTorch ImageAI weight file. Rename only if the contents are truly PyTorch state dict weights. |
| `Invalid weights!!!` | Weight file does not match the selected model architecture or custom label/anchor config. | Match `setModelTypeAs...()` to the weight family. For custom models, use the detection JSON generated with those weights. |
| Error loading custom JSON or missing `anchors`/`labels` | `CustomObjectDetection.setJsonPath()` points to the wrong file or a malformed config. | Provide the ImageAI custom detection config JSON with top-level `labels` and `anchors`. Route asset production to `custom-training-and-data` if needed. |
| `Invalid model type...` before loading | No model-type setter was called, or RetinaNet was requested in custom mode. | For COCO call one of RetinaNet/YOLOv3/TinyYOLOv3 setters. For custom detection use only YOLOv3 or TinyYOLOv3. |

## Object filter errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `object 'X' doesn't exist in the supported object classes` | `CustomObjects` keyword does not match the loaded COCO label list. | Check [coco-object-classes.md](coco-object-classes.md). Replace spaces with underscores and account for YOLO versus RetinaNet label differences. |
| Car/motorcycle filter works for RetinaNet but not YOLO, or vice versa | Label naming differs by class file. | YOLO/TinyYOLO use `motorbike`; RetinaNet uses `motorcycle`. Similar differences include `aeroplane`/`airplane`, `sofa`/`couch`, `tvmonitor`/`tv`. |
| Custom model filter returns no objects | Dictionary keys do not match custom JSON labels after replacing spaces with underscores. | Inspect the JSON `labels` list and create keys from those exact labels. Omit the filter to confirm the model detects anything first. |
| Older code calls `detectCustomObjectsFromImage` and fails | Current ImageAI 3.x still-image source uses `detectObjectsFromImage(custom_objects=...)`. | Replace the method call with `detectObjectsFromImage` and pass the `custom_objects` dictionary. |

## Output and extraction errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid output_type '...'` | `output_type` is not exactly `file` or `array`. | Use `output_type="file"` or `output_type="array"`. |
| No annotated image is written | `output_type="file"` was used without `output_image_path`. | Provide `output_image_path` when a saved annotated file is desired. The API still returns detections if no output path is supplied. |
| Extraction in file mode fails with a directory-exists error | Current source uses `os.mkdir()` for `output basename + "-extracted"`; it does not reuse existing extraction directories. | Delete or rename the existing extraction directory before the call, or choose a fresh output filename. |
| Extraction paths directory name differs from old docs | Current source appends `-extracted`, while some older docs describe `-objects`. | Trust the current source behavior: output basename plus `-extracted`. |
| Returned extraction list is empty | No detections survived `minimum_percentage_probability`, or no detections were produced. | Lower `minimum_percentage_probability` for diagnosis, verify the input image and model family, then raise the threshold after detections appear. |
| File output with extraction but missing output path | Extraction paths need an output basename to derive the extraction directory. | Use file output with an explicit `output_image_path`, or use `output_type="array"` with extraction to receive crop arrays. |

## Image input and array behavior

| Symptom | Likely cause | Fix |
|---|---|---|
| `image path '...' is not found or a valid file` | Missing input file, unsupported file extension, or relative path resolved against unexpected cwd. | Use an explicit path to `.jpg`, `.jpeg`, or `.png`. The bundled helper resolves paths without assuming cwd. |
| `Invalid image input format` | Input is not a path, Numpy array, or PIL image. | Pass a supported object directly as `input_image`; current source does not need `input_type`. |
| Unexpected colors in returned arrays or crops | ImageAI reads arrays with OpenCV conventions and renders output arrays in BGR order. | Convert BGR/RGB explicitly at application boundaries, for example before displaying with PIL or returning through a web API. |
| Older examples using `input_type="array"` fail | Current still-image signatures do not include `input_type`. | Pass the Numpy array directly as `input_image` and set only `output_type="array"` if you need an array returned. |

## Threshold, no-detection, and display confusion

| Symptom | Likely cause | Fix |
|---|---|---|
| No detections | Threshold too high, wrong model family, bad weights/config, unsupported labels, or image has no target objects. | Start without `custom_objects`, use a moderate `minimum_percentage_probability` such as 30-50, verify the model path/config, then restore stricter filters. |
| Too many false positives | Threshold too low or custom YOLO objectness too permissive. | Increase `minimum_percentage_probability`; for custom detection also increase `objectness_treshold` or adjust `nms_treshold`. |
| Changing display flags changes only the image, not returned detections | `display_object_name`, `display_percentage_probability`, and `display_box` affect rendering only. | Use `minimum_percentage_probability` and filters to change the detection list. |
| Confusion between percentage and score units | Detections return percentage values, but internal thresholds compare 0-1 scores. | Pass `minimum_percentage_probability` in 0-100 units. Custom `nms_treshold`/`objectness_treshold` use 0-1 units. |

## RetinaNet COCO91 note

RetinaNet changes the class list to COCO91 during `loadModel()`. The returned labels and `CustomObjects` keyword names may include COCO91-only names such as `street sign`, `hat`, `shoe`, `eye glasses`, `plate`, `mirror`, `window`, `desk`, `door`, `blender`, and `hair brush`, plus `unlabeled`. If a COCO80 label keyword fails, check the RetinaNet list in [coco-object-classes.md](coco-object-classes.md).

## Helper-script diagnostics

The bundled `scripts/detect_image.py` performs preflight checks before loading weights. Typical parser/runtime messages:

- `--json-path is required in custom mode`: custom model inference needs the detection config JSON.
- `retinanet is only supported in --mode coco`: custom detection supports only YOLOv3/TinyYOLOv3.
- `--output-image is required when --output-type file is used with --extract`: extraction file paths need a basename.
- `Extraction directory already exists`: choose a new output image path or remove the directory first.
- `Unsupported object names`: the helper validates filters against COCO lists or custom JSON labels before inference when possible.

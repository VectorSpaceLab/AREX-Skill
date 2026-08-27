# Custom model configs and adapter workflow

This reference covers model YAML structure, custom-model loading rules, and the
difference between config-only customization and adding a new adapter. It is
self-contained; do not rely on a repository checkout to interpret it.

## Minimum config contract

For custom model loading, the config file must be valid YAML and must include:

```yaml
type: yolov8
name: my-detector-v1
display_name: My detector
```

- `type`: adapter identifier. For config-only customization it must be one of
  X-AnyLabeling's supported custom model types (for example `yolov8`,
  `segment_anything`, `ppocr_v6`, `remote_server`). If the type is new, follow
  the unadapted-model development workflow below.
- `name`: internal model index. Custom names may contain only letters, numbers,
  dots, underscores, and hyphens; they must not be `.` or `..`; they must be one
  path segment with no slash, backslash, absolute path, or spaces.
- `display_name`: human-readable name shown in the UI dropdown.

Model-specific adapters usually require more fields. The base `Model` class
checks each adapter's `Meta.required_config_names` before inference starts.
Common required fields include `model_path`, `classes`, threshold fields,
encoder/decoder path pairs, OCR detector/recognizer path pairs, or remote/API
settings.

## Common optional and model-specific fields

| Field | Meaning | Typical models |
|---|---|---|
| `provider` | Informational provider/source name shown with the config. | Almost all built-in configs. |
| `model_path` | Local path, relative path, absolute path, HTTP(S) URL, or model id for adapters that support model-id loading. | YOLO, DETR, classification, SAM video, Florence2, RAM, depth, matting. |
| `encoder_model_path`, `decoder_model_path` | Separate encoder/decoder files. | SAM, SAM2, SAM3, GeCo, grounding+SAM, OpenVision. |
| `det_model_path`, `rec_model_path`, `cls_model_path` | OCR detector/recognizer/classifier files. | PPOCR v4/v5/v6. |
| `classes` | Label list or, for some pose configs, a mapping from class to keypoint names. Boolean-looking names such as `yes`, `no`, `on`, `off`, `true`, and `false` are loaded as strings under `classes`/`filter_classes`. | Detection, segmentation, classification, pose, OCR/layout. |
| `filter_classes` | Optional active subset for class filtering. | Detection/segmentation families that expose class filtering. |
| `conf_threshold`, `iou_threshold`, `confidence_threshold`, `nms_threshold` | Confidence, IoU, SAHI, or NMS thresholds; names vary by adapter. | YOLO/DETR/SAHI/grounding/counting/lane families. |
| `max_det` | Maximum detections to keep. | YOLO-family configs. |
| `input_width`, `input_height`, `input_size`, `target_size` | Fixed inference size or model-specific target size. | YOLO variants, SAM variants, lane, grounding. |
| `engine` | YOLO-family backend selector: `ort`, `dnn`, or `trt`. | YOLO base families including `yolo26`. |
| `tracker` | Tracker options including `tracker_type` such as `bytetrack`, `botsort`, or `tracktrack`. | `*_track` model types. |
| `config_file` | Added by ModelManager when a config is loaded; built-ins use resource-style values and custom configs use absolute normalized file paths. | Runtime-internal field; do not rely on users to author it. |

## Adapted custom model workflow

Use this when the model architecture is already supported by an existing
`type`.

1. Choose the nearest built-in family from
   [model-overview.md](model-overview.md). Match task, output shape, model file
   format, and expected ONNX/input/output contract.
2. Copy the shape of that config into a new YAML file under your project/model
   workspace. Keep the same `type`; choose a unique valid `name`; set a clear
   `display_name`.
3. Point path fields at local files or reachable URLs. Relative paths are
   resolved first from the current process directory and then relative to the
   YAML file's folder.
4. Update `classes` to exactly match training/export class order. For pose,
   keep the keypoint mapping consistent with the model's keypoint metadata.
5. Tune thresholds such as `conf_threshold`, `iou_threshold`, `max_det`,
   `epsilon_factor`, `filter_classes`, or adapter-specific OCR/lane parameters.
6. For older YOLOv5 exports only, include `anchors` and `stride` if the adapter
   requires them. Do not add anchors/stride to newer YOLO exports unless the
   selected adapter expects them.
7. If using a YOLO-family TensorRT engine, set `engine: trt` and use a `.engine`
   `model_path`. Otherwise leave `engine` absent or set it to `ort`/`dnn`.
8. Load the YAML through the UI's custom model loader. The loader validates the
   minimum fields and saves the custom entry before attempting to load the
   actual model.

Example adapted YOLO-style config:

```yaml
type: yolov8
name: factory-detector-v1
display_name: Factory detector v1
provider: Internal
model_path: ./weights/factory-detector.onnx
conf_threshold: 0.25
iou_threshold: 0.45
max_det: 300
classes:
  - part
  - scratch
  - missing_screw
filter_classes:
  - scratch
  - missing_screw
```

Example TensorRT variant:

```yaml
type: yolo26
name: factory-detector-trt-v1
display_name: Factory detector TensorRT v1
provider: Internal
model_path: ./weights/factory-detector.engine
engine: trt
conf_threshold: 0.25
max_det: 300
classes:
  - part
  - scratch
```

## Custom ModelManager behavior

- At most five custom models are retained. Adding a sixth custom model drops the
  least-recently-used saved custom entry.
- Custom configs are stored in the user configuration and merged into the model
  list on ModelManager initialization.
- Invalid or missing custom config files are removed from the active custom list
  during registry loading.
- A custom config `name` is validated before saving. Valid examples include
  `ok.Name-1`, `_underscore`, and `a..b`. Invalid examples include `bad/name`,
  `nested\\model`, `/absolute/path`, `has space`, `.`, `..`, non-ASCII names,
  and the empty string.
- Custom loaded configs are marked `is_custom_model: true` and their runtime
  `name` is prefixed with `_custom_` if it does not already have that prefix.
  Do not include `_custom_` in user docs unless referring to runtime internals.

## Unadapted model development workflow

Use this only when no existing adapter can consume the model by config changes.
This is source-code work, not a normal custom-loader operation.

1. Define a new YAML config with mandatory `type`, `name`, and `display_name`,
   plus fields required by the implementation, such as `model_path`, `classes`,
   thresholds, or encoder/decoder files.
2. Add a model-registry entry mapping `model_name` to the config file.
3. Add the new `type` to the custom-capable type list and, if needed, to UI
   behavior lists for widgets such as confidence/IoU controls, prompts,
   mask fineness, class filtering, preserving existing annotations, reset
   tracker, cached auto-labeling, or API token support.
4. Implement a subclass of `Model` with a `Meta` class:
   - `required_config_names`: the fields that must exist before initialization.
   - `widgets`: UI controls needed by the adapter.
   - `output_modes` and `default_output_mode`: rectangle, polygon, point,
     rotated box, or another supported output mode.
5. In `__init__`, call `super().__init__`, resolve model files with
   `get_model_abs_path`, create the inference engine, and validate model-specific
   metadata before predicting.
6. Implement `predict_shapes(self, image, filename=None)` to return an
   `AutoLabelingResult` with X-AnyLabeling `Shape` objects, and implement
   `unload(self)` to release model/session resources.
7. Add a branch in the model-loading manager that imports and instantiates the
   new adapter for the new `type`, and emits the correct segmentation-selected
   state when the model is promptable/SAM-like.
8. Add safe tests for config registration, required-field errors, postprocessing,
   and any edge-case metadata parsing. Do not test by downloading large weights
   unless the test explicitly owns that expensive dependency.

Minimal adapter shape, distilled:

```python
class MyModel(Model):
    class Meta:
        required_config_names = ["type", "name", "display_name", "model_path"]
        widgets = ["button_run"]
        output_modes = {"rectangle": "Rectangle"}
        default_output_mode = "rectangle"

    def __init__(self, model_config, on_message):
        super().__init__(model_config, on_message)
        model_abs_path = self.get_model_abs_path(self.config, "model_path")
        if not model_abs_path:
            raise FileNotFoundError("Could not initialize model")
        # create engine/session here

    def predict_shapes(self, image, filename=None):
        # convert image, run inference, create Shape objects
        return AutoLabelingResult([], replace=True)

    def unload(self):
        # release session/model handles
        pass
```

## Config validation without weights

Use the bundled inspector to parse YAML and check registry-style constraints
without downloading or instantiating model weights:

```bash
python sub-skills/auto-labeling-models/scripts/inspect_model_configs.py \
  --custom-config ./my-model.yaml --json
```

This verifies YAML parseability, minimum custom fields, valid custom name,
whether the `type` is in the supported custom type list, and missing path-like
fields. It cannot prove that a model file matches the adapter's tensor contract;
that requires loading the model in a prepared runtime.

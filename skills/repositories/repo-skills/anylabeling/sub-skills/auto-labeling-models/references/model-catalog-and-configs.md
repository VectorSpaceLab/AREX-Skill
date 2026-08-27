# Model catalog and custom config contracts

This reference covers the data and extension contracts for AnyLabeling's auto-labeling models. It is self-contained and names Python modules by import path only; do not depend on a particular source checkout being available.

## Core model types and registration

AnyLabeling auto-labeling uses a singleton registry:

- `ModelRegistry.register(type_name)` is a class decorator. It stores the concrete model class under the string key and returns the class unchanged.
- `ModelRegistry.get(type_name)` returns the registered class or `None`.
- `ModelRegistry.list_models()` returns the currently registered type keys.

The supported model type keys verified for this skill are:

| Type key | Concrete purpose | Runtime output default |
| --- | --- | --- |
| `segment_anything` | Segment Anything / MobileSAM / SAM2 / SAM3 / CoreML SAM2 wrapper | polygon masks by default, rectangle optional |
| `yolov5` | YOLOv5 OpenCV-DNN object detector | rectangles |
| `yolov8` | YOLOv8 OpenCV-DNN object detector | rectangles |

Registration happens by import side effect. The package-level auto-labeling module imports the concrete modules so their decorators execute. If a new model class is added, it must be imported by the package auto-labeling initializer as well as registered with `@ModelRegistry.register("new_type")`; otherwise `ModelManager` can see a catalog entry but still raise `Unknown model type` when loading it.

## Built-in catalog behavior

The built-in catalog is a YAML list named `models.yaml` in the package auto-labeling config resources. The verified catalog has 22 entries:

- 17 entries with `type: segment_anything`.
- 5 entries with `type: yolov8`.
- No built-in `yolov5` entries, although custom `yolov5` configs are accepted by the custom-model gate.

Each built-in catalog entry must include:

| Field | Meaning |
| --- | --- |
| `name` | Stable model id. Also names the local model cache subdirectory. |
| `display_name` | Text shown in the model selector. |
| `download_url` | A `.zip` URL or a Hugging Face repository URL used only when the built-in model is not downloaded. |
| `type` | Registry key such as `segment_anything` or `yolov8`. |

Many built-in entries intentionally omit concrete `model_path`, `encoder_model_path`, and `decoder_model_path` fields in the packaged catalog because downloaded archives include a fuller `config.yaml`. `ModelManager.load_model_configs()` overlays an already-present cache `config.yaml` on top of the catalog entry. This lets fields present in the catalog survive if the cached file is sparse, while downloaded configs supply model paths and thresholds.

Use the bundled `scripts/inspect_model_catalog.py` to summarize a catalog without downloading anything.

## Download and cache semantics

`ModelManager` handles built-in model setup as follows:

1. Load the built-in catalog from package resources.
2. For each built-in model, ensure a cache directory exists under `$HOME/anylabeling_data/models/<name>/` and ensure a `config.yaml` is present there.
3. If the cache config does not exist, write the catalog entry into that cache config and mark `has_downloaded: false` in memory.
4. On selection, if `has_downloaded` is false, download from `download_url` into a temporary directory.
5. If the URL ends in `.zip`, download and extract the zip, then find a contained `config.yaml`.
6. If the URL starts with `https://huggingface.co`, call `snapshot_download()` for the repository and then write the current model config as `config.yaml` in the snapshot directory.
7. Replace the model cache directory with the extracted/snapshot directory, then set `has_downloaded: true` in the cache config.

Important consequences:

- Built-in downloads are side-effecting and network dependent; the bundled diagnostic scripts do not trigger them.
- A missing `download_url` prevents first-time built-in model load.
- Hugging Face failures are usually network, proxy, authentication/rate-limit, or disk-space issues rather than YAML schema issues.
- UTF-8 BOMs in YAML are handled by reading configs with `utf-8-sig`; custom diagnostics should do the same.

## Custom model admission gate

A custom model is loaded from a user-selected YAML file. The custom-model gate requires the file to exist and parse to a mapping with:

- `type`
- `name`
- `display_name`
- `type` in exactly `segment_anything`, `yolov5`, or `yolov8`

Custom models are stored in user config and marked as already downloaded. The custom loader does not use `download_url` to fetch files. Referenced model files must already exist either next to the custom config or under `$HOME/anylabeling_data/models/<name>/`.

At most five custom models are kept. Re-adding the same config path updates its `last_used`; adding a sixth custom config drops the least-recently used record from the app config and attempts to remove the old empty config directory.

Use the bundled `scripts/check_custom_model_config.py` before loading a custom YAML in the UI.

## Runtime path resolution for model files

All concrete model classes inherit `Model.get_model_abs_path(model_config, field_name)`. It resolves each path field in this order:

1. A file or directory matching the field value relative to the directory containing `config.yaml`.
2. A file or directory under `$HOME/anylabeling_data/models/<name>/<field value>`.

The method returns the cache candidate even when it does not exist, so concrete model initializers or ONNX/CoreML sessions are the point where missing files become failures. Diagnostics should therefore check both the relative config directory and the model cache candidate explicitly.

## Segment Anything config fields

`segment_anything` covers SAM1, MobileSAM, SAM2, SAM3, and one CoreML SAM2 branch. The class-level required fields are:

| Field | Required by base check | Also required at runtime | Notes |
| --- | --- | --- | --- |
| `type` | yes | yes | Must be `segment_anything`. |
| `name` | yes | yes | Used for cache lookup. |
| `display_name` | yes | yes | Shown in UI. |
| `encoder_model_path` | yes | yes | File for ONNX encoders or directory/package path for CoreML assets. |
| `decoder_model_path` | yes | yes | File for ONNX decoder or CoreML package path. |
| `input_size` | no | yes | Accessed directly by the wrapper. |
| `max_width` | no | yes | Accessed directly by the wrapper. |
| `max_height` | no | yes | Accessed directly by the wrapper. |
| `language_encoder_path` | no | required for SAM3 path in current wrapper | Required when `language_encoder_path` is present or the decoder is detected as SAM3. |
| `confidence_threshold` | no | optional | Defaults to `0.5`; used by SAM3 score filtering. |

Segment Anything output modes are `polygon` and `rectangle`; default is `polygon`.

### SAM variant detection

The wrapper loads the decoder ONNX graph once and checks input names:

1. If the decoder has `backbone_fpn_0` or `language_mask`, it is treated as SAM3.
2. Else if the decoder has `high_res_feats_0`, it is treated as SAM2.
3. Else it is treated as SAM1 / MobileSAM.

`vision_pos_enc_0` and `vision_pos_enc_1` are deliberately not used for SAM3 detection because ONNX simplification may remove them.

A config with `language_encoder_path` is also forced down the SAM3 path. A custom config whose decoder is SAM3 but lacks `language_encoder_path` is a known difficult failure: variant detection selects SAM3, then the wrapper tries to resolve the missing `language_encoder_path` key. Add a valid language encoder path or adjust the wrapper before expecting the custom config to load.

### CoreML branch

The CoreML SAM2 branch is selected when the resolved decoder path string contains `coreml`. The CoreML implementation lazily imports `coremltools` and loads three `.mlpackage` assets in one directory:

- `SAM2_1LargeImageEncoderFLOAT16.mlpackage`
- `SAM2_1LargeMaskDecoderFLOAT16.mlpackage`
- `SAM2_1LargePromptEncoderFLOAT16.mlpackage`

CoreML is macOS-oriented. A custom CoreML config whose resolved decoder path does not contain `coreml` may accidentally fall through to ONNX variant detection even if it points at a `.mlpackage` directory.

## YOLOv5 and YOLOv8 config fields

Both YOLO model types use OpenCV DNN, accept the same config schema, and emit rectangle shapes with `replace=True`.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | `yolov5` or `yolov8`. |
| `name` | yes | Used for cache lookup. |
| `display_name` | yes | Shown in UI. |
| `model_path` | yes | Usually an ONNX model file, resolved next to config first, then model cache. |
| `input_width` | yes | Blob width; positive integer. |
| `input_height` | yes | Blob height; positive integer. |
| `score_threshold` | yes | Used by YOLOv5 class-score filtering; still required by YOLOv8 metadata. |
| `nms_threshold` | yes | Passed to `cv2.dnn.NMSBoxes`. |
| `confidence_threshold` | yes | Objectness/filter threshold. |
| `classes` | yes | Non-empty class-name list. Shape labels come from this list. |

YOLOv5 parses outputs shaped like `[1, 25200, 85]` for COCO-style exports. YOLOv8 transposes the first forward output and expects rows with four box coordinates plus class scores, often `[1, 8400, 84]` for 80 classes.

## Adding a new model type safely

When extending AnyLabeling with a new auto-labeling model type:

1. Implement a `Model` subclass with `Meta.required_config_names`, `Meta.widgets`, `Meta.output_modes`, and `Meta.default_output_mode`.
2. Decorate it with `@ModelRegistry.register("new_type")`.
3. Import the module in the package auto-labeling initializer so registration happens on normal startup.
4. Add a catalog entry with `type: new_type` and any required fields.
5. If the new type should be accepted as a custom model, update the custom-model type allow-list in `ModelManager.load_custom_model()`; registration alone is not enough for custom configs.
6. Provide a no-download diagnostic path analogous to the bundled scripts so users can validate YAML and local paths before opening the UI.

For the difficult case "Unknown model type after adding a new class and a catalog entry," check import-side registration first, then the catalog `type` string, then the custom-model allow-list if the model is loaded through the custom config UI.

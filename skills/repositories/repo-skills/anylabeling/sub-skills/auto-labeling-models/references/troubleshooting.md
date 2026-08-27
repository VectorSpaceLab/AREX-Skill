# Auto-labeling model troubleshooting

Use this reference when AnyLabeling's model-backed auto-labeling fails to load, download, prompt, infer, or produce expected shapes.

## Fast triage checklist

1. Identify whether the failure is at catalog discovery, custom config admission, download/cache setup, model initialization, inference, or post-processing.
2. Run `scripts/inspect_model_catalog.py` for built-in catalog questions or `scripts/check_custom_model_config.py` for a custom YAML. These scripts are read-only and do not download models.
3. Confirm the model `type` is one of the registered/runtime-supported types: `segment_anything`, `yolov5`, `yolov8`.
4. Confirm every required path field resolves either next to the config file or inside `$HOME/anylabeling_data/models/<name>/`.
5. For Segment Anything, determine the actual variant: SAM3 by `backbone_fpn_0` or `language_mask`; SAM2 by `high_res_feats_0`; fallback SAM1/MobileSAM otherwise.
6. For UI prompt issues, distinguish Visual mode from Text mode. Text-only detection is SAM3-only.

## Unknown model type

Symptom examples:

- Loading a catalog entry raises `Unknown model type: <name>`.
- A newly added model appears in `models.yaml` but cannot instantiate.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Concrete model module was not imported at package auto-labeling startup. | Import the module in the package auto-labeling initializer so `@ModelRegistry.register(...)` executes. |
| Catalog `type` string does not exactly match the registered decorator key. | Make the YAML `type` and decorator key identical. |
| Custom model uses a new registered type not in the custom-model allow-list. | Add the type to the custom-model validation gate if custom YAML loading should support it. |
| Duplicate registration overwrote an existing type. | Check registry warnings and avoid reusing a type key unless replacement is intentional. |

Difficult extension case: after adding a new class and catalog entry, first verify `ModelRegistry.list_models()` contains the type after importing the package auto-labeling module; then inspect the YAML `type`; then update the custom gate only if the failing path is `...Load Custom Model`.

## Invalid custom config

Symptoms:

- UI status says `Error in loading custom model: Invalid path.`
- UI status says `Error in loading custom model: Invalid config file.`
- UI status says `Error in loading custom model: Invalid config file format.`
- Loading starts but then fails with a missing key or missing model-file error.

Checks:

1. The selected file must exist and be YAML.
2. The root YAML object must be a mapping, not a list or scalar.
3. Common fields must include `type`, `name`, and `display_name`.
4. `type` must be `segment_anything`, `yolov5`, or `yolov8` for the custom-model UI path.
5. Type-specific fields must be present. Segment Anything also needs runtime fields `input_size`, `max_width`, and `max_height` even though they are not in the base required-field list.
6. If the file was created on Windows, read with UTF-8 BOM handling. AnyLabeling uses `utf-8-sig` for model configs.

Run:

```bash
python scripts/check_custom_model_config.py /path/to/config.yaml
```

Use `--schema-only` when model files are intentionally absent and you only want YAML/key validation.

## Missing model files

Symptoms:

- `Could not download or initialize encoder of Segment Anything.`
- `Could not download or initialize decoder of Segment Anything.`
- `Could not download or initialize YOLOv5 model.`
- `Could not download or initialize YOLOv8 model.`
- ONNX Runtime or OpenCV DNN reports file-not-found.

Resolution order:

1. Check whether the path field value exists relative to the directory containing `config.yaml`.
2. If not, check `$HOME/anylabeling_data/models/<name>/<path field value>`.
3. For custom configs, remember that `download_url` is not used to fetch files. Put files in one of the two resolution locations.
4. For built-ins, inspect whether cache `config.yaml` has `has_downloaded: true` and whether the downloaded archive/snapshot actually contains the files named by config.
5. For `.mlpackage` CoreML assets, accept directories as model paths.

## Missing download URL or failed download

Symptoms:

- `Missing download_url in config file.`
- `Could not download model.`
- Hugging Face snapshot errors.
- A zip download succeeds but extraction cannot find `config.yaml`.

Likely causes:

- Built-in cache config says `has_downloaded: false` but lacks `download_url`.
- Network, DNS, proxy, TLS interception, rate-limit, or Hugging Face availability issue.
- Not enough disk space for temporary download/extraction.
- Archive format changed and no contained `config.yaml` is present.

Fixes:

- Restore the built-in catalog/cache config with a valid `download_url`.
- Retry with network/proxy settings appropriate for the environment.
- Pre-download the model externally and place a complete folder in the model cache.
- For Hugging Face, verify the URL resolves to a repository path, not only a single unresolved file path unless the code path supports it.
- Keep large SAM3 downloads optional unless SAM3 behavior is the target.

## BOM YAML and invisible keys

A UTF-8 BOM at the start of a YAML file can turn the first key into an invisible variant such as `\ufefftype`. AnyLabeling reads model configs with `utf-8-sig`, so current model-manager paths strip the BOM. If a separate tool reports `type` missing while AnyLabeling does not, update that tool to read with `utf-8-sig`.

The bundled scripts read YAML with `utf-8-sig`.

## SAM3 text prompt not active

Symptoms:

- Typing text does nothing.
- Text-only prompt returns empty shapes.
- Prompt terms are not used as labels.

Checks:

1. The loaded model must be detected as SAM3. Non-SAM3 Segment Anything models force Visual mode.
2. The UI prompt mode must be Text. Text-only detection is not active merely because the prompt box contains text.
3. In Text mode, comma-separated terms are split and each term is run separately. Empty terms are ignored.
4. The target object must plausibly exist in the image. Text-only `truck` prompts need a truck image.
5. `language_encoder_path` must exist. Without the real language encoder or tokenizer, language-conditioned output may be empty or meaningless.
6. If `osam` is unavailable, SAM3 falls back to zero tokens. Install the expected tokenizer dependency for meaningful text prompts.
7. Lower `confidence_threshold` temporarily to distinguish prompt mismatch from filtering.

## Threshold filters all SAM3 masks

SAM3 keeps masks only where `score > confidence_threshold`. A threshold of `0.5` is the default. If all scores are at or below the threshold, the result shape is `(0, 1, H, W)` and the wrapper emits no shapes.

Debug sequence:

1. Lower the confidence threshold and retry.
2. Confirm text mode versus visual mode.
3. Try a broad prompt term and a representative image.
4. Confirm model files are from a compatible SAM3 export and that the language encoder matches the decoder.
5. If geometry is used, verify points/rectangles are inside the image and refer to the intended object.

## Bool-mask conversion errors

SAM3 decoders can return boolean masks. NumPy 2.x does not allow assigning `255` into a bool array the same way older code sometimes did. The wrapper avoids this by casting masks to `float32`, thresholding, then casting to `uint8` before contour extraction.

If downstream custom code still fails on bool masks:

```python
mask = mask.astype("float32")
mask[mask > 0.0] = 255
mask[mask <= 0.0] = 0
mask = mask.astype("uint8")
```

Blank masks should produce no shapes; non-blank bool, float, and uint8 masks should all produce contours when the object area is large enough.

## ONNX variant detection mistakes

Expected decoder-input signatures:

| Variant | Detection signal |
| --- | --- |
| SAM3 | `backbone_fpn_0` or `language_mask` |
| SAM2 | `high_res_feats_0` |
| SAM1 / MobileSAM | fallback when neither SAM3 nor SAM2 signal exists |

SAM3 has priority over SAM2 if both signals appear. `vision_pos_enc_0` and `vision_pos_enc_1` are not reliable detection signals because simplification may remove them.

Difficult custom SAM3 case:

- A custom YAML omits `language_encoder_path`.
- Its decoder ONNX inputs include `backbone_fpn_0` or `language_mask`.
- The wrapper detects SAM3 and then tries to resolve `language_encoder_path`, producing a missing-key failure.

Fix: add a valid `language_encoder_path` to the YAML and ensure the file resolves next to the config or in the model cache. If the decoder is not actually SAM3, regenerate or choose the correct decoder.

Use:

```bash
python scripts/check_custom_model_config.py /path/to/config.yaml
```

When the `onnx` package is installed and the decoder file is present, the script reports this mismatch before UI load.

## CUDA, GPU package, and ONNX Runtime confusion

AnyLabeling has two different backend concepts:

- YOLOv5/YOLOv8 use OpenCV DNN. In a GPU-preferred package build, they request OpenCV CUDA backend/target.
- SAM-family ONNX models use ONNX Runtime sessions with `onnxruntime.get_available_providers()` in SAM2/SAM3 paths and default session behavior in SAM1/MobileSAM.

Consequences:

- Installing a GPU package does not guarantee OpenCV was built with CUDA.
- ONNX Runtime CUDA provider availability is separate from OpenCV CUDA availability.
- A CPU-only environment can still load CPU ONNX Runtime providers.
- GPU/provider warnings are not equivalent to missing model files or invalid YAML.

Diagnose provider issues separately from config validation.

## CoreML confusion

CoreML SAM2 is a macOS branch and lazily imports `coremltools`. It expects `.mlpackage` assets. If it fails on Linux or Windows, that does not imply ONNX SAM2 is broken.

Checks:

1. Confirm the platform is macOS.
2. Confirm `coremltools` is installed in the app environment.
3. Confirm the resolved decoder path contains `coreml`; otherwise the wrapper may attempt ONNX variant detection instead of the CoreML branch.
4. Confirm all three CoreML package assets are in the expected folder.
5. Do not mix ONNX SAM2 config fields with CoreML asset directories unless the wrapper branch logic is intentionally being changed.

## YOLO loads but boxes look wrong

Common causes:

- `input_width` or `input_height` does not match the model export.
- `classes` length does not match the output tensor class dimension.
- A YOLOv5 export is loaded with `type: yolov8`, or a YOLOv8 export is loaded with `type: yolov5`.
- Thresholds are too high or NMS suppresses all boxes.
- The image conversion path differs from the export's expected preprocessing.

Actions:

1. Verify `type`, tensor output shape, and class count.
2. Temporarily lower thresholds.
3. Run a direct OpenCV DNN forward smoke check outside the UI.
4. If boxes are shifted or scaled, recheck model input dimensions and preprocessing assumptions.

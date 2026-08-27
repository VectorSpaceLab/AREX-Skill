# Conversion and deployment troubleshooting

Use this reference for failures owned by `conversion-and-deployment`. Route
missing downloads and license gates to `model-acquisition`; route runtime demo
adaptation to `inference-demos` after backend preflight.

## Symptom table

| Symptom | Likely cause | Recovery |
|---|---|---|
| Catalog says a format exists, but the file is not in the checkout. | The README table records availability, while artifacts may require folder-specific downloads or a fuller checkout. | Route to `model-acquisition`; inspect download scripts and license before fetching. |
| Conversion script imports TensorFlow, ONNX Runtime, OpenVINO, CoreML, TFJS, or TensorRT and fails immediately. | Backend-specific converter/runtime is not installed. | Install only the selected converter family in an isolated environment, or switch to an already converted artifact. Do not treat import failure as model corruption. |
| TFLite INT8 conversion asks for `representative_dataset` or calibration arrays. | Post-training quantization needs activation ranges. | Provide representative real samples with matching shape/layout/preprocessing. For smoke-only tests, use tiny local data and label output non-calibrated. |
| Calibration script references COCO, Cityscapes, TFDS, `.npy` calibration files, tarballs, or remote storage. | Required representative data is absent or large. | Stop for user approval before network or large dataset work; regenerate only from approved data. |
| Full-integer or EdgeTPU conversion fails because input/output remains float. | The converter made INT8 internals but not integer I/O, or used Select TF ops. | Require TFLite builtins INT8 and explicit integer input/output types. Recheck representative data and unsupported ops. |
| EdgeTPU compiler rejects ops or produces partial/no acceleration. | The model contains unsupported ops, unsupported tensor types, dynamic behavior, or postprocessing not compilable for EdgeTPU. | Keep CPU TFLite as fallback; simplify or replace unsupported postprocessing only with model-specific evidence. Do not claim EdgeTPU deployment until compiler and hardware runtime pass. |
| Error mentions only `float32` and `uint8` supported or a node failed to invoke. | Quantized model/operator type mismatch in TFLite/EdgeTPU path. | Verify input/output dtype, quantization parameters, and whether the model needs a special rewrite or CPU fallback. |
| ONNX-to-TFLite output has wrong boxes, masks, or keypoints. | Layout, color order, normalization, or postprocessing changed during conversion. | Compare input/output metadata, transpose handling, and postprocess nodes. Use the folder's demo preprocessing as ground truth. |
| ONNX converter complains about INT64, dynamic axes, opset, or unsupported ops. | Source ONNX uses features unsupported by the target converter/runtime. | Use local rewrite/preprocess scripts when available, freeze shapes if acceptable, or choose an existing artifact. Stop if shape semantics are unknown. |
| OpenVINO cannot read files or reports missing weights. | `.xml` and `.bin` pair are mismatched, renamed, or separated. | Select both files with the same stem from the same artifact set before changing runtime settings. |
| OpenVINO output differs from TFLite/ONNX baseline. | Input layout, precision, preprocessing, or output postprocessing differs. | Confirm shape/order and compare with deterministic input; route inference comparison to `inference-demos`. |
| TFJS browser load fails despite `model.json` existing. | Weight shards are missing or browser file/CORS rules block loading. | Keep `model.json` with all referenced shards and serve through a local/static server; then test in the target browser backend. |
| TFJS/WebGL is slower or unavailable. | Browser/GPU backend is absent, disabled, or falls back to CPU. | Verify backend selection in the actual browser/device; do not infer WebGL acceleration from conversion success. |
| TF-TRT conversion or first inference fails. | No NVIDIA GPU, version mismatch, unsupported segment, dynamic shape, or insufficient memory. | Confirm GPU visibility and CUDA/TensorRT/TensorFlow compatibility; use fixed shapes and baseline TensorFlow fallback. |
| CoreML artifact cannot be verified in the current environment. | Runtime verification requires Apple platform support. | Mark conversion/inspection only; ask for target Apple runtime before claiming deployment. |
| Performance claim requested for Raspberry Pi/EdgeTPU/GPU but hardware is absent. | Target-specific acceleration cannot be proven locally. | Offer packaging or desktop smoke checks only and mark target performance unverified. |
| Accuracy drops after quantization. | Calibration data is too small, unrepresentative, or preprocessed differently; quantization mode may be too aggressive. | Rebuild with representative data that mirrors deployment; compare against FP32 baseline using `inference-demos`. |
| Converter uses network commands, downloads tarballs, or writes cookies. | Script performs acquisition as part of conversion. | Route to `model-acquisition`; require approval for network/storage and run in the selected model directory only. |
| License is unclear for a converted artifact. | Conversion scripts may be MIT while source model license differs by folder. | Check the selected folder license before redistribution or deployment. |

## Fast diagnostic sequence

1. Identify the selected model directory and target backend.
2. Query catalog flags; prefer an existing target artifact if available.
3. Run `scripts/classify_conversion_script.py` on candidate scripts without
   executing them.
4. Check for representative-dataset, network, and hardware risks.
5. Validate artifact packaging: single file for `.tflite`/`.onnx`/`.mlmodel`,
   XML+BIN pair for OpenVINO, `model.json`+shards for TFJS.
6. State the highest proof level actually reached: planned, converted, loaded,
   or target-hardware executed.

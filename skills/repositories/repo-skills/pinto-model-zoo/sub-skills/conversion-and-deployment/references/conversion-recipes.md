# Conversion and quantization recipes

This reference distills PINTO_model_zoo conversion evidence into planning rules.
The zoo is a collection of model folders, scripts, and pre-converted artifacts;
it is not an installable package with one universal converter. Always plan from
the selected model folder and the bundled catalog, then inspect local scripts
before executing anything.

## Catalog flags and format families

Catalog flags indicate that the README tables listed an artifact family for a
model. They do not prove the artifact is already present in a partial checkout.
Use `model-catalog` first, then `model-acquisition` if files must be fetched.

| Flag/family | Meaning for planning | Main constraints |
|---|---|---|
| `ONNX` | `.onnx` interchange artifact, often the current source for newer models. | Check opset, static vs dynamic shapes, input layout, post-processing nodes, and whether INT64 tensors must be rewritten for some runtimes. |
| TensorFlow / SavedModel / `.pb` / `.h5` | TensorFlow graph family used as a source for many TFLite conversions. | Confirm signatures, input names, NHWC layout, preprocessing, and whether custom or Select TF ops are required. |
| `FP32` TFLite/TensorFlow family | Float baseline artifact. | Usually easiest to smoke-test; larger and slower than quantized variants. |
| `FP16` | Float16 weight artifact. | Usually keeps float input/output; useful for smaller models and GPU/ARM FP16 paths, but not a substitute for EdgeTPU full integer. |
| `WQ` | Weight quantization. | Reduces stored weights; commonly keeps float input/output; representative data is usually not required. |
| `DQ` | Dynamic range quantization. | Usually no representative dataset; activations may remain dynamic/float at runtime; not sufficient for EdgeTPU. |
| `INT8` | Integer-quantized artifact. | Requires calibration or representative data when produced post-training; input/output may still be float unless forced. |
| Full integer TFLite | TFLite builtins INT8 with integer input/output. | Required before EdgeTPU compilation; demands representative data and stricter op coverage. |
| `TPU` / EdgeTPU | EdgeTPU-oriented TFLite artifact. | Requires a full-integer TFLite model, compiler success, supported ops, and hardware/runtime for actual acceleration. |
| `OV` | OpenVINO IR `.xml` + `.bin` pair. | Both files must share a stem and match the selected precision/shape; CPU execution is the portable baseline. |
| `CM` | CoreML `.mlmodel` or package. | Runtime verification is Apple-platform specific; non-Apple systems can inspect or convert but should not claim device execution. |
| `TFJS` | TensorFlow.js `model.json` plus weight shards. | Browser or Node runtime needs all shards, correct preprocessing, and a local server/CORS-safe load path. |
| `TF-TRT` | TensorFlow-TensorRT optimized SavedModel family. | Requires NVIDIA GPU, matching CUDA/TensorRT/TensorFlow stack, and shape-aware engine building. |

## General decision rules

1. **Use a preconverted artifact when available.** If the catalog has the target
   flag and acquisition can provide it, prefer that over rebuilding a fragile
   cross-framework chain.
2. **Keep conversion and inference separate.** A successful converter run only
   proves artifact creation. Route runtime smoke or accuracy checks to
   `inference-demos` after file existence and backend preflight pass.
3. **Match preprocessing exactly.** Calibration and final inference must use the
   selected model's shape, dtype, color order, layout, and normalization. Do not
   reuse another model's representative data unless those properties match.
4. **Record unverified assumptions.** If a script references unavailable source
   weights, a remote dataset, a device compiler, or vendor hardware, stop and ask
   for that input or approval instead of inventing a fallback.

## Common conversion chains

### ONNX to TFLite

Use this when the selected model has ONNX but no suitable TFLite artifact.

Planning steps:

1. Inspect the ONNX model's input names, static shapes, layout, and opset. Many
   ONNX exports are NCHW; TFLite models usually expect NHWC or converter-inserted
   transposes.
2. Inspect local `convert*.sh`, `onnx_*`, or `*tflite*` scripts. PINTO folders
   often contain comments or commands that name the intended converter chain.
3. Convert ONNX to a TensorFlow/SavedModel or direct TFLite path using the model
   folder's intended converter family when present.
4. If INT8 or full integer is requested, provide representative samples with the
   exact deployed preprocessing.
5. If EdgeTPU is requested, enforce full-integer TFLite and run an EdgeTPU
   compiler gate before any hardware claim.

Stop when dynamic shapes, unsupported ops, custom post-processing, missing
source weights, or layout ambiguity cannot be resolved from local evidence.

### TensorFlow/SavedModel to TFLite

Use this when scripts call `TFLiteConverter.from_saved_model`, `saved_model_cli`,
or contain SavedModel directories.

Mode selection:

- **Float TFLite / FP32:** convert without quantization; best baseline for
  converter sanity.
- **Weight quantization / WQ:** enable size optimization only; representative
  data is usually not required and input/output commonly remain float.
- **Dynamic range / DQ:** enable default optimization without a representative
  dataset; useful for smaller CPU artifacts, not EdgeTPU.
- **FP16:** configure float16 supported type; keeps a float interface for many
  runtimes.
- **INT8:** enable default optimization and set `representative_dataset`; verify
  output type expectations.
- **Full integer:** set representative data, restrict supported ops to TFLite
  builtins INT8, and set integer input/output types (`uint8` or `int8`) matching
  the selected script/runtime.

The README evidence includes representative generators that take a bounded
number of samples and resize them to the target model shape before yielding
batches. Treat this as a pattern: calibrate with representative real inputs, not
random tensors, unless the user only needs a converter smoke test explicitly
marked as non-calibrated.

### ONNX static quantization

Some folders quantize ONNX directly with an ONNX Runtime calibration data reader.
Use this when a script imports quantization APIs, defines a calibration reader,
or writes `_uint8.onnx`/similar outputs.

Planning steps:

1. Preprocess/simplify the ONNX model only as directed by local scripts.
2. Load calibration arrays/images in the model's expected layout. Scripts may
   transpose NHWC calibration images to NCHW for ONNX input.
3. Select the quantization format and activation type already used by the local
   script unless the user has a reason to change it.
4. Keep the float ONNX model and quantized ONNX model side-by-side for fallback.

Stop if calibration arrays are missing and cannot be regenerated from approved,
representative inputs.

### TFLite to other families

The zoo contains evidence of TFLite-centered conversion chains to SavedModel,
ONNX, OpenVINO, CoreML, TFJS, TF-TRT, and device blobs. Prefer existing artifacts
or folder-specific scripts. When rebuilding:

- confirm whether the TFLite model contains custom ops, Select TF ops, or fused
  post-processing;
- preserve input/output metadata and quantization parameters;
- verify that the target backend can represent quantized tensors and postprocess
  nodes;
- do not claim backend execution until the target runtime loads the artifact.

### OpenVINO IR

Use OpenVINO when the target is CPU deployment, Intel accelerator tooling, or an
existing `OV` catalog flag.

Minimum checks:

- `.xml` and `.bin` files exist with the same stem;
- precision and input shape match the user's target;
- preprocessing and output interpretation are known;
- the selected OpenVINO runtime can read the IR version.

### CoreML

Use CoreML when the target is Apple deployment and the catalog or local scripts
show `CM`, `coremltools`, or `.mlmodel` outputs.

Minimum checks:

- input image/tensor type, scale, bias, channel order, and shape are preserved;
- output names and postprocessing expectations are documented;
- execution is verified on an Apple runtime or explicitly marked unverified.

### TensorFlow.js

Use TFJS when the target is browser or Node deployment and the catalog/local
folder provides `TFJS`, `model.json`, or converter scripts.

Minimum checks:

- `model.json` and all weight shards are present together;
- the load path is served from a local/static server rather than a raw file path
  when browser security requires it;
- WebGL/WebGPU acceleration claims are verified in the actual browser/device.

### TF-TRT

Use TF-TRT only for NVIDIA GPU deployment. It is not a generic CPU conversion.

Minimum checks:

- TensorFlow, TensorRT, CUDA, driver, and GPU are compatible in the target
  environment;
- input shapes are known because engines may be built lazily for each shape;
- memory headroom is sufficient for conversion and first-run engine build;
- fallback to ordinary TensorFlow is planned if TF-TRT cannot build a segment.

## Calibration and representative data

Representative data is needed when post-training quantization estimates
activation ranges, especially INT8 and full-integer TFLite or static ONNX
quantization. It should match real deployment inputs.

Checklist:

- same model input shape/resolution;
- same layout (`NCHW` vs `NHWC`), color order (`RGB` vs `BGR`), dtype, and value
  range;
- same normalization, resize, crop, and padding as inference;
- enough diverse samples for the task, kept small enough for approved runtime;
- no network download unless explicitly approved.

Stop and ask before downloading large datasets, using Google Drive/S3/curl/wget,
or generating calibration arrays from private data. If only a smoke test is
approved, use a tiny local sample and label the result "converter smoke only,
not accuracy-calibrated".

## Planning output checklist

A complete conversion plan should state:

- selected model directory/name and catalog flags consulted;
- source artifact and target artifact family;
- exact local scripts inspected, if any;
- conversion chain and precision mode;
- representative data source or reason none is required;
- backend preflight gates and stop conditions;
- expected output filenames/stems;
- smoke-test handoff to `inference-demos`.

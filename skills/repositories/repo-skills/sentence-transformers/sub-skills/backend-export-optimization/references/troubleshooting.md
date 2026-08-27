# Backend Export Troubleshooting

## Install and Import Failures

Symptom: `backend="onnx"` raises an error about Optimum or ONNX Runtime.

- Install the CPU extra with `pip install "sentence-transformers[onnx]"`.
- Install the GPU extra with `pip install "sentence-transformers[onnx-gpu]"` when CUDA ONNX Runtime providers are required.
- Verify availability with `python scripts/backend_export_check.py --check onnx`.
- If a requested provider is unavailable, inspect `onnxruntime.get_available_providers()` and switch `model_kwargs={"provider": "CPUExecutionProvider"}` or install the correct runtime.

Symptom: `backend="openvino"` raises an error about Optimum or OpenVINO.

- Install `pip install "sentence-transformers[openvino]"`.
- For static OpenVINO quantization, also ensure `datasets` is installed because calibration data is required.
- Verify availability with `python scripts/backend_export_check.py --check openvino`.

Symptom: importing export helpers fails.

- Import helpers from `sentence_transformers` or `sentence_transformers.backend`: `export_optimized_onnx_model`, `export_dynamic_quantized_onnx_model`, and `export_static_quantized_openvino_model`.
- Confirm the package version exposes backend APIs with `python scripts/backend_export_check.py --signatures`.

## API Misuse

Symptom: `export_optimized_onnx_model` or `export_dynamic_quantized_onnx_model` says the model must be loaded with `backend="onnx"`.

- Recreate the model with `backend="onnx"` before calling ONNX helpers.
- Do not pass a PyTorch or OpenVINO model into ONNX optimization/quantization helpers.

Symptom: `export_static_quantized_openvino_model` says the model must be loaded with `backend="openvino"`.

- Recreate the model with `backend="openvino"` before static OpenVINO quantization.
- Do not pass an ONNX model into the OpenVINO quantization helper.

Symptom: a custom OpenVINO calibration dataset call fails.

- Either omit all dataset override arguments or supply all of `dataset_name`, `dataset_config_name`, `dataset_split`, and `column_name`.
- Confirm the named column contains strings that the tokenizer can process.

## File Selection Failures

Symptom: loading an optimized or quantized file silently exports a fresh base file or warns that no file exists.

- Pass the exact `model_kwargs={"file_name": ...}` for the artifact you want.
- ONNX optimized example: `onnx/model_O3.onnx`.
- ONNX dynamic quantized example: `onnx/model_qint8_avx512_vnni.onnx`.
- OpenVINO static quantized example: `openvino/openvino_model_qint8_quantized.xml`.
- Use `model_kwargs={"export": False}` when you want loading to fail instead of exporting a fallback artifact.

Symptom: multiple ONNX or OpenVINO files exist and the wrong one loads.

- Always set `file_name` for repositories containing several variants.
- Keep `file_suffix` stable during export so load-time file names are predictable.

Symptom: OpenVINO `.xml` exists but loading fails due to missing binary weights.

- Keep the paired `.bin` next to the `.xml` file.
- When publishing an OpenVINO artifact, upload both files under the `openvino/` folder.

## Hub and PR Workflow Failures

Symptom: pushing an optimized or quantized file to a Hub model fails.

- Authenticate with a token that can create commits or pull requests for the target repository.
- Prefer `push_to_hub=True, create_pr=True` for public or shared models to avoid direct writes.
- Load PR artifacts with `revision=f"refs/pr/{pr_number}"` and the expected `file_name` before asking maintainers to merge.

Symptom: after a PR merges, the code still uses `revision="refs/pr/..."`.

- Remove `revision` after merge and keep only `backend` plus the matching `model_kwargs={"file_name": ...}`.

## Backend and Service Limits

Symptom: ONNX or OpenVINO is not faster than PyTorch.

- Benchmark with the user's actual model, text lengths, device, and batch size; docs note ONNX/OpenVINO can be slower for some workloads.
- Use ONNX dynamic int8 quantization primarily for CPU targets, not GPUs.
- Use ONNX `O4` only when mixed-precision GPU execution is suitable.

Symptom: GPU provider selection fails.

- Confirm the provider appears in `onnxruntime.get_available_providers()`.
- Match `onnxruntime-gpu`, CUDA, and driver compatibility outside Sentence Transformers.
- Fall back to `CPUExecutionProvider` for a deterministic CPU smoke test.

Symptom: generated files are unexpectedly re-created on every run.

- For local models, call `model.save_pretrained(...)` after the first export.
- For Hub models, call `model.push_to_hub(..., create_pr=True)` and then load the exported file after the PR is available.

## Workflow-Specific Pitfalls

Symptom: exported ONNX/OpenVINO output does not match Sentence Transformers when used directly outside the library.

- The exported backend file is the Transformer component, not the full high-level pipeline.
- For dense models, add pooling and normalization outside the library.
- For sparse models, add SPLADE pooling and sparse vector post-processing outside the library.
- For CrossEncoder models, apply the same activation or score normalization expected by the original CrossEncoder.

Symptom: user asks for binary embeddings, scalar embeddings, or smaller retrieval indexes.

- Do not solve that with backend export helpers. Route to output-vector quantization and retrieval utilities.
- Backend quantization speeds model inference; output-vector quantization compresses embeddings after inference.

Symptom: model download or export is not allowed in a production validation step.

- Use `scripts/backend_export_check.py` without `--model` to inspect imports and signatures only.
- Add `--model` and `--backend` only when the environment is allowed to download/load and potentially export a model.

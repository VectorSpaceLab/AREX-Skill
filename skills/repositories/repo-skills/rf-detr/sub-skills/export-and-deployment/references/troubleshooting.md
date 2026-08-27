# RF-DETR export troubleshooting

Use this guide when an export/deployment task fails, appears to hang, or produces an unexpected file. Keep fixes scoped to export/deployment; route ordinary prediction/training questions to the sibling sub-skills.

## Fast diagnosis checklist

1. Run `python scripts/inspect_export_options.py ...` with the intended `--format`, `--shape`, `--backend`, and `--soc`.
2. Confirm the requested extra is installed (`rfdetr[onnx]`, `[tensorrt]`, `[tflite]`, `[executorch]`, or `[coreml]`).
3. Confirm `shape` dimensions are positive and divisible by `patch_size * num_windows`.
4. Confirm the target format supports the requested batch policy: no dynamic batch for ExecuTorch or native CoreML.
5. Confirm `backend`/`soc` are only used for `format="executorch"`.
6. If the model has been optimized with `inference(inplace=True)`, instantiate a fresh model before export.
7. Reproduce backend-heavy failures in a fresh isolated environment with only the target extra installed.

## Missing optional dependencies

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| ONNX import/export errors | ONNX extra missing | `pip install "rfdetr[onnx]"` |
| TensorRT builder import error | TensorRT/Polygraphy not installed or not usable on host | `pip install "rfdetr[tensorrt]"`; verify NVIDIA driver/CUDA/TensorRT runtime |
| TFLite `onnx2tf`/TensorFlow import error | TFLite extra missing or Python version outside marker window | Use Python 3.12 and `pip install "rfdetr[tflite]"` |
| ExecuTorch import error | ExecuTorch extra missing or unsupported Python wheel | `pip install "rfdetr[executorch]"`; Python must have a compatible wheel (`<3.14` in the verified package facts) |
| ExecuTorch CoreML backend import error | `coremltools` or ExecuTorch Apple backend unavailable | Install `coremltools`; use an environment where the backend exists |
| ExecuTorch QNN import error | QNN delegate absent from pip wheel | Build ExecuTorch from source against QAIRT/QNN SDK; set the needed SDK environment outside generated runtime files |
| Native CoreML import/convert error | `coremltools` missing or torch/coremltools mismatch | `pip install "rfdetr[coreml]"`; respect the `torch<2.12` extra constraint until upstream issues change |
| Roboflow deployment import error | Roboflow SDK absent | Install the training/deploy dependency set, for example `pip install "rfdetr[train]"`, or install `roboflow` separately |

## Invalid format/backend combinations

- `format="trt"` is accepted as `"tensorrt"`.
- `format="pte"` is accepted as `"executorch"`.
- `backend` is required only for `format="executorch"`; supplying `backend` with ONNX, TFLite, TensorRT, or native CoreML is ignored with a warning.
- `soc` is required only for ExecuTorch `backend="qnn"`; supplying `soc` elsewhere is ignored with a warning.
- ExecuTorch backend names are case-normalized, but only `xnnpack`, `coreml`, and `qnn` are valid.
- `backend="qnn"` without `soc` raises. Use a target SoC name such as `SM8650` when that matches the device.
- `format="coreml"` plus `backend="coreml"` still means native CoreML; `backend` is ignored. To get an ExecuTorch `.pte` using the CoreML delegate, use `format="executorch", backend="coreml"`.

## Shape and batch failures

| Error pattern | Meaning | Fix |
| --- | --- | --- |
| `shape` must be positive / wrong arity / bool or float dimensions | `shape` is not a two-int positive `(height, width)` tuple | Pass integers such as `shape=(512, 512)` |
| `not divisible by ...` | Height or width is not divisible by `patch_size * num_windows` | Choose a valid multiple; for `rfdetr-small`, multiples of 32 are typical |
| default resolution not divisible | The instantiated model config is inconsistent for export | Pass explicit valid `shape` or instantiate a compatible model/config |
| `patch_size` mismatch | Explicit `patch_size` differs from the model config | Omit `patch_size` unless you know the model's configured value |
| `num_windows must be a positive integer` | Model config is invalid | Fix the model/config before export |
| `dynamic_batch` with ExecuTorch/CoreML | Fixed-shape runtime path | Export one `.pte`/`.mlpackage` per batch size; keep `dynamic_batch=False` |

## Output-name surprises

- `output_name` is a full filename stem override, not an output directory. It is sanitized to a basename and extension-stripped.
- `output_name="dir/model.onnx"` becomes `model`, not `dir/model`.
- `output_name` suppresses precision/backend suffixes for TensorRT, ExecuTorch, and native CoreML, so you must track precision/backend elsewhere if you choose a custom name.
- ONNX `backbone_only=True` always appends `-backbone`, even with `output_name`.
- TFLite always writes multiple precision files, so it keeps `_fp32`, `_fp16`, and optionally `_dynamic_range_quant` suffixes even with `output_name`.
- TFLite GridSample rewriting may add `_gs_patched` before precision suffixes; this is normal for RF-DETR graphs containing GridSample.
- Empty `output_name=""` falls back like `None`; all-separator names such as `"///"` are invalid.

## TensorRT-specific failures

- A `.trt` engine is tied to the build GPU architecture and TensorRT version. Rebuild on the target deployment GPU/runtime rather than shipping one engine across heterogeneous GPUs.
- If FP16 builder support is absent, set `fp16=False` or accept the RF-DETR fallback to an `_fp32.trt` engine where supported.
- Do not expect `format="tensorrt"` output to be loaded by inference-models. If inference-models is the runtime, use ONNX/checkpoint/model id and request the backend there.
- TensorRT end-to-end checks are GPU/driver/TensorRT gated; use ONNX as the portable fallback when those gates are unavailable.

## TFLite-specific failures

- TFLite export is experimental. Pin TensorFlow, `onnx2tf`, and related packages for production.
- Use Python 3.12 for the public `[tflite]` extra because dependency markers are constrained to `>=3.12,<3.13` in the verified package facts.
- If conversion hangs with no traceback after ONNX/TensorFlow activity, suspect ONNX imported before TensorFlow. Run export in a fresh process and import TensorFlow first, or let RF-DETR's TFLite export route preload TensorFlow before ONNX.
- Static/full-integer INT8 is not supported. `quantization="int8"` means dynamic-range INT8.
- Poor or random validation/calibration data can silently harm deployment quality. Use representative images or NHWC float32 arrays.
- If TFLite runtime outputs collapse or are wrong, confirm the GridSample patch was applied and avoid unvalidated `onnx2tf` backend changes.
- Run TFLite conversion serially. The converter uses process-global monkey patches around NumPy loading and onnx2tf validation data.

## ExecuTorch-specific failures

- `dynamic_batch=True` is intentionally refused because ExecuTorch 1.3.x cannot safely resize RF-DETR windowed-attention reshapes.
- Runtime loading (`executorch.runtime`) can fail from a torch/ExecuTorch ABI mismatch even when export itself works. Pin torch to a version compatible with the installed ExecuTorch wheel when local runtime validation is needed.
- QNN requires a source build against the QAIRT/QNN SDK and on-device validation. The pip wheel route is not enough.
- QNN `.pte` files are SoC-specific; include the target SoC in the export request and filename unless you intentionally override `output_name`.
- ExecuTorch runtime reads input buffers as contiguous NCHW. A non-contiguous tensor/array can produce plausible-shaped but incorrect low-confidence outputs without an error. Always materialize contiguity after permuting.
- The Vulkan backend is not exposed in RF-DETR's verified export contract.

## Native CoreML-specific failures

- Native CoreML is fixed-shape and rejects `dynamic_batch=True`.
- Running `.mlpackage` models requires Apple Core ML runtime support. Linux environments can be unsuitable for runtime validation even if package import succeeds.
- `coreml_precision="float16"` changes numeric behavior and output filename; evaluate detections rather than expecting raw fp32 tensor parity.
- `coreml_precision` must be `None`, `"float32"`, or `"float16"`.
- CoreML output tensor names are coremltools-inferred; match outputs by position.
- Keypoint native CoreML export is not verified in the available evidence.

## Optimized model and checkpoint failures

- `RFDETR.export()` and `deploy_to_roboflow()` need the original model weights. If `model.inference(inplace=True)` has cleared them, instantiate a fresh model/checkpoint and export before in-place optimization.
- For untrusted checkpoints, avoid unsafe full-pickle loading. Use safe checkpoint pathways and only enable trust for checkpoints from a trusted source.
- Checkpoint patch-size mismatches are architectural incompatibilities; instantiate the matching model variant/config or use a compatible checkpoint.

## Roboflow deployment failures

- Missing API key: pass `api_key=...` or set `ROBOFLOW_API_KEY` in the environment used for deployment.
- Custom architectures with no `self.size` need an explicit `size` argument for deployment.
- Passing a `size` different from the model's own size emits a warning and deploys as the explicit size.
- Use `export_for_roboflow(output_dir)` when you only need a local bundle and do not want a network upload.

## When to stop and ask

Ask for clarification rather than guessing when:

- The target hardware/runtime is unknown and the user requests "best" export format.
- The TensorRT engine is expected to run on a different GPU than the build host.
- The user requests QNN but does not know the target Snapdragon SoC.
- The user requests TFLite INT8 without representative data and accuracy matters.
- The user asks for native CoreML or ExecuTorch CoreML but does not distinguish Xcode/Core ML from ExecuTorch runtime.

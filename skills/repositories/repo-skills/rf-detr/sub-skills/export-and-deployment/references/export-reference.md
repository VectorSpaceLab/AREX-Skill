# RF-DETR export reference

This reference summarizes RF-DETR 1.10.0.dev export behavior for future agents. It is scoped to public package use and generated skill-tree guidance; use the public package install commands, not local editable-install paths.

## Public export API

```python
RFDETR.export(
    output_dir="output",
    infer_dir=None,
    backbone_only=False,
    opset_version=17,
    verbose=True,
    shape=None,
    batch_size=1,
    dynamic_batch=False,
    patch_size=None,
    format="onnx",
    quantization=None,
    calibration_data=None,
    max_images=100,
    *,
    backend=None,
    soc=None,
    fp16=True,
    notes=None,
    coreml_precision=None,
    output_name=None,
)
```

Use `RFDETRSmall`, `RFDETRSegSmall`, or `RFDETRKeypointPreview` as concrete public examples when a task needs a model family. Pass `pretrain_weights="checkpoint.pth"` or use `RFDETR.from_checkpoint(path, trust_checkpoint=False, **kwargs)` when exporting a fine-tuned checkpoint.

## Formats and aliases

| `format` value | Alias | Artifact | Main purpose | Export path |
| --- | --- | --- | --- | --- |
| `"onnx"` | none | `.onnx` | Stable cross-runtime baseline | PyTorch trace to ONNX |
| `"tensorrt"` | `"trt"` | `.trt` | Raw TensorRT deployment on the build GPU family | ONNX first, then TensorRT Python API through Polygraphy |
| `"tflite"` | none | `.tflite` | TensorFlow Lite mobile/edge deployment | ONNX first, then ONNX -> TF/TFLite through `onnx2tf` |
| `"executorch"` | `"pte"` | `.pte` | PyTorch on-device runtime | Direct `torch.export` -> ExecuTorch, no ONNX step |
| `"coreml"` | none | `.mlpackage` | Native Apple Core ML / Xcode deployment | Direct `torch.export` -> `coremltools`, no ONNX or ExecuTorch |

Unknown formats raise `ValueError`. The public `rfdetr` console script primarily covers Lightning-style training/inference commands (`fit`, `validate`, `test`, `predict`); use the Python API above for TFLite, ExecuTorch, and native CoreML export.

## Shape, patch, and batch constraints

- `shape` is `(height, width)`. If omitted, RF-DETR uses the instantiated model's resolution.
- Each dimension must be positive and divisible by `patch_size * num_windows` for the selected model.
- `patch_size` normally comes from `model.model_config.patch_size`; an explicit `patch_size` must match the model config.
- `dynamic_batch=True` creates a dynamic batch axis for ONNX and therefore the ONNX stage used by TFLite/TensorRT. Spatial dimensions remain fixed.
- `dynamic_batch=True` is not supported for ExecuTorch or native CoreML; both paths reject it before heavy export work.
- `batch_size` is the static example batch size baked into fixed-batch artifacts. For mobile/CoreML/ExecuTorch, export one file per deployment batch size.

Common block sizes from public configs:

| Variant family | Typical block size | Notes |
| --- | ---: | --- |
| Detection nano/small/medium/large | 32 | `patch_size=16`, `num_windows=2` |
| Legacy/base style detection | 56 | `patch_size=14`, `num_windows=4`; avoid new examples with base variants |
| Segmentation nano | 12 | `patch_size=12`, `num_windows=1` |
| Segmentation small/medium/large/xlarge/2xlarge | 24 | `patch_size=12`, `num_windows=2` |
| Keypoint preview | 24 | keypoints are preview-only |

## Output names

RF-DETR resolves a filename stem from `output_name` first, then the model variant name such as `rfdetr-small`, then a generic default. Path components and file extensions in `output_name`/variant-like values are stripped to a basename stem. An `output_name` that resolves to an empty stem is invalid.

| Format | Default naming when a variant is known | Naming detail |
| --- | --- | --- |
| ONNX | `rfdetr-small.onnx` | `backbone_only=True` adds `-backbone`; without variant: `inference_model.onnx` or `backbone_model.onnx` |
| TensorRT | `rfdetr-small_fp16.trt` or `rfdetr-small_fp32.trt` | precision suffix reflects the built engine unless `output_name` is set |
| TFLite | `rfdetr-small_fp32.tflite`, `rfdetr-small_fp16.tflite`, optionally `rfdetr-small_dynamic_range_quant.tflite` | TFLite always writes per-precision files; a GridSample patch may add `_gs_patched` before the precision suffix |
| ExecuTorch | `rfdetr-small_xnnpack.pte`, `rfdetr-small_coreml.pte`, or `rfdetr-small_qnn_SM8650.pte` | backend/SoC suffix is load-bearing unless `output_name` is set |
| Native CoreML | `rfdetr-small_fp32.mlpackage` or `rfdetr-small_fp16.mlpackage` | precision suffix is load-bearing unless `output_name` is set |

`output_name="my-model"` suppresses detail suffixes for single-artifact formats: `my-model.onnx`, `my-model.trt`, `my-model.pte`, `my-model.mlpackage`. ONNX backbone export is the exception: `my-model-backbone.onnx`. TFLite is also an exception because it writes multiple precision artifacts: `my-model_fp32.tflite`, `my-model_fp16.tflite`, and optionally `my-model_dynamic_range_quant.tflite` (or `_gs_patched_*` names after GridSample rewriting).

## Output tensor contracts

- Detection exports use input name `input` and outputs `dets`, `labels`.
- Segmentation exports add `masks`.
- Keypoint exports add `keypoints`.
- `backbone_only=True` exports output `features`.
- ONNX/TFLite exported graphs return raw tensors, not postprocessed detections. Decode boxes/logits outside the graph.
- ONNX consumers should match outputs by name (`dets`, `labels`, `masks`, `keypoints`), not by shape. At exactly three classes, logits last dimension (`num_classes + 1`) can equal the box dimension `4`, making shape-based routing dangerous.
- Native CoreML `.mlpackage` outputs are named by coremltools, not necessarily `dets`/`labels`; match by output position using the same order as the ONNX output contract.

## Optional dependency matrix

Install only the backend extra needed for the target artifact. Avoid combining backend extras with known incompatible torch stacks unless the resolver explicitly supports it.

| Capability | Public install | Important dependency facts |
| --- | --- | --- |
| Baseline package | `pip install rfdetr` | Python `>=3.10`; includes PyTorch/torchvision/transformers/supervision and core API |
| ONNX export/inference | `pip install "rfdetr[onnx]"` | Includes `onnx`, `onnxsim`, `onnx_graphsurgeon`, `onnxruntime`, `polygraphy`; Python 3.10 uses `onnxruntime<1.24` |
| TensorRT engine export | `pip install "rfdetr[tensorrt]"` | Includes `onnxruntime-gpu`, `tensorrt>=8.6.1`, `polygraphy`; requires NVIDIA CUDA/TensorRT runtime to build/use engines |
| TensorRT async benchmark helper | `pip install "rfdetr[tensorrt-bench]"` | Adds `pycuda`; not required for ordinary `build_engine` parity or raw engine creation |
| TFLite export | `pip install "rfdetr[tflite]"` | Extra is gated to Python `>=3.12,<3.13`; includes ONNX conversion deps, `onnx2tf>=2.4,<3`, TensorFlow; `onnxruntime` is not included in this extra |
| ExecuTorch export | `pip install "rfdetr[executorch]"` | `executorch>=1.3,<2.0` for Python `<3.14`; XNNPACK wheel path is portable CPU; runtime loading may need a torch ABI pin such as `torch<2.13` for executorch 1.3.1 |
| Native CoreML export | `pip install "rfdetr[coreml]"` | `coremltools>=8,<10` plus `torch<2.12`; running Core ML models requires Apple Core ML runtime |
| Roboflow deployment | `pip install "rfdetr[train]"` or install `roboflow` | `deploy_to_roboflow()` uses the Roboflow SDK and a network/API key; `export_for_roboflow()` writes the local bundle without network |
| Plus variants | `pip install "rfdetr[plus]"` | Plus weights/classes are provided by the separate `rfdetr_plus` package and license boundary |

## Format-specific constraints

### ONNX baseline

- Best first export for external runtimes, inference-models, OpenVINO, ONNX Runtime, and many accelerator toolchains.
- `notes` embeds user metadata in ONNX as `rfdetr_notes`; strings are stored verbatim and dict/list/other JSON-serializable values are JSON-encoded. Falsy non-`None` values are still embedded. Non-finite JSON values can raise.
- Use `opset_version=17` unless a target runtime forces a different choice.

### TensorRT

- `format="tensorrt"` first writes ONNX, then calls the in-process TensorRT builder. No `trtexec` binary is required.
- `fp16=True` is the default. If the TensorRT build lacks an FP16 builder flag, RF-DETR can fall back to FP32 and the filename reflects `_fp32`.
- A `.trt` engine is not portable across GPU architectures, TensorRT versions, or often deployment images. Build it on the same machine/GPU family/runtime you deploy to.
- Do not use `format="tensorrt"` to feed inference-models; inference-models builds/manages its own TRT engine.

### TFLite

- Experimental and sensitive to upstream TensorFlow/onnx2tf/ai_edge_litert changes.
- `quantization` accepts `None`, `"fp32"`, `"fp16"`, `"int8"`.
- `None`, `"fp32"`, and `"fp16"` still produce both FP32 and FP16 files.
- `"int8"` produces an additional dynamic-range INT8 model (INT8 weights, float activations). Static/full-integer INT8 is not supported.
- `calibration_data` can be `None`, an image directory, a `.npy` path, or a NumPy array. Directory images are loaded from common image extensions and capped by `max_images`; `.npy`/array data must be NHWC float32 in `[0, 1]` with three channels.
- The converter uses calibration data for ONNX-vs-TF validation; dynamic-range INT8 does not require representative data for activation calibration, but representative validation data is still better than random data.
- Import TensorFlow before ONNX in a fresh process for TFLite routes if your program imports both.

### ExecuTorch

- Experimental direct `torch.export` path; no ONNX intermediate.
- Public `RFDETR.export(format="executorch", ...)` requires an explicit `backend`.
- Backends: `xnnpack` portable CPU fp32, `coreml` Apple delegate fp16, `qnn` Qualcomm Snapdragon HTP fp16.
- `backend="qnn"` requires `soc`, for example `SM8650`, and an ExecuTorch source build against the QAIRT/QNN SDK. The pip wheel does not include the QNN delegate.
- `dynamic_batch=True` is refused. Export one `.pte` per batch.
- ExecuTorch runtime inputs must be contiguous NCHW tensors; after any transpose/permute, call `np.ascontiguousarray(...)` or `Tensor.contiguous()`.

### Native CoreML

- Experimental direct `.mlpackage` path via `torch.export` + `coremltools`.
- `format="coreml"` is not the same as `format="executorch", backend="coreml"`.
- `coreml_precision=None`/`"float32"` selects FP32 for tighter CPU parity; `"float16"` selects a smaller ANE-oriented bundle with expected numeric drift.
- `dynamic_batch=True` is refused. Export fixed-shape `.mlpackage` bundles.
- `backend` and `soc` are ignored with warnings for native CoreML because it is backend-agnostic at export API level.
- Detection and segmentation have export/parity coverage; keypoint CoreML export is not established in the verified evidence.

### Roboflow deployment bundle

- `export_for_roboflow(output_dir)` writes `weights.pt` and `class_names.txt` without a network call.
- `deploy_to_roboflow(workspace, project_id, version, api_key=None, size=None)` wraps bundle creation and uploads through the Roboflow SDK. It needs an API key argument or `ROBOFLOW_API_KEY`.
- Both bundle/deploy paths must run before `inference(inplace=True)` clears the original model weights.

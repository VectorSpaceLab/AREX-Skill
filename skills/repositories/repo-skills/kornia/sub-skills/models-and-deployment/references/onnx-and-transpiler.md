# ONNX And Transpiler Notes

This reference covers ONNX export/runtime helpers and Ivy-backed framework
conversion. It assumes a working PyTorch install and only uses ONNX / ONNX
Runtime / Ivy if those optional packages are available.

## ONNX export surfaces

### Generic exporter

`kornia.core.mixin.onnx.ONNXExportMixin` is the common export path for many
model and application wrappers.

Key behavior:

- Default input/output names are `input` / `output`.
- Default export opset is 17.
- Dynamic axes are inferred from `-1` dimensions in the input/output shape
  lists.
- If `save=True`, the exporter writes the ONNX file after constructing the
  `onnx.ModelProto` in memory.

Use this when the model already exposes a direct tensor-to-tensor forward.

### Model-specific overrides

Some models override the generic path because their Python forward is not a
single tensor graph.

- `DexiNed.to_onnx(...)` exports the edge model and keeps edge-map shapes.
- `RTDETR.to_onnx(...)` names outputs `pred_logits` and `pred_boxes`.
- `Sam.to_onnx(...)` exports the image encoder only; the prompt encoder and mask
decoder are not emitted as one ONNX graph because the full forward accepts
Python prompt structures.
- `ObjectDetector.to_onnx(...)` and `EdgeDetector.to_onnx(...)` can include or
exclude preprocessing/postprocessing, depending on whether the deployment stack
will handle those steps separately.
- `HFONNXComunnityModel.to_onnx(...)` can export the whole combined ONNX stack or
just the core model graph.

## ONNXModule and ONNXSequential

```python
from kornia.onnx import ONNXModule, ONNXSequential
```

### `ONNXModule`

Wrap one ONNX graph and obtain an ONNX Runtime session immediately.

Signature shape to remember:

```python
ONNXModule(op, providers=None, session_options=None, cache_dir=None, target_ir_version=None, target_opset_version=None)
```

Use it when:

- you already have one ONNX graph,
- you want a small runtime wrapper around a single export,
- you need to switch providers or session options without hand-writing ORT glue.

### `ONNXSequential`

Chain multiple ONNX graphs together.

```python
ONNXSequential(*ops, providers=None, session_options=None, io_maps=None, cache_dir=None, auto_ir_version_conversion=False, target_ir_version=None, target_opset_version=None)
```

Operational notes:

- Each adjacent pair of graphs is merged with ONNX composition utilities.
- `io_maps` describes how names on one boundary connect to the next boundary.
  Use one boundary entry per adjacent pair, for example
  `[[('output', 'input')]]` for a two-model chain. When omitted, Kornia assumes
  default `output`→`input` names.
- If `auto_ir_version_conversion=True`, Kornia will attempt to convert graph
  versions to a compatible target, defaulting to IR 9 and opset 17.
- `providers` are passed to ONNX Runtime in priority order.
- `session_options` should be used only when the installed ONNX Runtime version
  actually supports the requested knobs.

### Provider helpers

The ONNX Runtime mixin exposes provider switches on the session:

- `as_cpu(...)`
- `as_cuda(device_id=0, ...)`
- `as_tensorrt(device_id=0, ...)`
- `as_openvino(device_type="GPU", ...)`

Use them only when the matching execution provider is installed. `as_cuda` is
for `onnxruntime-gpu`, not CPU-only ORT.

## Loader and cache behavior

`kornia.onnx.utils.ONNXLoader` is the main loader/cache helper.

Supported inputs:

- local `.onnx` file paths,
- direct HTTP/HTTPS URLs,
- `hf://...` Kornia-hosted ONNX identifiers.

Important behavior:

- `download=False` is the safe mode for probes and offline review.
- `load_config(...)` fetches the associated JSON preprocessor config for some
  Hugging Face ONNX-community models.
- `add_metadata(...)` writes source/version metadata into the graph.
- `io_name_conversion(...)` renames input/output/node edges when a remote graph
  uses different node names than Kornia expects.

## HF ONNX community wrapper

`HFONNXComunnityModelLoader` and `HFONNXComunnityModel` combine a remote ONNX
model with optional preprocessing and postprocessing graphs.

Use them when:

- the model ships as a preprocessor JSON plus ONNX graph,
- you want to load an ONNX-community pipeline from Hugging Face,
- you need a deployable chain that still looks like a Kornia model.

This path is networked by design. It should be treated as optional and must not
run in default no-download probes.

## Transpiler notes

```python
import kornia
np_kornia = kornia.to_numpy()
jax_kornia = kornia.to_jax()
tf_kornia = kornia.to_tensorflow()
```

Operational notes:

- Transpilation is lazy: the first call converts on demand and is much slower
  than later calls.
- NumPy transpilation does not support trainable modules.
- JAX/TensorFlow transpilation can work for functions, classes, and trainable
  modules, but native compiler compatibility is limited.
- The generated source is cached by Ivy in the working directory, so repeated use
  from the same directory can be faster.

## Deployment heuristics

1. Export the smallest tensor graph that matches the deployment boundary.
2. Keep preprocessing/postprocessing in the graph only when the target runtime
   can support it.
3. Prefer a single device and dtype across the entire export path.
4. If ONNX or ORT is missing, stop at config inspection or native PyTorch export
   planning; do not simulate ONNXRuntime behavior.
5. If Ivy is missing, treat transpilation as unavailable rather than degraded.

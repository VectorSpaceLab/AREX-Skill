# Model Conversion Notes

Model conversion in Detectron2 spans TorchScript artifacts, optional Caffe2/ONNX exports, and checkpoint-format conversion. Keep these concerns separate.

## TorchScript Artifact Behavior

TorchScript exports from Detectron2 tracing/scripting can be loaded by PyTorch without importing Detectron2 Python code, but they may still need PyTorch and torchvision custom operators at runtime. C++ consumers typically need compatible libtorch and, for tracing/scripting exports, torchvision C++ operators.

Tracing artifacts created through `TracingAdapter` expose flattened tensor inputs/outputs. The adapter records schemas during export-time Python work, but the saved traced model itself usually accepts tensors rather than Detectron2 dictionaries. Preserve or document the schema mapping in deployment code if the consuming application needs rich `Instances` objects.

Scripting artifacts can preserve more of the model interface, but scripting works only when the model and all relevant `Instances` fields are statically scriptable. Use it for dynamic batch requirements only after confirming model-family support.

## Input Shape and Batch Constraints

- Tracing supports dynamic image height/width when the model path is trace-safe, but the number of input images is fixed by the sample used for tracing.
- Scripting can support dynamic batch size for supported official models.
- `caffe2_tracing` does not support batch inference in the documented deployment path.
- Caffe2-style exported graphs consume tensor/image-info inputs rather than Detectron2's high-level `list[dict]` interface.
- Random images can produce invalid or incomplete traces for detection models if they do not exercise proposal/mask/keypoint branches; use representative images or dataset samples.

## ONNX Caveats

Detectron2's ONNX paths are best treated as advanced export or graph-inspection tools. Depending on method and model, ONNX graphs may contain ATen fallback, custom ops, Caffe2-specific operators, or dynamic axes that need downstream runtime work.

Before promising ONNX runtime compatibility:

1. Confirm the `onnx` package is installed and compatible with the active PyTorch version.
2. Confirm any custom symbolic registrations or opset expectations.
3. Decide whether the goal is graph export, Netron inspection, Caffe2 conversion, ONNX Runtime execution, or TensorRT conversion.
4. Run a minimal representative export first; ONNX failures can include unsupported ops, shape specialization surprises, or process crashes in older stacks.

## Caffe2 and Protobuf Caveats

Caffe2 support is optional. In modern PyTorch builds, importing Caffe2 may fail, and Detectron2's Caffe2 export APIs are exposed only when those imports succeed. Treat Caffe2 as unavailable until proven.

Caffe2 exported protobuf files generally include graph and parameter files, but raw Caffe2 outputs may not include final Detectron2 post-processing. `Caffe2Model` can wrap protobuf models in Python to mimic Detectron2-style inference, but production applications often implement their own lightweight post-processing.

## Torchvision Checkpoint Conversion

Detectron2 has a small conversion utility for torchvision ResNet checkpoints. It maps torchvision key names such as `layer2` and batch-norm keys into Detectron2-style ResNet keys and writes a pickle with:

- `model`: converted state dictionary with NumPy arrays.
- `__author__`: `torchvision`.
- `matching_heuristics`: `True`.

Use this only when the task is to adapt a torchvision ResNet backbone checkpoint for a Detectron2 config. It is not a deployment exporter and does not produce TorchScript, ONNX, or Caffe2 artifacts.

When using such converted weights, configs usually also need torchvision-compatible normalization and stem assumptions, such as RGB format and ImageNet pixel mean/std. Route config editing details to the configuration sub-skill.

## Artifact Inventory

Common outputs by path:

- Tracing/scripting TorchScript: `model.ts`, plus optional `model_ts_code.txt`, `model_ts_IR.txt`, `model_ts_IR_inlined.txt`, and `model.txt` from `dump_torchscript_IR`.
- Tracing ONNX: `model.onnx` when using an ONNX export branch.
- Caffe2 protobuf: `model.pb`, `model_init.pb`, `model.pbtxt`, and optional graph visualization files.

Store export outputs in a dedicated output directory and avoid mixing artifacts from different methods, configs, devices, or weights in one directory.

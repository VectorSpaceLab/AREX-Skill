# FastReID deployment workflows

This reference distills the FastReID v1.3 deployment surfaces into self-contained operating guidance. It does not bundle heavyweight exporters, Caffe protobuf code, TensorRT engines, images, checkpoints, or compiled libraries. Use it to plan and diagnose deployment work before writing or running an export entrypoint in the user's prepared application environment.

## Common prerequisites for every export

1. **FastReID imports from source or an installed application checkout.** The package import name is `fastreid`; this repository version is source-only, so distribution metadata may be absent even when imports work.
2. **A complete config is available.** Merge the user's YAML/config object first, apply `opts`, then freeze. For project configs, import the project package and call its `add_*_config` function before merging project-only keys.
3. **A local checkpoint is available.** Exports load `cfg.MODEL.WEIGHTS`. Do not assume model-zoo weights are downloaded; require an explicit local path when producing an artifact.
4. **Disable unwanted pretraining downloads.** For export checks and eval-only/export builds, defrost config and set `MODEL.BACKBONE.PRETRAIN = False` before `build_model(cfg)`.
5. **Match device and shape.** `cfg.MODEL.DEVICE`, `cfg.INPUT.SIZE_TEST`, export batch size, runtime batch size, and engine/device target must agree.
6. **Use the same preprocessing for validation.** FastReID image deployment surfaces read OpenCV BGR images, convert to RGB, resize to `(width, height)`, create `float32` CHW tensors, and compare L2-normalized feature vectors.

## ONNX export and ONNX Runtime inference

### Optional packages

- Export: `torch`, `onnx`, `onnxoptimizer`, `onnxsim`.
- Runtime inference: `onnxruntime`, `numpy`, `cv2`/OpenCV.
- Project models: project package import dependencies as listed in [project-extensions.md](project-extensions.md).

The ONNX export surface imports ONNX packages before parsing CLI arguments. If `--help` fails with `ModuleNotFoundError: onnx`, classify it as a missing optional dependency, not as a broken parser.

### Export interface template

Use an export entrypoint that implements the following interface:

```bash
python <onnx-export-entrypoint> \
  --config-file <config.yml> \
  --name <artifact-name> \
  --output <output-dir> \
  --batch-size <export-batch-size> \
  --opts MODEL.WEIGHTS <checkpoint.pth> MODEL.DEVICE <cpu-or-cuda>
```

FastReID v1.3 ONNX export behavior to preserve:

- Build the model with `fastreid.modeling.meta_arch.build_model(cfg)` after config merge.
- Set `MODEL.BACKBONE.PRETRAIN = False` before model construction.
- If `MODEL.HEADS.POOL_LAYER == "FastGlobalAvgPool"`, replace it with `"GlobalAvgPool"` for export compatibility.
- Load the checkpoint with `Checkpointer(model).load(cfg.MODEL.WEIGHTS)`.
- If the backbone has a `deploy(True)` method, call it before export.
- Run the model in eval mode.
- Trace with a dummy input shaped `(batch_size, 3, cfg.INPUT.SIZE_TEST[0], cfg.INPUT.SIZE_TEST[1])` on the model device.
- Optimize ONNX with passes such as `extract_constant_to_initializer`, `eliminate_unused_initializer`, and `fuse_bn_into_conv` when available.
- Simplify and validate the graph with `onnxsim.simplify`; fail the export if simplification reports an invalid graph.
- Remove initializers from graph inputs for ONNX IR versions that permit it.

### Inference interface template

Use an ONNX Runtime entrypoint that implements the following interface:

```bash
python <onnx-inference-entrypoint> \
  --model-path <artifact-name>.onnx \
  --input <image-a.jpg> <image-b.jpg> \
  --height <image-height> \
  --width <image-width> \
  --output <feature-output-dir>
```

Runtime behavior to preserve:

- Load the ONNX graph with `onnxruntime.InferenceSession`.
- Use the first graph input name from the session.
- For each local image: read with OpenCV, convert BGR to RGB, resize to `(width, height)`, cast to `float32`, transpose to CHW, and add a batch dimension.
- Run the session and L2-normalize features along axis 1.
- Write feature arrays only to an explicit output directory when requested.

### ONNX validation

Compare PyTorch and ONNX Runtime outputs on the same local images and the same checkpoint/config:

```python
import numpy as np
np.testing.assert_allclose(torch_features, onnx_features, rtol=1e-3, atol=1e-6)
```

If this fails, check preprocessing order, config shape, feature normalization, unsupported operators, export batch size, and project imports before treating the model weights as bad.

## Caffe conversion and inference

### Optional packages and artifacts

- PyTorch conversion helpers compatible with FastReID's Caffe export path.
- PyCaffe import package `caffe` and its protobuf runtime.
- A compatible Caffe runtime for inference; GPU mode may be used by the original runtime path.
- Local FastReID checkpoint and config.
- Generated protobuf/vendor helper code is **not bundled** by this skill; treat it as an external Caffe-environment responsibility.

### Conversion interface template

Use a Caffe export entrypoint that implements the following interface:

```bash
python <caffe-export-entrypoint> \
  --config-file <config.yml> \
  --name <artifact-name> \
  --output <output-dir> \
  --opts MODEL.WEIGHTS <checkpoint.pth> MODEL.DEVICE <cpu-or-cuda>
```

FastReID v1.3 Caffe conversion behavior to preserve:

- Merge config and load checkpoint as in the ONNX workflow.
- Set `MODEL.BACKBONE.PRETRAIN = False`.
- Set `MODEL.HEADS.POOL_LAYER = "Identity"`.
- Set `MODEL.BACKBONE.WITH_NL = False` for the baseline conversion path.
- Trace a dummy tensor shaped `(1, 3, cfg.INPUT.SIZE_TEST[0], cfg.INPUT.SIZE_TEST[1])`.
- Save both `*.prototxt` and `*.caffemodel` in the explicit output directory.

### Required prototxt adjustments

The baseline Caffe conversion path requires manual prototxt edits before reliable inference:

1. In MaxPooling layers, remove `ceil_mode: false` if the target Caffe parser rejects it.
2. Add a global average pooling layer after the final spatial activation when needed:

```prototxt
layer {
  name: "avgpool1"
  type: "Pooling"
  bottom: "relu_blob49"
  top: "avgpool_blob1"
  pooling_param {
    pool: AVE
    global_pooling: true
  }
}
```

3. Rename the final output top to `output` so inference can read the expected blob.

### Caffe inference interface template

```bash
python <caffe-inference-entrypoint> \
  --model-def <artifact-name>.prototxt \
  --model-weights <artifact-name>.caffemodel \
  --input <image-a.jpg> <image-b.jpg> \
  --height <image-height> \
  --width <image-width> \
  --output <feature-output-dir>
```

Caffe preprocessing differs slightly from the ONNX Runtime path in this version: after BGR-to-RGB conversion and CHW conversion, it applies ImageNet-style channel mean/std normalization in pixel units. Validate Caffe output against PyTorch on the same local images with a tolerance such as `rtol=1e-3, atol=1e-6` after feature normalization.

## TensorRT from ONNX

### Optional packages and hardware

- `tensorrt` Python package for engine build.
- `pycuda` for the Python inference wrapper.
- NVIDIA GPU, compatible CUDA driver/runtime, and TensorRT version.
- A valid ONNX model exported for the desired input shape and batch behavior.

TensorRT export imports `tensorrt` before argument parsing. If `--help` fails with `ModuleNotFoundError: tensorrt`, classify it as a missing optional runtime stack.

### Engine build interface template

```bash
python <trt-export-entrypoint> \
  --onnx-model <artifact-name>.onnx \
  --name <engine-name> \
  --output <output-dir> \
  --mode fp32 \
  --batch-size <max-batch-size> \
  --height <image-height> \
  --width <image-width> \
  --channel 3
```

Runtime behavior to preserve:

- Use TensorRT explicit batch network creation.
- Parse the ONNX file and report every parser error when parsing fails.
- Re-mark output tensors through identity layers so outputs have predictable names.
- Build an engine for `fp32`, `fp16`, or `int8` only when the builder and hardware support the selected mode.
- Serialize the engine only to an explicit output directory.

The int8 calibrator path in this FastReID version is known to be fragile; treat int8 as experimental unless a complete calibration dataset, TensorRT stack, and target device are available.

### TensorRT inference interface template

```bash
python <trt-inference-entrypoint> \
  --model-path <engine-name>.engine \
  --input <image-a.jpg> <image-b.jpg> \
  --batch-size <engine-batch-size> \
  --height <image-height> \
  --width <image-width> \
  --output <feature-output-dir>
```

TensorRT inference behavior to preserve:

- Deserialize the engine on the target GPU.
- Allocate host/device buffers from engine bindings.
- Pad partial final batches with zeros, then discard padded outputs.
- Use BGR-to-RGB conversion, resize, CHW `float32`, and L2-normalized features.
- Rebuild the engine if GPU architecture, TensorRT version, batch size, binding shapes, or driver/runtime compatibility changes.

## FastRT C++ TensorRT path

FastRT is a separate C++ TensorRT implementation that defines the ReID network through TensorRT network APIs rather than relying on an ONNX parser. Use it only when a C++/TensorRT build stack is part of the user's target deployment.

Operating flow:

1. Generate a `.wts` file from a local PyTorch checkpoint.
2. Edit the C++ model constants to match the trained config: weights path, engine path, max batch size, input height/width, output feature size, device id, backbone type, head type, head pooling, last stride, IBN flag, non-local flag, and embedding dimension.
3. Build with CMake flags appropriate for the target:
   - `BUILD_FASTRT_ENGINE=ON` to build the engine implementation.
   - `BUILD_DEMO=ON` to build a demo executable.
   - `USE_CNUMPY=ON` when the demo needs CNumPy helpers.
   - `BUILD_FP16=ON` for FP16 if the GPU supports it.
   - `BUILD_INT8=ON` and `INT8_CALIBRATE_DATASET_PATH=<local-dir-ending-with-slash>` for int8 calibration.
   - `BUILD_PYTHON_INTERFACE=ON` to build a Python extension around the C++ engine.
4. Serialize an engine, then deserialize it for inference.
5. Verify C++/TensorRT output against PyTorch output on identical local images before using speed-mode builds.

There is no CPU-equivalent verification for FastRT. Treat it as unverified until it compiles and runs on the target TensorRT/CUDA stack.

## Validation checklist

- `scripts/check_deployment_dependencies.py` reports all packages required for the chosen backend as installed.
- Project packages for custom configs are imported before config merge/build.
- `MODEL.BACKBONE.PRETRAIN` is disabled unless a pretrain download is intentionally allowed.
- `MODEL.WEIGHTS` points to a local checkpoint that matches the config.
- Export batch, runtime batch, `INPUT.SIZE_TEST`, and engine binding shapes match.
- Same images and same preprocessing are used across PyTorch and deployed runtimes.
- Numeric comparison tolerances are appropriate for the backend precision (`fp32` tighter than `fp16`/`int8`).
- Caffe and TensorRT artifacts are rebuilt when their target runtime changes.

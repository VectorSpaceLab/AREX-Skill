# YOLOX Deployment Backends

YOLOX includes examples for several deployment stacks. Treat every backend here as optional until the target environment is probed.

| Backend | Input artifact | Best for | Requirements | Caveats |
|---|---|---|---|---|
| ONNXRuntime | ONNX graph | Portable Python/CPU/GPU inference | `onnxruntime`, exported ONNX, OpenCV/numpy postprocess | Preserve YOLOX resize ratio and postprocess thresholds. |
| TensorRT Python | PyTorch checkpoint converted through `torch2trt` | NVIDIA GPU latency | CUDA GPU, TensorRT, `torch2trt`, matching torch/CUDA | Engine is hardware/runtime-specific; batch/fp16 choices matter. |
| TensorRT C++ | Serialized TensorRT engine | C++ NVIDIA deployment | TensorRT SDK, CUDA, compiler | Requires building against local SDK; not portable as a generic script. |
| OpenVINO | ONNX or converted IR | Intel CPU/iGPU/VPU deployment | OpenVINO runtime/tools | Opset and Focus/decode behavior can affect conversion. |
| ncnn | ncnn `.param`/`.bin` | Lightweight/mobile C++/Android | ncnn tools/SDK, compiler or Android toolchain | Older conversion flows may need Focus-layer handling or graph edits. |
| MegEngine | MegEngine model/runtime | MegEngine ecosystem | MegEngine runtime/tools | Separate framework path, not PyTorch base install. |
| nebullvm | Optimized model artifact | Automated inference optimization | nebullvm stack and supported accelerator | Extra dependencies and benchmark-style checks may be expensive. |

## ONNXRuntime operating notes

ONNXRuntime inference must reproduce YOLOX preprocessing and postprocessing:

1. Resize with aspect-ratio preservation to `exp.test_size`.
2. Keep the resize ratio to map boxes back to original image coordinates.
3. Run the ONNX session with the correct input tensor name and shape.
4. Decode outputs if the graph was exported with raw head outputs.
5. Apply confidence threshold, NMS, and class-name mapping consistent with training.

If boxes appear shifted or scaled wrong, check `decode_in_inference`, ratio rescaling, channel order, and whether class/confidence columns are interpreted like YOLOX PyTorch `postprocess`.

## TensorRT decision point

Do not promise TensorRT support just because CUDA works. TensorRT requires a compatible TensorRT installation, torch/CUDA ABI alignment, and generated engine files for the target hardware. If the user only has a `.pth` checkpoint, export/deploy in this order:

1. Validate PyTorch model/Exp/checkpoint compatibility.
2. Export ONNX or run the TensorRT conversion path in a TensorRT-ready environment.
3. Validate the engine on the same runtime family that will serve it.

## Legacy weights

YOLOX update notes describe a preprocessing breaking change where old weights require `--legacy` in PyTorch demo/eval. Current deployment demos do not support those old legacy weights. Use a compatible older YOLOX version for deployment or regenerate weights under the current preprocessing contract.

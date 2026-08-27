# Quantization and TensorRT

YOLOv7-d2 contains experimental deployment material for ONNX quantization, int8 demos, and TensorRT C++/Python workflows. Treat these as optional advanced workflows.

## Source artifact routing

- `deploy/demo_quantized_int8.py`: reference-only; despite its name, it uses a TensorRT inferencer backend plus SparseInst-style mask/scores/labels postprocessing.
- `deploy/quant_onnx/readme.md` and `deploy/quant_onnx/*.py`: reference-only; they show ONNXRuntime/AtomQuant quantization experiments, calibration readers, and opset sensitivity notes.
- `deploy/trt_cc/readme.md` and C++ demo: reference-only; they show a YOLOX TensorRT engine build/run pattern with local TensorRT/CUDA/OpenCV assumptions.
- `tools/demo_trt_detr.py`: reference-only DETR TensorRT demo with fixed-shape TensorRT/PyCUDA assumptions.
- `tools/demo_onnx_detr.py`: DETR ORT behavior is covered in [onnxruntime-inference.md](onnxruntime-inference.md).

## Quantization notes

The source quantization files include ONNXRuntime quantization experiments and other external tool stacks. They may require:

- A completed ONNX model.
- Calibration data/images.
- ONNXRuntime quantization APIs or other quantization packages.
- Model-family-specific postprocessing.
- Careful opset choices. The source notes SparseInst/keypoint quantization problems around opset changes.

Do not run quantization as a default check. Ask for the model, calibration policy, target runtime, and acceptable accuracy drop.

## TensorRT notes

The C++ TensorRT demo pattern is:

```bash
mkdir build
cd build
cmake ..
make -j8
./demo_yolox path/to/model.trt -i path/to/image.jpg
```

This requires TensorRT headers/libraries, CUDA, a compatible engine or ONNX-to-engine build path, CMake, compiler, and GPU access. Engine compatibility is tied to TensorRT version, GPU, and build settings.

## Verification boundary

A PyTorch CUDA smoke does not verify TensorRT or quantized inference. Verify each target runtime separately with its own provider/toolchain and a small known input.

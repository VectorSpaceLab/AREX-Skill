# Backend Compatibility

## CPU

CPU PaddlePaddle is the portable baseline and is enough for source inspection,
Fast/Auto experiments, and many short videos. Install CPU Paddle before general
requirements:

```bash
pip install paddlepaddle==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install -r requirements.txt
```

## CUDA

For NVIDIA GPU acceleration, install a PaddlePaddle GPU wheel whose CUDA tag is
compatible with the host driver and GPU. The README highlights CUDA 11.8 and CI
also shows CUDA 12.6 packaging paths. Verify with a backend probe; do not rely
on Task Manager or generic messages.

```bash
pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
pip install -r requirements.txt
```

If the GPU is newer than the supported Paddle CUDA runtime, prefer a documented
DirectML/ONNX path or a CPU baseline instead of forcing an incompatible wheel.

## DirectML and ONNX providers

DirectML is a Windows-oriented acceleration path for AMD, Intel, and some
NVIDIA devices:

```bash
pip install paddlepaddle==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install -r requirements.txt
pip install -r requirements_directml.txt
```

`HardwareAccelerator` detects ONNX Runtime providers other than CPU, including
DirectML, ROCm, MIGraphX, VitisAI, OpenVINO, Metal, CoreML, and CUDA providers.
Provider presence is acceleration evidence only after the relevant OCR/export
path is also usable.

## Verification signals

- `paddle.is_compiled_with_cuda()` must be true for Paddle CUDA.
- `paddle.static.cuda_places()` should report at least one usable CUDA place.
- `onnxruntime.get_available_providers()` should list a non-CPU provider for
  ONNX acceleration.
- VSE's `HardwareAccelerator.accelerator_name` should report GPU/provider when
  hardware acceleration is enabled.

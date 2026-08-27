# Platforms, TensorRT-RTX, DLA, Jetson, and Windows

## Platform support summary

Torch-TensorRT is GPU-focused. Public docs for this source snapshot identify Linux x86-64 GPU, Linux SBSA GPU, Windows GPU Dynamo workflows, and Jetson source builds as supported areas. Linux ppc64le is not supported.

## TensorRT-RTX

TensorRT-RTX is a drop-in-style TensorRT variant for RTX desktop/laptop/workstation targets, exposed through the `torch-tensorrt-rtx` distribution while keeping import path `torch_tensorrt`.

Use it when:

- Target machines are RTX GPUs and the user wants TensorRT-RTX runtime JIT behavior.
- The user asks for RTX runtime cache, dynamic-shape kernel specialization, or `cuda_graph_strategy` in `RuntimeSettings`.
- The user installed `torch-tensorrt-rtx` and `ENABLED_FEATURES.tensorrt_rtx` is true.

Cautions:

- Torch-TensorRT docs describe RTX support as experimental.
- FX frontend and QDP plugin support may be disabled in TensorRT-RTX builds.
- Runtime cache/settings should be applied before first execution.

## DLA / Jetson

DLA is available on supported NVIDIA embedded platforms, not on ordinary data-center GPUs unless the hardware exposes DLA.

Rules:

- DLA supports FP16 and INT8 only.
- Use `torch_tensorrt.Device("dla:0", allow_gpu_fallback=True)` in Python workflows where DLA is supported.
- For TorchScript/C++ DLA examples, set DLA device type, GPU id managing DLA, DLA core id, FP16/INT8 precision, and optional GPU fallback.
- Jetson source builds may need JetPack-specific flags and platform-compatible PyTorch wheels/containers.

## Windows x86-64 cross-compile

`torch_tensorrt.dynamo.cross_compile_for_windows` compiles on Linux x86-64 and emits an exported program containing Windows-compatible engines.

Requirements:

- Linux x86-64 build host with CUDA and TensorRT installed.
- Windows x86-64 target with a compatible NVIDIA GPU.
- Windows target has same-or-newer CUDA compute capability or the build uses compatible settings.
- Cross-compile feature gate is available.

Limitations documented by the project:

- `enable_cross_compile_for_windows=True` is set by the cross-compile API; do not set it manually on generic compile calls.
- Lazy engine initialization and engine caching are disabled during cross-compilation.
- Use `hardware_compatible=True` for Ampere-or-newer GPU portability when needed.

## Windows ARM64 source build

The repository documents native and cross-build workflows for Windows ARM64 TensorRT-RTX wheels. Important constraints:

- Visual Studio 2022 C++ tools with ARM64 compiler components.
- CUDA Toolkit 13.4 Preview in the documented snapshot.
- Compatible Windows ARM64 PyTorch 2.14 package and Python 3.13.
- Native ARM64 build uses ARM64 Python; cross-build uses x64 Python plus target ARM64 torch/CUDA/Python roots.
- Cross-build passes `--windows-on-arm` or `TORCHTRT_TARGET_PLATFORM=windows-arm64`.

Route detailed command construction to the build/maintenance sub-skill.

## Compatibility notes

- TensorRT engines are not universally portable. Check GPU compute capability, TensorRT version, CUDA version, package flavor, and compatibility flags.
- Moving from standard TensorRT to TensorRT-RTX or back can change available features and runtime behavior.
- Prefer target-like validation for every deployment platform.

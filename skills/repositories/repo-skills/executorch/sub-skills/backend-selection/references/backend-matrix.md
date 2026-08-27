# Backend Matrix

| Backend | Platform | Hardware | Python/export surface | Build/runtime prerequisites | CPU substitute |
| --- | --- | --- | --- | --- | --- |
| XNNPACK | Linux/macOS/Windows/Android/iOS | CPU | `XnnpackPartitioner` | XNNPACK build enabled for runtime; usually best first delegate | Full for CPU behavior |
| Core ML | iOS/macOS | Apple Neural Engine/GPU/CPU | Core ML partitioner/quantizer | `coremltools`, Apple runtime/toolchain for execution | None for Apple delegate execution |
| MPS/Metal | iOS/macOS | Apple GPU | MPS/Metal partitioners | macOS/iOS toolchain and Metal-capable target | None for delegate execution |
| Vulkan | Android/Linux/Windows | GPU | Vulkan backend/partitioner | Vulkan SDK/driver/glslc/submodules | None for GPU behavior |
| CUDA/AOTI | Linux/Windows | NVIDIA GPU | CUDA/AOTI partitioner | CUDA-capable PyTorch/toolchain and CMake CUDA targets | None for GPU behavior |
| OpenVINO | Linux/Intel targets | CPU/GPU/NPU | OpenVINO backend | OpenVINO dependency/runtime availability | Partial; CPU can validate only non-accelerated logic |
| Qualcomm QNN | Android/Qualcomm | NPU/DSP/GPU/CPU through QNN | QNN partitioner/compile specs | QNN SDK, Android NDK, SoC/device or x86 mode | None; route to `qualcomm` |
| MediaTek | Android/MediaTek | NPU | MediaTek backend examples | MediaTek SDK/tooling/device | None |
| Samsung Exynos | Android/Samsung | CPU/GPU/NPU | Samsung backend examples | Samsung SDK/device prerequisites | None |
| NXP | Embedded/NXP | NPU | Neutron/NXP partitioner | NXP SDK/toolchain/device | None |
| Cadence | Embedded/DSP | DSP | Cadence backend examples/tests | Cadence toolchains/simulators | None |
| Arm Ethos-U/VGF | Embedded/Arm/Android | NPU/GPU | Arm partitioners/quantizers | Vela/TOSA/VGF deps, FVP/board/toolchain | Partial for graph checks only |
| Cortex-M | Embedded Arm MCU | CPU/CMSIS-NN | CortexMQuantizer + graph passes | Arm toolchain/FVP for implementation | Partial; route to `cortex-m` |

## Backend Criticality Rule

Mark a backend required only when the user's task cannot be truthfully completed without proving that backend. Otherwise, document backend commands and prerequisites while keeping verification CPU/import/static unless the user provides the SDK/device.


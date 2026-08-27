# Build and Install Workflows

## Purpose

Use this reference to choose the smallest safe install/build path for ExecuTorch. Hardware SDKs, mobile devices, and broad optional dependencies are prerequisites, not assumptions.

## Environment Baseline

- Python: 3.10 through 3.14.
- C++: C++17-compatible compiler. Linux commonly uses GCC/Clang; Windows requires Visual Studio 2022+ with Clang-CL; macOS requires Xcode Command Line Tools.
- CMake: 3.24+ is expected by package build metadata.
- Prefer an isolated conda/venv over system Python or Conda `base`.

## Python Package Paths

| Goal | Command pattern | Notes |
| --- | --- | --- |
| Published package user | `pip install executorch` | Use when the user only needs public wheel behavior. Backend pybindings present depend on the wheel/platform. |
| Source development | `./install_executorch.sh --editable` | Installs dependencies, configures CMake, builds Python package artifacts, and keeps Python code editable. |
| Lean source install | `./install_executorch.sh --minimal` | Reduces dependencies/features for export-focused workflows. Do not claim backend/runtime pybindings are present until imports prove it. |
| Dependency already prepared | `pip install -e . --no-build-isolation` | Faster after a previous full install. Re-run full install after C++/extension/build-option changes. |
| Use pinned PyTorch | `./install_executorch.sh --use-pt-pinned-commit` | Useful for install conflicts or Intel macOS cases where current wheels are unavailable. |

## CMake Runtime Builds

Configure once, then build repeatedly:

```bash
cmake -B cmake-out --preset linux -DCMAKE_BUILD_TYPE=Release
cmake --build cmake-out --parallel "$(nproc 2>/dev/null || sysctl -n hw.ncpu)"
```

Common configure presets discovered from the repository include `linux`, `macos`, `windows`, `android-arm64-v8a`, `android-x86_64`, `ios`, `ios-simulator`, `pybind`, `profiling`, `zephyr`, `arm-baremetal`, `arm-ethosu-linux`, `llm-release`, `llm-release-cuda`, `llm-release-metal`, `llm-debug`, `llm-debug-cuda`, `llm-debug-metal`, `llm-debug-vulkan`, `mlx-release`, and `mlx-debug`.

### Frequently Used CMake Flags

| Flag | Enables |
| --- | --- |
| `EXECUTORCH_BUILD_XNNPACK=ON` | XNNPACK CPU delegate. |
| `EXECUTORCH_BUILD_COREML=ON` | Core ML delegate and Apple Core ML artifacts. |
| `EXECUTORCH_BUILD_MPS=ON` | Apple MPS backend. |
| `EXECUTORCH_BUILD_VULKAN=ON` | Vulkan backend; requires Vulkan tooling/submodules. |
| `EXECUTORCH_BUILD_CUDA=ON` | CUDA/AOTI backend; requires CUDA-capable toolchain and compatible PyTorch. |
| `EXECUTORCH_BUILD_QNN=ON` | Qualcomm backend; requires QNN SDK path and usually Android NDK/device workflows. |
| `EXECUTORCH_BUILD_OPENVINO=ON` | OpenVINO backend on Linux. |
| `EXECUTORCH_BUILD_EXTENSION_MODULE=ON` | Higher-level C++ `Module` API; depends on loader/flat tensor/named data map components. |
| `EXECUTORCH_BUILD_EXTENSION_TENSOR=ON` | C++ Tensor convenience API. |
| `EXECUTORCH_BUILD_DEVTOOLS=ON` | Developer tools and profiling/debug support. |
| `EXECUTORCH_BUILD_TESTS=ON` | C++ test targets. |
| `EXECUTORCH_OPTIMIZE_SIZE=ON` | Size-optimized release build; route to `binary-size` for analysis. |

## Cross-Compilation Entry Points

- Android AAR/native builds require Android SDK/NDK and ABI selection. Keep NDK paths explicit and route backend-specific Android delegate setup to `backend-selection` or `qualcomm`.
- Apple frameworks require macOS/Xcode. Link generated frameworks with the documented force-load/all-load style when static registration symbols are otherwise pruned.
- Embedded/Zephyr/Arm workflows require board/toolchain/FVP prerequisites and route to `cortex-m` for CMSIS-NN details.

## Success Signals

- Python install: `import executorch.exir` succeeds and, if runtime pybindings are required, `import executorch.runtime` succeeds without `_portable_lib` errors.
- CMake configure: the expected preset and `EXECUTORCH_*` flags appear in the cache.
- Runtime build: expected libraries/executables appear under the build/install directory.
- Source checkout health: expected submodule sentinel files exist for the selected backend; missing unrelated optional submodules should not block CPU-only work.


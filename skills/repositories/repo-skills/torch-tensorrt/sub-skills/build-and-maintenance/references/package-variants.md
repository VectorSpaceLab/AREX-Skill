# Package Variants

Torch-TensorRT source and wheels use build flags that change available features. Pick the variant before suggesting commands.

## Common build flags and environment selectors

| Flag / variable | Effect | Use when |
| --- | --- | --- |
| `PYTHON_ONLY=1` or `--py-only` | Builds a Python-only distribution and skips C++ runtime/TorchScript components. | The user only needs Dynamo/Python runtime workflows. |
| `NO_TORCHSCRIPT=1` or `--no-ts` | Skips the legacy TorchScript frontend while keeping the C++ runtime available. | The user does not need TorchScript but does need runtime libraries. |
| `USE_TRT_RTX=1` or `--use-rtx` | Builds the TensorRT-RTX variant. | The target is RTX hardware or TensorRT-RTX behavior is explicitly required. |
| `CU_VERSION=cu13x` | Overrides CUDA version tagging in packaging logic. | The build must match a specific CUDA wheel family. |
| `TORCHTRT_TARGET_PLATFORM=windows-arm64` / `--windows-on-arm` | Targets Windows ARM64 build flow. | The user is building a Windows ARM64 wheel or cross-build. |
| `JETPACK_BUILD=1` | Enables JetPack-specific build behavior when building for Jetson. | The target is NVIDIA Jetson / embedded. |

## Practical selection rules

- Use `PYTHON_ONLY=1` when the user wants lightweight Python-only import/compile workflows and accepts that C++/TorchScript serialization support may be reduced.
- Use `NO_TORCHSCRIPT=1` when the user wants runtime support but not the legacy TorchScript frontend.
- Use `USE_TRT_RTX=1` when the target machine and dependency stack are RTX-specific.
- Use platform selectors only when the host and target requirements match the documented build flow.

## Version alignment

The repository's build metadata is tied to the installed PyTorch/CUDA/TensorRT family. Mismatches can produce import or ABI issues even when the wheel builds.

Checklist:

- PyTorch version aligns with build metadata.
- CUDA family matches the selected wheel/index.
- TensorRT or TensorRT-RTX family matches the chosen flavor.
- The user knows whether the artifact is a source build, editable install, or release wheel.

## Don't confuse package names

- Import path stays `torch_tensorrt`.
- Distribution names differ: `torch-tensorrt` vs `torch-tensorrt-rtx`.
- The build variant determines available features, not just the import path.

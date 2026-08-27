# Artifact Deployment Matrix

Use this matrix before writing final compile/save instructions.

| User target | Preferred artifact | Compile/save shape | Runtime dependencies | Verification |
| --- | --- | --- | --- | --- |
| Python inference with PyTorch available | `.ep` ExportedProgram | `torch_tensorrt.save(compiled, "model.ep", output_format="exported_program", inputs=... or arg_inputs=...)` | Python, PyTorch, compatible Torch-TensorRT behavior for TRT-backed submodules | Load with `torch.export.load(...).module()` or `torch_tensorrt.load(...).module()` and compare output. |
| C++/libtorch inference | `.ts` TorchScript | `torch_tensorrt.save(compiled, "model.ts", output_format="torchscript", inputs=...)` | libtorch and Torch-TensorRT runtime libraries, compatible CUDA/TensorRT | C++ smoke with `torch::jit::load` and representative tensors. |
| Linux package without Torch-TensorRT import at runtime | `.pt2` AOTInductor | `torch_tensorrt.save(compiled, "model.pt2", output_format="aot_inductor", retrace=True, arg_inputs=...)` | Linux AOTInductor runtime, PyTorch AOTI loader | `torch._inductor.aoti_load_package("model.pt2")` and C++ AOTI loader if needed. |
| TensorRT-native runtime only | `.engine` | `convert_exported_program_to_serialized_trt_engine(..., require_full_compilation=True)` then write bytes | TensorRT runtime, target GPU compatibility | Deserialize with TensorRT runtime and run a binding-level smoke. |
| Triton serving with Torch-TensorRT/PyTorch backend | model repository directory | Package artifact and `config.pbtxt` | Triton Server image/backend with matching runtime deps | Start Triton in an approved environment and run a client request. |
| ExecuTorch target | `.pte` | ExecuTorch export/lowering flow | ExecuTorch and target runtime packages | Load with target ExecuTorch runtime. |

## Portability checks

Ask these before promising portability:

- Was the engine built with `hardware_compatible=True` when moving across Ampere-or-newer GPU SKUs?
- Was `version_compatible=True` used when moving across compatible TensorRT versions?
- Does the target have the same package flavor: standard TensorRT vs TensorRT-RTX?
- Is the target OS supported by the artifact format? AOTInductor packaging is Linux-focused; Windows cross-compile has its own API and limitations.
- Are runtime libraries on the library path for C++/TorchScript artifacts?
- Are dynamic shape ranges sufficient for target requests?

## Minimal artifact validation plan

For any artifact:

1. Save the artifact from a small representative input.
2. Start a fresh Python or target process.
3. Load the artifact.
4. Execute one min, one opt, and one max shape for dynamic profiles when relevant.
5. Compare against eager output or task metrics.
6. Record package versions, GPU name/compute capability, CUDA driver/runtime, TensorRT version, and artifact flags.

## Red flags

- User wants `.engine` while the model requires PyTorch fallback.
- User wants C++ deployment but installed a Python-only Torch-TensorRT build.
- User wants TensorRT-RTX runtime settings with a standard TensorRT package.
- User wants DLA on hardware without DLA or with FP32-only expectations.
- User wants to move engines across machines without testing version/hardware compatibility.

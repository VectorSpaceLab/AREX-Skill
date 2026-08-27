# Serialization and TensorRT Engine Artifacts

Choose the artifact before writing save/load code. Torch-TensorRT supports several targets with different runtime dependencies.

## Artifact matrix

| Artifact | Produce with | Load/run with | Best for | Main requirements |
| --- | --- | --- | --- | --- |
| `.ep` ExportedProgram | `torch_tensorrt.save(compiled, "model.ep", output_format="exported_program", inputs=... or arg_inputs=...)` | `torch.export.load("model.ep").module()` or `torch_tensorrt.load("model.ep").module()` | Python deployment with PyTorch integration. | Python runtime, PyTorch, compatible Torch-TensorRT behavior for TRT submodules. |
| `.ts` TorchScript | `torch_tensorrt.save(..., output_format="torchscript")` | Python `torch.jit.load` or C++ `torch::jit::load` | C++/libtorch deployment with Torch-TensorRT runtime. | TorchScript frontend/runtime libraries enabled; not Python-only. |
| `.pt2` AOTInductor package | `torch_tensorrt.save(..., output_format="aot_inductor", retrace=True, arg_inputs=...)` | `torch._inductor.aoti_load_package` in Python or AOTI package loader in C++ | Linux self-contained package without Torch-TensorRT import at inference time. | Linux AOTInductor stack; correct retrace and dynamic shapes. |
| `.engine` raw TensorRT bytes | `torch_tensorrt.dynamo.convert_exported_program_to_serialized_trt_engine(...)` then write bytes. | TensorRT runtime deserialization or other TRT-native runtime. | No PyTorch wrapper at inference time. | Entire graph must be TensorRT-convertible; no PyTorch fallback. |
| `.pte` ExecuTorch | ExecuTorch lowering/export flow plus Torch-TensorRT backend. | ExecuTorch runtime package. | Edge/mobile-like workflows that use ExecuTorch. | ExecuTorch dependency and target runtime; optional in many installs. |

## ExportedProgram save/load

```python
compiled = torch_tensorrt.compile(model, ir="dynamo", inputs=example_inputs)
torch_tensorrt.save(compiled, "model.ep", output_format="exported_program", inputs=example_inputs)
loaded = torch.export.load("model.ep").module()
out = loaded(*example_inputs)
```

Use this for Python-side deployment when C++ runtime is not the primary target. If `torch_tensorrt.load` is used, still verify that the loaded module executes in the target environment.

## TorchScript save/load

```python
torch_tensorrt.save(compiled, "model.ts", output_format="torchscript", inputs=example_inputs)
# Python smoke
ts = torch.jit.load("model.ts")
# C++ uses torch::jit::load with Torch-TensorRT runtime libraries available.
```

Do not recommend `.ts` if `ENABLED_FEATURES.torchscript_frontend` or `ENABLED_FEATURES.torch_tensorrt_runtime` is false.

## AOTInductor package

```python
torch_tensorrt.save(
    compiled,
    "model.pt2",
    output_format="aot_inductor",
    retrace=True,
    arg_inputs=example_inputs,
    dynamic_shapes=dynamic_shapes,
)
```

Use for Linux AOTI deployment when the user wants a `.pt2` package and can verify AOTInductor compatibility. `retrace=True` is important when compiled modules contain TRT engine subgraphs.

## Raw TensorRT engine

```python
exported = torch.export.export(model, tuple(example_inputs))
engine_bytes = torch_tensorrt.dynamo.convert_exported_program_to_serialized_trt_engine(
    exported,
    arg_inputs=example_inputs,
    require_full_compilation=True,
    hardware_compatible=True,
)
with open("model.engine", "wb") as f:
    f.write(engine_bytes)
```

This is not graph partitioning. If any op is unsupported, conversion fails. Use `torch_tensorrt.compile(..., require_full_compilation=True)` first when the user wants an early full-coverage check.

## Windows cross-compile

`torch_tensorrt.dynamo.cross_compile_for_windows` compiles on a Linux x86-64 build machine and creates Windows-compatible engine bytes inside an exported program. Requirements:

- Linux x86-64 build host with CUDA and TensorRT installed.
- Windows x86-64 target with compatible NVIDIA GPU and same-or-newer CUDA compute capability.
- Cross-compile runtime libraries available; feature gate `windows_cross_compile` should be true.
- Lazy engine initialization and engine caching are disabled during cross-compile.

Use `hardware_compatible=True` if the target may be a different Ampere-or-newer GPU architecture.

## Serialization troubleshooting

- If saving succeeds but loading fails, verify artifact/runtime match first: Python `.ep`, TorchScript `.ts`, AOTI `.pt2`, raw `.engine`, or ExecuTorch `.pte`.
- If execution after load fails with TensorRT runtime/cache errors, reproduce with a tiny static-shape model, disable optional runtime cache/CUDA graph settings, and verify standard TensorRT versus TensorRT-RTX behavior.
- If C++ cannot load `.ts`, check that the runtime library is on the library path and that the wheel/build included C++ runtime support.
- If a raw engine cannot deserialize, check TensorRT version compatibility, GPU compute capability, hardware-compatible/version-compatible flags, and whether the target runtime matches the build runtime.

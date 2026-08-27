# API Surface Map

Use this map to route named Torch-TensorRT APIs to the nearest sub-skill and reference.

## Top-level package APIs

| API | Purpose | Read next |
| --- | --- | --- |
| `torch_tensorrt.compile(module, ir='default', inputs=None, arg_inputs=None, kwarg_inputs=None, enabled_precisions=None, **kwargs)` | Main compile entry point. Use `ir='dynamo'` for modern AOT compile; `ir='torchscript'` only for legacy/TorchScript-capable builds. | `sub-skills/compilation-and-export/SKILL.md` |
| `torch_tensorrt.save(module, file_path, output_format='exported_program', inputs=None, arg_inputs=None, kwarg_inputs=None, retrace=True, dynamic_shapes=None, **kwargs)` | Save compiled modules as ExportedProgram, TorchScript, or AOTInductor package. | `sub-skills/compilation-and-export/references/serialization-and-engines.md` and deployment sub-skill |
| `torch_tensorrt.load(file_path, extra_files=None, format=None, **kwargs)` | Load Torch-TensorRT saved artifacts when supported by the artifact type/runtime. | `sub-skills/deployment-and-distributed/references/artifact-deployment-matrix.md` |
| `torch_tensorrt.Input(...)` | Static or dynamic input shape/dtype/layout spec for compilation. | `sub-skills/compilation-and-export/references/dynamic-shapes-and-inputs.md` |
| `torch_tensorrt.Device(...)` | GPU or DLA target device spec. | Compilation and deployment sub-skills |
| `torch_tensorrt.MutableTorchTensorRTModule(...)` | Runtime-recompilable/mutable module wrapper for changing weights or inputs. | `sub-skills/runtime-optimization/SKILL.md` |

## Dynamo/export APIs

| API | Purpose | Read next |
| --- | --- | --- |
| `torch.compile(model, backend='torch_tensorrt' or 'tensorrt', options={...})` | JIT-style compile on first execution. Good for quick integration, less explicit artifact control. | Compilation workflows |
| `torch_tensorrt.dynamo.trace(mod, inputs=..., arg_inputs=..., kwarg_inputs=...)` | Export a model with decompositions tuned for Torch-TensorRT. | Compilation workflows |
| `torch.export.export(model, args, dynamic_shapes=...)` | PyTorch export step used before explicit Dynamo compile. | Dynamic-shape reference |
| `torch_tensorrt.dynamo.compile(exported_program, inputs=..., arg_inputs=..., min_block_size=..., require_full_compilation=..., use_python_runtime=..., ...)` | Explicit AOT compile of an `ExportedProgram` to a `torch.fx.GraphModule`. | Compilation API reference |
| `torch_tensorrt.dynamo.CompilationSettings(...)` | Dataclass-like settings object underlying Dynamo compile options. | Compilation API reference |
| `torch_tensorrt.dynamo.convert_exported_program_to_serialized_trt_engine(...)` | Compile an entire exported program into raw TensorRT engine bytes. | Serialization/engines reference |
| `torch_tensorrt.dynamo.cross_compile_for_windows(...)` | Compile on Linux x86-64 for Windows x86-64 execution when cross-compile libraries are available. | Deployment/platform reference |

## Runtime APIs

| API | Purpose | Read next |
| --- | --- | --- |
| `torch_tensorrt.runtime.enable_cudagraphs(compiled_module, cuda_graph_strategy=None)` | Context manager for CUDA Graph execution. | Runtime optimization sub-skill |
| `torch_tensorrt.runtime.enable_output_allocator(module)` | Context manager enabling output allocator support. | Runtime API reference |
| `torch_tensorrt.runtime.enable_pre_allocated_outputs(module)` | Context manager for preallocated output buffers. | Runtime API reference |
| `torch_tensorrt.runtime.weight_streaming(module)` | Context manager for TensorRT weight streaming. | Runtime performance/memory reference |
| `torch_tensorrt.runtime.runtime_config(target_or_targets, **overrides)` | Scoped runtime overrides for one or more modules. | Runtime workflows |
| `torch_tensorrt.runtime.RuntimeSettings(...)` | TensorRT-RTX runtime knobs: dynamic-shape kernel specialization, CUDA graph strategy, runtime cache. | Runtime workflows and installation/features |

## Debugging/extensibility APIs

| API | Purpose | Read next |
| --- | --- | --- |
| `torch_tensorrt.dynamo.Debugger(...)` | Capture FX graphs, engine profiles, layer info, and build monitoring. | Extensibility/debugging sub-skill |
| `dryrun=True` or a dryrun path in compile settings | Produce compile coverage/partitioning analysis without committing to a full workflow. | Debugging reference |
| `torch_executed_ops`, `require_full_compilation`, `min_block_size` | Control fallback and graph partitioning. | Operator coverage reference |
| `torch_tensorrt.kernels.cuda_kernel_op(...)`, `ptx_op(...)`, `KernelSpec(...)` | QDP custom CUDA kernel registration and PTX integration. | Kernel API reference |

## CLI and repository APIs

| Surface | Purpose | Read next |
| --- | --- | --- |
| `torchtrtrun` | Distributed inference launcher around `torch_tensorrt.distributed.run`. | Deployment/distributed sub-skill |
| `setup.py` / package build flags | Build source wheels with standard, Python-only, no-TorchScript, RTX, Jetson, and Windows ARM64 variants. | Build/maintenance sub-skill |
| `justfile`, `tests/ci/suites.py`, `noxfile.py` | Local test and CI lane selection for maintainers. | Build/maintenance sub-skill |

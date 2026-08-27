# Export and Runtime API Reference

## Key Python APIs

| API | Use | Notes |
| --- | --- | --- |
| `torch.export.export(model, args, dynamic_shapes=...)` | Capture a PyTorch model into an `ExportedProgram` | Model should usually be in `eval()` mode for inference export. |
| `executorch.exir.to_edge_transform_and_lower(exported, partitioner=[...])` | Lower and optionally delegate partitions | Without partitioners, use portable/default lowering for functional validation. |
| `EdgeProgramManager.to_executorch()` | Produce an ExecuTorch program manager | The resulting object exposes `.buffer` for `.pte` serialization. |
| `ExecutorchBackendConfig` | Configure memory planning, passes, delegate segment extraction, external constants, and other backend options | Keep advanced options localized and document why each non-default is needed. |
| `EdgeCompileConfig` | Configure edge dialect validity and preserved ops | Useful when a backend or pass requires preserving specific ops. |
| `executorch.export.export` | Higher-level export session API | Supports recipes, artifacts, ETRecord generation, and multi-stage planning. |
| `Runtime.get().load_program(path)` | Python runtime load when pybindings are available | Missing `_portable_lib` is an install/build problem. |
| `portable_lib._load_for_executorch(pte, ptd)` | Python pybinding load for `.pte` plus optional `.ptd` | Use for program-data separation validation. |

## C++ Runtime Concepts

- Low-level runtime APIs avoid dynamic allocation and are best for constrained targets.
- Higher-level C++ `Module` and `Tensor` extensions simplify loading `.pte` files and creating tensors but require the corresponding extension build options/libraries.
- Static kernel registration libraries often require force-load or whole-archive linker behavior.

## CV Input Contracts

For image models, preserve batch/channel/height/width layout, dtype, scaling, channel order, normalization, and output decoding. If app preprocessing differs from the export example input, compare eager and ExecuTorch outputs with realistic task tolerances before moving to device-only testing.


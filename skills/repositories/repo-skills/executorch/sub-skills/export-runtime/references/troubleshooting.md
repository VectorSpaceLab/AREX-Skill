# Export and Runtime Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Export fails on Python control flow | Data-dependent branches or loops | Use `strict=False` for diagnostics, replace tensor-dependent ifs with `torch.cond`, or export loop bodies as methods. |
| Dynamic input fails at runtime | Missing or incorrect `dynamic_shapes` bounds | Re-export with explicit bounded `Dim` entries that cover deployment sizes. |
| `.to_executorch()` fails after backend partitioning | Unsupported op, dtype, layout, or backend compile spec | Retry without delegate to separate core export from backend support; then inspect backend-specific docs/sub-skill. |
| Accuracy mismatch after quantization | Poor calibration data or backend-specific quantizer mismatch | Evaluate quantized PyTorch module before lowering; compare SQNR or task metric; use backend quantization guidance. |
| `Runtime.get()` import error | Native runtime pybindings not built in the installed package | Reinstall/rebuild with runtime pybindings; this is not a model-export issue. |
| `program.fbs` or other schema/resource file missing during serialization | Source-path-only import or incomplete package data instead of a full wheel/editable build | Route to `setup-build` and install/build the package so packaged FlatBuffers schema resources are present. |
| `.ptd` not found or ignored | Program-data separation produced separate tensor data but runtime loader only loaded `.pte` | Use the pybinding/runtime API that accepts both program and tensor-data paths. |
| Method name missing | Multi-method export used different keys or only `forward` was exported | Inspect available method names before invoking; export wrappers for methods that PyTorch export cannot capture directly. |


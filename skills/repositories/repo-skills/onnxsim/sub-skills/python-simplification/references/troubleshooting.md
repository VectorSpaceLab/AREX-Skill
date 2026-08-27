# Troubleshooting

This sub-skill owns simplification-specific failure modes. If the problem is
install, import, wheel, C API, Rust, or WASM related, route that work to the
sibling `bindings-and-packaging` sub-skill instead.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError`, missing compiled extension, or import-time build errors | Packaging / install issue, not a simplification issue | Hand off to `bindings-and-packaging`. Do not try to diagnose it here. |
| `ValueError: The following execution provider(s) are not available ... Available providers: ...` | The requested provider is not built into the installed `onnxruntime` | Install the correct provider build, such as `onnxruntime-gpu` for CUDA, or drop back to CPU. |
| `Execution providers other than CPUExecutionProvider require onnxruntime` | `onnxruntime` is absent and the request is non-CPU | Install `onnxruntime` if you need non-CPU execution, or use the CPU provider only. |
| `--cuda` and `--providers` conflict | The CUDA shortcut was combined with an explicit provider list | Use one or the other. `--cuda` means `--providers CUDAExecutionProvider CPUExecutionProvider`. |
| `The shape of input ... has dynamic size, please set an input shape manually with --test-input-shape` | The checker needs a concrete input shape for a non-batch dynamic dimension | Provide `overwrite_input_shapes` for simplification and `test_input_shapes` for validation. |
| `shape[0] of input ... is dynamic, we assume it represents batch size and set it as 1 when testing` | Only the batch dimension is dynamic | Accept the batch-as-1 default for checks, or provide an explicit `test_input_shape` if 1 is not appropriate. |
| `Check failed. Please be careful to use the simplified model...` or `Tensor X changes after optimization` | Equivalence mismatch after folding or optimization | Inspect with `--graph-diff`, increase `check_rtol` / `check_atol`, try `input_fill="arange"` or `"ones"`, or isolate the cause with `--skip-optimization`, `--skip-fuse-bn`, or `--skip-constant-folding`. |
| Large tensor warning for `Tile`, `ConstantOfShape`, or `Expand` | Folding would bake a huge tensor into the output | Raise or lower `--no-large-tensor` / `tensor_size_threshold`, or save external data instead of inlining. |
| Output save fails or the model exceeds the inline save limit | The model needs external data | Use `--save-as-external-data` or `onnx.save(..., save_as_external_data=True, all_tensors_to_one_file=True, location=...)`. |
| `No Op registered for ...` or custom-op validation errors | The model uses a custom operator whose schema is not in onnxsim's registry | Register the schema in Python `onnx`, then simplify again. Disable automatic import only if you need to preserve the registry state. |
| `custom_lib is only supported when onnxruntime is installed` | Custom-op execution requires ONNX Runtime | Install `onnxruntime`, or omit `custom_lib` when using the reference evaluator fallback. |

## Provider validation rule

onnxsim preflights provider availability before constant folding starts. That is
intentional: `onnxruntime` may otherwise silently drop an unavailable provider
and continue on CPU, which would hide the configuration error. The expected
behavior here is:

- `onnxruntime` is optional.
- Non-CPU providers require `onnxruntime` and the correct provider build.
- An unavailable provider raises `ValueError` and lists the available
  providers.

## Custom-op recovery rule

If the model contains a custom operator in the default ONNX domain, onnxsim may
still simplify the rest of the graph, but ONNX checker errors that mention the
custom op are expected until the schema is registered. Import the schema first,
or keep the op in a vendor-specific domain if that matches the export path.

## When to stop

If the issue still looks like package layout, compiled extension loading, or
binding compatibility, stop here and route to `bindings-and-packaging`.

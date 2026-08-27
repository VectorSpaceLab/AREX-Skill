# API and CLI Summary

This reference summarizes the verified simplification surface for the current
`onnxsim` package. It focuses on the workflows owned by this sub-skill; custom
rewriter design and deep profiling are routed to the sibling
`advanced-graph-control` sub-skill.

## Verified Python API

```python
onnxsim.simplify(
    model: Union[str, onnx.ModelProto],
    check_n: int = 0,
    perform_optimization: bool = True,
    skip_fuse_bn: bool = False,
    overwrite_input_shapes=None,
    test_input_shapes=None,
    skipped_optimizers: Optional[List[str]] = None,
    skip_constant_folding=False,
    skip_shape_inference=False,
    input_data=None,
    dynamic_input_shape: bool = False,
    custom_lib: Optional[str] = None,
    include_subgraph: bool = False,
    unused_output: Optional[Sequence[str]] = None,
    tensor_size_threshold: str = "1.5GB",
    mutable_initializer: bool = False,
    *,
    initializers_as_constants: bool = True,
    inline_functions: bool = False,
    import_custom_schemas: bool = True,
    input_shapes=None,
    target_opset_version: Optional[int] = None,
    custom_rewriter: Optional[Callable[[onnx.ModelProto], Union[onnx.ModelProto, bool, NoneType]]] = None,
    function_rewrite_rules: Optional[Sequence[Tuple[onnx.FunctionProto, onnx.FunctionProto]]] = None,
    check_rtol: float = 1e-4,
    check_atol: float = 1e-5,
    input_fill: str = "random",
    providers: Optional[Sequence[backend.Provider]] = None,
    profile: Optional[str] = None,
    ort_profile: Optional[str] = None,
    merge_ort_profile: bool = False,
) -> Tuple[onnx.ModelProto, bool]
```

Returned tuple: `(simplified_model, success_bool)`.

## Verified helpers

- `onnxsim.import_onnx_schemas() -> int`
- `onnxsim.backend.validate_providers(providers)`
- `onnxsim.backend.run_model(model, inputs, output_names=None, custom_lib=None, providers=None)`
- `onnxsim.model_info.diff_graphs(model_ori, model_opt)` and
  `onnxsim.model_info.print_graph_diff(model_ori, model_opt)`

## Parameter groups

| Group | Main parameters | Notes |
| --- | --- | --- |
| Input model | `model` | Accepts a file path or an in-memory `ModelProto`. |
| Shape pinning | `overwrite_input_shapes`, `test_input_shapes`, `input_shapes` | `input_shapes` is deprecated; use the two explicit maps instead. |
| Validation | `check_n`, `check_rtol`, `check_atol`, `input_data`, `input_fill` | `check_n=0` disables the random-input equivalence loop. `input_data` overrides `input_fill`. |
| Optimization | `perform_optimization`, `skipped_optimizers`, `skip_fuse_bn`, `skip_constant_folding`, `skip_shape_inference`, `mutable_initializer`, `initializers_as_constants`, `unused_output` | `perform_optimization=False` skips the optimizer pass set. |
| Graph shape / control flow | `include_subgraph`, `inline_functions` | `inline_functions=True` only inlines local model-defined functions. |
| Schema / opset | `import_custom_schemas`, `target_opset_version` | Custom schemas from Python `onnx` are bridged into onnxsim before validation. |
| Backend | `providers`, `custom_lib` | `providers` controls constant-folding execution providers. `custom_lib` is for ORT custom ops. |
| Advanced hooks | `custom_rewriter`, `function_rewrite_rules` | Present in the signature, but detailed usage belongs to `advanced-graph-control`. |
| Profiling | `profile`, `ort_profile`, `merge_ort_profile` | Present in the signature, but detailed workflow belongs to `advanced-graph-control`. |
| Tensor size control | `tensor_size_threshold` | Guards against folding huge tensors. The CLI `--no-large-tensor` flag maps here. |

## CLI groups

### I/O and checking

- Positional: `input_model`, `output_model`, optional `check_n`.
- `--check-rtol`, `--check-atol`, `--input-fill`, `--input-data-path`.
- `--overwrite-input-shape`, `--test-input-shape`.
- Deprecated aliases: `--input-shape`, `--dynamic-input-shape`.

### Optimization and folding

- `--skip-optimization [pass ...]`.
  - With no pass names, it skips all optimizer passes.
  - With pass names, it skips only the named optimizers.
- `--skip-constant-folding`, `--skip-shape-inference`, `--skip-fuse-bn`.
- `--mutable-initializer`, `--initializers-as-non-constants`.
- `--unused-output`.
- `--include-subgraph`.
- Deprecated alias: `--skip-optimizer`.

### Schema, opset, and functions

- `--skip-schema-import`.
- `--target-opset`.
- `--inline-functions`.
- `--enable-onnxruntime-optimization`.

### Backend and profiling

- `--providers`.
- `--cuda` is a shortcut for `--providers CUDAExecutionProvider CPUExecutionProvider`.
- `--profile`, `--ort-profile`, `--merge-ort-profile`.
- `--list-default-optimizers`, `-v/--version`.

### Output and diagnostics

- `--save-as-external-data`.
- `--graph-diff`.
- `--no-large-tensor [threshold]`. A bare flag means `1KB`; omitting the
  flag leaves the default large-tensor threshold (`1.5GB`).

## Important behavior notes

- CPU folding is the default.
- `onnxruntime` is optional at runtime.
- Non-CPU providers require `onnxruntime` and the appropriate provider build.
- `--cuda` cannot be combined with `--providers`.
- `--graph-diff` prints node and value changes matched by output tensor name.
- The simplifier preserves local function inlining only when explicitly requested.

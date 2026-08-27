# Compilation API Reference

This reference summarizes public APIs inspected from the package and source docs. Check the user's installed version before assuming every option exists.

## `torch_tensorrt.compile`

Signature shape:

```python
torch_tensorrt.compile(
    module,
    ir="default",
    inputs=None,
    arg_inputs=None,
    kwarg_inputs=None,
    enabled_precisions=None,
    **kwargs,
)
```

- `module`: PyTorch `nn.Module`, `ExportedProgram`, TorchScript module, FX graph, or callable accepted by the selected IR.
- `ir`: use `"dynamo"` for current Python workflows. `"torchscript"` requires TorchScript feature gates. `"default"` lets the package infer but is less explicit.
- `inputs`: sequence of real tensors or `torch_tensorrt.Input` objects. Prefer `Input` for dynamic shapes.
- `arg_inputs` / `kwarg_inputs`: example positional/keyword inputs used by export/retrace/save workflows.
- `enabled_precisions`: set of `torch.dtype` or Torch-TensorRT dtype values, for example `{torch.float32}` or `{torch.float16}`.
- `**kwargs`: passes through Dynamo/TorchScript-specific compile settings such as `min_block_size`, `require_full_compilation`, `torch_executed_ops`, `workspace_size`, `optimization_level`, `use_python_runtime`, caches, refit, and resource settings.

## `torch_tensorrt.dynamo.compile`

Use after `torch.export.export(...)` or `torch_tensorrt.dynamo.trace(...)` returns an `ExportedProgram`.

Important settings by category:

| Category | Options |
| --- | --- |
| Inputs/devices | `inputs`, `arg_inputs`, `kwarg_inputs`, `device` |
| Precision/perf | `enabled_precisions` through top-level compile, `disable_tf32`, `truncate_double`, `use_fp32_acc`, `optimization_level`, `num_avg_timing_iters`, `max_aux_streams` |
| Partitioning/fallback | `min_block_size`, `require_full_compilation`, `torch_executed_ops`, `torch_executed_modules`, `pass_through_build_failures`, `use_fast_partitioner`, `fallback_data_dependent_ops` |
| Dynamic/resource behavior | `assume_dynamic_shape_support`, `timing_cache_path`, `cache_built_engines`, `reuse_cached_engines`, `engine_cache_dir`, `engine_cache_size`, `lazy_engine_init`, `offload_module_to_cpu`, `enable_resource_partitioning`, `cpu_memory_budget`, `dynamically_allocate_resources` |
| Compatibility | `version_compatible`, `hardware_compatible`, `engine_capability`, `enable_cross_compile_for_windows` |
| Advanced graph handling | `enable_experimental_decompositions`, `enable_autocast`, `autocast_*`, `decompose_attention`, `attn_bias_is_causal` |
| Weights/refit | `immutable_weights`, `refit_identical_engine_weights`, `strip_engine_weights`, `enable_weight_streaming` |
| Analysis | `dryrun` |

Default `min_block_size` is 5 in this source snapshot. Lower it only when small TRT subgraphs are useful; it can increase overhead or make poor partitions.

## `torch_tensorrt.dynamo.trace`

```python
torch_tensorrt.dynamo.trace(mod, inputs=None, *, arg_inputs=None, kwarg_inputs=None, **kwargs)
```

Exports a model with decompositions tuned for Torch-TensorRT. Use it when plain `torch.export.export` fails on patterns that Torch-TensorRT has special decomposition handling for, but still validate exported behavior.

## `CompilationSettings`

`torch_tensorrt.dynamo.CompilationSettings` collects the same settings into a dataclass-like object. It is useful when building repeatable compile configuration in libraries or tests. Not every high-level call requires instantiating it directly.

## `Input`

`torch_tensorrt.Input` accepts static shapes or dynamic shape ranges. Typical forms:

```python
static = torch_tensorrt.Input((1, 3, 224, 224), dtype=torch.float32)
dynamic = torch_tensorrt.Input(
    min_shape=(1, 3, 224, 224),
    opt_shape=(4, 3, 224, 224),
    max_shape=(8, 3, 224, 224),
    dtype=torch.float16,
    name="x",
)
```

Use `name` when mapping keyword inputs or matching documentation. Use `shared_dims` for named dynamic dimensions that must match across multiple inputs.

## `Device`

Typical forms:

```python
gpu = torch_tensorrt.Device("cuda:0")
dla = torch_tensorrt.Device("dla:0", allow_gpu_fallback=True)
```

DLA is for supported NVIDIA embedded platforms and supports FP16/INT8 only. Do not suggest DLA on data-center GPUs without DLA.

## `torch_tensorrt.save` and `load`

```python
torch_tensorrt.save(
    module,
    file_path,
    output_format="exported_program",  # also "torchscript" or "aot_inductor"
    inputs=None,
    arg_inputs=None,
    kwarg_inputs=None,
    retrace=True,
    dynamic_shapes=None,
    **kwargs,
)

torch_tensorrt.load(file_path, extra_files=None, *, format=None, **kwargs)
```

Use `arg_inputs` or `inputs` consistently with how the module was compiled. Use `retrace=True` for AOTInductor packaging when TRT engine subgraphs are present.

## `convert_exported_program_to_serialized_trt_engine`

Use for raw TensorRT engine bytes:

```python
engine_bytes = torch_tensorrt.dynamo.convert_exported_program_to_serialized_trt_engine(
    exported,
    arg_inputs=example_inputs,
    require_full_compilation=True,
    hardware_compatible=True,
)
```

This API compiles the whole exported program as one TensorRT engine. If any operator is unsupported, conversion fails; it does not provide PyTorch fallback subgraphs like `compile()`.

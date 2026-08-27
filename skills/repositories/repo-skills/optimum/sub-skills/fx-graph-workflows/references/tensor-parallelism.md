# Optional FX automatic tensor parallelism

This reference covers Optimum's optional automatic tensor-parallel surface under `optimum.fx.parallelization`. Treat this as backend-gated guidance, not as a CPU-required workflow. The CPU-safe transformation APIs are covered in `fx-optimization.md`.

## First gate: import and version compatibility

Try the import before planning any work:

```python
from optimum.fx.parallelization import parallelize_model, parallelize_backend, ParallelExecutionCtx
```

A verified inspection on Python 3.11 raised:

```text
ValueError: mutable default <class 'slice'> for field index is not allowed: use default_factory
```

The repository's tensor-parallel CI workflow used Python 3.10. If this error appears, do not patch local site-packages during a user task. Use a Python 3.10 environment matching the repository workflow, or refresh this generated skill after upstream code changes fix the dataclass default.

## Backend requirements

Full tensor-parallel execution is optional and requires all of the following:

- A Python version where `optimum.fx.parallelization` imports successfully.
- PyTorch with `torch.compile` support. Native tests gate on `torch.__version__ >= 2.3.0`.
- CUDA-capable PyTorch and NVIDIA GPUs for the native workflow.
- Initialized `torch.distributed` process groups, normally with NCCL on CUDA.
- One device per rank and a tensor-parallel process group passed to `ParallelExecutionCtx`.
- Model dimensions divisible by tensor-parallel world size for sharded layers.
- Local model files or explicit permission to use/cache Hub models.

CPU-only environments can inspect documentation and, if imports work, maybe inspect signatures. They do not validate the distributed backend.

## Public API map

### `ParallelExecutionCtx`

`ParallelExecutionCtx` is the dynamic execution context passed through the FX backend pipeline. It includes:

- `tp_group`: tensor-parallel `torch.distributed.ProcessGroup` for the current rank.
- `current_device`: `torch.device` for the current rank.
- `example_inputs`: tensors captured by Dynamo and consumed by the backend pipeline.
- `parallel_layer_cache`: preserves created parallel replacement layers across recompilations.
- `param_cache`: preserves newly created parameters across recompilations.
- `weight_map`: optional mapping from parameter names to checkpoint shard files.
- `last_optimized_graph_module`: latest transformed graph module after a compile.
- `compile_times`: count of backend compilations. Recompile paths rely on caches above.

Create it only after distributed initialization:

```python
tp_group = torch.distributed.new_group()
ctx = ParallelExecutionCtx(tp_group=tp_group, current_device=torch.device("cuda", local_rank))
```

### `parallelize_backend(graph_module, example_inputs, ctx, config)`

This is the `torch.compile` backend function. It:

1. Stores `example_inputs` in `ctx`.
2. Builds and runs the parallel pass pipeline.
3. Increments `ctx.compile_times`.
4. Stores the optimized graph in `ctx.last_optimized_graph_module`.
5. Returns the optimized `GraphModule`.

Use it directly only when you already have a GraphModule and distributed context.

### `parallelize_model(model, parallel_ctx, *model_args, **kwargs)`

This is the high-level API for automatic model parallelism.

Important keyword behavior:

- `model`: a local directory or model identifier string.
- `revision`: defaults to `main`.
- `cache_dir`: optional cache location for model files.
- `local_files_only`: defaults to `False`; set to `True` to avoid network access.
- `skip_load_weights`: defaults to `False`; set to `True` for configuration-only/dummy-weight dry runs.
- Extra keyword arguments matching `Config` fields override the parallel config.
- Remaining keyword arguments are forwarded to model config/model construction.

Operationally, `parallelize_model` may download or read model files, loads config through Transformers `AutoConfig`, builds the model with meta-aware initialization, moves non-meta tensors to `parallel_ctx.current_device`, initializes parameter metadata, and returns a `torch.compile(..., fullgraph=True, backend=...)` callable.

## Static `Config` knobs

The backend constructs a static config with these fields:

- `lint_and_recompile=True`: lint/recompile after each pass.
- `clean_markers_after_all_passes=True`: remove analysis markers after the pipeline.
- `weight_init_fn`: default normal initialization for new `Linear` and `Embedding` weights.
- `enable_sequence_parallel=False`: opt-in for Megatron-style sequence parallel search paths.

Pass matching keyword arguments to `parallelize_model(...)` to override these fields.

## Parallel pass pipeline

The backend pass pipeline does four high-level operations:

1. `ParallelAxisSolverPass`: decomposes/functionalizes the graph and searches for a feasible parallel axis solution.
2. `ParallelLayerAnnotatePass`: annotates `Linear`, `Embedding`, and supported cross-entropy nodes with replacement strategy information.
3. `ParallelLayerReplacePass`: swaps compatible modules/functions for parallel equivalents and adjusts hard-coded shape parameters when necessary.
4. `InitializeOrLoadWeightsPass`: slices, loads, initializes, and caches parameters for the current rank.

The solver is heuristic. It is intended to reduce boilerplate for transformer-like models, not to prove an optimal memory/communication plan for arbitrary graphs.

## Tensor-parallel replacements

Optimum replaces only recognized, compatible graph patterns.

- `ColumnParallelLinear`: shards a `Linear` layer along output features. `out_features` must be divisible by tensor-parallel world size. It can gather output when needed.
- `RowParallelLinear`: shards a `Linear` layer along input features. `in_features` must be divisible by world size. It can scatter input and all-reduce output.
- `VocabParallelEmbedding`: shards an `Embedding` along vocabulary dimension. `num_embeddings` must be divisible by world size.
- `VocabParallelCrossEntropyLoss` and functional wrapper: sharded cross entropy for vocab-parallel logits. Weighted mode, custom ignore index, and label smoothing are not supported by the current wrapper.

If a dimension is not divisible by world size, expect a runtime error telling you to check the parallel dimension and tensor-parallel group size.

## Safe triage flow

1. Confirm the task is really tensor parallelism, not ordinary graph optimization.
2. Import `optimum.fx.parallelization`. If Python 3.11 dataclass error appears, stop and use the Python 3.10/upstream-fix path.
3. Check `torch.cuda.is_available()` and `torch.__version__ >= 2.3.0` before scheduling native execution.
4. Decide whether model files are local. If not, ask whether downloads/cache use are allowed.
5. Initialize `torch.distributed` per rank and create a process group before constructing `ParallelExecutionCtx`.
6. Start with `skip_load_weights=True` only for dummy/dry runs; full correctness needs the intended weight-loading path.
7. After a compiled call, inspect `ctx.last_optimized_graph_module` for replacement layers and `ctx.compile_times` for recompile behavior.
8. For correctness, compare losses or logits across ranks and against a non-parallel or world-size-one baseline when feasible.

## Native verification boundaries

Native tensor-parallel tests exercise model identifiers, process spawning, CUDA devices, `torch.compile`, distributed process groups, and multiple world sizes. They are reference-only for this base skill unless the user explicitly provides hardware, compatible Python/PyTorch, model cache/download permission, and time budget.

The CPU FX smoke script in this sub-skill intentionally does not import or execute tensor parallelism.

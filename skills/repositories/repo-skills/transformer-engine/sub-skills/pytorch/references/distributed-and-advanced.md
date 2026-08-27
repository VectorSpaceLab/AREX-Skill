# Distributed and Advanced PyTorch Surfaces

## 1) FSDP, checkpointing, and sharded initialization

### TE checkpointing

Use `te.checkpoint(...)` when the wrapped callable contains TE modules.

- It falls back to native PyTorch checkpointing when no TE modules are present.
- `distribute_saved_activations=True` is for tensor-parallel settings and requires distributed initialization.
- `get_rng_state_tracker` should be a `CudaRNGStatesTracker` when model-parallel RNG streams must be reproducible.
- Keep `use_reentrant` explicit when you need to match a known recompute mode.

### FSDP-style initialization

For large sharded models, the safest pattern is:

1. Create the model on `meta` when possible.
2. Apply sharding.
3. Materialize parameters with TE reset / initialization.
4. Seed optimizer master weights from preserved high-precision init values when needed.

This pattern pairs naturally with `quantized_model_init(enabled=True, preserve_high_precision_init_val=True)`.

### Selection note

- `fuse_wgrad_accumulation=True` is not compatible with vanilla PyTorch FSDP2 in the same way it is with TE-integrated sharded training stacks, because the fused wgrad path bypasses ordinary autograd gradient flow.
- If a sharded path needs `main_grad` buffers or special optimizer handling, keep that requirement explicit before enabling fused wgrad accumulation.

## 2) Userbuffers and communication / GEMM overlap

Use the userbuffer helpers when the model needs overlap between communication and GEMM work.

- Call `initialize_ub(...)` before constructing overlap-enabled modules.
- Call `destroy_ub()` during teardown.
- `UserBufferQuantizationMode.FP8` enables low-precision overlap buffers.
- `UserBufferQuantizationMode.NONE` keeps the buffers in high precision.

### Prerequisites

- Single-node tensor-parallel topology is the safest starting point.
- Fast interconnects such as NVLink or NVSwitch are required for good overlap behavior.
- `CUDA_DEVICE_MAX_CONNECTIONS=1` should be set for the overlap path.
- On older-than-SM90 systems, a fallback may require `UB_SKIPMC=1`.

### Selection note

Only enable `ub_*` or overlap flags after the process groups and userbuffer runtime are initialized.

## 3) CPU offload

Use `get_cpu_offload_context(...)` for sequential models whose activations can be moved to CPU during the forward pass and restored during backward.

### Default scheduling

- `num_layers` is the number of layers to offload.
- `model_layers` is the total number of layers in the model.
- The returned context manager wraps each layer forward.
- The returned sync function registers the reload hook.

### Manual synchronization

- Set `manual_synchronization=True` when the training pattern is not strictly "all forward, then all backward."
- The returned `ManualOffloadSynchronizer` lets you call `start_offload_layer`, `release_activation_forward_gpu_memory`, and `start_reload_layer` explicitly.

### Practical notes

- CPU offload works with all PyTorch modules, not just TE layers.
- It is best suited to sequential stacks.
- Use `mark_not_offload(tensor)` to exclude tensors that should stay on GPU.
- When capturing CUDA graphs, capture the entire forward/backward sequence if offload/reload is involved.

## 4) Operation fuser

TE's op-fuser surface lets you build custom fused blocks bottom-up.

### Core pieces

- `ops.Sequential` is the container that attempts fusion.
- `FusibleOperation` is the abstract TE op base.
- `BasicOperation` is the low-level op with `op_forward` / `op_backward`.
- `FusedOperation` replaces one or more basic ops.
- `register_forward_fusion`, `register_backward_fusion`, and `register_forward_backward_fusion` register fusion passes.

### When to use it

- When the built-in monolithic module is too restrictive.
- When you want a custom fusion around `Linear`, normalization, activation, or communication ops.
- When you need fine-grained routing through `MakeExtraOutput` / `AddExtraInput` channels.

### Important rules

- Bind channels before the first forward call.
- Channels do not cross a regular PyTorch module boundary.
- A channel-connected op may still be replaced by a registered fused implementation.
- `ops.Quantize` can encourage quantized fusions when a model is split across multiple `Sequential` containers.

## 5) Debug tools

Use Nvidia-DL-Framework-Inspect with TE's bundled debug features when you need to inspect precision, tensor statistics, or GEMM behavior.

### Setup pattern

- Call `nvdlfw_inspect.api.initialize(...)` once on every rank.
- Pass a configuration YAML file with the layer-feature mapping.
- Point `feature_dirs` at the bundled TE debug features directory shipped with the package.
- Provide `log_dir` for debug logs and statistics logs.
- Set `default_logging_enabled=True` when you want default file logging.

### Layer naming and iteration hooks

- Pass `name="..."` when constructing TE layers so the debug output is easier to match.
- Call `debug_api.step()` at the end of each forward/backward iteration.
- In multi-GPU runs, use `debug_api.set_tensor_reduction_group(...)` when you want stats reduced across something narrower than the world group.

### Selection notes

- TE debug features are the right way to inspect or temporarily disable low-precision behavior on a per-layer basis.
- Use the debug tools when you need to answer "what precision did this GEMM actually run in?" rather than changing the model itself.

## 6) Attention, export, and graph capture

### Attention placement

- `DotProductAttention` is the lower-level attention surface.
- `MultiheadAttention` bundles the common MHA path.
- `TransformerLayer` is the full transformer block with tensor-parallel and context-parallel hooks.

### ONNX/export notes

- Use `onnx_export(enabled=True)` around export if TE translation rules are needed.
- Warm the module once before export.
- Keep the export path on PyTorch 2.4 or newer.
- Pair with `te_translation_table` when the exporter needs TE-specific op lowering.

### Graph capture notes

- `make_graphed_callables` is the TE helper for repeated CUDA-graph execution after warmup.
- It is most useful when the call pattern is stable and the captured region is small.

## 7) Topology caveats

- Communication/GEMM overlap is most reliable on single-node NVLink/NVSwitch systems.
- Tensor-parallel modules that use overlap flags need the process groups ready before construction.
- `GroupedLinear` and grouped GEMM paths often have tighter cuBLAS version requirements than plain BF16/FP16 linear layers.
- When a larger distributed example becomes unstable, fall back to the bundled BF16 `Linear` smoke first, then reintroduce sharding or overlap.

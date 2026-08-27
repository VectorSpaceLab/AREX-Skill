# PyTorch API Reference

This reference summarizes the runtime PyTorch surface for Transformer Engine. It favors practical selection notes over exhaustive constructor details.

## 1) Core module replacements

| API | Use when | Practical notes |
| --- | --- | --- |
| `transformer_engine.pytorch.Linear` | Replacing a single `torch.nn.Linear` with TE compute and quantization support. | Set `params_dtype` to `torch.float32`, `torch.bfloat16`, or `torch.float16` to match your precision plan. If you do **not** use `torch.autocast`, the input tensor dtype must match the parameter dtype. |
| `transformer_engine.pytorch.GroupedLinear` | Running multiple GEMMs together, especially expert or batched linear paths. | Use `num_gemms` plus grouped-weight flags when you want one module to represent many linear projections. Bias is not supported together with tensor parallelism. |
| `transformer_engine.pytorch.LayerNorm` / `RMSNorm` | Standalone normalization with TE kernels. | Use these when only normalization needs TE behavior; combine with `Linear` or `ops.Sequential` for custom blocks. |
| `transformer_engine.pytorch.LayerNormLinear` | The common `LayerNorm -> Linear` fusion. | Best choice when you want a ready-made transformer sub-block with fused normalization + GEMM behavior. |
| `transformer_engine.pytorch.LayerNormMLP` | The common transformer MLP block. | Use for `LayerNorm -> FC1 -> activation -> FC2` patterns. |
| `transformer_engine.pytorch.DotProductAttention` | Low-level attention construction. | Use when you need explicit control over attention layout, context parallel groups, or custom attention plumbing. |
| `transformer_engine.pytorch.MultiheadAttention` | Standard MHA blocks. | Higher level than `DotProductAttention`; pairs attention with projections and tensor-parallel settings. |
| `transformer_engine.pytorch.TransformerLayer` | Full encoder/decoder-style transformer blocks. | Use this when you want a ready-made end-to-end block. Key knobs include `params_dtype`, `layer_type`, `self_attn_mask_type`, `parallel_attention_mlp`, `fuse_qkv_params`, `fuse_wgrad_accumulation`, `device`, and `name`. |
| `transformer_engine.pytorch.dot_product_attention.inference.InferenceParams` | Attention inference cache management. | Useful for autoregressive decoding or paged/non-paged inference state. |
| `transformer_engine.pytorch.CudaRNGStatesTracker` | Model-parallel RNG state management. | Use with checkpointing or tensor-parallel modules when multiple CUDA RNG streams must remain reproducible. |

### Selection notes

- Use the smallest module that matches the structure you need. `Linear` and `LayerNormLinear` are easier to validate than a full `TransformerLayer`.
- Prefer `TransformerLayer` only when you need the standard block topology and its fused internal paths.
- `GroupedLinear` is the right choice for expert-style or batched GEMMs; it is not a drop-in for ordinary dense layers.

## 2) Precision and quantization control

### `transformer_engine.pytorch.autocast`

```python
with te.autocast(enabled=True, calibrating=False, recipe=None, amax_reduction_group=None):
    output = module(inp)
```

Use `te.autocast` for FP8/MXFP8/NVFP4-style quantized compute.

- Forward must run inside the context.
- Backward should run outside the context.
- `recipe` selects the low-precision scheme.
- `calibrating=True` collects statistics without actually enabling quantized compute.
- `amax_reduction_group` is the distributed group used to reduce amax values.
- Some FP8 linear paths expect both dimensions to be divisible by 16.
- If `recipe.reduce_amax=True`, avoid calling the same module more than once inside one `autocast` region.

Do **not** confuse this with `torch.autocast`:

- `torch.autocast` controls BF16/FP16 compute dtype.
- `te.autocast` controls TE quantized low-precision recipes.

### `transformer_engine.pytorch.quantized_model_init`

```python
with te.quantized_model_init(enabled=True, recipe=None, preserve_high_precision_init_val=False):
    model = te.Linear(768, 768)
```

Use this when you want TE parameters to be stored in quantized form at initialization time.

- `enabled=True` stores only quantized parameter copies.
- `recipe` selects the quantization recipe used for parameter creation.
- `preserve_high_precision_init_val=True` keeps the original high-precision initializer value on CPU so optimizer master weights can be seeded later.

Typical uses:

- FP8 training with optimizer master weights.
- Inference where only the quantized weights are needed.
- Meta-device / FSDP-style initialization where the high-precision seed is needed later.

### Deprecated aliases

- `transformer_engine.pytorch.fp8_autocast` is a legacy alias for `autocast`.
- `transformer_engine.pytorch.fp8_model_init` is a legacy alias for `quantized_model_init`.

## 3) Checkpointing, graphs, and RNG

### `transformer_engine.pytorch.checkpoint`

```python
y = te.checkpoint(function, *args, use_reentrant=True, distribute_saved_activations=False, tp_group=None)
```

Use TE checkpointing when the wrapped function contains TE modules.

- It falls back to `torch.utils.checkpoint.checkpoint` when no TE modules are involved.
- `distribute_saved_activations=True` requires distributed initialization and is meant for tensor-parallel settings.
- `get_rng_state_tracker` should be a `CudaRNGStatesTracker` when model-parallel RNG bookkeeping is needed.
- `use_reentrant=False` runs the full recompute path through PyTorch's non-reentrant checkpoint logic.

### `transformer_engine.pytorch.make_graphed_callables`

Use this for CUDA graph capture of repeated TE callables after warmup.

- Warm up the callable first.
- Prefer the smallest stable subgraph that gives you a performance win.

### `transformer_engine.pytorch.CudaRNGStatesTracker`

Use this when tensor-parallel or checkpointed recomputation needs multiple named CUDA RNG states.

- `reset()` clears all tracked state.
- `add(name, seed)` registers a seed.
- `fork(name)` temporarily switches to a tracked RNG stream.
- `get_states()` / `set_states()` let you snapshot and restore all tracked states.

## 4) CPU offload helpers

### `transformer_engine.pytorch.get_cpu_offload_context`

Use this for activation offload in sequential models.

- Default scheduling returns a context manager plus a sync function.
- Manual synchronization returns a `ManualOffloadSynchronizer` for explicit offload/reload control.
- `model_layers` is the total layer count; `num_layers` is the number of layers to offload.
- The pattern works with any PyTorch modules, not only TE layers.

### `transformer_engine.pytorch.mark_not_offload`

Use this to exclude tensors that should remain on GPU.

### `transformer_engine.pytorch.ManualOffloadSynchronizer`

Use the synchronizer methods when the model does not follow a simple sequential forward/backward order.

## 5) Loss and GLU helpers

### `transformer_engine.pytorch.parallel_cross_entropy`

Use this for tensor-parallel language-model losses when logits are distributed.

### `transformer_engine.pytorch.interleave_glu_tensor` / `deinterleave_glu_tensor`

Use these to convert between contiguous gate/linear layouts and TE's block-interleaved GLU layout.

- `interleave_glu_tensor(tensor, interleave_size)` converts a contiguous gate/linear tensor into block-interleaved form.
- `deinterleave_glu_tensor(tensor, interleave_size)` restores the contiguous layout.
- These helpers are most useful for `SwiGLU`, `GEGLU`, and related fused GLU paths.

## 5) Data types and support gates

### `transformer_engine.pytorch.DType`

Use this enum when interacting with low-level quantized tensors or quantizers.

Common members:

- `kByte`
- `kInt32`
- `kFloat32`
- `kFloat16`
- `kBFloat16`
- `kFloat8E4M3`
- `kFloat8E5M2`
- `kFloat4E2M1`

### Availability checks

All availability checks support `return_reason=True` and should be called **before** constructing a recipe or module that depends on that precision.

- `is_fp8_available(...)` — delayed-scaling / current-scaling FP8 availability.
- `is_mxfp8_available(...)` — MXFP8 availability.
- `is_fp8_block_scaling_available(...)` — FP8 block-scaling availability.
- `is_nvfp4_available(...)` — NVFP4 availability.
- `is_bf16_available(...)` — BF16 availability on the current device.
- `get_device_compute_capability()` — current GPU compute capability tuple.
- `get_cudnn_version()` — runtime cuDNN version tuple.
- `get_default_recipe()` — runtime default recipe for the current device.

### Selection note

- Use the specific availability check for the precision you actually want.
- A false result is a hard gating signal, not a warning.
- Do not assume FP8 is available just because BF16 is available.

## 6) Mixture-of-Experts helpers

- `moe_permute`
- `moe_permute_with_probs`
- `moe_unpermute`
- `moe_sort_chunks_by_index`
- `moe_sort_chunks_by_index_with_probs`

Use these when you need to reorder tokens for expert routing and then restore the original order.

### Selection note

Pair these helpers with `GroupedLinear` or custom dispatch/combine logic when building MoE blocks.

## 7) Userbuffer / comm-overlap helpers

- `initialize_ub(...)` — initialize the userbuffer communication overlap runtime before constructing overlap-enabled modules.
- `destroy_ub()` — tear down the userbuffer runtime.
- `UserBufferQuantizationMode.FP8`
- `UserBufferQuantizationMode.NONE`

Use these when a model needs TE's userbuffer-based communication/computation overlap.

### Selection note

Only enable the overlap flags after the relevant process groups and userbuffer runtime are ready.

## 8) Quantized tensors and quantizers

### Storage and tensor classes

- `QuantizedTensorStorage`
- `QuantizedTensor`
- `Float8TensorStorage`
- `MXFP8TensorStorage`
- `Float8BlockwiseQTensorStorage`
- `NVFP4TensorStorage`
- `Float8Tensor`
- `MXFP8Tensor`
- `Float8BlockwiseQTensor`
- `NVFP4Tensor`

### Quantizer classes

- `Quantizer`
- `Float8Quantizer`
- `Float8CurrentScalingQuantizer`
- `MXFP8Quantizer`
- `Float8BlockQuantizer`
- `NVFP4Quantizer`

### Utility functions

- `prepare_for_saving`
- `restore_from_saved`

### Selection notes

- `QuantizedTensor.dequantize()` returns a high-precision tensor.
- `QuantizedTensor.quantize_()` updates the tensor in place.
- Use the storage classes when you need to inspect or serialize the underlying quantized representation.
- Use the quantizer classes when you need to build or update quantized tensors from high-precision data.

## 9) Operation fuser surface

### Core infrastructure

- `ops.Sequential`
- `ops.FusibleOperation`
- `ops.BasicOperation`
- `ops.FusedOperation`
- `ops.register_forward_fusion`
- `ops.register_backward_fusion`
- `ops.register_forward_backward_fusion`

### Common basic operations

- `ops.Linear`
- `ops.GroupedLinear`
- `ops.LayerNorm`
- `ops.RMSNorm`
- `ops.Bias`
- `ops.Dropout`
- `ops.Identity`
- `ops.Reshape`
- `ops.MakeExtraOutput`
- `ops.AddExtraInput`
- `ops.Quantize`
- `ops.GELU`
- `ops.SiLU`
- `ops.SwiGLU`
- `ops.GLU`
- `ops.GEGLU`
- `ops.ReLU`
- `ops.ReGLU`
- `ops.SReLU`
- `ops.SReGLU`
- `ops.QGELU`
- `ops.QGEGLU`
- `ops.ScaledSwiGLU`
- `ops.ScaledClampedQGeGLU`
- `ops.AllGather`
- `ops.AllReduce`
- `ops.ReduceScatter`
- `ops.ConstantScale`
- `ops.L2Normalization`
- `ops.BasicLinear`

### Low-level Triton helpers

- `triton.mhc.mhc_fused_sinkhorn`
- `triton.mhc.mhc_fused_scale`
- `triton.mhc.mhc_fused_aggregate`
- `triton.mhc.mhc_fused_expand_combine`
- `triton.mhc.mhc_fused_projection`

### Selection notes

- Use `ops.Sequential` when you want to compose TE operations bottom-up and let the fuser decide what can be fused.
- Bind extra input/output channels before the first forward call if you need routed tensors inside one fuser.
- Channels do not cross a regular PyTorch module boundary or a different `ops.Sequential` instance.
- `ops.Quantize` is an expert technique for encouraging quantized fusions when a larger model is split across multiple containers.
- Treat the Triton MHC helpers as backend-facing building blocks; most agents should prefer the higher-level attention and MHA modules instead.

## 10) Export

### `transformer_engine.pytorch.export.onnx_export`

Use this as a context manager around ONNX export when TE translation rules are needed.

- Requires PyTorch 2.4 or newer.
- Warm the module up before export.
- Combine with `te_translation_table` when calling `torch.onnx.export(..., dynamo=True, custom_translation_table=...)`.

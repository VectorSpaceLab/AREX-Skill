# Transformer Engine JAX/Flax API Reference

This reference is a self-contained map of the public JAX/Flax names exported by Transformer Engine and the JAX API page. Use it to choose imports and to keep framework distinctions clear.

## Canonical imports

```python
import jax
import jax.numpy as jnp
import transformer_engine.jax as te
import transformer_engine.jax.flax as te_flax
from transformer_engine.common import recipe
```

Import `jax` before `transformer_engine.jax` in standalone programs and smoke tests. This avoids CUDA/custom-call initialization-order failures observed in TE's JAX test coverage.

## Top-level `transformer_engine.jax` exports

| API | Purpose | Notes |
| --- | --- | --- |
| `te.autocast(enabled=False, recipe=None, mesh_resource=None)` | Context manager for TE low-precision quantization and global sharding resources. | When `recipe is None`, TE creates a default `DelayedScaling()` recipe. When `enabled=True`, TE checks hardware/software support and asserts with a reason if the active recipe is unsupported. In JAX, model initialization must occur inside the enabled context to create quantization metadata. |
| `te.fp8_autocast(enabled=False, fp8_recipe=None, mesh_resource=None)` | Deprecated alias-like context manager. | Use `te.autocast(enabled=..., recipe=..., mesh_resource=...)` for new code. Expect a `DeprecationWarning`. |
| `te.update_collections(new, original)` | Merge updated non-param Flax collections back into an original variables dict/FrozenDict. | `new` replaces matching keys in `original` and preserves non-updated collections. Use when gradients or module application return TE quantization metadata that must persist across steps. |
| `te.NVTE_FP8_COLLECTION_NAME` | String constant naming the TE FP8 metadata collection. | Current value is `"fp8_metas"`. Delayed-scaling wrappers may also use `_overwrite_with_gradient` for metadata updated through gradients. Treat these as non-parameter Flax variables. |
| `te.MeshResource(dp_resource=None, tp_resource=None, tpsp_resource=None, fsdp_resource=None, pp_resource=None, cp_resource=None, ep_resource=None)` | Dataclass mapping TE logical resources to physical mesh axis names. | Pass to `te.autocast(..., mesh_resource=...)` or `transformer_engine.jax.sharding.global_shard_guard`. `dp` is data parallel, `tp` tensor parallel, `tpsp` tensor-sequence parallel, `fsdp` fully sharded data parallel, `cp` context parallel, `ep` expert parallel, `pp` pipeline parallel. |
| `te.flax` | Flax module namespace. | Same object as `transformer_engine.jax.flax`. |
| `te.quantize` | Quantization helper namespace. | Contains recipe support probes such as `get_supported_quantization_recipes`, `is_scaling_mode_supported`, and `ScalingMode`; these are useful guards even though they are not in the minimal top-level `__all__`. |

## Quantization support helpers

Use these helpers when the code path may enter FP8/MXFP8/NVFP4. They are runtime guards, not proof from the model shape alone.

```python
from transformer_engine.jax.quantize import (
    ScalingMode,
    get_supported_quantization_recipes,
    is_scaling_mode_supported,
)

supported_recipes = [type(r).__name__ for r in get_supported_quantization_recipes()]
ok, reason = is_scaling_mode_supported(ScalingMode.DELAYED_TENSOR_SCALING)
```

Support gates distilled from the runtime helpers:

- `DelayedScaling` and `Float8CurrentScaling` use tensor FP8 scaling and require device compute capability 8.9 or newer, plus compatible CUDA/cuBLASLt.
- `MXFP8BlockScaling` requires Blackwell-class support in TE's guard: compute capability 9.9 or newer, CUDA/cuBLASLt 12.8 or newer, and JAX 0.5.3 or newer.
- `NVFP4BlockScaling` requires compute capability 10.0 or newer, CUDA/cuBLASLt 12.8 or newer, and JAX 0.5.3 or newer.
- A100-class systems can pass BF16 TE DenseGeneral execution while returning an empty supported recipe list; do not claim FP8 support on such hardware.

## Flax module exports

`transformer_engine.jax.flax.__all__` exposes the following public module names. Construct these as Flax Linen modules and pass a Flax variables dict/FrozenDict to `.apply`.

### `te_flax.LayerNorm`

```python
te_flax.LayerNorm(
    epsilon=1e-6,
    layernorm_type="layernorm",  # "layernorm" or "rmsnorm"
    zero_centered_gamma=False,
    scale_init=None,
    scale_axes=("embed",),
    bias_init=...,               # default zeros
    bias_axes=("embed",),
    dtype=jnp.float32,
)
```

Applies layer norm or RMSNorm over the final dimension and returns an output with the input dtype. `dtype` controls parameter allocation; the input tensor dtype controls computation/output dtype in common BF16/FP16 flows.

### `te_flax.DenseGeneral`

```python
te_flax.DenseGeneral(
    features,
    kernel_init=None,
    kernel_axes=(),
    use_bias=True,
    bias_init=...,               # default zeros
    bias_axes=(),
    enable_low_rank_adaptation=False,
    low_rank_adaptation_dim=32,
    low_rank_adaptation_alpha=None,
    axis=-1,
    dtype=jnp.float32,
    input_axes=(),
    transpose_batch_sequence=False,
    quantization_checkpoint_name=None,
)
```

Dense transform `y = x A^T + b`. Use it as a TE-managed replacement for `flax.linen.Dense` or `DenseGeneral` when the layer should own parameters and optional TE quantizers. `features` may be an int or tuple. `kernel_axes`, `bias_axes`, and `input_axes` provide logical-axis annotations for sharding.

### `te_flax.LayerNormDenseGeneral`

```python
te_flax.LayerNormDenseGeneral(
    features,
    enable_layernorm=True,
    layernorm_type="layernorm",
    epsilon=1e-6,
    zero_centered_gamma=False,
    scale_axes=("embed",),
    ln_bias_axes=("embed",),
    kernel_axes=(),
    use_bias=False,
    bias_axes=(),
    return_layernorm_output=False,
    axis=-1,
    dtype=jnp.float32,
    layernorm_input_axes=None,
    dot_input_axes=None,
    depth_scaling=None,
    transpose_batch_sequence=False,
    quantization_checkpoint_name=None,
)
```

Fuses or composes layer norm followed by DenseGeneral. Returns `(dense_output, layernorm_output_or_None)`. When `return_layernorm_output=False` and quantization is active, TE can use a fused layernorm+dense path.

### `te_flax.LayerNormMLP`

```python
te_flax.LayerNormMLP(
    intermediate_dim=2048,
    enable_layernorm=True,
    layernorm_type="layernorm",
    epsilon=1e-6,
    kernel_axes_1=("embed", "act", "mlp"),
    kernel_axes_2=("mlp", "embed"),
    use_bias=False,
    return_layernorm_output=False,
    activations=("gelu",),
    activation_params=None,
    intermediate_dropout_rate=0.0,
    intermediate_dropout_rng_name="dropout",
    dtype=jnp.float32,
    ffn1_ckpt_name="ffn1",
    ffn2_ckpt_name="ffn2",
    quantization_checkpoint_name=None,
)
```

Layer norm plus two dense projections separated by activation(s). Returns `(mlp_output, layernorm_output_or_None)`. Gated activations such as `("gelu", "linear")`, `("silu", "linear")`, and related pairs are supported by the module logic.

### `te_flax.DotProductAttention`

```python
te_flax.DotProductAttention(
    head_dim,
    num_attention_heads,
    num_gqa_groups=None,
    attention_dropout=0.0,
    attn_mask_type="causal",
    attn_bias_type=None,
    dropout_rng_name="dropout",
    float32_logits=False,
    qkv_layout="bshd_bshd_bshd",
    scale_factor=None,
    transpose_batch_sequence=False,
    window_size=None,
    max_segments_per_seq=1,
    context_parallel_causal_load_balanced=False,
    context_parallel_axis="",
    context_parallel_strategy="DEFAULT",
    context_checkpoint_name="context",
    softmax_type="vanilla",
    score_mod=None,
    score_mod_bprop=None,
)
```

Call form:

```python
out = dpa.apply(
    variables,
    query,
    key,
    value,
    sequence_descriptor=None,
    bias=None,
    deterministic=True,
    score_mod_tensors=None,
    score_mod_bprop_tensors=None,
)
```

Layouts include separate BSHD (`"bshd_bshd_bshd"`), packed QKV (`"bs3hd"`), packed KV (`"bshd_bs2hd"`), and THD packed-sequence variants (`"t3hd"`, `"thd_t2hd"`, `"thd_thd_thd"`). Mask types include `"no_mask"`, `"padding"`, `"causal"`, and causal+padding combinations. `score_mod` is experimental and requires fused attention; it does not silently fall back when fused attention is disabled or no fused kernel is available.

### `te_flax.MultiHeadAttention`

```python
te_flax.MultiHeadAttention(
    head_dim,
    num_attention_heads,
    num_gqa_groups=None,
    attention_dropout=0.0,
    input_layernorm=True,
    layernorm_type="layernorm",
    layernorm_epsilon=1e-6,
    return_layernorm_output=False,
    use_bias=False,
    attn_mask_type="causal",
    attn_bias_type=None,
    enable_rotary_pos_emb=False,
    low_rank_adaptation_scope="none",
    dtype=jnp.float32,
    fuse_qkv_params=True,
    transpose_batch_sequence=False,
    enable_sequence_parallel=False,
    scale_attn_logits=False,
    float32_logits=False,
    window_size=None,
    softmax_type="vanilla",
    score_mod=None,
    score_mod_bprop=None,
)
```

Call form:

```python
out = mha.apply(
    variables,
    inputs_q,
    inputs_kv,
    mask=None,
    bias=None,
    decode=False,
    deterministic=True,
    score_mod_tensors=None,
    score_mod_bprop_tensors=None,
)
```

This module owns Q/K/V and output projections around `DotProductAttention`. It supports self-attention and cross-attention, GQA/MQA through `num_gqa_groups`, optional input layer norm, rotary position embedding, sequence parallelism, LoRA scopes, and fused QKV parameters.

### `te_flax.RelativePositionBiases`

```python
te_flax.RelativePositionBiases(
    num_buckets,
    max_distance,
    num_attention_heads,
    embedding_init=...,          # Flax default embedding initializer
    embedding_axes=("heads", "relpos_buckets"),
    dtype=jnp.float32,
)
```

Call as `bias = module.apply(variables, q_seqlen, k_seqlen, bidirectional=True)`. Output shape is `(1, num_attention_heads, q_seqlen, k_seqlen)`.

### `te_flax.TransformerLayer` and `TransformerLayerType`

```python
te_flax.TransformerLayer(
    hidden_size=512,
    mlp_hidden_size=2048,
    num_attention_heads=8,
    num_gqa_groups=None,
    layernorm_type="layernorm",
    layernorm_epsilon=1e-6,
    hidden_dropout=0.1,
    attention_dropout=0.1,
    intermediate_dropout=0.0,
    mlp_activations=("gelu",),
    use_bias=False,
    apply_residual_connection_post_layernorm=False,
    output_layernorm=False,
    float32_attention_logits=False,
    layer_type=te_flax.TransformerLayerType.ENCODER,
    self_attn_mask_type="causal",
    self_attn_bias_type=None,
    enable_relative_embedding=True,
    enable_rotary_pos_emb=False,
    dtype=jnp.float32,
    drop_path=0.0,
    fuse_qkv_params=True,
    transpose_batch_sequence=False,
    enable_sequence_parallel=False,
    scale_attn_logits=False,
    window_size=None,
    softmax_type="vanilla",
    score_mod=None,
    score_mod_bprop=None,
)
```

Call form:

```python
out = layer.apply(
    variables,
    inputs,
    encoded=None,
    attention_mask=None,
    encoder_decoder_mask=None,
    deterministic=True,
    decode=False,
    max_decode_length=None,
    score_mod_tensors=None,
    score_mod_bprop_tensors=None,
)
```

`TransformerLayerType.ENCODER` builds the encoder-style self-attention + MLP block. `TransformerLayerType.DECODER` adds cross-attention using `encoded` and `encoder_decoder_mask`.

## Replacement helpers

### `te_flax.extend_logical_axis_rules(rules)`

Extends existing Flax logical-axis rules with TE logical axes according to the active `MeshResource`. Call while a TE sharding resource is active, typically inside `te.autocast(..., mesh_resource=...)` or a `global_shard_guard` context. It is mainly needed by `TransformerLayer`; lower-level modules can use explicit `kernel_axes`, `bias_axes`, and input axes.

### `te_flax.wrap_function_in_te_state_module(f, quantization_recipe, name=None, quantization_checkpoint_name=None)`

Wraps a function in a Flax module that can create and carry TE quantizer state. The wrapped function receives `generate_quantizer_set` as its first argument.

### `te_flax.make_dot_general_cls(quantization_recipe)`

Returns a Flax module class suitable for `flax.linen.Dense(..., dot_general=te_dot_general_cls())`. Use this when an existing Flax layer should keep owning the kernel parameter and sharding annotations while TE replaces only the GEMM implementation. Batch dimensions in `dot_general` must be empty.

### `te_flax.make_grouped_dense_cls(quantization_recipe, quantization_checkpoint_name=None)`

Creates a TE grouped-dense/ragged-dot module instance. Quantized grouped GEMM is restricted to `MXFP8BlockScaling`; use `None` for BF16/no quantization. Group sizes are passed at call time and determine quantizer grouping.

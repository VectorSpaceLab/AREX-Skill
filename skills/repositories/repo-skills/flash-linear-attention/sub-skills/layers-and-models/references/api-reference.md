# Layer, Module, and Model API Reference

Use this for verified import surfaces and representative constructor signatures. Inspect the active installed package for exact details before editing code because FLA evolves quickly.

## Import surfaces

```python
import fla
import fla.layers as layers
import fla.modules as modules
import fla.models as models
```

Important export behavior:

- `fla.layers.__all__` contains public token-mixing layer classes such as `GatedLinearAttention`, `KimiDeltaAttention`, `MultiScaleRetention`, `LinearAttention`, `RWKV7Attention`, and `WallAttention`.
- `fla.modules.__all__` contains fused building blocks such as `RMSNorm`, `LayerNorm`, `FusedRMSNormGated`, `FusedLinearCrossEntropyLoss`, `RotaryEmbedding`, and `ShortConvolution`.
- `fla.models.__all__` contains Config, Model, and ForCausalLM classes for many architectures.
- Top-level `fla.__all__` exports layer classes and non-Config model classes when optional imports succeed. It intentionally omits names ending in `Config`; import configs from `fla.models`.

## Representative layer constructors

### `GatedLinearAttention`

```python
from fla.layers import GatedLinearAttention

GatedLinearAttention(
    mode="chunk",
    hidden_size=1024,
    expand_k=0.5,
    expand_v=1.0,
    num_heads=4,
    num_kv_heads=None,
    feature_map=None,
    use_short_conv=False,
    conv_size=4,
    conv_bias=False,
    use_output_gate=True,
    gate_fn="swish",
    elementwise_affine=True,
    norm_eps=1e-5,
    gate_logit_normalizer=16,
    gate_low_rank_dim=16,
    clamp_min=None,
    fuse_norm=True,
    layer_idx=None,
)
```

Use `mode="chunk"` for training/high-throughput paths, `mode="fused_recurrent"` for recurrent/decode-style paths, and `mode="fused_chunk"` where supported. Set `layer_idx` when cache update behavior is needed.

### `KimiDeltaAttention`

```python
from fla.layers import KimiDeltaAttention

KimiDeltaAttention(
    hidden_size=2048,
    expand_v=1,
    head_dim=128,
    num_heads=16,
    num_v_heads=None,
    mode="chunk",
    use_short_conv=True,
    allow_neg_eigval=False,
    safe_gate=False,
    lower_bound=None,
    conv_size=4,
    conv_bias=False,
    layer_idx=None,
    norm_eps=1e-5,
    **kwargs,
)
```

Route KDA-specific gate, beta, FlashKDA, and context-parallel questions to `../../kda-and-context-parallel/SKILL.md`.

## Representative config constructors

### `GLAConfig`

```python
from fla.models import GLAConfig

GLAConfig(
    hidden_size=2048,
    expand_k=0.5,
    expand_v=1.0,
    hidden_ratio=4,
    intermediate_size=None,
    num_hidden_layers=24,
    num_heads=4,
    num_kv_heads=None,
    feature_map=None,
    attn_mode="chunk",
    use_short_conv=False,
    conv_size=4,
    use_output_gate=True,
    clamp_min=None,
    hidden_act="swish",
    max_position_embeddings=2048,
    elementwise_affine=True,
    norm_eps=1e-6,
    use_gk=True,
    use_gv=False,
    attn=None,
    use_cache=True,
    vocab_size=32000,
    fuse_norm=True,
    fuse_swiglu=True,
    fuse_cross_entropy=True,
    fuse_linear_cross_entropy=False,
    **kwargs,
)
```

`GLAConfig().model_type == "gla"`.

### `KDAConfig`

```python
from fla.models import KDAConfig

KDAConfig(
    attn_mode="chunk",
    hidden_size=2048,
    expand_v=1.0,
    use_short_conv=True,
    allow_neg_eigval=False,
    safe_gate=False,
    lower_bound=None,
    conv_size=4,
    head_dim=128,
    num_heads=16,
    num_v_heads=None,
    max_position_embeddings=2048,
    num_hidden_layers=24,
    norm_eps=1e-6,
    attn=None,
    use_cache=True,
    vocab_size=32000,
    fuse_norm=True,
    fuse_swiglu=True,
    fuse_cross_entropy=True,
    use_l2warp=False,
    **kwargs,
)
```

`KDAConfig().model_type == "kda"`.

## Fused modules

```python
from fla.modules import RMSNorm, FusedLinearCrossEntropyLoss

RMSNorm(hidden_size, elementwise_affine=True, bias=False, eps=1e-5, device=None, dtype=None)
FusedLinearCrossEntropyLoss(ignore_index=-100, label_smoothing=0.0, logit_scale=1.0, logit_softcapping=None, num_chunks=8, reduction="mean", use_l2warp=False, l2_penalty_factor=0.0001, accumulate_grad_in_fp32=True)
```

Fused modules often route to Triton kernels, so CPU construction can pass while realistic forward paths require an accelerator backend. For minimal CPU smoke checks, construct configs and modules without forcing fused kernel execution.

## Tiny construction pattern

```python
from transformers import AutoModelForCausalLM
from fla.models import GLAConfig

config = GLAConfig(
    hidden_size=32,
    num_hidden_layers=1,
    num_heads=4,
    hidden_ratio=2,
    max_position_embeddings=64,
    vocab_size=128,
    fuse_norm=False,
    fuse_swiglu=False,
    fuse_cross_entropy=False,
)
model = AutoModelForCausalLM.from_config(config)
```

This creates random weights and should not download checkpoints. If construction imports FlashAttention or an optional fused backend, disable the related config feature or install the optional dependency.

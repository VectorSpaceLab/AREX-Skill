# API reference

This sub-skill is distilled from the public package APIs and the installed signature snapshot for `vector-quantize-pytorch`.

## Public imports

```python
from vector_quantize_pytorch import VectorQuantize, RandomProjectionQuantizer
```

## VectorQuantize

### Constructor

```python
VectorQuantize(
    dim,
    codebook_size,
    codebook_dim=None,
    heads=1,
    separate_codebook_per_head=False,
    decay=0.8,
    eps=1e-5,
    freeze_codebook=False,
    kmeans_init=False,
    kmeans_iters=10,
    sync_kmeans=True,
    use_cosine_sim=False,
    layernorm_after_project_in=False,
    threshold_ema_dead_code=0,
    channel_last=True,
    accept_image_fmap=False,
    accept_3d_fmap=False,
    commitment_weight=1.0,
    commitment_use_cross_entropy_loss=False,
    orthogonal_reg_weight=0.0,
    orthogonal_reg_active_codes_only=False,
    orthogonal_reg_max_codes=None,
    codebook_diversity_loss_weight=0.0,
    codebook_diversity_temperature=100.0,
    stochastic_sample_codes=False,
    sample_codebook_temp=1.0,
    straight_through=False,
    rotation_trick=None,
    directional_reparam=False,
    directional_reparam_variance=5e-3,
    sync_codebook=None,
    sync_affine_param=False,
    ema_update=None,
    vq_bridge=None,
    manual_ema_update=False,
    learnable_codebook=None,
    in_place_codebook_optimizer=None,
    manual_in_place_optimizer_update=False,
    affine_param=False,
    affine_param_batch_decay=0.99,
    affine_param_codebook_decay=0.9,
    sync_update_v=0.0,
    return_zeros_for_masked_padding=True,
    route_gradients_to_input=True,
)
```

### Forward

```python
quantized, indices, loss = vq(x, ...)
```

With `return_loss_breakdown=True`, the return becomes:

```python
quantized, indices, loss, breakdown = vq(x, return_loss_breakdown=True)
```

With `indices=...` supplied, the module returns the quantized output plus a cross-entropy match loss for the supplied codes rather than the default loss tuple.

### Helper methods

- `get_output_from_indices(indices)`: reconstructs the current codebook output for the provided indices.
- `update_ema_indices(x, indices, mask=None)`: manual EMA update path; pass a single index tensor, not a top-k stack.
- `manual_ema_update=True` defers the final codebook refresh in the internal update path; it is not a substitute for `update_ema_indices`.
- `codebook`: exposes the current codebook tensor.

### Common output shapes

| Mode | Input layout | Quantized | Indices | Notes |
| --- | --- | --- | --- | --- |
| sequence | `(B, N, D)` | `(B, N, D)` | `(B, N)` | default layout |
| masked sequence | `(B, N, D)` + `lens` or `mask` | `(B, N, D)` | `(B, N)` | padded values become zero and indices become `-1` when `return_zeros_for_masked_padding=True` |
| top-k | `(B, N, D)` | `(B, N, K, D)` | `(B, N, K)` | commit loss is returned per token and per candidate |
| image fmap | `(B, C, H, W)` with `accept_image_fmap=True` | `(B, C, H, W)` | `(B, H, W[, heads])` | no `mask` |
| 3D fmap | `(B, C, D, H, W)` with `accept_3d_fmap=True` | `(B, C, D, H, W)` | `(B, D, H, W[, heads])` | no `mask` |

### Constructor notes

- `codebook_dim` sets the internal latent codebook dimension before the projection back to `dim`.
- `heads>1` uses a multi-headed codebook path. If `separate_codebook_per_head=True`, each head owns its own codebook.
- `kmeans_init=True` initializes from the first batch seen by the module.
- `use_cosine_sim=True` switches to cosine-style matching.
- `threshold_ema_dead_code>0` enables stale-code replacement.
- `orthogonal_reg_weight>0` adds an orthogonal regularizer to the loss during training.
- `codebook_diversity_loss_weight>0` adds a diversity term during training.
- Choose one backward path at a time: plain STE (`rotation_trick=False`, `directional_reparam=False`), rotation trick, or directional reparam.
- `directional_reparam=True` requires stale-code replacement to stay enabled.
- `rotation_trick=None` lets the module choose its built-in default; set it explicitly if you need plain STE.
- `sync_codebook` follows distributed state by default.
- `vq_bridge` is the optional FVQ bridge path. It is only relevant when the bridge dependency is available and the codebook is learnable.

## RandomProjectionQuantizer

### Constructor

```python
RandomProjectionQuantizer(
    *,
    dim,
    codebook_size,
    codebook_dim,
    num_codebooks=1,
    norm=True,
    **kwargs,
)
```

### Forward

```python
indices = rq(x)
loss = rq(x, indices=target_indices)
```

### Behavior

- Returns indices by default.
- Returns a cross-entropy loss when `indices` is supplied.
- Uses a frozen random projection and a `VectorQuantize` instance internally.
- The wrapped quantizer uses cosine matching and separate codebooks per head.
- The wrapped quantizer runs in eval mode for the projection quantizer path.
- `num_codebooks` controls the trailing index dimension.

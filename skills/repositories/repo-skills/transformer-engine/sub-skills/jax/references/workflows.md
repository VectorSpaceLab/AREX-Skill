# JAX/Flax Workflows

This reference gives copy-ready patterns for using Transformer Engine in JAX/Flax applications. It avoids dataset downloads and assumes the target environment already has a compatible `transformer_engine[jax]` installation.

Construction-time verification facts to preserve:

- JAX/JAXLIB 0.10.2 import was verified in a prepared runtime.
- On A100, a BF16 `te_flax.DenseGeneral` forward and gradient passed.
- On A100, `get_supported_quantization_recipes()` returned an empty list; do not claim FP8/MXFP8/NVFP4 support on A100.

## 1. BF16/FP16 parameter and compute rules

For Transformer Engine JAX modules:

- Parameter allocation precision is controlled by the module `dtype` argument.
- Computation/output precision follows the dtype of the input tensor for high-precision BF16/FP16/FP32 flows.
- BF16 is the safest default for NVIDIA Ampere and newer when no low-precision recipe is available.
- FP16 can be used when the surrounding training code already handles FP16 numerical constraints.

Minimal BF16 DenseGeneral block:

```python
import jax
import jax.numpy as jnp
from flax import linen as nn
import transformer_engine.jax.flax as te_flax

class TEDenseBlock(nn.Module):
    features: int

    @nn.compact
    def __call__(self, x):
        x = te_flax.LayerNorm(epsilon=1e-6, dtype=jnp.float32)(x)
        return te_flax.DenseGeneral(
            features=self.features,
            use_bias=True,
            dtype=jnp.bfloat16,
        )(x)

key = jax.random.PRNGKey(0)
x = jax.random.normal(key, (4, 16), dtype=jnp.bfloat16)
model = TEDenseBlock(features=32)
variables = model.init(key, x)
y = model.apply(variables, x)
assert y.dtype == jnp.bfloat16
```

Forward + gradient smoke:

```python
def loss_fn(params, x):
    y = model.apply({"params": params}, x)
    return jnp.asarray(y, jnp.float32).sum()

loss, grads = jax.jit(jax.value_and_grad(loss_fn))(variables["params"], x)
jax.block_until_ready((loss, grads))
```

## 2. Replace only a Flax Dense GEMM

Use `te_flax.make_dot_general_cls(recipe_obj)` when an existing Flax model should keep owning its `kernel` parameter, optimizer state, and sharding annotations while TE replaces only the GEMM path.

```python
from flax import linen as nn
from transformer_engine.common.recipe import DelayedScaling
import transformer_engine.jax.flax as te_flax

te_dot_general_cls = te_flax.make_dot_general_cls(DelayedScaling())

class ExistingDenseBlock(nn.Module):
    features: int

    @nn.compact
    def __call__(self, x):
        return nn.Dense(
            features=self.features,
            use_bias=False,
            dtype=x.dtype,
            dot_general=te_dot_general_cls(),
        )(x)
```

Guard this path with recipe support before module initialization. Some recipes are unsupported on common BF16-capable GPUs; initializing at module import time can raise before a test can skip.

## 3. BF16 TransformerLayer pattern

Use `te_flax.TransformerLayer` when you want TE to own the attention + MLP block instead of manually composing `LayerNormDenseGeneral`, `DotProductAttention`, and `LayerNormMLP`.

```python
import jax
import jax.numpy as jnp
import transformer_engine.jax.flax as te_flax

batch, seqlen, hidden, heads = 2, 8, 64, 4
x = jax.random.normal(jax.random.PRNGKey(1), (batch, seqlen, hidden), dtype=jnp.bfloat16)

layer = te_flax.TransformerLayer(
    hidden_size=hidden,
    mlp_hidden_size=4 * hidden,
    num_attention_heads=heads,
    mlp_activations=("gelu",),
    self_attn_mask_type="causal",
    enable_relative_embedding=False,
    use_bias=True,
    attention_dropout=0.0,
    intermediate_dropout=0.0,
    hidden_dropout=0.0,
    dtype=jnp.bfloat16,
    transpose_batch_sequence=False,
)

rngs = {"params": jax.random.PRNGKey(2), "dropout": jax.random.PRNGKey(3)}
variables = layer.init(rngs, x, deterministic=True)
y = layer.apply(variables, x, deterministic=True, rngs={"dropout": rngs["dropout"]})
assert y.shape == x.shape
```

Set all dropout rates to `0.0` and `deterministic=True` for deterministic smoke tests. Re-enable dropout in real training and pass the `dropout` RNG collection.

## 4. Hardware-gated low-precision recipe context

Recipes are provided by `transformer_engine.common.recipe`; support is checked by TE's JAX quantization helpers.

```python
from transformer_engine.common.recipe import (
    DelayedScaling,
    Float8CurrentScaling,
    MXFP8BlockScaling,
    NVFP4BlockScaling,
)
from transformer_engine.jax.quantize import get_supported_quantization_recipes

supported = {type(r).__name__ for r in get_supported_quantization_recipes()}

if "DelayedScaling" in supported:
    fp8_recipe = DelayedScaling()
elif "Float8CurrentScaling" in supported:
    fp8_recipe = Float8CurrentScaling()
else:
    fp8_recipe = None  # Stay in BF16/FP16; do not force FP8.
```

Known hardware gates:

- `DelayedScaling` and `Float8CurrentScaling`: require compute capability 8.9 or newer. A100 is compute capability 8.0 and should be treated as unsupported for these modes even if BF16 TE kernels work.
- `MXFP8BlockScaling`: Blackwell-class path guarded by compute capability 9.9 or newer and CUDA/cuBLASLt 12.8 or newer.
- `NVFP4BlockScaling`: compute capability 10.0 or newer and CUDA/cuBLASLt 12.8 or newer.

Do not claim that a recipe is available until the target process returns it from `get_supported_quantization_recipes()` or `is_scaling_mode_supported(...)`.

## 5. JAX autocast semantics: initialize inside the context

JAX differs from PyTorch: initialize the model inside the enabled TE autocast context so the Flax variable tree captures quantization metadata. Applying a model that was initialized outside the context may silently fall back to high precision or lack the metadata needed for correct low-precision updates.

```python
import flax
import jax
import jax.numpy as jnp
import transformer_engine.jax as te
import transformer_engine.jax.flax as te_flax
from transformer_engine.common.recipe import DelayedScaling

recipe = DelayedScaling()
mesh_resource = te.MeshResource()
key = jax.random.PRNGKey(0)
x = jax.random.normal(key, (2, 8, 64), dtype=jnp.bfloat16)

with te.autocast(enabled=True, recipe=recipe, mesh_resource=mesh_resource):
    model = te_flax.DenseGeneral(features=64, use_bias=True, dtype=jnp.bfloat16)
    variables = model.init(key, x)

other_vars, params = flax.core.pop(variables, "params")
```

Forward/backward should also run under a matching autocast context:

```python
def loss_fn(params, other_vars, x):
    var_collect = {"params": params, **other_vars}
    with te.autocast(enabled=True, recipe=recipe, mesh_resource=mesh_resource):
        out = model.apply(var_collect, x)
    return jnp.asarray(out, jnp.float32).mean()

loss, (param_grads, other_grads) = jax.value_and_grad(loss_fn, argnums=(0, 1))(
    params, other_vars, x
)
```

`other_grads` may contain quantization-state updates rather than optimizer gradients. Preserve these non-param collections across steps.

## 6. Persist quantization collections in a train loop

A robust pattern is to keep optimizer parameters separately while threading TE's non-param variable collections through every train and eval call.

```python
import flax
import transformer_engine.jax as te

# After init inside autocast:
other_vars, params = flax.core.pop(variables, "params")

@jax.jit
def train_step(params, other_vars, batch, rngs):
    def loss_fn(full_vars):
        with te.autocast(enabled=True, recipe=recipe, mesh_resource=mesh_resource):
            pred = model.apply(full_vars, batch["x"], rngs=rngs)
        loss = jnp.asarray(pred, jnp.float32).mean()
        return loss

    full_vars = {"params": params, **other_vars}
    loss, grads = jax.value_and_grad(loss_fn)(full_vars)
    new_other_vars, param_grads = flax.core.pop(grads, "params")
    merged_other_vars = te.update_collections(new_other_vars, other_vars)
    return loss, param_grads, merged_other_vars
```

Notes:

- `te.NVTE_FP8_COLLECTION_NAME` is `"fp8_metas"` and is not an optimizer parameter collection.
- Delayed scaling can add amax/scale history collections such as `_overwrite_with_gradient`; keep the whole non-param variable tree.
- Evaluation should receive the latest non-param collections too. Running eval without them can disable or alter low-precision behavior.
- For `NVFP4BlockScaling`, pass an `sr_rng` RNG when stochastic rounding is required by the recipe.

## 7. Fused attention workflow

For attention after Q/K/V projections, `te_flax.DotProductAttention` supports BSHD and THD layouts, MHA/GQA/MQA, causal/padding masks, sliding-window attention, context parallel fields, and experimental `score_mod` callbacks.

Separate BSHD GQA pattern:

```python
import jax
import jax.numpy as jnp
from transformer_engine.jax.flax import DotProductAttention

batch, seqlen, q_heads, kv_heads, head_dim = 1, 128, 8, 2, 64
q = jax.random.normal(jax.random.PRNGKey(0), (batch, seqlen, q_heads, head_dim), dtype=jnp.bfloat16)
k = jax.random.normal(jax.random.PRNGKey(1), (batch, seqlen, kv_heads, head_dim), dtype=jnp.bfloat16)
v = jax.random.normal(jax.random.PRNGKey(2), (batch, seqlen, kv_heads, head_dim), dtype=jnp.bfloat16)

dpa = DotProductAttention(
    head_dim=head_dim,
    num_attention_heads=q_heads,
    num_gqa_groups=kv_heads,
    attn_mask_type="causal",
    qkv_layout="bshd_bshd_bshd",
    attention_dropout=0.0,
    transpose_batch_sequence=False,
)
variables = dpa.init(jax.random.PRNGKey(3), q, k, v, deterministic=True)
out = dpa.apply(variables, q, k, v, deterministic=True)
assert out.shape == q.shape
```

Fused attention defaults:

- `NVTE_FUSED_ATTN=1` is the default; TE uses cuDNN fused attention when an eligible kernel exists.
- If a normal attention configuration has no fused kernel, TE warns and falls back to JAX-native unfused attention.
- `score_mod` is stricter: if fused attention is disabled or no fused kernel exists, TE raises a `ValueError` instead of falling back.
- Set `NVTE_FUSED_ATTN=0` before process start to force unfused attention for diagnosis.
- Set `NVTE_ALLOW_NONDETERMINISTIC_ALGO=0` before process start when deterministic attention kernels are required.

## 8. Validation commands

Run the bundled BF16 DenseGeneral smoke in the target environment:

```bash
python skills/disco/transformer-engine/sub-skills/jax/scripts/jax_bf16_smoke.py --device cuda --batch-size 2 --in-features 16 --features 8
```

If your current directory is this sub-skill directory, use:

```bash
python scripts/jax_bf16_smoke.py --device cuda
```

Expected output includes:

- JAX and JAXLIB versions.
- Visible devices and selected device.
- Output shape/dtype.
- A finite loss and finite gradients.
- The supported quantization recipe names for the current hardware. An empty list is valid on A100.

For an import-only check:

```bash
python - <<'PY'
import jax
import transformer_engine.jax as te
import transformer_engine.jax.flax as te_flax
print("jax", jax.__version__)
print("te top-level", te.__all__)
print("te flax", te_flax.__all__)
PY
```

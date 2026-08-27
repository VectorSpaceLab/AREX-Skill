# JAX Sharding and Checkpointing

Transformer Engine JAX can participate in normal JAX/Flax sharding, but TE modules also need a `MeshResource` so TE kernels know which physical mesh axes represent data, tensor, sequence, context, FSDP, pipeline, or expert parallelism.

## MeshResource basics

```python
import jax
from jax.experimental import mesh_utils
from jax.sharding import Mesh, NamedSharding, PartitionSpec as P
from transformer_engine.jax.sharding import MeshResource, global_shard_guard

# Example: 2 data-parallel x 2 tensor-parallel devices.
devices = mesh_utils.create_device_mesh((2, 2))
mesh = Mesh(devices, axis_names=("dp", "tp"))
mesh_resource = MeshResource(dp_resource="dp", tp_resource="tp")

with jax.set_mesh(mesh), global_shard_guard(mesh_resource):
    # Initialize/apply TE modules, create shardings, and run compiled steps here.
    pass
```

Equivalent when you are already using `te.autocast`:

```python
import transformer_engine.jax as te

with jax.set_mesh(mesh):
    with te.autocast(enabled=False, mesh_resource=mesh_resource):
        # BF16/FP16 TE code with TE sharding resource active.
        pass
```

Use `enabled=False` when you want TE sharding resources but not FP8/NVFP4 quantization.

`MeshResource` fields:

| Field | Meaning |
| --- | --- |
| `dp_resource` | Data-parallel batch sharding axis. |
| `tp_resource` | Tensor-parallel hidden/head sharding axis. |
| `tpsp_resource` | Tensor sequence parallel axis. Do not enable simultaneously with `tp_resource` for the same mesh. |
| `fsdp_resource` | Fully sharded data-parallel weight axis. |
| `cp_resource` | Context-parallel sequence axis for supported attention paths. |
| `ep_resource` | Expert-parallel axis for MoE token dispatch/combine paths. |
| `pp_resource` | Pipeline-parallel resource name when a higher-level pipeline stack uses it. |

## TE logical axes

TE defines logical axis constants in `transformer_engine.jax.sharding`:

```python
from transformer_engine.jax import sharding as te_sharding

te_sharding.BATCH_AXES       # "nvte_batch"
te_sharding.SEQLEN_AXES      # "nvte_seqlen"
te_sharding.SEQLEN_TP_AXES   # "nvte_seqlen_tp"
te_sharding.SEQLEN_CP_AXES   # "nvte_seqlen_cp"
te_sharding.HEAD_AXES        # "nvte_head"
te_sharding.HIDDEN_AXES      # "nvte_hidden"
te_sharding.HIDDEN_TP_AXES   # "nvte_hidden_tp"
te_sharding.JOINED_AXES      # "nvte_joined"
te_sharding.W_NO_SHARD_AXES  # "nvte_w_no_shard"
te_sharding.W_FSDP_AXES      # "nvte_w_fsdp"
te_sharding.W_TP_AXES        # "nvte_w_tp"
te_sharding.W_JOINED_AXES    # "nvte_w_joined"
```

TE maps these logical axes to mesh axes using the active `MeshResource`. For example, `BATCH_AXES` maps to `fsdp_resource` when FSDP is active, otherwise to `dp_resource`; `HEAD_AXES`, `HIDDEN_TP_AXES`, and `W_TP_AXES` map to `tp_resource` or `tpsp_resource`.

## Logical-axis deprecation warning

TE has a fallback path that converts TE logical-axis names directly into `PartitionSpec` values. That fallback emits a `DeprecationWarning` similar to: TE logical axes such as `BATCH_AXES` and `SEQLEN_AXES` are deprecated and should be used through Flax logical-axis rules instead.

Preferred pattern:

```python
from flax.linen import partitioning as nn_partitioning
import transformer_engine.jax as te
import transformer_engine.jax.flax as te_flax

base_rules = ()
with te.autocast(enabled=False, mesh_resource=mesh_resource):
    rules = te_flax.extend_logical_axis_rules(base_rules)

with nn_partitioning.axis_rules(rules):
    # Initialize modules that emit params_axes, especially TransformerLayer.
    variables = model.init(rngs, x, deterministic=True)
```

Use explicit module axes for lower-level modules:

```python
te_flax.DenseGeneral(
    features=out_features,
    kernel_axes=("embed", "mlp"),
    bias_axes=("mlp",),
    input_axes=("batch", "seqlen", "embed"),
    dtype=jnp.bfloat16,
)
```

`extend_logical_axis_rules` validates that user-provided rules do not conflict with TE's mapping. It is mainly needed for `TransformerLayer`; generic layers like `DenseGeneral` need explicit `kernel_axes`/`bias_axes` when they do not have default semantic axes.

## Dense DP/TP pattern

A common DP=2/TP=2 dense plan:

```python
from jax.sharding import NamedSharding, PartitionSpec as P

input_sharding = NamedSharding(mesh, P("dp", None, None))
kernel_sharding = NamedSharding(mesh, P(None, "tp"))
output_grad_sharding = NamedSharding(mesh, P("dp", None, "tp"))

x = jax.device_put(x, input_sharding)
dy = jax.device_put(dy, output_grad_sharding)
params = variables["params"]
params = {
    **params,
    "Dense_0": {
        **params["Dense_0"],
        "kernel": jax.device_put(params["Dense_0"]["kernel"], kernel_sharding),
    },
}
variables = {**variables, "params": params}

with jax.set_mesh(mesh), global_shard_guard(mesh_resource):
    loss, grads = jax.jit(train_step)(variables, x, dy)
```

For `TransformerLayer`, prefer `jax.eval_shape(model.init, ...)` to inspect `params_axes`, convert those axes with the extended logical rules, then use `jax.jit(..., in_shardings=..., out_shardings=...)` for initialization and train/eval steps.

## Checkpoint policies for TE GEMMs

JAX checkpoint policies that look only for `jax.lax.dot_general` can miss TE GEMMs because TE does not always lower GEMMs as plain `lax.dot_general` primitives.

Use TE-aware policies:

```python
import jax
import transformer_engine.jax.checkpoint_policies as te_ckpt

remat_fn = jax.checkpoint(
    fn,
    policy=te_ckpt.dots_and_te_gemms_with_no_batch_dims,
)

# Broader dot checkpointing variant:
remat_fn_all_dots = jax.checkpoint(
    fn,
    policy=te_ckpt.checkpoint_dots_and_te_gemms,
)
```

Available TE policy names:

| Policy | Use |
| --- | --- |
| `te_gemms_saveable` | Matches TE GEMM primitives and JAX scaled-matmul wrapper; useful to compose with custom policies. |
| `dots_and_te_gemms_with_no_batch_dims` | TE-compatible replacement for no-batch-dims dot policies. |
| `checkpoint_dots_and_te_gemms` | TE-compatible replacement for broader dot checkpointing. |

Policies that do not filter by dot primitive, such as save-by-name or everything-saveable policies, can also work if they match the intended activation-saving behavior.

## Quantization checkpoint names

Several TE modules accept `quantization_checkpoint_name`. `LayerNormMLP` also accepts `ffn1_ckpt_name` and `ffn2_ckpt_name`. Use these names when rematerialization policy or debugging needs stable names around quantization outputs.

```python
block = te_flax.LayerNormMLP(
    intermediate_dim=4096,
    dtype=jnp.bfloat16,
    quantization_checkpoint_name="quantization",
    ffn1_ckpt_name="ffn1",
    ffn2_ckpt_name="ffn2",
)
```

When `quantization_checkpoint_name` is set under a supported quantization recipe, TE's JAXPR can include named checkpoint values for quantized tensors. When it is `None`, those explicit names are absent.

## Distributed and fused-attention caveats

- Exact fused-attention availability depends on shape, dtype, GPU architecture, cuDNN/frontend version, mask type, bias type, layout, dropout/training mode, sliding-window settings, and context-parallel strategy.
- Standard `DotProductAttention` can warn and fall back to unfused JAX attention when fused attention is requested but no fused kernel is available.
- `score_mod` requires fused attention. If `NVTE_FUSED_ATTN=0` or no fused kernel is available, TE raises a `ValueError` instead of falling back.
- Context parallel examples often require a multi-GPU mesh and sequence descriptors for packed/padded layouts. Validate with small synthetic BSHD/THD inputs before moving to large training batches.
- Multi-process JAX requires `jax.distributed.initialize(...)` before device or mesh inspection. Shut down distributed JAX at process end.
- For cuBLASMp collective GEMM capture, XLA command buffers may need `--xla_gpu_enable_command_buffer=+COLLECTIVES` before `jax.distributed.initialize()`. This is only relevant to collective GEMM paths using cuBLASMp, not ordinary single-GPU BF16 smoke tests.

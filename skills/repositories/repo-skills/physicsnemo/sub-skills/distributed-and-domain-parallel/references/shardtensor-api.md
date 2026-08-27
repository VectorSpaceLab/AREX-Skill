# ShardTensor and distributed API map

| Object | Signature / fact | Notes |
| --- | --- | --- |
| `DistributedManager.initialize` | `initialize()` | Sets up launcher/rank/device state. |
| `DistributedManager.initialize_mesh` | `initialize_mesh(mesh_shape, mesh_dim_names)` | Returns a named `DeviceMesh`. |
| `scatter_tensor` | `scatter_tensor(tensor, global_src, mesh, placements, global_shape=None, dtype=None, requires_grad=False)` | Core input-scatter helper for ShardTensor workflows. |
| `sync_module_over_mesh` | `sync_module_over_mesh(module, mesh, src_mesh_rank=0, verify=False)` | Copies plain parameters and buffers across the domain mesh. |
| `ShardTensor` | `ShardTensor(local_tensor, spec, *, requires_grad)` | Activation-side distributed tensor with uneven sharding support. |
| `TensorPromotionMode` | Promotion controls are part of the domain-parallel machinery | Use when debugging or validating promotion behavior. |

## Decision table

| Situation | Wrapper | Why |
| --- | --- | --- |
| Domain-only, params are plain tensors | none | Broadcast plain params once, then rely on ShardTensor promotion. |
| DDP + domain, params are plain tensors | DDP | DDP handles the ddp axis; ShardTensor handles the domain axis. |
| Parameter sharding or DTensor params | FSDP2 | DDP cannot manage DTensor params. |
| FSDP1 / `distribute_module` | do not use | That is the older DTensor-era pattern and is not the current recommended route. |

## Behavioral rules

- ShardTensor is for activations / inputs, not wholesale model rewrites.
- Per-domain-group batch size must be 1.
- Inputs, not model code, should be scattered across the domain mesh.
- `full_tensor()` and `redistribute(...)` are gather-style operations used when a full tensor is needed for logging or validation.
- Async collectives must be waited on before program exit or the runtime may warn.

## Tiny smoke expectations

- A valid smoke can prove import, mesh creation, and one tiny scatter/sync path.
- A real domain-parallel verification uses actual CUDA-capable GPUs under `torchrun`, `mpirun`, or `srun`.

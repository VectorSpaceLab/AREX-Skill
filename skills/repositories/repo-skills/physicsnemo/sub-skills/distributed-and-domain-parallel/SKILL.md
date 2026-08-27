---
name: distributed-and-domain-parallel
description: "Route PhysicsNeMo distributed launches, DDP/FSDP2, DeviceMesh,
  ShardTensor, and domain-parallel input/output handling."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PhysicsNeMo distributed and domain parallel

Use this sub-skill when the task is about `DistributedManager`, launchers, DDP/FSDP2, named `DeviceMesh` layouts, `ShardTensor` inputs, scatter/sync APIs, or `torch.compile` caveats around domain parallelism.

## Trigger phrases

- "How do I launch PhysicsNeMo with torchrun, mpirun, or srun?"
- "How do I use DistributedManager or initialize a DeviceMesh?"
- "How do I combine DDP or FSDP2 with ShardTensor?"
- "How do I scatter inputs across the domain mesh?"
- "Why is `requires_grad_` or `sync_module_over_mesh` failing?"
- "Can I compile this ShardTensor model with torch.compile?"

## Quick decision tree

1. **Need only a single process or a CPU import smoke?** Use [`scripts/domain_parallel_smoke.py`](scripts/domain_parallel_smoke.py) with no flags.
2. **Need 2+ GPUs and a real distributed proof?** Launch the smoke with `--distributed` under `torchrun`, `mpirun`, or `srun`.
3. **All model params remain plain tensors?** Use DDP on the explicit `ddp` mesh group, or no wrapper if only domain parallelism is active.
4. **Need memory sharding or DTensor parameters?** Use FSDP2 (`torch.distributed.fsdp.fully_shard`) on the `ddp` mesh only.
5. **Need `torch.compile`?** Compile only safe submodules; keep ring/sequence-sharded attention and other p2p collectives outside the compiled region.

## Non-negotiables

- `ShardTensor` is for activations, not wholesale model surgery.
- Do **not** recommend FSDP1 or `distribute_module`.
- Per-domain-group batch size must be 1; scale batch on the DDP axis only.
- Domain-parallel proof needs actual CUDA-capable GPUs. CPU-only is import/single-process only.

## Validation steps

- Confirm `DistributedManager.initialize()` gives the expected rank, world size, device, and launcher detection.
- Build a named mesh and verify `ddp_size * domain_size == world_size`.
- Scatter a tiny tensor over the domain mesh and gather it back with `full_tensor()`.
- Call `sync_module_over_mesh` on a tiny plain module and confirm weights and buffers match the source rank.
- If using `requires_grad=True`, check the leaf tensor and its gradient on the smoke path.
- For any `torch.compile` case, verify the eager path first.

## Use the bundled references

- [`references/distributed-workflows.md`](references/distributed-workflows.md) — launcher recipes, DDP/FSDP2 skeletons, logging, and checkpoint notes.
- [`references/shardtensor-api.md`](references/shardtensor-api.md) — `DeviceMesh`, `scatter_tensor`, `sync_module_over_mesh`, batch semantics, and `torch.compile` constraints.
- [`references/troubleshooting.md`](references/troubleshooting.md) — common ShardTensor and distributed failure modes.

## Route elsewhere when appropriate

- Model-family selection or example picking → [`../model-selection/SKILL.md`](../model-selection/SKILL.md)
- Data loading, readers, and dataloaders → [`../datapipes/SKILL.md`](../datapipes/SKILL.md)
- Mesh creation/validation/repair utilities → [`../mesh-and-geometry/SKILL.md`](../mesh-and-geometry/SKILL.md)
- Diffusion sampler/preconditioner internals → [`../diffusion-and-generative/SKILL.md`](../diffusion-and-generative/SKILL.md)
- Active-learning loops or ONNX export → [`../active-learning-and-deployment/SKILL.md`](../active-learning-and-deployment/SKILL.md)

# PhysicsNeMo distributed workflows

## Minimal launch patterns

### Single process / import smoke

- Initialize `DistributedManager` and inspect the resolved device.
- This is enough for CPU import checks and launcher-free verification.

### `torchrun`

```bash
torchrun --standalone --nproc-per-node=2 your_script.py --domain-size 2
```

Use this when the workflow needs real multi-process proof.

### `mpirun` / `srun`

- Use the same script entry point.
- PhysicsNeMo’s distributed utilities detect launcher context and derive the rank/device configuration.

## DDP and FSDP2 skeleton

- If all model parameters remain plain tensors, wrap the model with DDP on the `ddp` mesh group.
- If the workflow needs DTensor parameters or parameter sharding, use FSDP2 (`torch.distributed.fsdp.fully_shard`) on the DDP mesh only.
- Sync plain weights and buffers over the domain mesh before wrapping.

## Domain-parallel recipe

1. Initialize `DistributedManager`.
2. Build a 2-D mesh with named axes `ddp` and `domain`.
3. Assert `ddp_size * domain_size == world_size`.
4. Scatter a tiny input tensor over the domain mesh with `scatter_tensor`.
5. Keep the per-domain-group batch size at 1.
6. Validate `full_tensor()` or a tiny loss/backward path only after the input scatter path works.

## Logging and checkpoint notes

- Domain-parallel examples often pair with standard checkpoint/logging helpers from `physicsnemo.utils`.
- Build and verify the data/model path first; only then layer on expensive checkpoint or experiment-tracking logic.

## `torch.compile` notes

- Compile only safe submodules and keep sharded attention / collective-heavy fragments eager when domain size is greater than 1.
- Use `dynamic=False` for fixed-shape workloads.
- Re-check eager behavior before comparing compiled numerics.

---
name: distributed
description: "Composer distributed launch, rank, device, sampler, auto
  microbatching, and parallelism workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Composer Distributed

Use this sub-skill when a task needs Composer-specific distributed launch, rank or world-size reasoning, sampler wiring, device/backend selection, auto microbatching caveats, or FSDP/FSDP2/tensor-parallel configuration basics.

## Route here

- Convert a single-process training script into a `composer` launcher command.
- Choose `--nproc`, `--world_size`, `--node_rank`, `--base_rank`, `--master_addr`, and `--master_port` for single-node or multi-node runs.
- Capture non-rank-zero stdout/stderr with filename placeholders such as `{rank}` or `{local_rank}`.
- Read rank values through `composer.utils.dist` instead of parsing environment variables by hand.
- Add `dist.get_sampler(dataset, shuffle=True)` for map-style datasets.
- Decide between `device="cpu"`, `device="gpu"`, MPS, TPU, HPU, and Neuron device helpers.
- Understand when `device_train_microbatch_size="auto"` can recover from CUDA OOMs.
- Prepare basic `parallelism_config` for DDP/FSDP/FSDP2/tensor-parallel work.

## Reroute

- Core `Trainer` fit/eval loops, optimizer stepping, checkpoint scheduling, or non-distributed resume: use `../training/SKILL.md`.
- Algorithm/method behavior and method-specific side effects: use `../methods/SKILL.md`.
- Loggers, profiler setup, tracing, and performance-analysis tooling: use `../observability/SKILL.md`.
- Export-only, inference, ONNX, TorchScript, or deployment flows: use `../inference-export/SKILL.md`.

## Read first

- [Launcher and ranks](references/launcher-and-ranks.md): CLI launcher, rank environment variables, output capture, and sampler wiring.
- [Parallelism and backends](references/parallelism-and-backends.md): device selection, FSDP/FSDP2/TP configuration, auto microbatching, and backend prerequisites.
- [Troubleshooting](references/troubleshooting.md): launch/backend/distributed failures and concrete recovery checks.
- [Device probe](scripts/device_probe.py): safe local Composer/Torch device surface check.
- [Launcher help](scripts/launcher_help.py): safe launcher usage printer that does not start training.

## Quick launch patterns

Single node with every visible GPU:

```bash
composer -n 8 train.py --config config.yaml
```

Single node with rank-specific child logs:

```bash
composer -n 8 --stdout stdout_{rank}.log --stderr stderr_{rank}.log train.py
```

Module mode, useful when the training entry point is importable:

```bash
composer -n 4 -m package.train --arg value
```

Multi-node requires explicit topology:

```bash
composer -n 8 --world_size 16 --node_rank 1 --master_addr host0 --master_port 29500 train.py
```

If `world_size > nproc`, provide enough information for Composer to infer the global ranks on this node.

## In-script distributed pattern

```python
from torch.utils.data import DataLoader
from composer.utils import dist

sampler = dist.get_sampler(dataset, shuffle=True)
loader = DataLoader(dataset, batch_size=32, sampler=sampler)

if dist.get_global_rank() == 0:
    print("rank zero logs once")
```

Use `get_world_size()`, `get_local_rank()`, `get_global_rank()`, `get_node_rank()`, and `get_local_world_size()` for diagnostics that also work in non-distributed runs.

## Device and backend rules

1. Start CPU-only if the issue is model logic, dataloader schema, or loss/metric behavior.
2. Move to `device="gpu"` only after PyTorch reports CUDA availability and the requested precision is supported.
3. Treat MPS/TPU/HPU/Neuron as backend-specific paths; verify the vendor runtime before claiming support.
4. For FSDP/FSDP2/tensor parallelism, align the world size with the requested sharding/replication/tensor degrees.
5. CPU importability is not proof that GPU launch, FSDP, or auto-microbatching is healthy.

## Auto microbatching decision guide

Set `device_train_microbatch_size="auto"` when a CUDA training run OOMs during forward/backward and the full batch should be split dynamically. It does not fix dataloader memory, CPU OOM, model construction OOM, callback OOM, or algorithm work that runs outside the Trainer forward/backward path. Be careful with BatchNorm when auto microbatching makes microbatches very small.

## Safe workflow

1. Run `python scripts/device_probe.py` to inspect import/device availability.
2. Run `python scripts/launcher_help.py` before composing launch commands.
3. Verify the training script works as `python train.py` or `python -m package.train` before multi-rank launch.
4. Add `dist.get_sampler` for map-style datasets.
5. Add rank-specific file placeholders before increasing ranks.
6. Add FSDP/FSDP2/TP only after ordinary DDP launch works.
7. Keep a tiny synthetic job for backend smoke; do not debug distributed launch on a full production run first.

## Ask or stop before proceeding

- The user asks for multi-node launch but cannot provide master address, rank topology, scheduler details, or network reachability.
- Required accelerator hardware or vendor runtime is unavailable.
- The task would launch a long training run, write to shared storage, or consume all GPUs without explicit approval.
- A sharded checkpoint must be loaded on a different world size and the checkpoint format/backends are unknown.
- FSDP/TP degrees conflict with visible world size or model architecture.

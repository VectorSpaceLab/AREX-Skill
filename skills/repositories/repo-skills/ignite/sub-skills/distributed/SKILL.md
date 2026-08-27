---
name: distributed
description: "Routes Ignite distributed launch, backend selection,
  auto-wrapping, and rank helper workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Ignite distributed workflows

Use this sub-skill when the request is about distributed backends, launcher setup, rank helpers, or the `auto_*` wrappers in `ignite.distributed`.

## Include here

- `Parallel`, `initialize`, `finalize`, `spawn`, `show_config`, `available_backends`, `backend`, `device`, and rank/world-size helpers.
- `auto_dataloader`, `auto_model`, `auto_optim`, and `DistributedProxySampler`.
- Collectives and coordination helpers such as `all_reduce`, `all_gather`, `all_gather_tensors_with_shapes`, `broadcast`, `barrier`, `new_group`, `one_rank_only`, and `one_rank_first`.
- Backend-specific routing for native PyTorch distributed (`gloo`, `nccl`, `mpi`), Horovod, and `xla-tpu`.
- Single-process serial runs, `torchrun`-style launches, and simple distributed smoke checks.

## Exclude or route elsewhere

- Engine construction, resume logic, and deterministic loop behavior belong in `sub-skills/engine/`.
- Checkpointing, logger integration, schedulers, progress bars, and profiling belong in `sub-skills/handlers/`.
- Metric math and evaluator contracts belong in `sub-skills/metrics/`.
- Legacy `ignite.contrib` notes live in `references/legacy-contrib.md`.

## Start here

- Read `references/api-reference.md` for backend names, launcher entry points, and collective-helper semantics.
- Read `references/workflows.md` for serial, single-process gloo, and launch-command recipes.
- Read `references/troubleshooting.md` when a backend is unavailable, initialization hangs, or a rank helper behaves unexpectedly.
- Run `scripts/distributed_smoke.py` for a safe serial-and-gloo check of the distributed helpers.

## Common triggers

- "How do I use Ignite with `torchrun` or `gloo`?"
- "How do I adapt my dataloader, model, or optimizer for distributed training?"
- "Why does `available_backends()` only return `('gloo',)`?"
- "How do I write rank-aware logging or a one-rank-only callback?"
- "How do I check the active backend, rank, or world size?"

## Useful boundary notes

This route owns the backend and collective helpers, but not the training loop or the metric/handler logic that often uses them. When a workflow spans distributed setup plus model quality or checkpointing, keep the distributed-specific details here and send the loop or side-effect questions to the owning sub-skill.

# Distributed API reference

## Launcher and backend selection

| Symbol(s) | Purpose | Notes |
| --- | --- | --- |
| `Parallel` | Context manager for launching or initializing distributed training. | Handles both spawn-style launches and already-launched environments such as `torchrun`. |
| `initialize` / `finalize` | Explicitly create or tear down the current distributed context. | Use when you do not want the `Parallel` context manager. |
| `spawn` | Spawn multiple worker processes for a chosen backend. | Use with `nccl`, `gloo`, `mpi`, `horovod`, or `xla-tpu` as available. |
| `available_backends` | Report installed backends for the current environment. | In a CPU-only setup it may only report `('gloo',)`. |
| `backend` / `model_name` / `device` | Inspect the active computation model. | Useful for logging and runtime debugging. |
| `get_rank` / `get_local_rank` / `get_world_size` / `get_nproc_per_node` / `get_nnodes` / `get_node_rank` | Inspect process topology. | These helpers work in serial mode too. |
| `set_local_rank` | Hint the local rank when the context was created manually. | Helps native distributed setups that were not launched through Ignite helpers. |
| `show_config` | Log the active backend, device, rank, and topology. | Useful for smoke checks and debugging. |

## Auto-wrapping helpers

| Symbol(s) | Purpose | Notes |
| --- | --- | --- |
| `auto_dataloader` | Adapt a dataloader to the active distributed context. | Adjusts batch size, workers, sampler, and pin-memory defaults as needed. |
| `auto_model` | Move/wrap a model for the current backend. | Uses DDP or DataParallel when appropriate; broadcasts initial states for Horovod. |
| `auto_optim` | Adapt an optimizer to the current backend. | Usually a no-op except for XLA and Horovod. |
| `DistributedProxySampler` | Wrap a user sampler for distributed use. | Only for samplers that are not already distributed samplers. |

## Collectives and coordination

| Symbol(s) | Purpose | Notes |
| --- | --- | --- |
| `all_reduce` | Reduce a tensor or scalar across processes. | Supports common reduction ops such as `SUM`, `MIN`, `MAX`, `PRODUCT`, `AND`, `OR`, and backend-specific variants. |
| `all_gather` | Gather tensors, numbers, strings, or objects across processes. | Tensor inputs should have the same shape on each process. |
| `all_gather_tensors_with_shapes` | Gather tensors that may differ in shape but share dimensionality. | You must provide the shapes ahead of time. |
| `broadcast` | Broadcast a tensor, scalar, string, or path from a source rank. | `safe_mode=True` allows placeholder values on non-source ranks. |
| `barrier` | Synchronize all participating processes. | Use before rank-sensitive file or logging operations. |
| `new_group` | Build a subgroup from a list of ranks. | Input is typically a list of integers. |
| `one_rank_only` | Decorator to run a function on one rank only. | Often used for logging, checkpointing, or downloads. |
| `one_rank_first` | Context manager that lets one rank run a block first. | Useful for downloads or workspace initialization. |
| `sync` | Rescan the active distributed context. | Useful if the process group was created or destroyed outside Ignite. |

## Backend matrix

| Backend | Typical use | Hardware / package requirements |
| --- | --- | --- |
| `gloo` | CPU distributed smoke tests and lightweight native distributed runs. | Native PyTorch distributed support; no GPU required. |
| `nccl` | Multi-GPU native PyTorch distributed training. | CUDA-capable GPUs plus a PyTorch build with NCCL support. |
| `mpi` | MPI-backed native distributed training. | A PyTorch build with MPI support. |
| `horovod` | Horovod-based distributed training. | The Horovod package and a compatible environment. |
| `xla-tpu` | TPU/XLA distributed training. | `torch_xla` and TPU support. |

## Boundary reminders

- `Parallel(backend=None)` is the serial path. It is not a shortcut for initializing another backend.
- `Parallel` and `initialize` only accept backends that are actually reported by `available_backends()`.
- `auto_*` helpers only change behavior when a distributed context is active.
- When a user asks for logging, checkpointing, or metric behavior that happens to be rank-aware, keep the backend mechanics here and hand the side effect itself to the matching sub-skill.

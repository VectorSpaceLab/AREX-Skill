# Distributed troubleshooting

## Backend availability and install issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `available_backends()` only reports `('gloo',)` | CPU-only native distributed support is available, but GPU or accelerator backends are not. | Use `gloo` for CPU smoke checks or install the backend-specific packages required for other modes. |
| `Backend should be one of ...` | The requested backend is not installed or not supported by the current build. | Choose a backend reported by `available_backends()` or install the missing backend package. |
| `Nccl backend is required but no cuda capable devices` | `nccl` was requested on a machine without CUDA GPUs. | Switch to `gloo` or run on a CUDA-capable machine. |
| `Horovod` or `torch_xla` import errors | Optional backend packages are not installed. | Install the matching backend package only when that backend is actually required. |

## Initialization and launch mistakes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `If backend is None, argument 'nproc_per_node' should be also None` | `Parallel(backend=None)` was given distributed spawn arguments. | Remove the distributed spawn arguments or choose a real backend. |
| `TCP initialization via init_method=... will hang` | A `tcp://` init method was used directly. | Use `env://` or set `MASTER_ADDR` / `MASTER_PORT` and let Ignite use the environment. |
| `PyTorch distributed configuration should define env variables ...` | The environment only partially defines rank/world-size variables. | Set `RANK`, `LOCAL_RANK`, and `WORLD_SIZE` together, or let Ignite initialize them. |
| `If number of nodes larger than one, arguments master_addr and master_port or init_method should be specified` | A multi-node launch is missing its rendezvous settings. | Provide `MASTER_ADDR` / `MASTER_PORT` or use an explicit init method. |
| `node_rank should be between ...` | An invalid node index was provided. | Fix the node rank to match the number of nodes. |

## Rank and collective issues

- `Parallel(backend=None)` is the serial path and does not initialize a process group.
- `one_rank_only(..., with_barrier=True)` requires a valid distributed context; use it only when all ranks participate.
- `one_rank_first(rank=...)` validates the rank against the world size or local process count.
- `all_gather_tensors_with_shapes` needs the full shape list ahead of time. If you do not know the shapes, use the object gather path elsewhere.
- `broadcast(..., safe_mode=True)` is the right choice when non-source ranks do not have a meaningful placeholder value.

## Auto-wrapper surprises

- `auto_dataloader` only adapts batch size, sampler, and worker count when the world size is larger than one.
- `auto_model` may wrap the model in `DistributedDataParallel` or `DataParallel` depending on the active backend and device availability.
- `auto_optim` is usually a no-op except for XLA and Horovod.
- If the wrapper seems to do nothing, confirm that the distributed context has been initialized first.

## When in doubt

Start with the serial path, then run a single-process `gloo` smoke check before trying multi-process or accelerator-specific launches.

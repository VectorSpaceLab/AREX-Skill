# Launcher, Ranks, World Size, And Sampling

Composer's public launcher command is the safest way to start a distributed
training script because it expands one user command into one process per local
rank and patches each child process with the expected PyTorch distributed
environment variables.

## Launcher Command Shape

Basic single-node launch:

```bash
composer -n 8 train.py --config config.yaml
```

Equivalent long-form flags and log capture:

```bash
mkdir -p logs
composer --nproc 8 \
  --stdout 'logs/stdout_rank{rank}.log' \
  --stderr 'logs/stderr_rank{rank}.log' \
  train.py --config config.yaml
```

Module or command mode:

```bash
composer -n 4 -m package.train --arg value      # child command: python -m package.train ...
composer -n 4 -c train-entrypoint --arg value   # child command: train-entrypoint ...
```

`-m/--module_mode` and `-c/--command_mode` are mutually exclusive. Without
`-c`, the launcher invokes the current Python executable before the training
script or module.

To print help without starting child processes, use the bundled safe wrapper:

```bash
python scripts/launcher_help.py
```

## Key Launcher Flags

| Flag | Meaning | Practical rule |
| --- | --- | --- |
| `-n`, `--nproc` | Number of processes to launch on this node. | Usually the number of local GPUs. If omitted, Composer checks `LOCAL_WORLD_SIZE`, then CUDA device count, and falls back to 1 on CPU-only hosts. |
| `--world_size` | Total process count across all nodes. | Defaults to `nproc` for single-node. Must be at least `nproc`. Set explicitly for multinode. |
| `--node_rank` | Integer node index. | Required in multinode unless `base_rank` is enough to infer it. |
| `--base_rank` | Lowest global rank launched on this node. | For uniform nodes, `base_rank = node_rank * nproc`. For irregular node sizes, provide both `base_rank` and `node_rank`. |
| `--master_addr` | Hostname or IP for rank-zero's store. | Required in multinode. Single-node defaults to loopback. |
| `--master_port` | TCP port for rank-zero's store. | Required in multinode. Single-node defaults to a free port. Use a unique port for concurrent jobs. |
| `--stdout` | Filename format for non-local-rank-zero stdout. | Include `{rank}` or `{local_rank}` to avoid file collisions. |
| `--stderr` | Filename format for non-local-rank-zero stderr. | Include `{rank}` or `{local_rank}` to avoid file collisions. |
| `-v`, `--verbose` | Emit launcher diagnostics. | Use during launch debugging. |

The output filename format supports `{rank}`, `{local_rank}`, `{world_size}`,
`{node_rank}`, and `{local_world_size}`. The launcher does not create missing
parent directories for these filenames; create the log directory first.

## Multinode Template

For two nodes with eight processes per node, run matching commands on each node
with the same master address and port:

```bash
# Node 0
mkdir -p logs
composer -n 8 --world_size 16 --node_rank 0 \
  --master_addr "$MASTER_ADDR" --master_port 29500 \
  --stdout 'logs/stdout_rank{rank}.log' \
  --stderr 'logs/stderr_rank{rank}.log' \
  train.py --config config.yaml

# Node 1
mkdir -p logs
composer -n 8 --world_size 16 --node_rank 1 \
  --master_addr "$MASTER_ADDR" --master_port 29500 \
  --stdout 'logs/stdout_rank{rank}.log' \
  --stderr 'logs/stderr_rank{rank}.log' \
  train.py --config config.yaml
```

If nodes have unequal local process counts, pass explicit `--base_rank` on each
node so global ranks cover `[0, world_size - 1]` exactly once.

## Environment Variables Seen By Training Code

Each child process receives:

| Variable | Meaning |
| --- | --- |
| `RANK` | Global rank in `[0, WORLD_SIZE - 1]`. |
| `WORLD_SIZE` | Total number of ranks. |
| `LOCAL_RANK` | Rank index on the current node in `[0, LOCAL_WORLD_SIZE - 1]`. |
| `LOCAL_WORLD_SIZE` | Number of local processes launched on this node. |
| `NODE_RANK` | Node index. |
| `MASTER_ADDR` | Rank-zero store host. |
| `MASTER_PORT` | Rank-zero store port. |
| `PYTHONUNBUFFERED` | Set to `1` for child output behavior. |
| `TORCH_NCCL_ASYNC_ERROR_HANDLING` | Set to `1` for NCCL error handling. |

## Rank And World-Size Helpers

Prefer these helpers instead of direct `os.environ` parsing. They return
single-rank defaults when distributed execution is not active.

```python
from composer.utils import dist

world_size = dist.get_world_size()          # default 1
rank = dist.get_global_rank()               # default 0
local_world_size = dist.get_local_world_size()  # default 1
local_rank = dist.get_local_rank()          # default 0
node_rank = dist.get_node_rank()            # default 0
```

If using Composer distributed collectives outside the `Trainer` lifecycle, call:

```python
from composer.utils import dist

dist.initialize_dist(device=None, timeout=300.0)
```

`initialize_dist` chooses the backend from `composer.utils.get_device(device)`.
If no distributed environment is set, it initializes a single-rank process group.
If the world size is greater than one, the required rank and master variables
must be complete and consistent.

Useful coordination helpers include `dist.barrier()`, `dist.all_reduce(...)`,
`dist.broadcast(...)`, `dist.all_gather(...)`, `dist.broadcast_object_list(...)`,
`dist.all_gather_object(...)`, and `dist.run_local_rank_zero_first()`.

## Distributed Sampling

For a map-style `torch.utils.data.Dataset` where every rank can see a full copy,
use Composer's sampler helper:

```python
from torch.utils.data import DataLoader
from composer.utils import dist

sampler = dist.get_sampler(dataset, shuffle=True, seed=17)
dataloader = DataLoader(dataset, batch_size=32, sampler=sampler)
```

`dist.get_sampler(dataset, drop_last=False, shuffle=False, num_replicas=None,
rank=None, seed=0)` returns a `torch.utils.data.distributed.DistributedSampler`
with `num_replicas` defaulting to `dist.get_world_size()` and `rank` defaulting
to `dist.get_global_rank()`.

Do not add this sampler to an `IterableDataset` or a streaming dataset that owns
its own rank sharding. If a dataset is already sharded by rank, use an ordinary
sequential or random sampler instead.

## Quick Diagnosis Checklist

- `world_size < nproc` is invalid.
- Multinode requires `master_addr`, `master_port`, and enough rank information to
  determine each node's global rank range.
- Rank-specific logs need `{rank}` or `{local_rank}` in filenames and a
  pre-created output directory.
- If every rank sees identical batches, inspect the `DataLoader` sampler first.

# Dask-DDP Index Batching

## Purpose and status

Read this reference only for optional distributed index-batching tasks: Dask-DDP, multi-GPU, multi-node scheduler files, `world_size`, `ddp_rank`, or `DistributedSampler` behavior. Core index batching works on CPU without Dask-DDP, and real cluster execution is not a required verification gate for this skill.

The public examples demonstrate Dask-DDP with index batching for PeMS-style traffic datasets. They are intentionally reference patterns here, not bundled runnable launchers, because they require real datasets, optional dependencies, distributed workers, and often GPUs.

## Prerequisites

- Install the package with DDP/index dependencies available. In public package terms, the `ddp` extra includes Dask distributed support, `dask_pytorch_ddp`, Pandas, and PyTables-related dependencies.
- Initialize a Dask client before dispatching training. A single-node run can create a local Dask cluster; a multi-node run should connect with a scheduler-file path created by the Dask scheduler.
- Initialize/use a PyTorch distributed process group through the Dask-DDP dispatch mechanism.
- Use a backend compatible with the hardware and process placement. The examples use `backend="gloo"`; GPU deployments must also use a CUDA-enabled PyTorch/PyG stack and correct per-rank device assignment.
- Pre-stage or allow download of the selected traffic dataset before launching many workers. The example pattern constructs the loader before dispatch so the dataset files exist before workers start.

## Loader and sampler arguments

DDP-aware `get_index_dataset` signatures expose:

```python
loader.get_index_dataset(
    lags=12,
    batch_size=batch_size,
    shuffle=shuffle,
    allGPU=-1,
    ratio=(0.7, 0.1, 0.2),
    world_size=world_size,
    ddp_rank=worker_rank,
    dask_batching=False,
)
```

Rules:

- Pass both `world_size=dist.get_world_size()` and `ddp_rank=dist.get_rank()` after distributed initialization.
- Leave both at `-1` outside DDP. Do not pass a rank with the default `world_size=-1`.
- When `ddp_rank != -1`, the loader creates `DistributedSampler(dataset, num_replicas=world_size, rank=ddp_rank, shuffle=shuffle)` for train, validation, and test splits.
- In a DDP training loop, call `train_loader.sampler.set_epoch(epoch)` only when a `DistributedSampler` is actually present.
- `ChickenpoxDatasetLoader` and `WindmillOutputLargeDatasetLoader` expose index batching but do not expose `world_size`/`ddp_rank` in their index methods.
- DDP-aware loader signatures exist for METR-LA, PeMS-Bay, PeMS-All-LA, and PeMS. The documented multi-node focus is PeMS-Bay, PeMS-All-LA, and full PeMS; treat METR-LA DDP as an advanced adaptation when the model example supports it.

## Single-node pattern

For a single node, the example pattern omits a scheduler file and creates a local Dask cluster with `npar` workers:

```python
from dask.distributed import Client, LocalCluster
from dask_pytorch_ddp import dispatch, results

cluster = LocalCluster(n_workers=npar)
client = Client(cluster)

futures = dispatch.run(
    client,
    train,
    args=args,
    loader=loader,
    epochs=epochs,
    batch_size=batch_size,
    allGPU=allGPU,
    backend="gloo",
)

handler = results.DaskResultsHandler(run_key)
handler.process_results(".", futures, raise_errors=False)
client.shutdown()
```

Inside `train`, derive rank information and request rank-partitioned dataloaders:

```python
worker_rank = dist.get_rank()
world_size = dist.get_world_size()

gpu_id = choose_local_gpu(worker_rank)  # Adapt to the node's actual GPU count.
if allGPU:
    loaders = loader.get_index_dataset(
        allGPU=gpu_id,
        batch_size=batch_size,
        world_size=world_size,
        ddp_rank=worker_rank,
    )
else:
    loaders = loader.get_index_dataset(
        batch_size=batch_size,
        world_size=world_size,
        ddp_rank=worker_rank,
    )
```

The source examples map worker rank to a GPU id with a modulo expression. When adapting, use the actual local GPU count rather than assuming a fixed number of GPUs per node.

## Multi-node scheduler-file pattern

For multi-node runs, start a Dask scheduler and workers outside the Python training script, configure them to write/read the same scheduler file, then connect the training launcher with:

```python
client = Client(scheduler_file=dask_cluster_file)
```

Operational checklist:

1. Choose a shared scheduler-file path visible to the launcher and workers.
2. Start one Dask scheduler that writes that file.
3. Start Dask workers on each participating node and point them at the scheduler file.
4. Confirm the scheduler has the expected number of workers before dispatching training.
5. Launch the Python Dask-DDP entry point with `--dask-cluster-file <scheduler-file>`, `--npar <workers-per-node>`, and `--dataset pems-bay`, `pemsAllLA`, or `pems` as appropriate.
6. Keep dataset download/pre-stage and worker filesystem visibility explicit; do not let every rank independently discover/download large traffic files.

A scheduler-specific shell launcher from the source examples was not bundled because it hard-codes HPC scheduler assumptions. Recreate only the portable steps above for the user's cluster manager.

## Argument reference from the Dask-DDP examples

| Argument | Meaning | Notes |
| --- | --- | --- |
| `--epochs`, `-e` | number of training epochs | Expensive for real datasets; keep synthetic or dry-run checks small. |
| `--batch-size`, `-bs` | per-rank dataloader batch size | Effective global batch is roughly per-rank batch times world size unless sampler padding changes sample counts. |
| `--gpu`, `-g` | parse as true/false for GPU index preprocessing | Requires CUDA; otherwise leave false and move CPU batches in the loop. |
| `--debug`, `-d` | print per-batch progress | Useful only for rank-zero logging in larger runs. |
| `--dask-cluster-file` | scheduler file for multi-node Dask client | Empty value means single-node local cluster in the examples. |
| `--npar`, `-np` | workers/GPUs per node in launcher logic | Also validate rank-to-device mapping. |
| `--dataset` | dataset selector | Example values include `pems-bay`, `pemsAllLA`, `pems`; A3TGCN adaptations may also include `metr-la`. |

## CPU-only or no-cluster fallback

If the user asks for DDP but has only CPU or no Dask cluster:

- Do not claim real multi-node behavior is verified.
- Use ordinary CPU index batching to validate tuple unpacking and model-loop shapes.
- Run [index_batching_smoke.py](../scripts/index_batching_smoke.py) to prove low-level `IndexDataset` mechanics.
- Explain the missing requirements: Dask distributed runtime, `dask_pytorch_ddp`, initialized scheduler/client, distributed process group, and optionally CUDA if `allGPU` is requested.

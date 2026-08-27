# Scaling and Backend Choices

Use this reference to choose the smallest PyG scaling pattern that satisfies the workload, then validate the package and backend environment before starting long training.

## Scaling decision table

| Situation | Prefer | Key APIs | First validation |
| --- | --- | --- | --- |
| Many small independent graphs | Mini-batch graph loading | `torch_geometric.loader.DataLoader` | Batch two tiny `Data` objects and inspect `batch`, `ptr`, `num_graphs`. |
| One large in-memory graph | Neighborhood sampling | `NeighborLoader`, `LinkNeighborLoader` | Iterate one tiny batch; optional sampling extensions may be needed. |
| Graph/features live behind a service or database | Remote backend abstraction | `FeatureStore`, `GraphStore`, `NodeLoader`, `LinkLoader`, custom `BaseSampler` | Verify tensor CRUD, edge layout, sortedness, and sampler output on a tiny fixture. |
| Partitioned graph across workers | Distributed PyG | `Partitioner`, `LocalFeatureStore`, `LocalGraphStore`, `DistNeighborLoader`, `DistLinkNeighborLoader` | Load every partition and inspect metadata before launch. |
| Model parallelism across accelerators | DDP or explicit model parallel design | `torch.nn.parallel.DistributedDataParallel`, PyG loaders | Run a single-batch process-local smoke test. |
| CPU sampling throughput bottleneck | Worker tuning and affinity | `num_workers`, `filter_per_worker`, `enable_cpu_affinity` | Compare throughput with and without affinity on the same input. |
| Unknown slowdown or memory spike | Profiling | `torch_geometric.profile`, `torch.profiler` | Profile a few warm batches before changing architecture. |

Route basic loader syntax to the `loaders-and-sampling` sub-skill and model architecture work to the `gnn-modeling` sub-skill when the task is not primarily about scaling or distributed execution.

## Large-graph neighbor sampling

For one large graph, start with `NeighborLoader` or `LinkNeighborLoader` before moving to distributed stores. Installed PyG 2.9 signatures include:

- `NeighborLoader(data, num_neighbors, input_nodes=None, input_time=None, replace=False, subgraph_type="directional", disjoint=False, temporal_strategy="uniform", time_attr=None, weight_attr=None, transform=None, transform_sampler_output=None, is_sorted=False, filter_per_worker=None, neighbor_sampler=None, directed=True, **kwargs)`.
- `LinkNeighborLoader(data, num_neighbors, edge_label_index=None, edge_label=None, edge_label_time=None, replace=False, subgraph_type="directional", disjoint=False, temporal_strategy="uniform", neg_sampling=None, neg_sampling_ratio=None, time_attr=None, weight_attr=None, transform=None, transform_sampler_output=None, is_sorted=False, filter_per_worker=None, neighbor_sampler=None, directed=True, **kwargs)`.

Practical defaults:

```python
loader = NeighborLoader(
    data,
    input_nodes=train_idx,
    num_neighbors=[15, 10],
    batch_size=1024,
    shuffle=True,
    num_workers=2,
)
```

Check these before scaling the run:

- `batch.batch_size` equals the number of seed nodes for the batch.
- `batch.n_id[:batch.batch_size]` maps local seed outputs back to global node IDs.
- Model depth matches sampling hops when using default directional subgraphs.
- `num_neighbors` is a list per hop, or a canonical edge-type dictionary with the same hop count for each type.
- Optional backend errors appear on iteration, not necessarily at loader construction.

## Remote `FeatureStore` and `GraphStore`

PyG supports remote or custom storage by separating features from graph topology:

- `FeatureStore` should provide efficient random feature lookup for tensors addressed by type/group/name/index attributes.
- `GraphStore` should store edge indices in a form that supports efficient sampling from input nodes or edges.
- A custom sampler can subclass or implement `BaseSampler` behavior and call specialized methods on the graph backend.
- `NodeLoader` and `LinkLoader` can operate on a `(feature_store, graph_store)` pair when paired with an appropriate sampler.

Remote backend validation checklist:

- Feature lookup returns tensors with stable dtype, shape, device, and ordering for repeated index requests.
- Graph lookup reports `EdgeAttr` metadata with correct edge type, layout, size, and sortedness.
- The graph store and sampler agree on row/column direction and whether CSC sorting by destination is required.
- Missing IDs produce clear errors instead of silent zero rows.
- Batches contain all features needed by the model and loss after remote fetch.
- The backend client handles connection cleanup and retries outside the model forward pass.

Remote stores are an integration boundary, not a place to hide model logic. Keep model code consuming ordinary `Data` or `HeteroData` batches after loader output is assembled.

## Optional sampling extensions

PyG can construct many objects with only `torch` and `torch_geometric`, but neighborhood sampling may require optional compiled packages when iterating loaders. Common packages to check are:

- `pyg-lib`: preferred acceleration path for many sampling operations and distributed merge helpers.
- `torch-sparse`: fallback sparse sampling path for some configurations.
- `torch-scatter`: common PyG extension used by many operations, depending on installation and model choices.

Run the bundled checker:

```bash
python scripts/check_sampling_backends.py --require-neighbor-backend
```

Treat missing optional extensions as environment issues. Install wheels matching the active Torch version, Python ABI, CUDA/CPU build, and PyG version; do not compile or download packages inside runtime smoke scripts.

## CPU affinity and worker tuning

`NodeLoader` and `LinkLoader` families support CPU worker affinity through `enable_cpu_affinity(...)` when `num_workers > 0`.

```python
loader = NeighborLoader(data, num_neighbors=[15, 10], batch_size=1024, num_workers=3)

with loader.enable_cpu_affinity(loader_cores=[0, 1, 2]):
    for batch in loader:
        train_step(batch)
```

Tuning principles:

- Start with `num_workers` in the 2-4 range, then measure.
- Use `filter_per_worker=True` for many CPU multiprocessing workloads when workers should gather node and edge features themselves.
- Assign loader workers and the main training process to disjoint physical cores when using external tools such as `numactl`, `KMP_AFFINITY`, or `GOMP_CPU_AFFINITY`.
- Avoid assigning worker cores that the launcher also gives to DDP compute processes.
- On dual-socket systems, test whether separating loader workers and model compute by NUMA socket improves locality.
- Disable or reduce affinity if throughput decreases; affinity is workload-specific.

## Profiling scalable workloads

Use PyG profiling only on short representative windows:

```python
from torch_geometric.profile import Profiler

with Profiler(model, profile_memory=True, use_cuda=False) as prof:
    out = model(batch.x, batch.edge_index)
print(prof.summary())
```

Available profiling helpers include `Profiler`, `profileit`, `torch_profile`, `xpu_profile`, `get_stats_summary`, `rename_profile_file`, and NVTX helpers. Practical guidance:

- Profile CPU first if CUDA is unavailable or if the bottleneck is sampling/feature fetch.
- Set `use_cuda` according to the actual tensor device; do not enable CUDA profiling just because the machine has a GPU.
- Warm up one or more batches before measuring model time.
- Separate sampling time, host-to-device transfer, forward pass, backward pass, and optimizer step if throughput is unclear.
- Do not export large traces in safe smoke tests; reserve trace files for explicit debugging tasks.

## Synthetic usability cases

Hard cases that exercise this sub-skill without hardware or network dependencies:

1. Backend availability checker assertions: run the bundled checker in an environment with and without optional extensions, assert JSON fields exist, and require actionable install notes when no neighbor backend is importable.
2. Tiny partition metadata sanity checklist: create a six-node synthetic graph, partition into two temporary parts in a controlled environment with required partition dependencies, load local stores for both parts, and assert metadata, partition books, and edge IDs are internally consistent.

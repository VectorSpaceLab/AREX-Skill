# Scalable and Distributed Troubleshooting

Start by classifying the failure as environment/backend, sampling configuration, partition metadata, distributed rendezvous, remote store contract, CPU affinity, or profiling. Reproduce on a tiny synthetic graph before changing production training code.

## Backend checker fails to import Torch or PyG

Symptoms:

- `ModuleNotFoundError: torch` or `ModuleNotFoundError: torch_geometric`.
- The bundled checker returns `ok: false` with a missing core package.
- PyG imports from a different environment than expected.

Fixes:

- Activate the Python environment intended for the training job.
- Install compatible `torch` and `torch_geometric` first; optional extensions come later.
- Run `python -c "import torch, torch_geometric; print(torch.__version__, torch_geometric.__version__)"` in the same shell used by the launcher.
- Keep public smoke scripts dependency-reporting only; they should not install packages or mutate environments.

## Optional sampling extension is missing

Symptoms:

- `NeighborLoader` or `LinkNeighborLoader` constructs but iteration raises an error about `pyg-lib` or `torch-sparse`.
- Distributed sampling fails when merging or sampling remote outputs.
- `check_sampling_backends.py --require-neighbor-backend` exits nonzero.

Fixes:

- Prefer a compatible `pyg-lib` wheel when available for the active Torch/Python/CUDA combination.
- Install `torch-sparse` only with wheels matching the active Torch build; CPU and CUDA wheels are not interchangeable.
- Check `torch-scatter` if model operations or older PyG paths require it.
- Re-run the checker after installation and paste the JSON into the issue or run log.
- If optional wheels are unavailable for the platform, reduce the task to `DataLoader` or full-batch smoke checks until the environment is rebuilt.

## CUDA or wheel mismatch

Symptoms:

- Imports fail with unresolved symbols or shared-object load errors.
- CUDA is available in `nvidia-smi` but `torch.cuda.is_available()` is false.
- Optional extensions were installed for a different Torch or CUDA build.

Fixes:

- Compare `torch.__version__`, `torch.version.cuda`, Python version, and extension wheel tags.
- Install all PyG optional extensions from the same compatibility matrix as the active Torch build.
- Use CPU wheels when the active Torch build is CPU-only.
- Do not allocate a GPU to diagnose imports; the checker reports CUDA availability without creating tensors on CUDA.
- For DDP, verify one-process CPU training before debugging multi-GPU launch.

## Rendezvous, RPC, or DDP hangs

Symptoms:

- `torchrun` starts but processes wait forever.
- RPC initialization times out.
- Some ranks enter the loader while others exit early.
- Port conflicts or firewall rules appear only on multi-node runs.

Fixes:

- Confirm every process uses the same `MASTER_ADDR`, rendezvous port, world size, and rank mapping.
- Keep DDP and RPC initialization ports distinct when both are manually configured.
- Prefer `gloo` for CPU sampling/RPC-oriented tests; use `nccl` only when CUDA devices are correctly assigned.
- Ensure `DistContext.rank`, `global_rank`, `world_size`, `global_world_size`, and `group_name` match the launcher topology.
- Add short barriers and rank-prefixed logging around process-group init, RPC init, first loader iteration, and shutdown.
- Always call RPC shutdown and process-group teardown in `finally` blocks to avoid stale workers.

## Partition metadata errors

Symptoms:

- `LocalGraphStore.from_partition(root, pid)` or `LocalFeatureStore.from_partition(root, pid)` asserts that a partition directory is missing.
- `META.json` does not match the graph type expected by the training script.
- Partition IDs from node or edge maps are out of range.
- Heterogeneous edge type keys do not match model metadata.

Fixes:

- Regenerate partitions from the same `Data` or `HeteroData` schema used by the training script.
- Confirm `pid` is less than the recorded number of partitions.
- Check that homogeneous layouts contain `node_map.pt` and `edge_map.pt`; hetero layouts contain per-type map files.
- Validate that edge indices reference valid local node IDs after partition loading.
- Keep partition roots immutable during distributed training.
- If `ClusterData` or partition generation requires unavailable optional dependencies, skip partition-native verification and use the backend checker plus metadata checklist instead.

## Remote store contract mistakes

Symptoms:

- Batches contain missing features, wrong feature rows, or duplicated node IDs.
- Custom stores work for full fetches but fail under sampled mini-batches.
- Graph sampling direction is reversed or edge types are missing.

Fixes:

- Validate `FeatureStore.put_tensor`, `get_tensor`, and `remove_tensor` semantics on a tiny typed tensor table.
- Validate `GraphStore.put_edge_index`, `get_edge_index`, `get_all_edge_attrs`, and edge layout metadata.
- Ensure graph store `size`, `edge_type`, layout, and `is_sorted` match what the sampler expects.
- Preserve requested index ordering when returning features.
- Fail loudly on missing IDs rather than returning zeros.
- Keep connection pooling, retries, authentication, and service-specific setup outside model code and out of public smoke scripts.

## CPU affinity makes performance worse

Symptoms:

- Throughput drops after enabling `enable_cpu_affinity`.
- Workers fail because requested core IDs do not exist or overlap with reserved ranks.
- Multi-process jobs oversubscribe cores.

Fixes:

- Benchmark `num_workers=0`, then 2-4 workers without affinity, then affinity with explicit core lists.
- Use only physical cores where possible; avoid assigning the same core to multiple heavy processes.
- Keep loader worker cores disjoint from DDP compute process cores.
- For small graphs, disable multiprocessing and affinity if overhead dominates.
- Revisit `filter_per_worker`; shared-memory pressure and feature placement can change the best value.

## Profiling output is empty or misleading

Symptoms:

- `Profiler` reports no useful events.
- CUDA timings are empty.
- Trace files show mostly data loading rather than model compute.

Fixes:

- Confirm the profiled forward path actually runs inside the context manager.
- Set `use_cuda=True` only when tensors and model are on CUDA.
- Warm up the loader and model before collecting a measurement.
- Profile model compute separately from sampling by materializing one batch first.
- Keep profiling windows short and representative; long distributed traces can be expensive and hard to interpret.

## Minimal escalation packet

When handing a scaling issue to another agent or human, include:

- Output from `scripts/check_sampling_backends.py`.
- PyTorch, PyG, Python, CUDA availability, and optional extension import statuses.
- Loader class, `num_neighbors`, `batch_size`, `num_workers`, `filter_per_worker`, and `subgraph_type`.
- Whether the data path uses in-memory `Data`, remote `FeatureStore`/`GraphStore`, or distributed `LocalFeatureStore`/`LocalGraphStore`.
- Partition count, current `pid`, and whether graph is homogeneous or heterogeneous.
- Launcher command with credentials and private paths removed.

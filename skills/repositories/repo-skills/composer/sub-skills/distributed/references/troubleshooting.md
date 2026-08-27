# Distributed Troubleshooting

Start with two safe probes that do not launch training:

```bash
python scripts/launcher_help.py
python scripts/device_probe.py
```

Then match the symptom below.

## Launcher And Rank Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `world_size(...) cannot be less than nproc(...)` | `--world_size` is smaller than local `--nproc`. | Set `--world_size` to total ranks across all nodes. For single node, omit it or set it equal to `--nproc`. |
| Multinode launch errors that `master_addr` or `master_port` is required | `--world_size > --nproc` but the rank-zero store address is incomplete. | Pass the same `--master_addr` and `--master_port` on every node. Use a port free on the master host. |
| `base_rank + nproc` would create a rank beyond `world_size` | Node rank range overlaps or exceeds the total process count. | Recompute global ranges. For uniform nodes use `base_rank = node_rank * nproc`; for irregular nodes pass explicit non-overlapping `--base_rank` values. |
| Composer cannot infer `node_rank` from `base_rank` | Unequal node process counts or a base rank not divisible by `nproc`. | Provide both `--node_rank` and `--base_rank`. |
| Processes hang at initialization | Different nodes used different `world_size`, `master_addr`, `master_port`, or rank ranges; firewall/port issue; one node never launched. | Compare the exact command on every node. Confirm the master port is reachable and all ranks `[0, world_size - 1]` are present exactly once. |
| A script reads missing rank environment variables | The script was run directly instead of through `composer`, or scheduler variables were partial. | Use the `composer` launcher, or call `dist.initialize_dist` only after supplying the full rank/master environment. |

## Logging And Output Capture

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Only one rank prints to console | Expected behavior: local rank zero is piped to console; other local ranks are captured or discarded. | Use `--stdout` and `--stderr` with rank placeholders to preserve all ranks. |
| Log files overwrite each other | The filename format lacks `{rank}` or `{local_rank}`. | Use names such as `logs/stdout_rank{rank}.log` and `logs/stderr_rank{rank}.log`. |
| Launcher fails opening a log path | Parent directory does not exist. | Run `mkdir -p logs` before launch or choose an existing directory. |
| Rank-specific debugging is confusing | Local rank and global rank are different in multinode. | Print both `dist.get_global_rank()` and `dist.get_local_rank()` in diagnostics. Use global `{rank}` for unique files across nodes. |

## Device And Backend Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `DeviceGPU cannot be created as torch.cuda is not available` | CUDA is not visible in the current process. | Check `python scripts/device_probe.py`, `CUDA_VISIBLE_DEVICES`, driver/container setup, and whether `--nproc` exceeds visible GPUs. Use `device='cpu'` only if the workflow supports CPU. |
| CPU-only host while GPU was requested | `get_device('gpu')` is explicit and will not fall back to CPU. | Change the user config to CPU for CPU-compatible debugging, or move to a CUDA host before validating GPU/FSDP/TP behavior. |
| Requested backend differs from current process group backend | Distributed was already initialized for another device class. | Restart the Python process. Initialize once with the intended device/backend. |
| `torch.distributed` unavailable with `world_size > 1` | PyTorch was built without distributed support or the selected backend is missing. | Install a PyTorch build with the needed distributed backend. Do not treat single-rank CPU import as proof of multi-rank support. |
| TPU/Neuron import error for `torch_xla` | XLA dependencies are absent. | Install and configure the appropriate XLA stack; for TPU set `PJRT_DEVICE=TPU`; Neuron construction sets `PJRT_DEVICE=NEURON` but still needs the Neuron/XLA packages. |
| HPU import error for Habana plugin | Habana frameworks are absent. | Use an HPU-enabled environment with Habana packages and HCCL support. |
| MPS selected but distributed launch is expected | `DeviceMPS` has no Composer distributed backend. | Treat MPS as local acceleration. Use CPU/GPU/XLA/HPU backends for distributed workflows. |

## Data Duplication And Sampling

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Metrics improve oddly fast or samples are duplicated across ranks | A map-style dataset was used without a `DistributedSampler`. | Create the sampler with `dist.get_sampler(dataset, shuffle=True, seed=...)` and pass it to `DataLoader(..., sampler=sampler)`. |
| Composer complains that a distributed sampler is required | The dataloader sampler is not rank-aware for a map-style dataset. | Use `composer.utils.dist.get_sampler` unless the dataset is iterable or already sharded. |
| Iterable/streaming dataset fails with `DistributedSampler` | Iterable datasets own their own sharding and do not support `DistributedSampler`. | Remove `DistributedSampler`; implement or verify sharding inside the iterable dataset. |
| Shuffling is identical every epoch in custom loops | The sampler epoch is not advanced. | Let Composer Trainer manage the dataloader when possible. In a manual loop, call the sampler's epoch setter before each epoch. |

## FSDP, FSDP2, And Tensor Parallel Configs

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| FSDP config rejects `device_mesh` | FSDP1 no longer accepts direct device-mesh specification. | Use `data_parallel_shard_degree` and `data_parallel_replicate_degree` for FSDP1, or use FSDP2 when a device mesh is explicitly required. |
| FSDP CPU offload expectation is not met | Composer's FSDP1 workflow exposes the flag but documents CPU offload as unsupported. | Set `cpu_offload=False` and solve memory with sharding, activation checkpointing, lower batch size, or manual microbatching. |
| Sharded checkpoint load fails or finds no checkpoint | `state_dict_type` or `load_path` points to the wrong format. | Match save/load `state_dict_type`. For sharded saves, point `load_path` at the shard directory, not an individual shard file. |
| FSDP2 config ignores or warns about attributes | FSDP2 accepts a smaller set of user-settable fields and is experimental. | Keep to `device_mesh`, `reshard_after_forward`, activation checkpointing/offload, `state_dict_type`, `load_monolith_rank0_only`, `mixed_precision`, and `verbose`; let Composer manage sync states. |
| Tensor-parallel launch fails or deadlocks | `tensor_parallel_degree` does not match the launched process mesh, or PyTorch tensor-parallel APIs are unavailable. | Verify world size and TP degree, then smoke check the exact model and `layer_plan` under the intended backend. |
| TP without FSDP behaves unexpectedly | Composer marks many TP combinations as experimental or unsupported. | Prefer a small explicit integration smoke check. If unsupported, use manual sharding outside this sub-skill's scope or route through training guidance. |

## Auto Microbatching

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `device_train_microbatch_size='auto'` fails on CPU or non-CUDA devices | Auto microbatching handles CUDA OOM, not generic memory pressure. | Use an explicit integer microbatch size on CPU/MPS/TPU/HPU/Neuron. |
| OOM from a callback, logger, checkpoint save, dataloader, or method still crashes | Auto microbatching catches OOMs in the forward/backward training path. | Reduce memory in the failing component, route logger/profiler issues to `../observability/SKILL.md`, or set a conservative integer microbatch size. |
| Auto microbatching reaches size 1 and fails | The batch/model cannot fit even one sample per microbatch, or memory is fragmented/leaked. | Reduce per-rank batch size, model size, sequence length, activation memory, or enable an appropriate sharding/checkpointing strategy. |
| BatchNorm accuracy regresses with auto microbatching | Very small microbatches produce noisy BatchNorm statistics. | Use SyncBatchNorm, replace BatchNorm with a normalization less sensitive to batch size, or manually choose a larger stable microbatch. |
| Profiling with auto microbatching is unstable | The microbatch search changes timing and may conflict with profiling assumptions. | Run a short auto-microbatch search first, record the stable integer size, then profile with that fixed value. |

## Minimal Debug Snippets

Rank print inside a training script:

```python
from composer.utils import dist

print(
    f"rank={dist.get_global_rank()} local_rank={dist.get_local_rank()} "
    f"world_size={dist.get_world_size()} local_world_size={dist.get_local_world_size()}"
)
```

Safe map-style dataloader:

```python
from torch.utils.data import DataLoader
from composer.utils import dist

sampler = dist.get_sampler(dataset, shuffle=True)
dataloader = DataLoader(dataset, batch_size=32, sampler=sampler)
```

Single-node smoke launch shape:

```bash
mkdir -p logs
composer -n 2 --stdout 'logs/stdout_rank{rank}.log' --stderr 'logs/stderr_rank{rank}.log' train.py
```

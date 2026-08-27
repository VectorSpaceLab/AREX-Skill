# GPU status and selection contract

## What is measured

The local detector uses `nvidia-smi` only. Discovery runs:

```text
nvidia-smi -L
```

Every non-empty line is counted and the detector returns zero-based indices
`[0, 1, ..., line_count - 1]`. A missing executable or a timeout produces an
empty list and a warning; a non-zero discovery exit is also treated as no
GPU. This is visibility discovery, not an allocation API.

Detailed status runs:

```text
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits
```

The six fields are, in order:

| Field | Returned key | Type/unit |
|---|---|---|
| `index` | `gpu_id` | integer, device index |
| `name` | `name` | string |
| `memory.used` | `memory_used_mb` | integer, MB |
| `memory.total` | `memory_total_mb` | integer, MB |
| `utilization.gpu` | `utilization_pct` | integer, percent |
| `temperature.gpu` | `temperature_c` | integer, °C |

The detector does **not** query process names or PIDs. A monitor may describe
processes separately, but a status row from this contract contains only the
six fields above. The bundled read-only script exposes the same measurements
and also derives selection lists.

## Exact Python API

The package-level functions have these signatures and shapes:

```python
detect_gpus() -> list[int]
# Example: [0, 1, 2, 3], or [] when discovery is unavailable.

gpu_status() -> list[dict]
# Each dict is exactly intended to contain:
# {
#   "gpu_id": int,
#   "name": str,
#   "memory_used_mb": int,
#   "memory_total_mb": int,
#   "utilization_pct": int,
#   "temperature_c": int,
# }

is_gpu_available(gpu_id: int, memory_threshold_mb: int = 1000) -> bool
get_usable_gpus(reserve_last: bool = True) -> list[int]
get_free_gpus(reserve_last: bool = True,
              memory_threshold_mb: int = 1000) -> list[int]
print_gpu_summary() -> None
```

`is_gpu_available` scans the detailed rows for the exact `gpu_id`. It returns
`False` when the ID is absent, when detailed status is unavailable, or when
`memory_used_mb` is **equal to or above** the threshold. The default is a
strictly-less-than 1000-MB test; it is not a utilization-percent test.

`get_free_gpus` first calls `get_usable_gpus`, then applies the same memory
predicate. Thus a device excluded by `reserve_last` can never appear in the
free list, even if its memory is low.

## Reserve-last policy

The configured default is:

```yaml
gpu:
  auto_detect: true
  reserve_last: true
```

The implementation applies the policy as follows:

| Detected list | `reserve_last=True` | `reserve_last=False` |
|---|---|---|
| `[]` | `[]` | `[]` |
| `[0]` | `[0]` | `[0]` |
| `[0, 1]` | `[0]` | `[0, 1]` |
| `[0, 1, 2]` | `[0, 1]` | `[0, 1, 2]` |

The one-GPU behavior is deliberate: excluding the last device would leave no
usable device, so a single detected GPU stays usable. With multiple GPUs the
last item in the discovery list is excluded. Because discovery enumerates
lines, this means the highest enumerated index in ordinary output. The policy
does not start a keeper, mark a device in the driver, or prevent another
process from using it.

## Launch and monitoring boundary

For a local experiment, the launcher accepts a string GPU value and exports it
as `CUDA_VISIBLE_DEVICES`; the command's process then sees that mask. A value
such as `"0"` selects one physical device, while a comma-separated value can
expose several. Do not assume the process's post-mask CUDA ordinal is the
same as the host ordinal when interpreting training logs.

The monitor polls process liveness, tails the latest log lines, and calls a
backend GPU-status method without an LLM call. Its local backend returns a
compact shape such as:

```python
{
    "gpus": [
        {"utilization": "12%", "memory": "234MB/147456MB"},
    ],
    "utilization": "12%",  # first GPU, or "N/A"
}
```

This compact monitor shape is not interchangeable with the detailed detector
shape above. SSH and Slurm transport, remote status, and scheduler allocation
belong to `execution-and-monitoring`. In Slurm mode, the login node may have no
usable `nvidia-smi`; scheduler queue occupancy is an advisory alternative, not
per-GPU memory/utilization data.

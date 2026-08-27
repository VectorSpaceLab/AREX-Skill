# GPU troubleshooting

## No GPU / missing `nvidia-smi`

**Symptom:** the status script says `nvidia-smi` is not found, or the detector
returns `[]`.

**Interpretation:** this is an unavailable local NVIDIA status, not evidence
that a device is free. The safe result is `usable_gpus=[]` and
`free_gpus=[]`. Check the host's PATH and NVIDIA driver installation with the
machine owner. Do not replace the result with a guessed device ID or with
PyTorch's package metadata. If this is an SSH or Slurm request, route the
transport to `execution-and-monitoring` rather than running local checks.

## `nvidia-smi` exits non-zero or times out

A driver/library problem, an unavailable device, or a transient command
failure can produce a non-zero result. The detector treats it as no status;
the bundled script reports the failure reason and does not derive free GPUs.
Retry only as a read-only check after the host issue is addressed. A timeout
is bounded at 10 seconds by the source detector and script.

## Status fields cannot be parsed

The detailed query must provide six comma-separated, unitless fields in the
order `index,name,memory.used,memory.total,utilization.gpu,temperature.gpu`.
Malformed rows are not valid availability evidence. Report status unavailable
rather than converting missing values to zero. The bundled script uses a CSV
parser and rejects incomplete/non-numeric rows; the package implementation may
raise on malformed numeric data, so callers should treat an exception as an
inspection failure.

## All devices look busy

“Free” uses only memory: `memory_used_mb < memory_threshold_mb`; it ignores GPU
utilization and process identity. The default threshold is 1000 MB and the
comparison is strict, so exactly 1000 MB is busy. A device with low memory but
active compute can still be selected by this simple heuristic; report that
limitation and confirm ownership before launch. To use a different threshold,
state it explicitly in the report and pass `--memory-threshold-mb` to the
bundled script.

## Reserved list is unexpectedly empty

With no detected rows, both lists must be empty. With exactly one detected GPU,
`reserve_last=true` intentionally keeps `[0]` usable rather than excluding the
only device. With two or more devices, it excludes the last enumerated device.
Set `--no-reserve-last` only when the user explicitly accepts using every
visible device; this does not create an OS-level reservation.

## PyTorch imports but CUDA is unavailable

The keeper requires both a successful `import torch` and
`torch.cuda.is_available()`. A CPU-only wheel, incompatible driver/runtime,
masked devices, or a broken driver can satisfy the first condition but fail
the second. Check `nvidia-smi` first, then ask the environment owner to verify
that the installed PyTorch build targets CUDA. Do not install or mutate an
environment from this skill, and do not start a keeper while diagnosing.

## Keeper cannot start on the requested GPU

Check that the ID is present in a fresh status report and that the user is not
asking the keeper to occupy a training device. The keeper does not prevalidate
IDs; PyTorch may raise for an invalid `cuda:<id>`. Use a positive interval:
zero can create a tight loop and negative values can fail in `sleep`. An
explicit SIGINT/SIGTERM is the intended stop path; report whether the process
actually exited and cleaned up.

## Remote and Slurm confusion

A controller on an SSH login host may not see the training host's GPUs. On a
Slurm login node, `nvidia-smi` may be unavailable by design; queue occupancy is
not per-device utilization or memory. Do not claim local GPU availability from
those signals. Route remote commands, scheduler allocation, and job lifecycle
to `execution-and-monitoring`.

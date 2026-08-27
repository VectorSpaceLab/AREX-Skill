# Optional GPU keep-alive

The keep-alive is a separate, side-effecting operation. It is **never** part of
read-only status checks and must not be started merely because
`reserve_last=true`. Its purpose is to maintain minimal CUDA activity on a
chosen device for environments that reclaim instances after prolonged GPU
idleness. It is not a scheduler reservation, health check, performance test, or
reliable guarantee that a cloud provider will retain an instance.

## Exact implementation contract

The keeper class is:

```python
GPUKeeper(gpu_id: int)
```

It exposes:

```python
start(interval: int = 300) -> None
_shutdown(signum, frame) -> None
```

Construction stores `gpu_id`, sets `_running=True`, clears `_tensor=None`, and
registers handlers for `SIGTERM` and `SIGINT`. The `start` method:

1. Imports `torch`. If import fails, it logs that PyTorch is not installed and
   returns without allocating anything.
2. Checks `torch.cuda.is_available()`. If false, it logs that CUDA is
   unavailable and returns.
3. Uses `torch.device(f"cuda:{gpu_id}")`.
4. Allocates `torch.zeros(1024, device=device, dtype=torch.float32)`, about
   4 KiB of FP32 storage (plus normal allocator/context overhead).
5. While `_running` is true, performs `_tensor.add_(1.0)`, then
   `_tensor.zero_()`, then sleeps for `interval` seconds.
6. After a signal changes `_running` to false, deletes the tensor, calls
   `torch.cuda.empty_cache()`, and logs that the keeper stopped.

The command-line entry point requires an integer `--gpu` and accepts
`--interval` with a default of 300 seconds (five minutes). The equivalent
explicit invocation is:

```bash
python -m gpu.keeper --gpu <id> --interval <seconds>
```

Only run that command after the user explicitly authorizes the side effect and
has chosen a device that is intentionally reserved. Do not run it in a check,
fixture, or verification command. A keep-alive occupies a CUDA context and a
small tensor, emits periodic work, may affect power/thermal accounting and
other workloads, and runs until interrupted or terminated.

## Prerequisites and limitations

A functioning NVIDIA driver must make `nvidia-smi` work, and the installed
PyTorch build must include CUDA support and report
`torch.cuda.is_available() == True`. A CPU-only PyTorch wheel, an incompatible
CUDA runtime/driver combination, a hidden device mask, or a missing driver can
all fail the CUDA check even when the `torch` import succeeds. Verify these
prerequisites before asking the user to opt in; do not install packages or
change environments as part of this skill.

The implementation does not validate that `gpu_id` exists before constructing
`cuda:<id>`; an invalid index can raise from PyTorch. It also does not validate
`interval`: zero causes a tight activity loop, and a negative value can make
`sleep` fail. Use a positive, conservative interval such as the default unless
the user has a documented reason to change it.

Signal handling is cooperative: the handlers only set `_running=False`; the
loop exits after the current operation/sleep returns. Cleanup is performed on
normal loop exit. An external hard kill, process crash, or exception before
cleanup can leave the process/context to the operating system; do not claim
cleanup occurred unless the stop log or process outcome confirms it.

## Stop and reporting procedure

- Send an interrupt or termination signal to the explicitly identified keeper
  process; do not kill unrelated training jobs.
- Wait for the process to exit, then inspect status read-only.
- Report the target GPU, interval, start/stop outcome, and any CUDA/import
  error. The keeper's activity should not be represented as training progress.
- If a training run needs the reserved device, stop the keeper first and
  re-check memory/utilization; the reserve-last policy alone does not stop it.

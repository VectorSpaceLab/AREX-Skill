# ChainerMN Troubleshooting

## `mpi4py` is missing

Symptoms:

- `create_communicator()` raises an import error.
- `../../scripts/chainermn_probe.py` reports `mpi4py=False`.

Recovery:

- Install MPI first.
- Install `mpi4py` against the same MPI implementation used by `mpiexec`.
- Re-run the probe before launching training.

## `mpiexec` or `mpicc` is missing

Symptoms:

- Launch commands fail before Python starts.
- The probe reports missing launcher or compiler commands.

Recovery:

- Install Open MPI, MPICH, or MVAPICH.
- Ensure the selected MPI implementation is first in `PATH`.
- Use `mpicc -show` and `mpiexec --version` to confirm the runtime.

## GPU communication fails

Symptoms:

- `pure_nccl` communicator creation fails.
- Workers crash when moving arrays between GPUs.
- NCCL import checks fail.

Recovery:

- Confirm CuPy is installed and `chainer.backends.cuda.available` is `True`.
- Confirm NCCL is enabled in CuPy.
- Use CUDA-aware MPI for high-performance GPU communication.
- Use `non_cuda_aware` or `naive` only when the performance trade-off is acceptable.

## Workers hang after an exception

MPI processes can hang if one Python worker raises an unhandled exception.
Recovery options:

- Launch with `python -m mpi4py yourscript.py`.
- Set `CHAINERMN_FORCE_ABORT_ON_EXCEPTION=1` when the code path supports it.
- Call `chainermn.global_except_hook.add_hook()` early in the script.

## Multiprocessing and InfiniBand crash

Symptoms:

- Training crashes or deadlocks when `MultiprocessIterator` creates child processes.

Recovery:

- Use `multiprocessing.set_start_method('forkserver')` or `spawn` before communicator creation.
- Create and join a tiny process before calling `chainermn.create_communicator()`.

## Epoch count is wrong

Symptoms:

- One "epoch" is not the same size as the original dataset.

Recovery:

- Scatter the dataset with `chainermn.scatter_dataset(...)`.
- Build each iterator from the rank-local shard.

## Output is duplicated on every rank

Symptoms:

- Multiple workers write repeated progress reports.

Recovery:

- Register console or file-output extensions only on `comm.rank == 0`.
- Wrap evaluation with `create_multi_node_evaluator(...)` when validation should be aggregated.

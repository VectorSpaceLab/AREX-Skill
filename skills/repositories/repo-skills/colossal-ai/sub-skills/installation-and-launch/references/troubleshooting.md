# Installation and Launch Troubleshooting

## Missing or wrong package

- `ModuleNotFoundError: colossalai`: install the `colossalai` distribution in the active environment.
- `please install Colossal-AI...` from direct source import: install the package instead of relying on `PYTHONPATH`.
- `colossalai` command missing: ensure the environment's scripts directory is on `PATH` or invoke through the environment manager.

## CUDA and extension issues

- CPU-only PyTorch: reinstall a CUDA-enabled PyTorch wheel that matches the driver.
- `CUDA_HOME` missing: only a blocker for AOT/source extension builds; not necessarily for PyTorch CUDA wheels.
- AOT build fails because torch is missing: install PyTorch before `BUILD_EXT=1`.
- Runtime extension compile fails: check compiler, toolkit version, PyTorch ABI, and GPU compute capability.

## Launch API errors

- Missing `RANK`/`WORLD_SIZE`: use `torchrun`/`colossalai run` for `launch_from_torch`, or call `launch` with explicit rank/world size.
- `invalid Python module` with `-m`: pass a module name, not a `.py` path.
- Missing script argument: `colossalai run` requires either `-m module` or a user script.
- Hostfile not found or duplicate host: validate the file path and ensure one unique hostname per non-empty line.
- `--include` and `--exclude` both set: choose only one filter.

## NCCL or networking failures

- Port collision: change `--master_port`.
- Processes disagree about rendezvous: verify every node uses the same `--master_addr`, `--master_port`, `--num_nodes`, and per-node process count.
- SSH or host connection failure: verify hostnames resolve, SSH ports are reachable, and user permissions match the cluster policy.
- Single process works but multi-GPU hangs: check visible GPU count, NCCL environment, driver/container passthrough, and topology sizes.

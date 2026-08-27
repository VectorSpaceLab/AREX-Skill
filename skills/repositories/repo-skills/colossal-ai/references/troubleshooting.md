# Cross-Cutting ColossalAI Troubleshooting

## Install and import failures

- `ModuleNotFoundError: colossalai`: install the `colossalai` distribution in the active Python environment.
- Windows setup failure: use Linux or WSL with compatible NVIDIA/CUDA support.
- Wrong Python or PyTorch version: verify Python, `torch.__version__`, and `torch.version.cuda`; match repository-supported PyTorch wheels before installing ColossalAI.
- `pip check` conflicts after installing app requirements: isolate app packages such as ColossalQA or ColossalChat in separate environments instead of mutating a core ColossalAI environment.

## CUDA and extension failures

- `torch.cuda.is_available() == False`: check GPU visibility, container runtime, driver, and whether the installed PyTorch wheel is CPU-only.
- `CUDA_HOME` or `nvcc` missing: only a blocker for AOT/source extension builds; not necessarily for PyTorch CUDA wheels.
- `no kernel image is available`: the installed binary or extension does not support the GPU compute capability. Use a newer supported CUDA/PyTorch wheel or rebuild against a compatible toolkit.
- Apex warning for fused RMSNorm: install Apex only if fused normalization is required; otherwise disable or avoid fused normalization flags.
- TensorNVMe warning for async save: install TensorNVMe only for async save/NVMe workflows. Ordinary checkpointing can use synchronous paths.

## Distributed launch failures

- `RANK`, `WORLD_SIZE`, `MASTER_ADDR`, or `MASTER_PORT` missing: call `colossalai.launch_from_torch()` only inside `torchrun` or `colossalai run`, or pass explicit rank/world size to `colossalai.launch(...)`.
- Port in use: set `--master_port` on `colossalai run` or `torchrun`, or choose a free port for `colossalai.launch(...)`.
- NCCL hang or timeout: check that every process uses the same master address/port/world size, that each process sees the intended GPU, and that network/firewall/IB settings match the cluster.
- Hostfile errors: hostfile lines are hostnames only; `--include` and `--exclude` are mutually exclusive and must name hosts present in the hostfile.

## Safe debug order

1. Run `python scripts/check_colossalai_environment.py --check-cli`.
2. If distributed state is needed, run a one-process `torchrun --standalone --nproc_per_node=1` smoke before scaling out.
3. Validate plugin/topology choices with helper scripts before launching training.
4. Add model weights, datasets, optional fused kernels, and services only after the core import/launch path is healthy.

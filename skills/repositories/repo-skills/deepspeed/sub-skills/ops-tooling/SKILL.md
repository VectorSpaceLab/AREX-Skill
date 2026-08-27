---
name: ops-tooling
description: "Diagnose DeepSpeed installs, build/JIT flags, CLI tools,
  autotuning, profiling, monitoring, DeepNVMe/GDS utilities, compression APIs,
  and repo policy checks safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepSpeed Ops Tooling

Use this sub-skill when an agent needs to inspect or explain DeepSpeed operational tooling rather than author a training loop, inference kernel injection, or parallelism design.

## Use For

- Installation and compatibility diagnosis with `ds_report` or `python -m deepspeed.env_report`.
- Build planning for JIT versus prebuilt ops, `DS_BUILD_*` flags, CUDA toolkit matching, optional extras, and `TORCH_EXTENSIONS_DIR` caching.
- Installed tool discovery for `deepspeed`, `ds`, `ds_report`, `ds_io`, `ds_nvme_tune`, and other safe CLI help checks.
- Autotuning launch planning, FLOPS profiler setup, monitor backend configuration, DeepNVMe/AIO/GDS guardrails, and compression API routing.
- DeepSpeed repo policy diagnostics such as CUDA/distributed import bans, license headers, and package index safety.

## Do Not Use For

- Training-loop JSON ownership or ZeRO/offload choices; route to `training-config`.
- Inference injection policies, tensor-parallel inference kernels, or Triton inference details; route to `inference-injection`.
- Pipeline/model parallel architecture or MoE expert design; route to `parallelism-moe`.

## Start Here

1. Run the bundled safe checker before destructive or long-running tooling:
   ```bash
   python scripts/check_deepspeed_tools.py
   ```
2. Use [CLI Reference](references/cli-reference.md) to choose the right installed tool and identify commands that only print help versus commands that run jobs or write storage.
3. Use [Workflows](references/workflows.md) for install triage, autotuning, profiling, monitors, DeepNVMe, and compression setup.
4. Use [Troubleshooting](references/troubleshooting.md) for common failures and safety gates.

## Safety Defaults

- Prefer read-only inspection: `--help`, imports, config parsing, and `ds_report` before running builds or I/O benchmarks.
- Treat `ds_io`, `ds_nvme_tune`, DeepNVMe write APIs, and GDS examples as potentially destructive unless the user explicitly provides a scratch directory and confirms writes.
- Treat autotuning as a real job launcher: it can start many training experiments and consume cluster GPUs.
- Never run `ds_ssh` or remote launch commands without explicit hostfile, SSH, and user approval.

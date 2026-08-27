# CLI Reference

This reference summarizes operational DeepSpeed commands and which ones are safe for routine diagnostics.

## Safe First Checks

- `python scripts/check_deepspeed_tools.py`: bundled skill helper that locates common DeepSpeed tools, runs selected `--help` commands with timeouts, and imports selected APIs without building ops or touching NVMe.
- `ds_report`: prints DeepSpeed op installed/compatible status plus general environment information. It is the fastest install triage entry point.
- `python -m deepspeed.env_report --hide_operator_status`: prints general environment information while suppressing the op compatibility table.
- `deepspeed --help`, `ds --help`, `ds_report --help`: safe CLI shape checks.

## Installed Scripts

`setup.py` installs different script sets by platform. On Linux the operational scripts include:

- `deepspeed`: distributed launcher entrypoint.
- `ds`: launcher alias.
- `ds_report`: environment and op compatibility report.
- `ds_bench`: benchmarking helper; inspect help before use.
- `ds_elastic`: elastic training helper.
- `dsr`: runner helper when installed.
- `ds_io`: DeepNVMe/AIO I/O benchmark; writes or reads files and must be safety-gated.
- `ds_nvme_tune`: DeepNVMe parameter sweep; writes benchmark files and can flush page cache.
- `ds_ssh`: remote execution helper; never run without explicit remote-execution approval.

## Launcher Flags

Use `deepspeed --help` or `ds --help` to inspect the full launcher syntax. Important operational flags include:

- `--hostfile`, `--include`, `--exclude`, `--num_nodes`, and `--num_gpus` for resource selection.
- `--master_port`, `--master_addr`, `--node_rank`, `--launcher`, and `--launcher_args` for distributed launch plumbing.
- `--no_ssh`, `--no_ssh_check`, `--force_multi`, and `--ssh_port` for multi-node SSH behavior.
- `--enable_each_rank_log` and `--save_pid` for operational observability.
- `--autotuning tune|run` for DeepSpeed autotuner integration.
- `--bind_cores_to_rank` and `--bind_core_list` for CPU core binding.

## `ds_report` and `deepspeed.env_report`

`ds_report` executes `deepspeed.env_report` and reports:

- C++/CUDA extension op installed status.
- Op compatibility status for JIT builds.
- `ninja` availability for JIT compilation.
- Torch, DeepSpeed, accelerator, wheel build, CUDA/HIP/CANN, and shared-memory details.

Useful options:

```bash
ds_report --hide_operator_status
ds_report --hide_errors_and_warnings
python -m deepspeed.env_report --hide_operator_status
```

Interpretation notes:

- `installed [NO]` plus `compatible [OKAY]` usually means the op can be JIT-built at first use.
- `compatible [NO]` means a dependency or accelerator/toolkit precondition is missing.
- Missing `ninja` blocks JIT extension builds.
- Missing `CUDA_HOME` or `nvcc` indicates the CUDA toolkit is not discoverable for CUDA op builds.

## Build and JIT Flags

DeepSpeed can JIT-build ops at runtime or prebuild selected ops at install time.

Common environment flags:

- `DS_BUILD_OPS=1`: attempt all compatible ops during installation.
- `DS_BUILD_AIO=1`: prebuild async I/O for DeepNVMe.
- `DS_BUILD_FUSED_ADAM=1`, `DS_BUILD_FUSED_LAMB=1`, `DS_BUILD_CPU_ADAM=1`, and related `DS_BUILD_*` flags: prebuild individual ops.
- `TORCH_CUDA_ARCH_LIST="7.5;8.0;8.6"`: restrict CUDA architectures for faster/more targeted builds.
- `TORCH_EXTENSIONS_DIR=...`: isolate JIT extension cache per environment.
- `DS_SKIP_CUDA_CHECK=1`: bypass CUDA version checks only when the user accepts compatibility risk.

Use prebuild flags when repeatability and startup latency matter. Prefer JIT when installing quickly or when the exact runtime environment is not yet known.

## DeepNVMe Tools

`ds_io` exposes AIO and torch I/O benchmark/test options. Its parser requires a folder mapping plus an I/O size, and defaults to write mode unless `--read` is given. Treat it as unsafe until the user confirms a scratch target.

Important `ds_io` options:

- `--folder` or `--folder_to_device_mapping`: target directory/directories.
- `--io_size`, `--block_size`, `--queue_depth`, `--loops`, `--warmup_loops`: benchmark dimensions.
- `--read`: read instead of default write.
- `--gpu`, `--use_gds`: GPU/GDS transfer modes.
- `--engine aio_handle|aio_basic|torch_io|torch_fast_io`: I/O backend.
- `--validate`: verify transfers.

`ds_nvme_tune` sweeps DeepNVMe parameters and writes logs/results. Before showing a runnable command or executing it:

- Confirm the path is scratch storage and may be written/deleted.
- Avoid `--flush_page_cache` unless sudo use is explicitly approved.
- Avoid `--gds` unless GDS is installed and GPU-device I/O is intended.
- Bound `--io_size`, `--loops`, and sweep configuration for shared systems.

Template only after approval:

```bash
ds_nvme_tune --nvme_dir /scratch/nvme --io_size 400M
```

## Repo Policy Diagnostics

DeepSpeed source evidence includes policy checks for maintainer work: accelerator-abstraction usage, avoiding direct `torch.distributed` imports in favor of `deepspeed.comm`, SPDX/`DeepSpeed Team` headers, and package-index safety. Those original repository scripts are not bundled as runtime helpers in this skill, so do not tell users to run source-checkout `scripts/...` paths from this generated skill.

For maintainer edits in a live DeepSpeed checkout, follow the repository's current contributor instructions and run the checkout's configured pre-commit hooks against changed files. For generated skill scripts, preserve the same policy in prose: use DeepSpeed communication abstractions, include required headers in new Python files, and avoid unsafe package-index flags.

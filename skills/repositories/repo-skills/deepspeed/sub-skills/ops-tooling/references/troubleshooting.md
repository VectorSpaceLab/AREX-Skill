# Troubleshooting

This guide maps common DeepSpeed ops/tooling symptoms to safe diagnostic actions.

## `ds_report` Shows Missing Ops

Interpret rows independently:

- `installed [NO]`, `compatible [OKAY]`: the op was not prebuilt but may JIT-build at first use.
- `installed [NO]`, `compatible [NO]`: missing prerequisites prevent both prebuild and JIT use.
- `ninja [FAIL]`: install `ninja` before relying on JIT extension loading.
- `async_io compatible [NO]`: often missing `libaio` headers/libraries; install the system development package or point `CFLAGS`/`LDFLAGS` at a custom install.
- `gds compatible [NO]`: confirm NVIDIA GDS installation and compatible GPU/storage stack.

Do not fix by setting every `DS_BUILD_*` flag blindly. First identify the specific op needed by the workload.

## CUDA Toolkit and `nvcc` Failures

Symptoms include missing `CUDA_HOME`, missing `nvcc`, or CUDA version mismatch during import/build checks.

Safe response:

1. Compare Torch CUDA version with the system toolkit version reported by `nvcc --version`.
2. Ensure the CUDA toolkit, not only runtime libraries, is installed when compiling CUDA ops.
3. Set `CUDA_HOME` only to a real toolkit root containing `bin/nvcc`.
4. Prefer matching major and minor CUDA versions when building wheels.
5. Use `DS_SKIP_CUDA_CHECK=1` only after warning that mismatched CUDA versions can cause build or runtime errors.

## Slow or Unsafe Builds

DeepSpeed source installs are quick in default JIT mode but slow when prebuilding all ops.

Mitigations:

- Prebuild only needed ops with focused `DS_BUILD_*` flags.
- Use build parallelism such as `build_ext -jN` only after confirming available CPU/memory.
- Set `TORCH_CUDA_ARCH_LIST` to known target architectures to avoid broad CUDA compilation.
- Use a unique `TORCH_EXTENSIONS_DIR` per environment to avoid stale cache reuse.
- Avoid building all ops on shared/login nodes unless explicitly approved.

## Optional Extras Missing

Autotuning model-based modes may require extra packages such as `tabulate` and optional ML tuner dependencies. Monitor backends may require `tensorboard`, `wandb`, or `comet_ml` packages. Compression examples may require task-specific model libraries.

When extras are missing:

- Recommend the narrow extra or package needed for the selected feature.
- Avoid broad reinstall instructions unless the environment is disposable.
- Re-run a safe import/help check before launching jobs.

## Autotuning Launch Surprises

Autotuning is not a dry-run parser. It launches experiments and writes result directories.

Warn when:

- The user chooses `--autotuning run` instead of `--autotuning tune`.
- `fast` is false, model-based tuning is selected, or trial counts are high.
- Results and experiment directories are on shared or quota-limited storage.
- Multi-node resource flags differ from the base training command.

If the base training command fails without autotuning, fix that first.

## FLOPS Profiler Confusion

Common issues:

- Output differs between training and inference because mode, precision, and batch size differ.
- Distributed runs report per-GPU values; model parallel size affects model-level totals.
- `output_file` paths silently write to the current process context when not absolute to the user's intended run directory.
- Custom modules may need smaller inputs or ignored modules to isolate failures.

Start with `get_model_profile` on a tiny representative input and increase detail only after the forward path works.

## Monitor Credentials and Outputs

TensorBoard and CSV are local-output friendly. WandB and Comet can require credentials, network access, and project/team naming.

Dry-run guidance:

1. Keep `wandb.enabled` and `comet.enabled` false while validating the DeepSpeed config shape.
2. Use `csv_monitor` or `tensorboard` with a user-approved local output directory for offline validation.
3. Use WandB/Comet offline modes only when the user confirms the installed backend supports the requested mode and where local logs should be stored.
4. Enable online WandB/Comet only after the user provides credentials through their normal secure environment and confirms network/project settings.

Do not:

- Put API keys or tokens in examples, config snippets, shell history, or generated files.
- Invent teams, project names, workspace names, or experiment names.
- Enable online backends in restricted environments without approval.
- Write logs to source or skill directories.

Prefer CSV/TensorBoard local logs when the user only wants operational observability.

## DeepNVMe, AIO, and GDS Safety

Treat these as storage-writing tools unless proven otherwise.

Before `ds_io`, `ds_nvme_tune`, `sync_pwrite`, `async_pwrite`, or GDS writes:

1. Ask for a scratch directory that can be overwritten.
2. Confirm desired data size, loops, GPU/GDS mode, and whether reads or writes are intended.
3. Avoid `--flush_page_cache` unless the user explicitly approves sudo/system cache effects.
4. Keep initial `io_size` small on shared systems.
5. For async APIs, call `wait()` before reusing tensors or files.

Skip AIO/GDS benchmarks when the task only asks to interpret `ds_report` or plan configuration.

## `ds_ssh` and Remote Execution

`ds_ssh` can execute commands on remote hosts. Do not run it as part of routine diagnostics. Require explicit user approval, host targets, expected command, and rollback/cleanup plan.

## Repo Policy Check Failures

DeepSpeed maintainer policy evidence includes checks for direct CUDA/distributed imports, required headers, and package-index usage. This generated skill does not bundle those original policy scripts, so do not instruct users to run source-checkout `scripts/...` paths from runtime guidance.

When editing a live DeepSpeed checkout:

- Replace direct `torch.cuda` and `.cuda()` usage with accelerator abstraction unless the code is intentionally CUDA-specific and allowed by the current repo policy.
- Use `import deepspeed.comm as dist` instead of direct `torch.distributed` imports in DeepSpeed code.
- Add `SPDX-License-Identifier: Apache-2.0` and `DeepSpeed Team` headers to new Python files when the current repo policy requires them.
- Prefer safer package-index flags according to the current repository checks.
- Run the checkout's configured pre-commit hooks only on changed files unless the user asks for a broad audit.

# Troubleshooting

Use this cross-cutting reference for DeepSpeed failures that span multiple sub-skills. Workflow-specific fixes live in each sub-skill's `references/troubleshooting.md`.

## Import Fails During Op Compatibility Probing

Symptoms:

- `MissingCUDAException: CUDA_HOME does not exist, unable to compile CUDA op(s)`
- Import succeeds in CPU environments but fails after installing a CUDA PyTorch wheel.
- `ds_report` reports missing compatible ops or missing build dependencies.

Likely causes:

- A CUDA driver is present, but the local CUDA toolkit or `nvcc` is not available.
- PyTorch CUDA wheel, driver, and toolkit versions do not line up for op building.
- A build flag requested prebuilt ops in an environment that can only use JIT or CPU inspection.

Recovery:

1. For config/API inspection, use a CPU-compatible PyTorch install or disable prebuild requests.
2. For real CUDA workflows, install a toolkit matching the PyTorch CUDA stack or use a documented wheel/build route.
3. Run `ds_report` before launching jobs and route build issues to `sub-skills/ops-tooling/`.

## Launcher Fails Before User Script Runs

Symptoms:

- Hostfile is missing or malformed.
- `--include` and `--exclude` conflict.
- `--num_nodes`/`--num_gpus` are combined with explicit resource filters.
- CPU-only environments fail local resource discovery.

Recovery:

- Use `sub-skills/training-config/scripts/launcher_resource_preview.py` to validate filters without launching.
- For multi-node no-SSH launches, each node needs consistent `--node_rank`, `--master_addr`, and `--master_port` arguments.
- Do not rely on visible-device environment variables when explicit resource filters are supplied.

## Config Validation Fails

Symptoms:

- Batch size assertion or unexpected inferred values.
- Duplicate JSON keys silently overriding earlier values.
- Deprecated aliases work in old configs but confuse new guidance.

Recovery:

- Use `sub-skills/training-config/scripts/validate_ds_config.py --world-size <ranks> ds_config.json`.
- Specify any two of `train_batch_size`, `train_micro_batch_size_per_gpu`, and `gradient_accumulation_steps`; let DeepSpeed infer the third.
- Prefer current field names, especially for ZeRO-3 gather/export and offload settings.

## Optional Tool Would Mutate Infrastructure

Symptoms:

- User asks to run `ds_io`, `ds_nvme_tune`, autotuning, `ds_ssh`, prebuilt op install, or remote launch.
- Command writes benchmark files, starts many jobs, compiles extensions, or executes across hosts.

Recovery:

- Route to `sub-skills/ops-tooling/`.
- Ask for explicit scratch paths, time limits, hostfile/SSH approval, backend details, and cleanup expectations before running.
- Prefer `--help`, config parsing, or a bounded dry-run-style check first.

## Model Download or Credential Surprise

Symptoms:

- Inference, monitor, hybrid-engine, or sequence-parallel examples try to download models or contact online services.
- WandB/Comet requests credentials or starts online logging.

Recovery:

- Treat downloads and online logging as opt-in.
- Use local tiny fixtures or config-only inspections for verification.
- Route inference model-loading questions to `sub-skills/inference-injection/` and monitor backend questions to `sub-skills/ops-tooling/`.

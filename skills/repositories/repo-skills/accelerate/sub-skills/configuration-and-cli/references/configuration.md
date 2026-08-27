# Accelerate Configuration Files

Accelerate reads launch defaults from a YAML or JSON config file. The default file is named `default_config.yaml` under the Accelerate cache directory: `$HF_HOME/accelerate` when `HF_HOME` is set, otherwise `$XDG_CACHE_HOME/huggingface/accelerate`, otherwise `~/.cache/huggingface/accelerate`. Prefer an explicit `--config_file path/to/config.yaml` in reproducible scripts and CI.

## Creation and Updates

- `accelerate config` starts an interactive questionnaire and writes a config file. Use `--config_file` to choose a non-default location.
- `accelerate config default --config_file path.yaml --mixed_precision no|fp16|bf16` writes a minimal default config without the interactive questionnaire.
- `accelerate config update --config_file path.yaml` loads an existing config and rewrites it with current defaults while preserving recognized values.
- `accelerate env --config_file path.yaml` prints environment and config details for debugging and issue reports.
- `accelerate test --config_file path.yaml` launches Accelerate's built-in distributed smoke script with the selected config.

## Top-Level Schema

Local-machine configs are represented by Accelerate's cluster config dataclass. Known top-level keys include:

- Required or core: `compute_environment`, `distributed_type`, `mixed_precision`, `use_cpu`, `debug`.
- Process placement: `num_processes`, `num_machines`, `machine_rank`, `gpu_ids`, `main_process_ip`, `main_process_port`, `rdzv_backend`, `same_network`, `main_training_function`, `enable_cpu_affinity`.
- Backend dictionaries: `deepspeed_config`, `fsdp_config`, `parallelism_config`, `megatron_lm_config`, `mpirun_config`, `fp8_config`, `dynamo_config`.
- TPU and remote command fields: `downcast_bf16`, `tpu_name`, `tpu_zone`, `tpu_use_cluster`, `tpu_use_sudo`, `command_file`, `commands`, `tpu_vm`, `tpu_env`.

SageMaker configs use `compute_environment: AMAZON_SAGEMAKER` and add keys such as `ec2_instance_type`, `iam_role_name`, `image_uri`, `profile`, `region`, `num_machines`, `gpu_ids`, `base_job_name`, `pytorch_version`, `transformers_version`, `py_version`, `sagemaker_inputs_file`, `sagemaker_metrics_file`, `additional_args`, `dynamo_config`, and `enable_cpu_affinity`. Do not invent arbitrary top-level keys; Accelerate rejects unknown keys when loading configs.

## Common Local Templates

Minimal CPU or single-process debug config:

```yaml
compute_environment: LOCAL_MACHINE
distributed_type: 'NO'
mixed_precision: 'no'
use_cpu: true
debug: false
num_processes: 1
num_machines: 1
machine_rank: 0
rdzv_backend: static
same_network: true
```

Two-process single-node multi-GPU config:

```yaml
compute_environment: LOCAL_MACHINE
distributed_type: MULTI_GPU
mixed_precision: fp16
use_cpu: false
debug: false
num_processes: 2
num_machines: 1
machine_rank: 0
gpu_ids: all
main_process_ip: null
main_process_port: null
rdzv_backend: static
same_network: true
```

Two-node template. Copy it to every node and change only `machine_rank` per node unless using a launcher such as SLURM that injects rank values:

```yaml
compute_environment: LOCAL_MACHINE
distributed_type: MULTI_GPU
mixed_precision: no
use_cpu: false
debug: false
num_processes: 8
num_machines: 2
machine_rank: 0
main_process_ip: 10.0.0.5
main_process_port: 29500
rdzv_backend: static
same_network: true
```

## Validation Rules

- `distributed_type` must be present. For non-distributed runs use `NO`; Accelerate can default `num_processes` to `1` for `NO`.
- `compute_environment` defaults to `LOCAL_MACHINE` if omitted, but include it explicitly in reusable templates.
- `mixed_precision` should be `no`, `fp16`, `bf16`, or `fp8` for launch. `config default` only exposes `no`, `fp16`, and `bf16`.
- Do not combine CPU mode with a distributed accelerator type. Use `distributed_type: 'NO'` plus `use_cpu: true` for CPU-only testing.
- For single-machine configs, keep `num_machines: 1`, `machine_rank: 0`, and usually `main_process_ip: null` / `main_process_port: null`.
- For multi-node configs, set total `num_processes` across all machines, not per-node processes. Use `machine_rank` values from `0` to `num_machines - 1`.
- If `num_processes: -1` appears in a config, launch requires a manual `--num_processes` override.
- Keep backend-specific dictionaries in their own nested keys. Route details of `deepspeed_config`, `fsdp_config`, TPU, Megatron-LM, and parallelism to the distributed-backends sub-skill.

## Safe Editing Workflow

1. Copy an existing working config or start with a minimal template.
2. Run `python scripts/validate_accelerate_config.py path/to/config.yaml` from this sub-skill to catch syntax, unknown top-level keys, and common conflicts.
3. Run `accelerate env --config_file path/to/config.yaml` to confirm Accelerate itself can load the config.
4. Run `accelerate test --config_file path/to/config.yaml` only when it is safe to start local subprocesses on the target machine.

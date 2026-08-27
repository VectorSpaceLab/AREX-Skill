# Distributed and Logging

This reference covers v0 train launch orchestration and observability. It focuses on commands and config keys; do not run distributed jobs unless the user explicitly asks and the hardware/network are ready.

## Launcher Behavior

`llamafactory-cli train` runs directly unless one of these conditions triggers distributed launch:

- `FORCE_TORCHRUN=1` is set.
- More than one device is visible and Ray/KTransformers paths are not active.
- `USE_MCA=1` is set, which forces `FORCE_TORCHRUN=1` for Megatron Core Adapter flows.

When distributed launch is triggered, LlamaFactory calls `torchrun` with environment-derived values and then runs the same training module under torchrun.

## Single-Node Multi-GPU

```bash
FORCE_TORCHRUN=1 NPROC_PER_NODE=8 \
  llamafactory-cli train train.yaml
```

Useful variables:

- `FORCE_TORCHRUN=1`: force the launcher to wrap training with `torchrun`.
- `NPROC_PER_NODE`: number of worker processes on this node; defaults to detected device count.
- `MASTER_ADDR`: rendezvous host; defaults to `127.0.0.1`.
- `MASTER_PORT`: rendezvous port; defaults to an available port chosen by the launcher.
- `OPTIM_TORCH=1`: default-enabled optimization path that sets `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` and `TORCH_NCCL_AVOID_RECORD_STREAMS=1` inside the torchrun environment.

## Multi-Node Static Launch

Run the same config on each node with a distinct `NODE_RANK` and shared master address/port:

```bash
# node 0
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=0 NPROC_PER_NODE=8 \
  MASTER_ADDR=192.168.0.1 MASTER_PORT=29500 \
  llamafactory-cli train train.yaml

# node 1
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=1 NPROC_PER_NODE=8 \
  MASTER_ADDR=192.168.0.1 MASTER_PORT=29500 \
  llamafactory-cli train train.yaml
```

Checklist:

- Every node must use the same config, model access, dataset access, code version, and package versions.
- `MASTER_ADDR` must be reachable from all nodes.
- `MASTER_PORT` must be open and unused.
- `NODE_RANK` starts at `0` and increments by node.
- Set a large `ddp_timeout` in the training config for slow model/dataset initialization.

## Elastic Launch

If `RDZV_ID` is set, the launcher uses torchrun rendezvous flags:

```bash
FORCE_TORCHRUN=1 MIN_NNODES=1 MAX_NNODES=3 MAX_RESTARTS=3 \
  RDZV_ID=llamafactory-job MASTER_ADDR=192.168.0.1 MASTER_PORT=29500 \
  llamafactory-cli train train.yaml
```

- `RDZV_ID` must be shared by participating nodes and unique per job.
- `MIN_NNODES` and `MAX_NNODES` create an elastic node range.
- `MAX_RESTARTS` controls fault-tolerant restarts.

## DeepSpeed

DeepSpeed is usually selected inside the train config:

```yaml
deepspeed: path/to/ds_z3_config.json
```

For a self-contained user config, copy or create a DeepSpeed JSON next to the user's config and point `deepspeed` at that local file. Common choices:

- ZeRO-0: minimal sharding, easiest debugging.
- ZeRO-2: optimizer/gradient sharding.
- ZeRO-3: parameter, optimizer, and gradient sharding; common for full fine-tuning or larger LoRA jobs.
- Offload variants: lower GPU memory, more CPU/NVMe pressure.

A compact ZeRO-3 shape is:

```json
{
  "train_batch_size": "auto",
  "train_micro_batch_size_per_gpu": "auto",
  "gradient_accumulation_steps": "auto",
  "gradient_clipping": "auto",
  "zero_allow_untested_optimizer": true,
  "bf16": {"enabled": "auto"},
  "fp16": {"enabled": "auto", "loss_scale": 0},
  "zero_optimization": {
    "stage": 3,
    "overlap_comm": false,
    "contiguous_gradients": true,
    "stage3_gather_16bit_weights_on_model_save": true
  }
}
```

Prefer `FORCE_TORCHRUN=1` when using DeepSpeed examples, even for one node.

## FSDP and Accelerate

Accelerate/FSDP examples use a separate Accelerate YAML with fields such as:

- `distributed_type: FSDP`.
- `num_machines`, `num_processes`, `machine_rank`, `main_process_ip`, `main_process_port`.
- `fsdp_config.fsdp_sharding_strategy`, `fsdp_auto_wrap_policy`, `fsdp_state_dict_type`, and related settings.

For multi-node FSDP, all nodes need consistent `main_process_ip`, `main_process_port`, total `num_processes`, and distinct `machine_rank`. If a user asks for FSDP conversion, preserve the train config separately from the Accelerate launch config.

## Ray

Ray is opt-in via environment:

```bash
USE_RAY=1 llamafactory-cli train train_ray.yaml
```

Config keys include:

```yaml
ray_num_workers: 4
ray_init_kwargs:
  runtime_env:
    env_vars:
      EXAMPLE_ENV: value
    pip:
      - emoji
```

Use Ray when the user already has a Ray-capable environment. Do not imply Ray is required for ordinary multi-GPU training; torchrun is the default route.

## MCA and HyperParallel

- `USE_MCA=1` enables Megatron Core Adapter argument classes and forces torchrun. It requires `mcore_adapter` and is only for selected `pt`, `sft`, and `dpo` paths.
- `use_hyper_parallel: true` dispatches `pt` or `sft` into HyperParallel when installed. It is intended for supported full-parameter distributed setups.

Route v1-only distributed YAMLs to `v1-experimental`.

## Experiment Logging

Common config keys:

```yaml
logging_steps: 10
plot_loss: true
report_to: none
run_name: debug-sft
```

`report_to` is inherited from Hugging Face Trainer and examples show `none`, `wandb`, `tensorboard`, `swanlab`, and `mlflow`. The Web UI also exposes `neptune`, `trackio`, and `all`.

Recommended defaults:

- Use `report_to: none` for smoke tests, reproductions, and examples without credentials.
- Use `run_name` when enabling any external tracker.
- Keep tracker API keys out of YAML when sharing configs.

### Trackio

When `trackio` is in `report_to`, parser validation requires `project`:

```yaml
report_to: trackio
project: my-project
trackio_space_id: org/space
run_name: run-001
```

If `trackio_space_id` is not `trackio` and lacks `/`, LlamaFactory warns that an `org/space` style id is typical.

### SwanLab

SwanLab uses finetuning args rather than only `report_to`:

```yaml
use_swanlab: true
swanlab_project: llamafactory
swanlab_workspace: my-workspace
swanlab_run_name: qwen3-lora-sft
swanlab_mode: cloud
```

`SwanLab` callbacks are added at train startup when `use_swanlab: true`. Avoid embedding `swanlab_api_key` in reusable configs.

## Profiling and Throughput

Trainer extensions include:

```yaml
enable_torch_profiler: true
profiler_output_dir: profiler
profiler_wait_steps: 1
profiler_warmup_steps: 1
profiler_active_steps: 1
profiler_repeat: 1
profile_modules: model.layers.0.self_attn,model.layers.*.mlp
include_effective_tokens_per_second: true
```

Only enable profiling for short, intentional runs; profiler traces can be large and slow training.

## FP8

FP8 keys are trainer arguments:

```yaml
fp8: true
fp8_backend: torchao
fp8_enable_fsdp_float8_all_gather: true
```

FP8 requires compatible PyTorch, Accelerate, backend packages, and Hopper-class or otherwise supported hardware. If FP8 was requested but not active, check backend compatibility before changing model/data settings.

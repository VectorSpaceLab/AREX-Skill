# Ray and Megatron-SWIFT Workflows

This reference covers `megatron` CLI usage, Ray orchestration, Mcore-Bridge, and distributed hardware choices for advanced ms-swift training. Use it for Megatron GRPO/GKD/RLHF, Ray GPU group placement, and parallelism debugging.

## Optional Stack First

Megatron-SWIFT is optional. A minimal ms-swift environment may support `swift rlhf --help` and `swift sample --help` while `megatron sft --help` fails because Megatron dependencies are missing. Before planning a Megatron or Ray job, check the stack with `scripts/check_optional_backends.py`.

Typical optional components:

- `ms-swift[megatron]` for the Megatron route and declared extras.
- `mcore-bridge` for safetensors/MCore model loading and simplified Megatron training.
- `megatron-core`, `transformer-engine`, optional `apex`, and compatible `flash-attn` for CUDA Megatron execution.
- `ray` for `megatron rlhf --use_ray true` YAML orchestration.
- `vllm` for GRPO/GKD rollout acceleration and server/colocate modes.

Do not hide missing optional dependencies as generic import failures. State which workflow is blocked and which optional backend is needed.

## Megatron CLI Shape

The `megatron` console script routes subcommands such as `sft`, `pt`, `rlhf`, and `export`. For RL work, use:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
NPROC_PER_NODE=4 \
MASTER_PORT=29600 \
megatron rlhf \
  --rlhf_type grpo \
  --model <model-id-or-path> \
  --dataset <dataset> \
  --tensor_model_parallel_size 1 \
  --pipeline_model_parallel_size 1 \
  --context_parallel_size 1 \
  --micro_batch_size 2 \
  --global_batch_size 32 \
  --steps_per_generation 4 \
  --num_generations 8 \
  --reward_funcs <reward-name> \
  --use_vllm true \
  --vllm_mode colocate \
  --vllm_gpu_memory_utilization 0.6 \
  --max_length 4096 \
  --max_completion_length 1024 \
  --bf16 true \
  --recompute_granularity selective \
  --finetune true
```

The `megatron rlhf` route supports `dpo`, `kto`, `grpo`, `gkd`, and `rm`. Standard `swift rlhf` supports additional TRL algorithms such as PPO, CPO, SimPO, and ORPO; use the non-Megatron trainer if a Megatron equivalent is not available.

## Completion-Level Batch Math

Megatron GRPO uses completion-level batch sizes, not prompt-level batch sizes.

| Quantity | Formula |
| --- | --- |
| Data parallel size | `dp_size = world_size / (TP × PP × CP)` |
| Global batch size | `global_batch_size = micro_batch_size × dp_size × gradient_accumulation_steps` |
| Generation batch size | `generation_batch_size = global_batch_size × steps_per_generation` |
| Rollout prompt count | `generation_batch_size / num_generations` |
| Training prompt count | `global_batch_size / num_generations` |
| Prompts per DP group | `global_batch_size / num_generations / dp_size` |

Validation checks:

- `world_size` must be divisible by `tensor_model_parallel_size × pipeline_model_parallel_size × context_parallel_size`.
- `generation_batch_size` must be divisible by `num_generations`.
- `generation_batch_size / num_generations` must be divisible by `dp_size`.
- `global_batch_size / num_generations / dp_size` must be at least one and divisible by `micro_batch_size`.
- For REAL loss in Megatron GRPO, `micro_batch_size` must be a multiple of `num_generations`.

Use `scripts/build_rlhf_command.py --mode megatron-grpo` to generate a non-executing skeleton and inspect these formulas before launching.

## Parallelism Dimensions

| Dimension | Argument | Use For | Pitfalls |
| --- | --- | --- | --- |
| Tensor parallel | `--tensor_model_parallel_size` | Split matrix/tensor work within layers | Often pair `--sequence_parallel true` when TP > 1. |
| Pipeline parallel | `--pipeline_model_parallel_size` | Split layers across stages | Layer counts must fit PP or use first/last layer overrides or a custom layout. |
| Context parallel | `--context_parallel_size` | Split long sequence/context workload | Affects DP formula and may interact with padding-free and MLP padding-free behavior. |
| Expert parallel | `--expert_model_parallel_size` | MoE expert sharding | Requires model/expert count compatibility; inspect MoE config before setting. |
| Expert tensor parallel | `--expert_tensor_parallel_size` | Tensor parallelism inside experts | Coordinate with EP and TP memory goals. |
| Virtual pipeline | `--virtual_pipeline_model_parallel_size` | Reduce PP bubbles | Adds communication overhead and may require microbatch tuning. |
| Sequence parallel | `--sequence_parallel true` | Reduce activation memory with TP | Only meaningful with tensor parallelism. |

Other useful Megatron controls:

- `--recompute_granularity selective|full|none`, `--recompute_modules`, `--recompute_method`, and `--recompute_num_layers` trade compute for memory.
- `--attention_backend flash|fused|unfused|auto|flash_2|flash_3|flash_4` must match installed attention kernels and model support.
- `--gradient_accumulation_fusion false` can work around missing `apex` in some setups.
- `--optimizer_cpu_offload true` and precision-aware optimizer arguments reduce GPU optimizer memory at CPU cost.
- `--no_save_optim true --no_save_rng true` reduce checkpoint size/time when restartability is less important.

## Mcore-Bridge Choices

Mcore-Bridge lets Megatron-SWIFT train directly from safetensors-style model paths using `--model`, `--adapters`, `--ref_model`, and `--ref_adapters`. MCore-native checkpoint arguments remain available:

- `--mcore_model` / `--mcore_adapter` load MCore-format checkpoints.
- `--mcore_ref_model` / `--mcore_ref_adapter` load reference model/adapters for DPO/GRPO/KTO.
- `--save_safetensors true` writes safetensors outputs; when optimizer state is saved, MCore checkpoint material may also be written for resume.
- `--to_mcore true` and `--to_hf true` are export routes, not training modes.

Use Mcore-Bridge when the model is supported and you want to avoid manual HF↔MCore conversion. Fall back to explicit `swift export --to_mcore true` or `megatron export` only when conversion precision, unsupported model integration, or checkpoint format requirements demand it.

## Megatron GRPO Rollout Modes

Megatron GRPO supports vLLM colocate and server modes.

Colocate pattern:

```bash
megatron rlhf \
  --rlhf_type grpo \
  --use_vllm true \
  --vllm_mode colocate \
  --vllm_gpu_memory_utilization 0.6 \
  --sleep_level 2 \
  --offload_model true \
  --offload_optimizer true \
  --offload_bridge false \
  --reward_funcs <reward-name> \
  ...
```

Server pattern:

```bash
swift rollout \
  --model <model-id-or-path> \
  --vllm_tensor_parallel_size 2 \
  --vllm_data_parallel_size 1 \
  --port 8000

megatron rlhf \
  --rlhf_type grpo \
  --use_vllm true \
  --vllm_mode server \
  --vllm_server_host 127.0.0.1 \
  --vllm_server_port 8000 \
  ...
```

Use server mode when training and inference need isolated GPUs, separate lifecycle management, or multi-node rollout servers. Use colocate mode for simpler single-node experiments when memory permits.

## Megatron GKD

Megatron GKD supports full and LoRA training, CP/PP/TP/EP, teacher offload, and student on-policy generation through vLLM.

Local teacher pattern:

```bash
megatron rlhf \
  --rlhf_type gkd \
  --model <student-model> \
  --teacher_model <teacher-model> \
  --dataset <dataset> \
  --gkd_logits_topk 64 \
  --beta 0.5 \
  --lmbda 1.0 \
  --use_vllm true \
  --vllm_mode colocate \
  --offload_teacher_model true \
  ...
```

Teacher-server pattern:

```bash
megatron rlhf \
  --rlhf_type gkd \
  --model <student-model> \
  --teacher_model_server http://localhost:8000 \
  --gkd_logits_topk 64 \
  --dataset <dataset> \
  ...
```

GKD limitations to surface:

- `teacher_model_server` requires `gkd_logits_topk`.
- `seq_kd true` teacher online generation is not currently supported in Megatron GKD and falls back to off-policy mode.
- On-policy generation requires vLLM; if `lmbda > 0` without vLLM, Megatron GKD falls back to off-policy dataset responses.
- Teacher model with different parallel parameters is a known limitation; keep teacher/student parallel dimensions aligned unless the current environment proves otherwise.

## Ray Megatron

Ray Megatron is functionally equivalent to non-Ray Megatron training for GRPO/GKD, but YAML declares GPU groups and Ray handles process creation and cross-node scheduling.

Launch shape:

```bash
ray start --head
# worker nodes: ray start --address=<head-ip>:6379
megatron rlhf --use_ray true --config <config.yaml>
```

### Colocate YAML Shape

Training and rollout share GPUs and alternate memory use:

```yaml
rlhf_type: grpo
model: <model-id-or-path>
dataset: <dataset>
reward_funcs: [accuracy, format]
micro_batch_size: 2
global_batch_size: 16
num_generations: 8
steps_per_generation: 4
use_vllm: true
colocate_groups: [[train, rollout]]
offload_model: true
offload_optimizer: true
sleep_level: 1
train:
  gpus: 4
  tensor_model_parallel_size: 1
  output_dir: megatron_output/ray_grpo_colocate
rollout:
  gpus: 4
  vllm_tensor_parallel_size: 1
  vllm_gpu_memory_utilization: 0.4
  vllm_max_model_len: 8192
```

Colocate requires train and rollout group GPU counts to match. Use lower vLLM memory utilization and offload controls when OOM occurs.

### Separate YAML Shape

Training and rollout use different GPUs:

```yaml
rlhf_type: grpo
model: <model-id-or-path>
dataset: <dataset>
reward_funcs: [accuracy, format]
micro_batch_size: 2
global_batch_size: 16
num_generations: 8
steps_per_generation: 4
use_vllm: true
train:
  gpus: 4
  tensor_model_parallel_size: 1
  output_dir: megatron_output/ray_grpo_separate
rollout:
  gpus: 4
  vllm_tensor_parallel_size: 1
  vllm_gpu_memory_utilization: 0.8
  vllm_max_model_len: 8192
```

Separate mode is easier to reason about and avoids memory contention, but requires more GPUs.

### Ray GKD Teacher Groups

For GKD, the teacher can be colocated with training or declared as a standalone group:

```yaml
rlhf_type: gkd
model: <student-model>
teacher_model: <teacher-model>
gkd_logits_topk: 64
lmbda: 1
use_vllm: true
colocate_groups: [[train, rollout]]
offload_teacher_model: true
train:
  gpus: 4
  tensor_model_parallel_size: 2
rollout:
  gpus: 4
  vllm_tensor_parallel_size: 2
```

A standalone teacher group is useful when the teacher should run as an independent vLLM inference engine on separate GPUs. It supports top-k distillation, while colocated teacher mode can support full-vocab and top-k depending on memory.

## Swift Ray Device Groups

The non-Megatron Ray helper can assign roles to device groups for supported workflows such as training and sampling. CLI `--device_groups` accepts a JSON string, but YAML is easier:

```yaml
device_groups:
  nproc_per_node: 4
  sample_group:
    device: GPU
    ranks: [0, 1]
    workers: [sampler]
  rm_group:
    device: GPU
    ranks: [2, 3]
    workers: [prm, orm]
```

Rules:

- `nproc_per_node` is the minimum number of GPUs per node needed by the Ray cluster.
- GPU `ranks` can be a list, an integer count, or `list(range(...))` in config contexts that support Python-like expressions.
- CPU ranks are a process count, not GPU IDs.
- Workers must match supported role names for the command; sampling/distill roles include `sampler`, `prm`, and `orm`.

## Multi-Node Environment Checklist

Before launching multi-node Megatron or Ray jobs:

- Set `NPROC_PER_NODE` to the local process/GPU count for non-Ray `megatron` commands.
- Set `MASTER_ADDR`, `MASTER_PORT`, `NNODES`, and `NODE_RANK` or the equivalent launcher variables when not using Ray-managed process startup.
- Keep `CUDA_VISIBLE_DEVICES` consistent with local rank expectations.
- Use a shared `MODELSCOPE_CACHE` and shared `output_dir` for multi-node Megatron jobs to avoid preprocessing inconsistency or checkpoint scattering.
- Prefer a unique `MASTER_PORT` per job on a shared machine.
- For NCCL issues, inspect `NCCL_*` environment, interconnect visibility, and firewall rules before changing training arguments.

## Hardware-Specific Notes

- CUDA Megatron stacks must align PyTorch, CUDA, Transformer Engine, Megatron-Core, FlashAttention, and mcore-bridge versions.
- If `apex` is missing and the failure mentions gradient accumulation fusion, try `--gradient_accumulation_fusion false` if the workflow tolerates it.
- Ascend/NPU workflows need the matching torch/NPU stack and may use `ASCEND_RT_VISIBLE_DEVICES` instead of `CUDA_VISIBLE_DEVICES`.
- FP8/FP4 routes require hardware and Transformer Engine support; do not enable them as generic memory fixes without confirming backend compatibility.

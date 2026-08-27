# Distributed Training

Axolotl is config-driven: the training YAML and launch command must agree on process count, sharding backend, and optional parallelism axes. Choose the topology before tuning method-specific fields.

## Launcher Decision Table

| Situation | Prefer | Axolotl shape | Notes |
| --- | --- | --- | --- |
| One node, model fits only when sharded | FSDP2 | `fsdp_version: 2` plus `fsdp_config` | Recommended default for new PyTorch-native sharded training. |
| Existing DeepSpeed workflow or ZeRO config | DeepSpeed | `deepspeed: deepspeed_configs/zero*.json` or an inline dict | Use one of the bundled Axolotl DeepSpeed JSONs or a reviewed local JSON. |
| Multi-node with one command from the head node | Ray Train | `use_ray: true`, `ray_num_workers: <gpus>` or `axolotl train ... --use-ray` | Requires a running Ray cluster and Ray installed in the user environment. |
| Multi-node with high-bandwidth network or HPC | `torchrun`/scheduler | `axolotl train config.yaml --launcher torchrun -- ...` | Pass rendezvous flags after `--`; set NCCL/network variables outside the YAML. |
| SLURM batch job | Scheduler launches torchrun/Axolotl | Scheduler directives plus the same Axolotl YAML | Keep cluster paths and modules in the job script, not in reusable skill content. |
| Long-context memory bottleneck | FSDP + context parallelism | `context_parallel_size: >1`, compatible attention backend | Effective data-parallel batch count is divided by `context_parallel_size`. |
| MoE expert memory bottleneck | Expert parallel plugin | `expert_parallel_size: >1`, optional `dp_shard_size`, plugin enabled | Requires DeepEP-capable hardware/software; route MoE model details to model-loading. |

## DeepSpeed

Use exactly one distributed sharding stack. A YAML with both `deepspeed` and `fsdp_config` is ambiguous and should be split into two candidate configs.

Axolotl-recognized DeepSpeed inputs:

- `deepspeed: deepspeed_configs/zero1.json` for ZeRO-1.
- `deepspeed: deepspeed_configs/zero2.json` for ZeRO-2.
- `deepspeed: deepspeed_configs/zero3.json` or `zero3_bf16.json` for ZeRO-3.
- CPU-offload variants for ZeRO-3: `zero3_bf16_cpuoffload_params.json` and `zero3_bf16_cpuoffload_all.json`.
- `zero1_torch_compile.json` and `zero2_torch_compile.json` when a DeepSpeed+compile experiment is intended.

Operational rules:

- Use `axolotl fetch deepspeed_configs` if a user needs the public DeepSpeed config bundle in their working directory.
- Prefer a config-path field in YAML for reproducibility; `axolotl train config.yml --deepspeed ...` is useful for quick experiments.
- Check the JSON `zero_optimization.stage` when a filename and stage expectation disagree.
- Treat CPU offload as a memory rescue that can be much slower and sensitive to CPU RAM, NUMA placement, and storage pressure.
- DeepSpeed and advanced N-D parallelism are not interchangeable. Axolotl docs recommend FSDP for N-D parallelism and note that DeepSpeed is only compatible with `tensor_parallel_size` among those axes.

## FSDP and FSDP2

For new work, prefer FSDP2:

```yaml
fsdp_version: 2
fsdp_config:
  auto_wrap_policy: TRANSFORMER_BASED_WRAP
  transformer_layer_cls_to_wrap: LlamaDecoderLayer
  state_dict_type: FULL_STATE_DICT
```

Key guidance:

- `fsdp_config` is the signal that FSDP is configured; `fsdp_version` alone is not enough.
- FSDP1-style `fsdp:` lists are deprecated. Convert to `fsdp_version: 2` plus `fsdp_config` fields such as `auto_wrap_policy`, `transformer_layer_cls_to_wrap`, `cpu_ram_efficient_loading`, `state_dict_type`, `final_state_dict_type`, `activation_checkpointing`, and `reshard_after_forward`.
- FSDP2 maps to ZeRO-style behavior through `reshard_after_forward`: false resembles ZeRO-2 memory behavior, true resembles ZeRO-3 with more communication and more parameter memory savings.
- `fp32_norms: true` requires real FSDP2 configuration: `fsdp_config` present and `fsdp_version: 2`.
- FSDP + QLoRA requires `adapter: qlora` plus an actual FSDP config. If CPU offload is needed, `offload_params: true` with `cpu_offload_pin_memory: false` can allow swap fallback at a performance cost.
- Full-parameter fine-tunes that OOM under one GPU usually need sharding, lower micro-batch size, activation techniques, or shorter `sequence_len`; do not solve this by changing training objective fields.

## N-D Parallelism

Axolotl exposes data, tensor, context, and expert axes:

```yaml
dp_shard_size: 4
dp_replicate_size: 2
tensor_parallel_size: 2
context_parallel_size: 1
expert_parallel_size: 1
fsdp_version: 2
fsdp_config:
  auto_wrap_policy: TRANSFORMER_BASED_WRAP
```

Use cases and constraints:

- `dp_shard_size` shards parameters/gradients/optimizer state; `dp_replicate_size` replicates those shards, useful for HSDP across nodes.
- `tensor_parallel_size` splits layer computation. It needs fast interconnect and is usually a poor fit across slow node boundaries.
- `context_parallel_size` splits sequence length for long-context training. It requires a divisor of the launched process count and a compatible attention path, typically `attn_implementation: flash_attention_2` for ring flash attention.
- `expert_parallel_size` shards MoE experts and is only relevant for MoE models with the expert-parallel integration enabled.
- For advanced EP validation, the product `expert_parallel_size * dp_shard_size * tensor_parallel_size * context_parallel_size` must match world size when EP is active.
- Avoid DDP + TP/CP compositions. If `dp_replicate_size > 1` while `dp_shard_size <= 1` and TP/CP is active, redesign around FSDP sharding.

## Ray, Torchrun, and Multi-Node

Ray:

- Set `use_ray: true` in YAML or pass `--use-ray` to `axolotl train`.
- Set `ray_num_workers` to the number of worker processes/GPUs expected for training.
- Optional `resources_per_worker` belongs in YAML when a heterogeneous Ray cluster needs GPU-type or custom-resource constraints.
- Run `ray status` on the head node before Axolotl; missing workers are an orchestration issue, not a YAML objective issue.

Torchrun:

- Use Axolotl's launcher pass-through for modern commands: `axolotl train config.yaml --launcher torchrun -- --nnodes ... --nproc_per_node ... --rdzv_id ... --rdzv_backend c10d --rdzv_endpoint host:port`.
- Use direct `torchrun -m axolotl.cli.train config.yaml` only for legacy scripts.
- Set `NCCL_IB_DISABLE=0`, `NCCL_SOCKET_IFNAME`, rendezvous host/port, and scheduler-provided rank variables in the shell or scheduler script, not inside the Axolotl YAML.

SLURM/HPC/cloud:

- Keep `#SBATCH`, modules, container setup, and cluster paths in the job script.
- Keep reusable model/training/distributed choices in the Axolotl config YAML.
- Confirm each node sees the same code, package version, datasets, output storage, and credentials before launching.
- For AMD HPC, prefer FSDP for multi-node and treat ROCm Flash Attention/xFormers workarounds as environment-specific prerequisites.

## Checkpoints and Sharded Saves

Distributed checkpoint behavior depends on backend:

- FSDP may save sharded model directories. If a user needs a single model artifact, use Axolotl's documented sharded FSDP merge workflow after training, not during static config review.
- DeepSpeed ZeRO-3 save/load needs DeepSpeed-aware consolidation paths; do not assume a plain `pytorch_model.bin` exists.
- Dynamic checkpoint triggers can be used in long jobs with `dynamic_checkpoint.enabled: true` and a trigger file in the output directory. File-triggered checkpoints are resumable; Control+C checkpoints save model weights only and are not full optimizer-state resumes.
- In multi-node jobs, ensure `output_dir` resolves to shared or intentionally node-local storage according to the user's cluster design.

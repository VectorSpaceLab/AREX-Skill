# Troubleshooting Advanced RL and Distributed Workflows

Use this guide when `swift rlhf`, `swift sample`, `swift rollout`, Ray, or `megatron` workflows fail after the basic command shape is known.

## Triage Order

1. Run the optional backend checker: `python scripts/check_optional_backends.py`.
2. Confirm the route exists: `swift rlhf --help`, `swift sample --help`, `swift rollout --help`, or `megatron rlhf --help`.
3. Verify the workflow-specific extras before changing training flags.
4. Reduce to a tiny dataset slice and one save/eval interval while debugging command semantics.
5. Only after command validation, launch GPU-heavy distributed jobs.

## Missing Optional Backends

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| `swift` command missing | Console script not installed or environment not activated | Install/activate ms-swift; a package import may still work even if PATH is wrong. |
| `megatron` command missing | Megatron extra not installed | Install a Megatron-capable ms-swift environment such as `pip install "ms-swift[megatron]" -U`. |
| Import error for `megatron.core` | `megatron-core` absent or incompatible | Install compatible Megatron-Core and re-run backend checker. |
| Import error for `mcore_bridge` | Mcore-Bridge absent | Install or update `mcore-bridge`; needed for simplified safetensors Megatron loading. |
| Transformer Engine or FlashAttention import/build error | CUDA/PyTorch/kernel version mismatch | Align CUDA, torch, transformer-engine, and flash-attn versions; avoid enabling FP8/flash features until imports pass. |
| `ray` import or cluster connection failure | Ray extra absent or cluster not started | Install Ray, start head/worker nodes, then launch `megatron rlhf --use_ray true --config ...`. |
| `vllm`, `lmdeploy`, or `sglang` import failure | Optional inference backend absent | Install only the backend required by the requested rollout/sampling/deploy plan. |
| `evalscope` missing | Evaluation extra absent | Treat as an evaluation optional dependency; it is not required for RL command planning. |

## Reward Function Problems

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Custom reward name not found | Plugin not imported or registry key mismatch | Pass `--external_plugins plugin.py`; ensure plugin runs `orms['name'] = ClassName`. |
| Reward gets `None` for `solution` | Dataset column was not preserved or not passed to rollout server | Check dataset preprocessing; for server multi-turn/env mode, use `--vllm_server_pass_dataset true`. |
| `TypeError: unexpected keyword argument` in reward | Reward signature too narrow | Add `**kwargs` to `__call__` and read optional fields defensively. |
| Rewards all identical | Bad parser, missing reference fields, or deterministic samples | Log sample completions, verify `solution`/task fields, increase sampling diversity, or enable `dynamic_sample`. |
| `accuracy` reward import error for math parser | `math_verify` or related parser missing | Install the math verification dependency or use a custom reward not requiring it. |
| Reward model OOM inside reward function | Heavy judge loaded in training process | Use async API reward, external service, or split PRM/ORM sampling pass. |
| Multi-task rewards pollute unrelated tasks | Reward returns numeric values for all rows | Return `None` for rows outside the reward's task and use clear task columns. |

For the difficult case where a custom ORM silently misses `solution`, instrument the reward once with lengths and `kwargs.keys()`, verify the dataset row has the field after conversion, then switch the reward to `def __call__(self, completions, solution=None, **kwargs)` and fail loudly if `solution is None` during smoke tests.

## GRPO Batch and Loss Errors

| Error/Signal | Check |
| --- | --- |
| `num_generations` less than 2 | GRPO needs at least two completions per prompt for group advantages. |
| `generation_batch_size` not divisible by `num_generations` | Adjust `steps_per_generation`, train batch size, or `num_generations`. |
| Reward std is zero | All completions in a group scored the same; improve reward discrimination, sampling diversity, or use `dynamic_sample`. |
| Overlong/truncated completions dominate | Reduce max prompt length, raise `max_completion_length`, enable `overlong_filter`, or add `soft_overlong` with `soft_cache_length`. |
| SAPO/GSPO conflict | SAPO expects token-level importance sampling; do not combine blindly with `importance_sampling_level sequence`. |
| REAL loss batch error in Megatron | Make `micro_batch_size` a multiple of `num_generations`. |
| `soft_overlong` assertion | Set `soft_cache_length` and ensure it is less than `soft_max_length` or `max_completion_length`. |

## Rollout and vLLM Placement

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Colocate OOM before first update | Training and vLLM compete for memory | Lower `vllm_gpu_memory_utilization`, set `sleep_level`, enable model/optimizer offload, reduce `vllm_max_model_len`. |
| Server mode cannot connect | Wrong host/port/base URL or firewall | Prefer `--vllm_server_base_url http://host:port`; increase `--vllm_server_timeout`; confirm server logs. |
| Weight sync too slow | Full-parameter sync overhead | Tune `SWIFT_UPDATE_WEIGHTS_BUCKET_SIZE`; for LoRA use `--vllm_enable_lora true` and matching rank. |
| Multi-turn server lacks dataset fields | Dataset not passed to rollout server | Add `--vllm_server_pass_dataset true` to the trainer. |
| Async rollout mismatch | `async_generate` uses previous policy | Disable async for stability or enable mismatch diagnostics/correction. |
| vLLM async engine fails with DP only | Backend limitation in some vLLM versions | Use both TP and DP, or upgrade vLLM. |
| Multimodal LoRA missing in rollout | vLLM tower/connector LoRA not enabled | Pass `--vllm_engine_kwargs '{"enable_tower_connector_lora": true}'` where supported. |

## Multi-Turn Scheduler and Gym Environment Issues

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Scheduler key not found | Plugin did not register `multi_turns['name']` | Import plugin with `--external_plugins`; check registry key spelling. |
| Env key not found | Plugin did not register `envs['name']` | Register in `swift.rollout.gym_env.envs`; pass `--gym_env name`. |
| No gym reward applied | `use_gym_env` false or env reward not emitted | Set `--use_gym_env true`; confirm scheduler returns `rollout_infos.total_reward`. |
| Conversation grows incorrectly | `step` mutates messages badly | Return `{'infer_request': req}` with valid OpenAI-style messages after each turn. |
| Loss mask/logprob mismatch | Scheduler returns modified text without aligned token IDs/logprobs | Return `response_token_ids`, matching `response_loss_mask`, and complete `rollout_logprobs` when modifying completions. |
| Colocate custom `run()` ignored | Full custom async `run()` is server-oriented | Prefer hooks/`step` for colocate compatibility, or use server mode for full custom run logic. |
| Environment resources leak | Env lacks cleanup | Implement `close()` and keep per-request state keyed by request identity. |

## Ray Device Groups and YAML

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Ray YAML parse error | Python expressions or unquoted strings unsupported in the loader context | Use plain YAML lists such as `[0, 1]` when in doubt. |
| Colocate group fails | Train and rollout GPU counts mismatch | In `colocate_groups: [[train, rollout]]`, make `train.gpus` and `rollout.gpus` equal. |
| Role has no GPUs | `workers` role not assigned to a device group | For Swift Ray, ensure roles such as `sampler`, `prm`, `orm` appear under `workers`. |
| Ray cluster hangs | Worker nodes not joined or resources invisible | Run `ray status`, verify GPU visibility on all nodes, and use shared storage/cache. |
| Ray Megatron GKD teacher fails | Teacher group mode incompatible | Use colocated teacher with `offload_teacher_model` or a separate teacher group with top-k distillation. |

## Torchrun and Distributed Environment

For non-Ray Megatron, check:

- `NPROC_PER_NODE` equals the number of local ranks/GPU processes.
- `CUDA_VISIBLE_DEVICES` exposes at least `NPROC_PER_NODE` devices.
- `MASTER_ADDR`, `MASTER_PORT`, `NNODES`, and `NODE_RANK` are correct for multi-node launches.
- `MASTER_PORT` is free and unique per job.
- `MODELSCOPE_CACHE` points to shared storage for multi-node preprocessing.
- `output_dir` is shared or intentionally node-local; checkpoint consolidation is harder if paths differ.
- NCCL can see the intended network interfaces and peer GPUs.

## Megatron Parallel Dimension Mismatches

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| DP size not integer | `world_size` not divisible by `TP × PP × CP` | Change `tensor_model_parallel_size`, `pipeline_model_parallel_size`, `context_parallel_size`, or GPU count. |
| Prompt/batch validation error | Completion-level batch math invalid | Recompute `global_batch_size`, `steps_per_generation`, `generation_batch_size`, and `num_generations`. |
| PP layer split error | Layers not divisible or multimodal stage imbalance | Use `decoder_first_pipeline_num_layers`, `decoder_last_pipeline_num_layers`, or `pipeline_model_parallel_layout`. |
| Sequence parallel ineffective | TP is 1 | Only enable sequence parallel when TP > 1. |
| MoE expert mismatch | EP/ETP incompatible with model expert count | Inspect model config and choose EP/ETP divisors that fit expert layout. |
| Pipeline hang | P2P communication mode or layout issue | Try changing `batch_p2p_comm`, inspect PP layout, and test without VPP. |
| MCore checkpoint resume fails | Used `--model` where MCore resume state is required | Resume optimizer/RNG state with `--mcore_model` or `--mcore_adapter`; use `--finetune false` for true resume. |

## Model Support Limitations

- Megatron-SWIFT model support is narrower than generic `swift rlhf`; if an architecture is unsupported by Mcore-Bridge/Megatron-Core, use the standard trainer or add model support first.
- FlashAttention and fused attention backends are not universal; switch `--attention_backend unfused` or adjust padding-free settings for unsupported architectures.
- Multimodal GRPO may need model-specific `vllm_limit_mm_per_prompt`, `MAX_PIXELS`, and rollout LoRA support.
- GKD teacher models with different parallel layouts are a known Megatron limitation; keep parallel dimensions aligned unless the installed version proves support.
- FP8/FP4, DeepEP, MTP, and emerging optimizer features require matching hardware and backend versions.

## Sampling and PRM/ORM Filtering

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Sampling OOM with PRM/ORM | Generator and reward model loaded together | Split into `sampler_engine vllm|transformers` first, then `sampler_engine no --cache_files ...`. |
| Cache pass cannot match rows | Dataset mismatch between passes | Provide the same `--dataset` on the cache filtering pass. |
| `rejected_response` missing | No PRM/ORM filtering active | Pass `--prm_model` or `--orm_model` and `--n_best_to_keep`. |
| Client distillation fails auth | Missing API key/base URL | Use environment variables for credentials and pass endpoint in `--engine_kwargs`. |

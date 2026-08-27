# Training configuration

EasyR1 launches RL post-training with:

```bash
python -m verl.trainer.main config=/path/to/easyr1_config.yaml key=value another.nested.key=value
```

The command builds a structured PPO-style config, optionally merges the YAML file named by `config=...`, then merges CLI overrides. CLI overrides have the highest priority. The training entry point initializes Ray if needed, creates actor/rollout/ref workers on FSDP plus vLLM, creates reward managers, builds dataloaders, and starts the Ray PPO trainer.

Passing a static lint check is not proof that training will run. Full EasyR1 training needs CUDA GPUs, Ray, vLLM, flash-attn, a compatible PyTorch/CUDA stack, model weights, dataset access, and enough GPU memory for the chosen model, sequence lengths, rollout count, tensor parallel size, and batch sizes.

## Merge order and generated fields

1. Start from EasyR1 dataclass defaults.
2. If `config=/path/to/file.yaml` is present, load that YAML and merge it.
3. Merge every remaining CLI `key=value` override.
4. Run post-initialization:
   - `worker.rollout.prompt_length` is set from `data.max_prompt_length`.
   - `worker.rollout.response_length` is set from `data.max_response_length`.
   - `worker.rollout.trust_remote_code` follows `worker.actor.model.trust_remote_code`.
   - actor KL fields follow `algorithm.disable_kl`, `algorithm.use_kl_loss`, `algorithm.kl_penalty`, and `algorithm.kl_coef`.
   - ref-worker micro-batch, padding-free, dynamic-batching, Ulysses, and torch-compile settings follow actor settings.
   - if `trainer.save_checkpoint_path` is omitted, it becomes `checkpoints/<project_name>/<experiment_name>`.
   - if `trainer.load_checkpoint_path` is set, it should resolve to a `global_step_*` checkpoint directory.

Use explicit CLI values for experiment-specific settings so the printed config at launch records the final run plan.

## Required top-level sections

A normal EasyR1 training YAML has four top-level mappings:

```yaml
data: {}
algorithm: {}
worker: {}
trainer: {}
```

The bundled linter treats missing sections as warnings because dataclass defaults can fill omitted fields, but a production config should keep all four sections visible.

## Data keys that affect launch shape

Detailed dataset columns, prompt templates, and reward-function implementation belong to `data-and-rewards`. For training launch decisions, these fields determine runtime shape:

| Key | Use |
| --- | --- |
| `data.train_files`, `data.val_files` | Dataset split identifiers or paths used by the dataloader. Remote identifiers require network or cache access. |
| `data.max_prompt_length` | Prompt token budget; also controls vLLM prompt length. Increase if VL image tokens overflow. |
| `data.max_response_length` | Generation budget; also controls vLLM `max_tokens`. Long DAPO runs can set this very high. |
| `data.rollout_batch_size` | Number of prompts per rollout batch; must be divisible by actor global batch size. |
| `data.mini_rollout_batch_size` | Optional generation sub-batch size; DAPO-style online filtering often uses a smaller value. |
| `data.val_batch_size` | Validation batch size; use smaller values for expensive VL validation. |
| `data.min_pixels`, `data.max_pixels`, `data.video_fps` | VL/video preprocessing limits that affect prompt length and memory. |
| `data.filter_overlong_prompts` | Whether to filter prompts that exceed token budget before training. |

## Algorithm and loss choices

### Advantage estimators

`algorithm.adv_estimator` is an enum-like string. Useful values are:

| Value | Meaning and constraints |
| --- | --- |
| `gae` | Uses critic/value learning. Enables critic workers and critic batch constraints. |
| `grpo` | Group relative policy optimization. Requires `worker.rollout.n > 1`. This is the default. |
| `grpo_passk` | Pass@k-style GRPO outcome estimator. It also needs grouped samples (`worker.rollout.n > 1`). |
| `reinforce_plus_plus` | REINFORCE++ outcome estimator; no critic. |
| `remax` | ReMax outcome estimator; generates a deterministic baseline response. |
| `rloo` | Leave-one-out group baseline. Requires `worker.rollout.n > 1`. |

There is no separate `adv_estimator=dapo` in the inspected EasyR1 configuration. DAPO-style launches keep the GRPO-style estimator and combine online filtering plus asymmetric clipping, commonly:

```bash
algorithm.disable_kl=True \
algorithm.online_filtering=True \
worker.actor.clip_ratio_low=0.2 \
worker.actor.clip_ratio_high=0.28
```

### Policy loss variants

`worker.actor.loss_type` selects policy loss math:

| Value | Typical use |
| --- | --- |
| `default` | Standard clipped policy loss used by GRPO, DAPO-style runs, Reinforce++, ReMax, and RLOO. |
| `gspo` | Sequence-level importance ratio. |
| `gspo_token` | Token-level GSPO variant used with `worker.actor.loss_avg_mode=seq` in examples. |
| `cispo` | CISPO loss; examples use wide clipping such as `clip_ratio_low=0`, `clip_ratio_high=4`. |
| `sapo` | SAPO loss with positive/negative token gates controlled by `tau_positive` and `tau_negative`. |

`worker.actor.loss_avg_mode` and `worker.critic.loss_avg_mode` accept `token` or `seq`.

### KL settings

| Key | Options and notes |
| --- | --- |
| `algorithm.disable_kl` | If true, no reference-policy KL metrics are logged and reference KL is effectively disabled. |
| `algorithm.use_kl_loss` | Moves KL handling into the actor loss path instead of reward shaping. |
| `algorithm.kl_penalty` | `kl`, `abs`, `mse`, `low_var_kl`, or `full`. |
| `algorithm.kl_coef` | KL coefficient. Defaults are conservative; DAPO examples commonly disable KL. |
| `algorithm.kl_type` | `fixed` or `adaptive`. Adaptive requires `kl_horizon > 0` and a target. |

### Online filtering for DAPO-style runs

When `algorithm.online_filtering=True`, EasyR1 computes rewards during batch creation, groups rollout responses by UID, and keeps only prompts whose average score is between `algorithm.filter_low` and `algorithm.filter_high` for `algorithm.filter_key`.

Important knobs:

```yaml
algorithm:
  online_filtering: true
  filter_key: overall        # or a reward-specific key such as accuracy_normalized
  filter_low: 0.01
  filter_high: 0.99
trainer:
  max_try_make_batch: 20     # -1 means no limit
```

If filtering is too strict, training can repeatedly regenerate or fail with no kept samples. Adjust the reward key, filter bounds, data quality, or `max_try_make_batch`.

## Worker and model configuration

### Actor batches and constraints

Relevant actor keys:

```yaml
worker:
  actor:
    global_batch_size: 128
    micro_batch_size_per_device_for_update: 1
    micro_batch_size_per_device_for_experience: 2
    max_grad_norm: 1.0
    padding_free: true
    dynamic_batching: true
    ulysses_size: 1
```

Validation rules enforced by the trainer/workers include:

- `data.rollout_batch_size % worker.actor.global_batch_size == 0`.
- `(data.rollout_batch_size * worker.rollout.n) % worker.actor.micro_batch_size_per_device_for_experience == 0`.
- Effective actor global batch per device must be divisible by `micro_batch_size_per_device_for_update`.
- If actor FSDP CPU offload is enabled, gradient accumulation is not allowed for that worker; align global and micro update batch sizes or disable FSDP CPU offload.
- `worker.actor.ulysses_size > 1` is useful for some text long-sequence runs, but EasyR1 documents VLM incompatibility with Ulysses parallelism, so avoid it for vision-language models unless the runtime has been specifically validated.

### Model, FSDP, optimizer, and offload keys

```yaml
worker:
  actor:
    model:
      model_path: Qwen/Qwen2.5-7B-Instruct
      tokenizer_path: null
      override_config: {}
      enable_gradient_checkpointing: true
      trust_remote_code: false
      freeze_vision_tower: false
    optim:
      lr: 1.0e-6
      weight_decay: 1.0e-2
      strategy: adamw          # adamw or adamw_bf16
      lr_scheduler_type: constant  # constant or cosine
    fsdp:
      enable_full_shard: true
      enable_cpu_offload: false
      enable_rank0_init: true
      torch_dtype: null        # use bf16 for reduced memory when supported
    offload:
      offload_params: true
      offload_optimizer: true
```

Use `worker.actor.fsdp.torch_dtype=bf16` and `worker.actor.optim.strategy=adamw_bf16` for BF16 training on supported GPUs. Actor model loading uses FlashAttention 2; missing `flash-attn` or an incompatible CUDA stack is a training-runtime blocker.

### LoRA configuration

LoRA is enabled when `worker.actor.model.lora.rank` is positive:

```yaml
worker:
  actor:
    model:
      lora:
        rank: 64
        alpha: 64
        target_modules: all-linear
        exclude_modules: .*visual.*
```

Cautions:

- For Qwen-VL or similar vision-language models, exclude the vision tower (for example `.*visual.*`) because vLLM LoRA does not support ViT LoRA in the distilled EasyR1 evidence.
- LoRA examples use small tensor parallel sizes, often `worker.rollout.tensor_parallel_size=1`; verify vLLM LoRA compatibility before increasing TP.
- LoRA checkpoint merging/export is not owned by this sub-skill; use `checkpoint-export` for conversion and merge details.

## Rollout and vLLM configuration

The rollout implementation is vLLM SPMD and assumes CUDA workers. Common keys:

```yaml
worker:
  rollout:
    name: vllm
    n: 5
    temperature: 1.0
    top_p: 1.0
    top_k: -1
    limit_images: 0
    dtype: bf16
    gpu_memory_utilization: 0.6
    enforce_eager: false
    enable_chunked_prefill: false
    tensor_parallel_size: 2
    max_model_len: null
    max_num_batched_tokens: 8192
    disable_tqdm: false
    val_override_config:
      temperature: 0.6
      top_p: 0.95
      n: 1
```

Hard constraints and useful checks:

- `worker.rollout.tensor_parallel_size` must be no larger than world size and must divide the rollout world size.
- World size is `trainer.nnodes * trainer.n_gpus_per_node` for normal launches.
- `worker.rollout.max_num_batched_tokens` must be greater than `data.max_prompt_length + data.max_response_length`.
- `worker.rollout.n > 1` is required for GRPO, GRPO Pass@k, and RLOO.
- Reduce `worker.rollout.gpu_memory_utilization` if vLLM CUDA memory errors occur.
- `worker.rollout.val_override_config` is a dict; quote it when using CLI overrides, for example `worker.rollout.val_override_config='{"temperature":0.6,"top_p":0.95,"n":1}'`.

## Reward hook configuration

Training launches need a reward manager, but reward implementation details are routed to `data-and-rewards`. Training-owned keys are:

```yaml
worker:
  reward:
    reward_function: /path/to/reward.py:compute_score
    reward_function_kwargs: {}
    skip_special_tokens: true
    num_cpus: 1
```

If the function suffix is omitted, EasyR1 assumes the callable name `main`. Use JSON-style quoting for CLI kwargs:

```bash
worker.reward.reward_function_kwargs='{"max_response_length":20480,"overlong_buffer_length":4096,"overlong_penalty_factor":1.0}'
```

For DAPO online filtering, ensure `algorithm.filter_key` matches a metric key emitted by the reward function.

## Trainer, logging, validation, save, and resume

Key trainer fields:

```yaml
trainer:
  total_epochs: 15
  max_steps: null
  project_name: easy_r1
  experiment_name: my_experiment
  logger: [file, wandb]
  nnodes: 1
  n_gpus_per_node: 8
  max_try_make_batch: 20
  val_freq: 5
  val_before_train: true
  val_only: false
  val_generations_to_log: 3
  save_freq: 5
  save_limit: 3
  save_model_only: false
  save_checkpoint_path: null
  load_checkpoint_path: null
  find_last_checkpoint: true
  ray_timeline: null
```

Logger values supported by the inspected config are `console`, `file`, `mlflow`, `swanlab`, `tensorboard`, and `wandb`. If a hosted logger is not authenticated, switch to `console` or `file` for the first run.

Resume behavior:

- If `trainer.load_checkpoint_path` is set, it must point to a `global_step_*` directory.
- Otherwise, if `trainer.find_last_checkpoint=True`, EasyR1 tries to find the latest checkpoint under `trainer.save_checkpoint_path`.
- `trainer.save_model_only=True` saves only model state and omits optimizer state; that is smaller but not equivalent to full training resume.
- Checkpoint-to-Hugging-Face export is handled by `checkpoint-export`, not by the training launcher itself.

## Multi-node notes

1. Start Ray on the head node:

```bash
ray start --head --port=6379 --dashboard-host=0.0.0.0
```

2. Start Ray on each worker node:

```bash
ray start --address=<head_node_ip>:6379
```

3. Check resources:

```bash
ray status
```

4. Launch `python -m verl.trainer.main ...` on the Ray head node only.

Set `trainer.nnodes` and `trainer.n_gpus_per_node` to match the Ray resource pool. If Ray reports fewer GPUs than requested, reduce those values or fix cluster registration before launching training.

## Safe validation workflow

From the directory containing this sub-skill, use:

```bash
python scripts/easyr1_config_lint.py /path/to/easyr1_config.yaml --strict
python scripts/easyr1_command_builder.py /path/to/easyr1_config.yaml \
  --override worker.actor.model.model_path=Qwen/Qwen2.5-7B-Instruct \
  --override trainer.n_gpus_per_node=8 \
  --multiline
```

The linter and command builder do not import EasyR1, start Ray, allocate GPUs, download data, or touch checkpoints.

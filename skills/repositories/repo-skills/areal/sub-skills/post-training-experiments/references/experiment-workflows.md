# Experiment Workflows

Use this reference to plan AReaL GRPO/PPO/SFT/DPO/RW runs after the YAML and overrides
pass `scripts/validate_experiment_config.py`. The commands below are distilled command
contracts, not links to a source checkout. Replace `<entrypoint>` and `<yaml>` with the
actual script/config in the user's project or copied experiment workspace.

## Pre-launch loop

1. Pick the family: GRPO, PPO, SFT, DPO, or RW.
2. Confirm the matching config class, trainer, and `train_dataset.type` from
   `config-api.md`.
3. Plan model/data paths and keep credentials out of YAML unless the user explicitly
   provides a safe secret-management path.
4. Choose a scheduler:
   - `scheduler.type=local` for a single machine.
   - `scheduler.type=ray` for an already-running Ray cluster.
   - `scheduler.type=slurm` for Slurm-managed multi-node jobs.
5. Check the physical GPU budget:
   - in separation mode, sum per-engine backend world sizes;
   - in colocation mode, count a colocated group once through its target role;
   - compare the result with `cluster.n_nodes * cluster.n_gpus_per_node`.
6. Set `cluster.fileroot` and `cluster.name_resolve.nfs_record_root` to storage visible
   to every participating worker for multi-node runs.
7. Validate:

```bash
python3 scripts/validate_experiment_config.py --kind <family> --config <yaml> [overrides...]
```

8. Only after validation, launch the actual experiment command.

## Universal launch pattern

The recommended mode is direct script execution with a single-controller scheduler:

```bash
python3 <entrypoint> \
  --config <yaml> \
  scheduler.type=local \
  experiment_name=<experiment> \
  trial_name=<trial> \
  cluster.n_nodes=1 \
  cluster.n_gpus_per_node=<gpu-count> \
  cluster.fileroot=<shared-or-local-fileroot> \
  stats_logger.wandb.mode=disabled
```

For Ray or Slurm, change `scheduler.type` and set cluster fields:

```bash
python3 <entrypoint> \
  --config <yaml> \
  scheduler.type=ray \
  cluster.n_nodes=<nodes> \
  cluster.n_gpus_per_node=<gpus-per-node> \
  cluster.fileroot=<shared-fileroot>
```

```bash
python3 <entrypoint> \
  --config <yaml> \
  scheduler.type=slurm \
  cluster.n_nodes=<nodes> \
  cluster.n_gpus_per_node=<gpus-per-node> \
  cluster.fileroot=<shared-fileroot>
```

Legacy SPMD launcher wrappers exist, but direct script execution with `scheduler.type`
is the default recommendation for new experiments.

## GRPO and PPO

GRPO/PPO use `PPOTrainer`. GRPO omits `critic`; PPO supplies `critic`.

### Minimal GRPO command shape

```bash
python3 <grpo-entrypoint> \
  --config <grpo-yaml> \
  scheduler.type=local \
  experiment_name=<experiment> \
  trial_name=<trial> \
  rollout.backend=sglang:d4p1t1 \
  actor.backend=fsdp:d4p1t1 \
  cluster.n_nodes=1 \
  cluster.n_gpus_per_node=8 \
  train_dataset.batch_size=256 \
  valid_dataset.batch_size=256 \
  stats_logger.wandb.mode=disabled
```

Typical GRPO sections:

```yaml
rollout:
  backend: sglang:d4p1t1
  consumer_batch_size: ${train_dataset.batch_size}
  max_head_offpolicyness: 2
  tokenizer_path: ${tokenizer_path}

gconfig:
  n_samples: 4
  max_new_tokens: 1024
  max_tokens: 2048
  temperature: 1.0

actor:
  backend: fsdp:d4p1t1
  path: <base-or-instruct-model>
  disable_dropout: true
  gradient_checkpointing: true
  dtype: bfloat16
  mb_spec:
    max_tokens_per_mb: 10240
  ppo_n_minibatches: 1
  use_decoupled_loss: true
  recompute_logprob: true
  rejection_sampling:
    metric: ratio
    upper: 5.0
  reward_norm:
    mean_level: group
    std_level: group
    group_size: ${gconfig.n_samples}
  adv_norm:
    mean_level: batch
    std_level: batch
```

`PPOTrainer.train()` is the only place the entrypoint should need to call the trainer.
For rollout-workflow RL it takes a workflow plus optional evaluation workflow:

```python
trainer.train(
    workflow="<RolloutWorkflow import path>",
    workflow_kwargs={...},
    eval_workflow="<optional eval workflow import path>",
    eval_workflow_kwargs={...},
)
```

If the user needs to write or debug that workflow or reward function, route to
`../custom-data-rewards-workflows/` and return here only for trainer/config wiring.

### PPO additions

PPO adds a critic and uses the same launch pattern:

```bash
python3 <ppo-entrypoint> \
  --config <ppo-yaml> \
  scheduler.type=local \
  rollout.backend=sglang:d4p1t1 \
  actor.backend=fsdp:d4p1t1 \
  critic.backend=fsdp:d4p1t1 \
  actor.mb_spec.max_tokens_per_mb=10240 \
  critic.mb_spec.max_tokens_per_mb=10240
```

Typical critic section:

```yaml
critic:
  backend: ${actor.backend}
  is_critic: true
  path: ${actor.path}
  optimizer: ${actor.optimizer}
  scheduling_strategy:
    type: colocation
    target: actor
```

### Algorithm variants from GRPO/PPO configs

AReaL exposes many PPO-family algorithms as config changes. Validate any variant before
launch.

| Variant | Override or config change |
|---|---|
| Synchronous debug mode | `rollout.max_head_offpolicyness=0` |
| Dr.GRPO-style normalization | `actor.adv_norm.mean_level=group actor.adv_norm.std_level=null` |
| RLOO | `actor.adv_norm.mean_level=group actor.adv_norm.std_level=null actor.adv_norm.mean_leave1out=true` |
| GSPO | `+actor.importance_sampling_level=sequence` |
| SAPO | `+actor.use_sapo_loss=true +actor.sapo_tau_pos=1.0 +actor.sapo_tau_neg=1.05 actor.use_decoupled_loss=false` |
| IcePop-style masking | `actor.rejection_sampling.metric=ratio` with chosen bounds |
| KPop-style masking | `actor.rejection_sampling.metric=binary_kl` with chosen bounds; validate first because some builds document this recipe before config validation accepts it |
| DAPO-style clipping | set `actor.eps_clip_higher` and any dynamic-batch settings the user requests |

Do not combine SAPO with `actor.use_decoupled_loss=true`. If a user asks for detailed
algorithm design or loss internals, route to the backend/algorithm expert owned by the
parent skill set, not this launch-planning sub-skill.

### Async rollout planning

AReaL's async RL overlaps rollout generation and training. Use:

```yaml
rollout:
  max_head_offpolicyness: 2  # 0 is synchronous; 2-8 is common async range

actor:
  use_decoupled_loss: true
  recompute_logprob: true
  rejection_sampling:
    level: token
    action: mask
    metric: ratio
    upper: 5.0
```

Higher `max_head_offpolicyness` increases throughput but can reduce training stability.
If `use_decoupled_loss=true` and `rejection_sampling=null`, AReaL will run but staleness
filtering is disabled.

### VLM GRPO notes

For vision-language GRPO, use the same PPOTrainer pattern but the entrypoint must load a
processor as well as a tokenizer and pass both to dataset loading and workflow kwargs.
Typical config additions:

```yaml
rollout:
  backend: vllm:d4p1t1  # or sglang:d...

gconfig:
  max_new_tokens: 512

sglang:
  enable_multimodal: true
  max_running_requests: 64

vllm:
  disable_sliding_window: false
```

If the task is to implement image formatting, a custom VLM reward, or a new VLM
workflow, route to `../custom-data-rewards-workflows/`.

### LoRA GRPO/PPO notes

LoRA planning rules:
- actor LoRA is FSDP-only;
- rollout must serve LoRA through SGLang or vLLM;
- set `rollout.use_lora: true`, `actor.use_lora: true`, and backend-specific LoRA
  enable fields;
- set `gconfig.lora_name` explicitly and keep the same adapter label across trainer and
  rollout.

Example fragment:

```yaml
rollout:
  use_lora: true

gconfig:
  lora_name: lora-trial0

actor:
  backend: fsdp:d4
  use_lora: ${rollout.use_lora}
  lora_rank: 16
  lora_alpha: 16
  target_modules: [all-linear]
  weight_update_mode: disk

sglang:
  enable_lora: ${actor.use_lora}
  max_lora_rank: ${actor.lora_rank}
```

Megatron actor + LoRA + SGLang rollout is not supported by the RL trainer; switch to
vLLM rollout, disable LoRA, or use FSDP actor.

## SFT

SFT uses `SFTTrainer` and `SFTConfig`. It has an actor only.

```bash
python3 <sft-entrypoint> \
  --config <sft-yaml> \
  scheduler.type=local \
  experiment_name=<experiment> \
  trial_name=<trial> \
  actor.backend=fsdp:d8p1t1 \
  actor.path=<model-or-checkpoint> \
  train_dataset.type=sft \
  valid_dataset.type=sft \
  actor.mb_spec.max_tokens_per_mb=4096 \
  stats_logger.wandb.mode=disabled
```

`SFTTrainer.train()` takes no workflow argument. The entrypoint should:

```python
config, _ = load_expr_config(args, SFTConfig)
tokenizer_or_processor = load tokenizer/processor from config.tokenizer_path
train_dataset = get_custom_dataset(..., dataset_config=config.train_dataset, ...)
valid_dataset = get_custom_dataset(..., dataset_config=config.valid_dataset, ...)
with SFTTrainer(config, train_dataset=train_dataset, valid_dataset=valid_dataset) as trainer:
    trainer.train()
```

For VLM SFT, load both processor and tokenizer and pass both to the dataset loader. If
the user needs to define the dataset schema, route to `../custom-data-rewards-workflows/`.

## DPO

DPO uses `DPOTrainer` and preference-pair data. It does not launch rollout workers.

```bash
python3 <dpo-entrypoint> \
  --config <dpo-yaml> \
  scheduler.type=local \
  experiment_name=<experiment> \
  trial_name=<trial> \
  actor.backend=fsdp:d8p1t1 \
  ref.backend=fsdp:d8p1t1 \
  actor.path=<policy-or-sft-checkpoint> \
  ref.path=<reference-checkpoint> \
  train_dataset.type=dpo \
  valid_dataset.type=dpo \
  actor.mb_spec.granularity=2 \
  actor.disable_dropout=true \
  stats_logger.wandb.mode=disabled
```

DPO essentials:
- `actor.beta` controls the KL penalty; common starting range is `0.05`–`0.5`.
- `actor.loss_type` is `sigmoid` or `ipo`.
- `actor.mb_spec.granularity=2` keeps chosen/rejected pairs together.
- `ref.optimizer=null` keeps the reference frozen.
- `ref.scheduling_strategy.type=colocation` with `target=actor` is the common GPU-saving
  pattern.

Expected useful metrics include `dpo/loss`, `dpo/chosen_reward`,
`dpo/rejected_reward`, `dpo/reward_accuracy`, and `dpo/reward_margin`.

## Reward-model (RW) training

RW uses `RWTrainer`, preference-pair data, and a critic/reward-model actor.

```bash
python3 <rw-entrypoint> \
  --config <rw-yaml> \
  scheduler.type=local \
  experiment_name=<experiment> \
  trial_name=<trial> \
  actor.backend=fsdp:d8p1t1 \
  actor.path=<model-or-checkpoint> \
  actor.is_critic=true \
  train_dataset.type=rw \
  valid_dataset.type=rw \
  actor.mb_spec.granularity=2 \
  stats_logger.wandb.mode=disabled
```

RW trainer validation requires `actor.is_critic=true`. If the user wants to use the RW
output as a reward source for PPO/GRPO, plan that as a separate PPO/GRPO experiment and
route custom reward/service wiring to the appropriate sibling sub-skill.

## Colocation and offload command planning

Use colocation when actor, critic, ref, or rollout roles should share GPUs. For
PPO/GRPO, trainer validation requires:

```yaml
enable_offload: true
actor:
  weight_update_mode: disk  # or awex for Megatron actor + SGLang rollout only
```

Example actor-rollout colocation pattern:

```bash
python3 <grpo-entrypoint> \
  --config <grpo-yaml> \
  scheduler.type=local \
  rollout.backend=sglang:d2 \
  actor.backend=fsdp:d2 \
  +rollout.scheduling_strategy.type=colocation \
  +rollout.scheduling_strategy.target=actor \
  enable_offload=true \
  actor.weight_update_mode=disk \
  sglang.mem_fraction_static=0.3
```

AWEX colocation is narrower:

```bash
python3 <grpo-entrypoint> \
  --config <grpo-yaml> \
  scheduler.type=local \
  rollout.backend=sglang:d1t2p1 \
  actor.backend=megatron:d2 \
  actor.weight_update_mode=awex \
  enable_offload=true \
  +sglang.enable_memory_saver=true
```

Do not tune NCCL, process-group, SGLang/vLLM, Megatron, FSDP, Archon, FP8, or OOM
internals here; route those details to `../distributed-engines-backends/`.

## Logging, checkpointing, and recovery

Recommended safe defaults when credentials and long-run storage are unknown:

```yaml
saver:
  freq_epochs: 1
  freq_steps: null
  freq_secs: null

recover:
  mode: disabled
  freq_epochs: 1
  freq_steps: null
  freq_secs: 3600

stats_logger:
  wandb:
    mode: disabled

perf_tracer:
  enabled: false
```

For recoverable long runs:

```yaml
recover:
  mode: auto
  retries: 3
  freq_steps: null
  freq_secs: 3600
```

Recovery checkpoints store model/optimizer/dataloader/RNG-style state and must be loaded
with a compatible backend and parallelism layout. Do not enable recovery with v2 train
controllers; use v1 or disable recovery.

A successful training step logs a message with this shape:

```text
Epoch <epoch>/<total_epochs> Step <step>/<steps_per_epoch> Train step <global_step>/<total_steps> done.
```

Logs and checkpoints are organized under the configured `fileroot` using the experiment
and trial names; see `config-api.md` for path patterns.

## Final safety checklist

Before launching an expensive run, confirm:

- [ ] The validator passes for the exact YAML and override list.
- [ ] `scheduler.type` matches the target environment.
- [ ] Physical GPU budget matches backend strings after colocation.
- [ ] `cluster.fileroot` and name-resolution root are shared for Ray/Slurm.
- [ ] Dataset `type` matches the experiment family.
- [ ] W&B/SwanLab/Trackio credentials are disabled or provided by the user.
- [ ] Recovery is intentionally disabled or configured with compatible v1 engines.
- [ ] Custom dataset/reward/workflow work is routed to `../custom-data-rewards-workflows/`.
- [ ] Backend internals and distributed failure analysis are routed to `../distributed-engines-backends/`.
- [ ] Online service/session/gateway lifecycle work is routed to `../services-cli-operations/`.

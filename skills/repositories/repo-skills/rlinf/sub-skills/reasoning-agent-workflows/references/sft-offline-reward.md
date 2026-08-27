# SFT, offline validation, and reward-model intersections

This reference covers RLinf SFT and reward workflows that intersect with reasoning and agentic work. It is self-contained; use it to construct user-specific configs and launch plans without opening source examples.

## SFT runner model

RLinf uses `SFTRunner` for several supervised-style workflows:

```text
init actor/reward-model worker -> optionally load checkpoint -> repeat train steps
-> periodic eval -> periodic checkpoint -> optional early stopping
```

Unlike online RL, SFT does not create rollout/reward/inference groups. The cluster placement normally only needs an `actor` component, though the actor may still be Megatron or FSDP-distributed.

Common runner fields:

```yaml
runner:
  task_type: sft
  max_epochs: 1              # or -1 when max_steps is the real limit
  max_steps: 6000
  val_check_interval: 1000
  save_interval: 1000
  resume_dir: null
  output_dir: /output/root
  experiment_name: my_sft_run
```

If a VLM SFT config has no `data.train_data_paths`, the VLM SFT entrypoint pattern switches to evaluation-only mode. Treat that as intentional only when the user asks for evaluation.

## VLM SFT

Use for supervised fine-tuning of Qwen2.5-VL, Qwen3-VL, Qwen3-VL-MoE, and related visual-language models.

FSDP-style config skeleton:

```yaml
cluster:
  component_placement:
    actor: all
runner:
  task_type: sft
data:
  type: vlm
  dataset_name: robo2vlmsft
  train_data_paths: /data/train-or-directory
  val_data_paths: /data/eval-or-directory
  prompt_key: question
  choice_key: choices
  answer_key: correct_answer
  image_keys: [image]
  apply_chat_template: true
  use_chat_template: true
  max_prompt_length: 1024
  lazy_loading: true
actor:
  group_name: ActorGroup
  training_backend: fsdp
  micro_batch_size: 1-4
  eval_batch_size: 1-8
  global_batch_size: 8+
  model:
    model_type: qwen2.5_vl
    model_path: /model/path
    precision: fp32|bf16
    is_lora: false
  fsdp_config:
    strategy: fsdp|fsdp2
    sharding_strategy: full_shard|no_shard
    mixed_precision:
      param_dtype: bf16
```

Megatron VLM SFT changes:

```yaml
actor:
  training_backend: megatron
  model:
    tensor_model_parallel_size: 2
    pipeline_model_parallel_size: 1
    model_type: qwen2.5_vl
    seq_length: 1024
  tokenizer:
    tokenizer_model: /model/path
  megatron:
    mbridge: true
    use_hf_ckpt: true
```

Preflight:

- Confirm `data.type: vlm`, a registered `dataset_name`, and non-empty `image_keys`.
- Confirm the model family matches package versions. Newer Qwen3-VL configs require recent Torch, SGLang, and Transformers.
- For LoRA runs, confirm `actor.model.is_lora`, `lora_rank`, `lora_path` if resuming, and the intended trainable modules.
- For video/reward-trend VLM SFT, confirm video root/data root environment variables or concrete paths before launch.

## LoRA in reasoning/SFT configs

LoRA is controlled under `actor.model`:

```yaml
actor:
  model:
    is_lora: true
    lora_rank: 16-64
    lora_path: null          # existing adapter path for resume/continue
```

Use LoRA when the user needs lower memory or parameter-efficient tuning. Avoid enabling it silently: downstream checkpoint layout, sync, and merge expectations differ from full-model training. If `is_lora: false`, `lora_rank` is ignored.

## Offline code-completion validation

The offline code-completion workflow reuses the reasoning runner and a rule reward that calls an LLM-as-judge. It is not the same as live coding online RL.

Distinguish the two modes:

| Mode | `runner.task_type` | Data source | Reward source | Services |
| --- | --- | --- | --- | --- |
| Live coding online RL | `coding_online_rl` | Feedback gathered through RLinf tracking endpoint | User accept/reject feedback | Completion endpoint and feedback endpoint exposed by RLinf |
| Offline validation | `reasoning` | Fixed JSONL code FIM dataset | `reward_type: code_offline` using LLM-as-judge | External judge API via environment variables |

Offline config anchors:

```yaml
runner:
  task_type: reasoning
algorithm:
  adv_type: grpo
  group_size: 8
  recompute_logprobs: true
data:
  type: math
  prompt_key: prompt
  answer_key: solutions
  train_data_paths: [/dataset/train.jsonl]
  val_data_paths: [/dataset/val.jsonl]
reward:
  reward_type: code_offline
  use_prompt: true
```

Required judge variables:

```text
LLMASJUDGE_API_URL
LLMASJUDGE_API_KEY
LLMASJUDGE_MODEL
```

Treat missing judge credentials as a blocker unless the user explicitly asks for config drafting only.

## Reward registry and rule rewards

RLinf’s rule reward registry includes:

| `reward.reward_type` | Typical workflow | Notes |
| --- | --- | --- |
| `math` | Math GRPO/PPO | Uses answer extraction and math verification; `reward_scale` sets positive/negative magnitude. |
| `vqa` | Visual QA reasoning | VLM-specific answer comparison path. |
| `code_offline` | Offline code FIM validation | Calls LLM-as-judge and can use prompts. |
| `searchr1` | SearchR1 multi-turn search | Evaluates search-answer trajectories. |
| `rstar2` | Code-tool math reasoning | Combines code-tool outcomes and math verification. |

Rule reward worker behavior:

- If rollout results lack response text, it decodes generated response ids using `reward.tokenizer`.
- If `reward.use_prompt: true`, it also passes decoded prompts into the reward class.
- If down-sampling is enabled under `algorithm.down_sampling`, reward processing may down-sample generated sequences before actor training.
- `use_reward_model: true` is not implemented in the generic reasoning reward worker path in the inspected version; use a dedicated reward-model training flow instead.

## Reward-model training through SFT runner

Some reward models are trained as supervised models using `SFTRunner` and a reward worker/actor wrapper. A representative reward training config uses:

```yaml
runner:
  task_type: sft
  early_stop:
    enabled: true
    monitor: val_loss
data:
  train_data_paths: /processed/train.pt
  val_data_paths: /processed/val.pt
actor:
  group_name: RewardActorGroup
  training_backend: fsdp
  micro_batch_size: 32
  global_batch_size: 64
  model:
    model_type: resnet
    arch: resnet18
    pretrained: true
    precision: fp32
```

Preflight:

- Confirm preprocessing has produced split `.pt` payloads or the expected serialized reward dataset format.
- Confirm `actor.model.model_type` matches an installed model implementation.
- Confirm early-stop metric names match metrics emitted by the reward worker.
- Route model-registration changes to `extension-development` if the reward model type is not already supported.

## SFT to RL handoff

After SFT, a reasoning/agentic RL run typically needs:

1. A model checkpoint exported or converted into the format expected by the chosen actor backend.
2. `rollout.model.model_path` and `actor.tokenizer.tokenizer_model` updated to the SFT checkpoint/tokenizer.
3. For Megatron training from HF checkpoints, `actor.megatron.use_hf_ckpt: true` and converter metadata aligned with tensor/pipeline parallel sizes.
4. For LoRA checkpoints, a decision whether to continue LoRA training, merge adapters, or load base plus adapter.
5. A reduced learning rate and careful KL/logprob monitoring when starting RL from SFT.

## Offline / supervised preflight checklist

Before launching SFT, offline judge, or reward-model training, verify:

- `runner.task_type` matches the workflow (`sft`, `reasoning`, or `coding_online_rl`).
- The selected runner creates the expected groups: only actor for SFT/reward training; actor/rollout/reward/inference for reasoning; online router/server rollout for coding online.
- `data.train_data_paths` and `data.val_data_paths` are concrete and readable from all workers.
- VLM configs include `image_keys`; video configs include video/data roots.
- `actor.training_backend` has its backend-specific block (`fsdp_config` or `megatron`).
- `actor.global_batch_size` is compatible with data size and micro-batch size.
- External judge/service environment variables are present for offline rewards.
- The run is not actually an embodied simulator workflow; route those to `embodied-workflows`.

# AReaL configuration cheatsheet

## Loading model

AReaL training drivers normally use:

```python
from areal.api.cli_args import GRPOConfig, load_expr_config
config, config_path = load_expr_config(args, GRPOConfig)
```

The command-line shape is:

```bash
python train_driver.py --config config.yaml key=value nested.key=value +new.key=value
```

Rules:

- `--config` points to a YAML file.
- Plain `key=value` overrides an existing config key.
- `+key=value` adds a Hydra/OmegaConf key not already present in the YAML.
- Config class must match the trainer: `GRPOConfig`/`PPOConfig` for RL, `SFTConfig` for SFT, `DPOConfig` for DPO, `RWConfig` for reward-model training.
- `load_expr_config()` writes a resolved config under the experiment log path on rank 0.

## Main config classes

| Class | Use | Required downstream route |
|---|---|---|
| `GRPOConfig` | GRPO-style online RL; subclass placeholder of `PPOConfig` for compatibility | `post-training-experiments` |
| `PPOConfig` | PPO-family online RL, agentic RL, teacher/distillation variants | `post-training-experiments` |
| `SFTConfig` | supervised fine-tuning | `post-training-experiments` |
| `DPOConfig` | preference optimization with actor/reference engines | `post-training-experiments` |
| `RWConfig` | reward-model training | `post-training-experiments` |
| `InferenceEngineConfig` | rollout/inference worker config | `distributed-engines-backends` and `services-cli-operations` |
| `TrainEngineConfig` | actor/critic/ref/teacher train engine config | `distributed-engines-backends` |
| `AgentConfig` | agent workflow execution settings under `rollout.agent` | `custom-data-rewards-workflows` |

## Shared required fields

Most experiment configs include:

```yaml
experiment_name: myexp
trial_name: trial1
cluster:
  n_nodes: 1
  n_gpus_per_node: 8
scheduler:
  type: local      # local, ray, or slurm
stats_logger:
  fileroot: /shared-or-local/logroot
saver:
  fileroot: /shared-or-local/logroot
recover:
  mode: auto
```

Avoid underscores in `experiment_name` and `-` or `/` in `trial_name` when matching AReaL's validation rules.

## Backend fields

Modern single-controller configs use per-engine backend fields:

```yaml
rollout:
  backend: sglang:d4
actor:
  backend: fsdp:d4
critic: null
ref: null
```

Examples:

- `rollout.backend=sglang:d2t4` — two SGLang rollout replicas, TP=4 each.
- `rollout.backend=vllm:d1t8` — one vLLM replica tensor-parallel across eight GPUs.
- `actor.backend=fsdp:d8` — FSDP actor world across eight ranks.
- `actor.backend=megatron:d2p2t4` — Megatron DP=2, PP=2, TP=4.
- `actor.backend=archon:d4p2t2` — Archon DP-shard=4, PP=2, TP=2.

Use the backend checker in `sub-skills/distributed-engines-backends/scripts/check_backend_plan.py` before launching.

## Dataset config

A dataset config is usually under `train_dataset` and `valid_dataset`:

```yaml
train_dataset:
  path: openai/gsm8k
  split: train
  type: rl
  batch_size: 1024
  max_length: 1024
valid_dataset:
  path: openai/gsm8k
  split: test
  type: rl
  batch_size: 1024
```

Built-in dataset routing recognizes GSM8K, Geometry3K, CLEVR Count 70K, VIRL39K, HH-RLHF, and TORL data names. Custom datasets should either be loadable from disk by Hugging Face `load_from_disk()` or have a custom loader/workflow contract; route to `custom-data-rewards-workflows`.

## Generation config

`GenerationHyperparameters` commonly appears as `gconfig` and `eval_gconfig`:

```yaml
gconfig:
  n_samples: 4
  max_new_tokens: 1024
  temperature: 1.0
  top_p: 1.0
  greedy: false
```

`n_samples` controls grouped rollout for GRPO-style algorithms. `eval_gconfig` may override temperature or decoding for evaluation. Backend support for every decoding option is not identical; check backend references before using beam search or unusual stop behavior.

## Agent workflow config

Agent workflow fields live under `rollout.agent`:

```yaml
rollout:
  agent:
    agent_cls_path: mypkg.agent.MyAgent
    mode: inline       # inline, subproc, online
    turn_discount: 0.9
    export_style: individual
    tool_call_parser: qwen
```

Route to `custom-data-rewards-workflows` for class contracts and to `services-cli-operations` for online sessions/services.

## Legacy migration warning

Removed keys `behave_imp_weight_cap` and `behave_imp_weight_mode` are intercepted and should be migrated to `rejection_sampling`:

```yaml
# disabled
rejection_sampling: null

# old token_mask with cap X
rejection_sampling:
  level: token
  action: mask
  metric: ratio
  upper: X

# old token_truncate with cap X
rejection_sampling:
  level: token
  action: clamp
  metric: ratio
  upper: X
```

## Safe config validation

Use the bundled validators before an expensive run:

```bash
python sub-skills/post-training-experiments/scripts/validate_experiment_config.py \
  --kind grpo --config config.yaml \
  -- scheduler.type=local actor.backend=fsdp:d4

python sub-skills/distributed-engines-backends/scripts/check_backend_plan.py \
  rollout.backend=sglang:d4 actor.backend=fsdp:d4 cluster.n_nodes=1 cluster.n_gpus_per_node=8
```

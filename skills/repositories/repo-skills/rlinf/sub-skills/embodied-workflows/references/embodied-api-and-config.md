# Embodied API and configuration map

This reference gives future agents a self-contained map of RLinf embodied config structure and runtime wiring. It is for planning and static review, not for launching expensive jobs.

## Entrypoint responsibilities

An embodied training entrypoint performs these steps:

1. Hydra composes a YAML config from `defaults` and command-line overrides.
2. RLinf validates `runner.task_type`, model type, environment type, and backend-specific constraints.
3. A `Cluster` is built from `cluster` config.
4. `HybridComponentPlacement` maps component names to local GPUs, node groups, or hardware ranks.
5. Worker groups are created:
   - `actor`: FSDP/FSDP2 policy worker or algorithm-specific actor.
   - `rollout`: HuggingFace multi-step rollout worker for action generation/logprobs/values.
   - `env`: synchronous, asynchronous, RTC, offload, or simulator/robot-specific env worker.
   - `reward` (optional): model/API reward worker for ResNet, VLM, or buffered VLM history rewards.
6. The runner initializes workers, syncs weights, drives rollouts, reward combination, advantage computation, actor update, metrics, checkpoints, and validation.

Channel directions in the embodied loop:

```text
rollout_channel: env -> rollout     (observations / inference requests)
env_channel:     rollout -> env     (actions / RTC responses)
actor_channel:   env -> actor       (trajectories or micro-batches)
reward_channel:  env <-> reward     (reward inputs and outputs when enabled)
```

## Common top-level config sections

| Section | Purpose | Key fields to inspect |
| --- | --- | --- |
| `defaults` | Hydra preset composition | `env/<preset>@env.train`, `env/<preset>@env.eval`, `model/<preset>@actor.model`, `hybrid_engines/<backend>@actor.fsdp_config`, weight syncer. |
| `hydra` | Runtime config search behavior | `searchpath` if config presets live outside the active config directory; `run.dir` and `output_subdir` if reproducibility matters. |
| `cluster` | Nodes/component placement | `num_nodes`, `component_placement`, `node_groups`, optional `hardware`, profiling. Syntax details route to setup-and-cluster. |
| `runner` | Task and run lifecycle | `task_type`, `only_eval`, `max_epochs`, `max_steps`, `save_interval`, `val_check_interval`, `resume_dir`, `ckpt_path`, `logger`, `weight_sync_interval`, `use_training_pipeline`, async/decoupled flags. |
| `algorithm` | Advantage/loss/reward math | `adv_type`, `loss_type`, `group_size`, `reward_type`, `logprob_type`, `entropy_type`, `gamma`, `gae_lambda`, `clip_ratio_*`, SAC replay/entropy fields, offline loss fields. |
| `env` | Environment worker config | `group_name`, `enable_offload`, `train`, `eval`, `data_collection`, `video_cfg`, `total_num_envs`, horizons, reset and termination flags. |
| `rollout` | Action generation/inference | `group_name`, `backend`, `sampling_params`, `model`, `pipeline_stage_num`, `rlt_feature_model`, `recompute_logprobs`. |
| `actor` | Trainable policy worker | `group_name`, `training_backend`, `model`, `micro_batch_size`, `global_batch_size`, optimizer, FSDP config, sync flags. |
| `reward` | Optional learned reward | `use_reward_model`, `worker_type`, `group_name`, `reward_mode`, `reward_weight`, `env_reward_weight`, `model`, `api`, `history_buffers`. |
| `data` | Offline/SFT/reward datasets | `train_data_paths`, `val_data_paths`, `dataset_type`, `dataset_name`, `repo_id`, `advantage_tag`, `returns_tag`, `demo_buffer`, loader fields. |

## `runner.task_type` map

| Task type | Relevant to this sub-skill? | Meaning |
| --- | --- | --- |
| `embodied` | Primary | Online simulator/robot/world-model training with actor, rollout, env, optional reward. |
| `embodied_eval` | Adjacent | Standalone eval uses env+rollout but no actor update; route operational details to operations-evaluation-debugging. |
| `offline` | Adjacent | Offline RL such as D4RL/IQL; actor trains from dataset, env/rollout are only needed for eval. |
| `sft` | Adjacent | VLA/VLM/reward/value supervised training that supplies checkpoints or labels for embodied workflows. |
| `reasoning`, `reasoning_eval`, `coding_online_rl` | Out of scope | Route to non-embodied skills. |

## Supported environment values

Installed inspection confirmed these environment type strings:

```text
maniskill, maniskill_rlt, libero, robotwin, isaaclab, metaworld, behavior,
calvin, robocasa, robocasa365, realworld, frankasim, habitat, opensora_wm,
wan_wm, genesis, embodichain, roboverse, d4rl, polaris
```

Static config review should distinguish **direct env type** from **Hydra default preset**. Root training configs often specify `env/<preset>@env.train` and `env/<preset>@env.eval`; the actual `env_type` may live inside those presets after composition. If a root config lacks `env.train.env_type` directly, infer the family from the preset name for planning, then treat exact type as unresolved until composed or verified.

Special env checks:

- `isaaclab` requires an init task id that maps to a registered IsaacLab task.
- `behavior` needs OmniGibson/Isaac Sim paths and headless flags.
- `realworld` uses hardware enumeration, robot identifiers, controller nodes, and safety constraints.
- `opensora_wm` / `wan_wm` require world-model checkpoints and initialization data; they may not provide proprioception or wrist views.
- `d4rl` appears under offline configs; it is not an online embodied training env.

## Supported model values

Installed inspection confirmed these model type strings:

```text
qwen2.5, qwen2.5_vl, qwen3, qwen3_vl, qwen3_moe, openvla, openvla_oft,
molmoact2, openpi, openpi_rlinf, starvla, mlp_policy, rlt_mlp_policy,
rlt_td3_mlp_policy, gr00t, dexbotic_pi, dexbotic_dm0, dreamzero, cnn_policy,
flow_policy, cma, lingbotvla, abot_m0, resnet, cfg_model, recap_value_model,
steam_value_model, qwen3_vl_moe, deepseek_v3, gr00t_n1d6, gr00t_n1d7, evo1
```

When a root config only imports `model/<preset>@actor.model`, infer the model family from the preset name for planning, but confirm the composed `actor.model.model_type` before launch.

## Algorithm/worker selection

`algorithm.loss_type` drives the actor worker class in embodied training:

| `loss_type` | Worker/runner implications |
| --- | --- |
| `actor_critic` or actor-style losses | Standard embodied FSDP actor; can support PPO/GRPO-style updates and optional training pipeline. |
| `embodied_sac` | SAC actor worker; training pipeline is not supported; replay-buffer and entropy-tuning fields matter. |
| `rlt_ac`, `rlt_td3` | RLT actor workers; verify stage-specific reference feature model and intervention/switch flags. |
| `embodied_dagger` | DAgger worker; expert/action source must be configured. |
| `embodied_nft` | NFT worker; route unfamiliar source changes to extension-development. |
| `decoupled_actor_critic` | Async PPO runner; validation is not implemented in that async path. |
| `offline_iql` | Offline runner rather than embodied runner; dataset and eval settings dominate. |

`runner.use_training_pipeline: True` streams packed actor micro-batches from env to actor while rollout progresses. It currently belongs to embodied FSDP PPO/GRPO-style actor training, not SAC, DAgger, NFT, or async real-world SAC.

## Environment section details

The following fields frequently matter when adapting a config:

```yaml
env:
  group_name: EnvGroup
  enable_offload: true        # optional top-level default
  train:
    env_type: <family>        # may come from Hydra preset
    rollout_epoch: 1
    total_num_envs: 8
    group_size: ${algorithm.group_size}
    auto_reset: true
    ignore_terminations: false
    use_fixed_reset_state_ids: false
    max_episode_steps: 80
    max_steps_per_rollout_epoch: 80
    enable_offload: true
    video_cfg:
      save_video: false
      video_base_dir: ${runner.logger.log_path}/video/train
  eval:
    total_num_envs: 16
    use_fixed_reset_state_ids: true
    video_cfg:
      save_video: false
      video_base_dir: ${runner.logger.log_path}/video/eval
```

Review rules:

- `max_steps_per_rollout_epoch` should be compatible with `actor.model.num_action_chunks` when that field is present.
- `group_size` in GRPO configs should be greater than 1 and match the env group size.
- `ignore_terminations`, `auto_reset`, and fixed reset-state flags change what constitutes a comparable rollout.
- `video_cfg.save_video: true` needs a `video_base_dir`; video makes runs slower and larger.
- `data_collection.enabled: true` needs `save_dir` and `export_format` (`pickle` or `lerobot`).

## Actor and rollout model fields

Important VLA/VLM fields vary by model family but commonly include:

```yaml
actor:
  group_name: ActorGroup
  training_backend: fsdp
  model:
    model_type: openvla_oft
    model_path: <checkpoint_dir>
    lora_path: <lora_dir_or_null>
    is_lora: true
    precision: bf16
    num_action_chunks: 8
    add_value_head: true
    unnorm_key: <dataset_or_env_key>
rollout:
  group_name: RolloutGroup
  sampling_params:
    do_sample: true
    temperature_train: 1.0
    temperature_eval: 0.6
```

For actor/rollout weight sync, both sides must agree on the model architecture and checkpoint. For OpenVLA/OpenVLA-OFT configs, `actor.model.model_path` and `rollout.model.model_path` commonly point to the same base model; LoRA paths may be actor-only or shared depending on the recipe. For OpenPI/OpenPI_RLinf, normalization-stat paths and action horizon are as important as the checkpoint itself.

## Reward config fields

When `reward.use_reward_model: true`, the embodied entrypoint creates a reward group unless `reward.standalone_realworld` is set. Model and API reward modes use the same top-level flow: env sends reward inputs, reward worker returns scalar/model outputs, env combines them with environment reward.

```yaml
reward:
  use_reward_model: true
  group_name: RewardGroup
  worker_type: model          # or api
  reward_mode: terminal       # per_step, terminal, history_buffer
  reward_weight: 1.0
  env_reward_weight: 0.0
  model:
    model_type: resnet        # resnet, vlm, buffered_vlm
    model_path: <checkpoint_or_base_model>
```

For buffered VLM Trend rewards, also inspect:

- `reward.model.input_builder_name` and `reward.model.reward_parser_name`.
- `reward.model.history_buffers.*.history_size`, `min_history_size`, and `history_keys`.
- `reward.interval_reward` behavior before enough history is available.
- `reward.worker_type: api`, `reward.api.api_base`, and optional router/server placement if using OpenAI-compatible/SGLang inference.

## Data collection and offline/SFT sections

Config blocks can enable dataset creation while training or run pure offline/SFT flows:

```yaml
env:
  eval:
    data_collection:
      enabled: true
      save_dir: ${runner.logger.log_path}/collected_data
      export_format: pickle     # or lerobot
      only_success: true
      robot_type: panda
      fps: 10
```

Offline and SFT fields:

```yaml
runner:
  task_type: offline            # or sft
data:
  dataset_type: d4rl            # offline example
  task_name: halfcheetah-medium-v2
  train_data_paths: <path_or_manifest>
  val_data_paths: <path_or_manifest>
  advantage_tag: <tag>          # CFG/RECAP/STEAM handoff
actor:
  training_backend: fsdp        # or megatron for supported VLM SFT
```

## Static review checklist

Use this checklist before recommending any launch:

- `runner.task_type` matches the intended workflow.
- Actor, rollout, env, and optional reward groups have placement owners.
- Env family and model family are compatible with the selected dependency environment.
- Model and dataset paths are real or explicitly provided as environment variables; placeholders are not left in launch-critical fields.
- GRPO group size, fixed reset policy, and env group size are coherent.
- SAC/RLPD configs have replay-buffer/demo data decisions.
- Reward configs have correct `reward_mode`, model/API type, parser/input builder, and reward weighting.
- Videos/data collection have output paths and disk-space implications.
- Real-world configs pass safety gates before any robot-affecting action.

# Reward data, offline RL, and SFT intersections

This reference covers embodied-adjacent workflows that create data or checkpoints for online RLinf embodied training: episode collection, reward-model datasets, VLM Trend rewards, real-robot replay buffers, D4RL/offline IQL, RECAP/STEAM/CFG, and VLA/VLM SFT.

## Episode collection during embodied runs

RLinf can wrap envs with an episode collector through config. It writes completed episodes asynchronously so training is not blocked.

```yaml
env:
  eval:
    data_collection:
      enabled: true
      save_dir: ${runner.logger.log_path}/collected_data
      export_format: pickle      # or lerobot
      only_success: false
      robot_type: panda
      fps: 10
      finalize_interval: 100
```

Formats:

| Format | Output | Use when |
| --- | --- | --- |
| `pickle` | one `.pkl` per episode, with raw observations/actions/rewards/infos | Reward-model preprocessing, custom diagnostics, preserving exact env data. |
| `lerobot` | Parquet data plus metadata JSON/JSONL | VLA SFT, LeRobot-compatible tools, normalization-stat calculation. |

Expected pickle episode shape:

```python
{
  "rank": int,
  "env_idx": int,
  "episode_id": int,
  "success": bool,
  "observations": list,   # includes reset observation at index 0
  "actions": list,
  "rewards": list,
  "terminated": list,
  "truncated": list,
  "infos": list,
}
```

Observation key lookup used by data export:

- Main image: `main_images`, then `image`, then `full_image`.
- Extra view: `extra_view_images`, then `extra_view_image`; stacked extra views fan out by index.
- State: `states`, then `state`.

Success detection checks recent `info` entries and nested `final_info`/`episode` fields for `success_once`, `success_at_end`, or `success`; if none are found it falls back to an internal episode-success flag.

Planning cautions:

- `only_success: true` saves disk but removes failures needed for reward classifiers.
- `lerobot` export needs consistent image/state/action dimensions across episodes.
- Distributed runs need rank-aware filenames; do not merge raw files by hand without checking collisions.
- Video/data collection increases I/O; shrink env count and horizon for smoke runs.

## ResNet reward dataset workflow

Use this when a single-frame image classifier should score task success.

1. Collect raw episodes in `pickle` format with both successes and failures.
2. Convert episodes into `train.pt` and `val.pt` reward splits.
3. Train a ResNet reward model with `actor.model.model_type: resnet`.
4. Enable `reward.use_reward_model: true` in the embodied RL config.

Preprocessing launch shape:

```bash
python <resnet-reward-preprocess-entrypoint> \
  --raw-data-path <collected_data_dir> \
  --output-dir <processed_reward_data_dir> \
  --num-samples-per-episode 5 \
  --val-split 0.2
```

Output schema:

```python
{
  "images": list[torch.Tensor],
  "labels": list[int],          # 1 success, 0 fail
  "metadata": dict,
}
```

Reward training config essentials:

```yaml
runner:
  task_type: sft
  logger:
    log_path: <reward_log_dir>
data:
  train_data_paths: <processed_reward_data_dir>/train.pt
  val_data_paths: <processed_reward_data_dir>/val.pt
actor:
  model:
    model_type: resnet
    arch: resnet18
    pretrained: false
    image_size: [3, 224, 224]
```

Online inference fields:

```yaml
reward:
  use_reward_model: true
  group_name: RewardGroup
  reward_mode: terminal       # terminal or per_step
  reward_threshold: 0.5
  reward_weight: 1.0
  env_reward_weight: 0.0
  model:
    model_type: resnet
    model_path: <reward_checkpoint>
```

Troubleshooting checks:

- If all labels are one class, inspect `only_success`, success keys, and sampling ratio.
- If images are missing, check observation keys (`main_images` vs `image` vs `full_image`).
- If reward inference is slow, use terminal mode or reduce image size/batch size before changing reward weights.

## VLM Trend reward workflow

Use this when progress is judged from short dual-view history windows rather than a single image.

1. Collect raw `pickle` episodes that include `main_images` and `extra_view_images`/`third_view_images`.
2. Slice episodes into fixed-length windows and label trend as `positive`, `negative`, or `unclear`.
3. Fine-tune a Qwen-VL-style VLM reward model with LoRA or full SFT.
4. Use `reward.model.model_type: buffered_vlm` during online RL.

Preprocessing launch shape:

```bash
python <vlm-trend-preprocess-entrypoint> \
  --raw-data-path <collected_data_dir> \
  --output-dir <processed_vlm_trend_dir> \
  --window-size 5 \
  --stride 1 \
  --delta-threshold 0.05
```

Processed layout:

```text
<processed_vlm_trend_dir>/
  dataset_info.json
  train/segments.jsonl
  train/pkl/*.pkl
  eval/segments.jsonl
  eval/pkl/*.pkl
```

VLM SFT config essentials:

```yaml
runner:
  task_type: sft
data:
  type: vlm
  dataset_name: vlm_trend_reward_sft
  train_data_paths: <processed_vlm_trend_dir>/train/segments.jsonl
  val_data_paths: <processed_vlm_trend_dir>/eval/segments.jsonl
  video_root: <processed_vlm_trend_dir>
  video_nframes: 5
actor:
  training_backend: fsdp       # megatron is supported by VLM SFT paths when configured
  model:
    model_type: qwen3_vl       # or qwen2.5_vl / qwen3_vl_moe where supported
    model_path: <base_vlm_checkpoint>
    is_lora: true
    lora_rank: 16
```

Online buffered VLM reward essentials:

```yaml
reward:
  use_reward_model: true
  group_name: RewardGroup
  worker_type: model          # or api
  reward_mode: history_buffer
  history_reward_assign: true
  reward_weight: 1.0
  env_reward_weight: 0.0
  model:
    model_type: buffered_vlm
    model_path: <base_vlm_checkpoint>
    lora_path: <trained_reward_lora>
    precision: bf16
    input_builder_name: vlm_trend_reward_input_builder
    reward_parser_name: vlm_trend_reward_parser
    input_builder_params:
      default_task_description: <task_text>
    reward_parser_params:
      positive_reward: 1.0
      negative_reward: -0.2
      unclear_reward: 0.0
      invalid_reward: 0.0
    history_buffers:
      history_window:
        history_size: 5
        min_history_size: 5
        input_interval: 1
        history_keys: [main_images, extra_view_images]
        input_on_done: false
    interval_reward: 0.0
```

API mode uses `reward.worker_type: api` and an OpenAI-compatible endpoint in `reward.api.api_base`. If `api_base` is empty, RLinf can launch a managed server/router when the router config and placement are present; route server details to setup-and-cluster.

## Reward worker interaction with embodied rollout

When reward model inference is enabled:

```text
Env worker steps env and stores raw env reward
Env worker sends reward input/history to Reward worker
Reward worker returns model scalar or parsed VLM reward
Env worker computes final reward:
  final_reward = env_reward_weight * env_reward + reward_weight * model_reward
Actor later computes advantages/returns from final rewards
```

Important implications:

- Learned reward does not replace bootstrap handling; bootstrap can still affect the last step according to algorithm config.
- `reward_threshold` applies to ResNet sigmoid outputs, not to buffered VLM parser outputs.
- `history_buffer` mode returns `interval_reward` until enough frames are available.
- Combining env reward and learned reward requires deliberate scale checks; do not set both weights blindly.

## Real-robot replay buffer and RLPD

Real-world RLPD uses high-quality teleoperated demonstrations as a prior buffer. Collection writes trajectories with:

```python
{
  "transitions": {
    "obs": {"states": ..., "main_images": ...},
    "next_obs": {"states": ..., "main_images": ...},
    "action": ...,
    "rewards": ...,
    "dones": ...,
    "terminations": ...,
    "truncations": ...,
  },
  "intervene_flags": ...,
}
```

RLPD/SAC configs then use fields such as `algorithm.demo_buffer` or data path fields to load prior data. Verify:

- The number of successful demonstrations matches `runner.num_data_episodes` or the intended target.
- `intervene_flags` are present for expert data.
- Action dimension matches the online policy (`no_gripper`, gripper type, dual-arm schema).
- The replay buffer is not accidentally mixed with a different task or robot.

## D4RL and offline IQL

D4RL recipes are embodied-adjacent offline RL, not online simulator training.

```yaml
runner:
  task_type: offline
  only_eval: false
  max_steps: 1000000
  local_update_steps: 1000
  val_check_interval: 100000
algorithm:
  loss_type: offline_iql
  gamma: 0.99
  tau: 0.005
  expectile: 0.7
  temperature: 3.0
data:
  dataset_type: d4rl
  task_name: halfcheetah-medium-v2
  dataset_path: null
```

Offline runner behavior:

- Actor trains from local dataset.
- Env/rollout workers are created only if evaluation is enabled.
- Checkpoints and metrics follow normal logger paths.
- If adapting to a new offline dataset, route source-code changes to extension-development.

## RECAP / STEAM / CFG policy optimization

These pipelines convert LeRobot-style data into advantage labels and then train a policy with classifier-free guidance.

### RECAP flow

```text
LeRobot SFT data + rollout data
  -> compute discounted returns sidecars
  -> train value model on normalized returns
  -> compute frame advantages
  -> CFG policy training uses positive/high-advantage and negative/low-advantage samples
```

Key handoff tags:

- `returns_tag`: written by return computation and read by value/advantage steps.
- `advantage_tag`: written by advantage computation and read by CFG training.

### STEAM flow

```text
LeRobot SFT data + rollout data
  -> train ensemble progress critics
  -> compute conservative ensemble advantages
  -> CFG policy training uses advantage-tagged samples
```

Key handoff tag:

- `advantage_tag`: the advantage computation step writes `advantages_<tag>` sidecars, and CFG reads the same tag.

### CFG training

CFG training is usually `runner.task_type: sft` with `model_type: cfg_model` or OpenPI-derived policy fields. Planning checks:

- SFT and rollout datasets use compatible embodiment/action schemas.
- Advantage tags match exactly across stages.
- Normalization statistics correspond to the target policy and embodiment.
- Generated checkpoint path is recorded for later online RL or evaluation.

## VLA SFT intersections

VLA SFT creates the prior checkpoint used by online embodied RL.

OpenPI/OpenPI_RLinf SFT planning fields:

```yaml
runner:
  task_type: sft
data:
  train_data_paths: <lerobot_dataset_or_manifest>
  val_data_paths: <optional_eval_dataset>
  repo_id: <dataset_repo_or_asset_id>
actor:
  training_backend: fsdp
  model:
    model_type: openpi          # or openpi_rlinf, dreamzero, evo1, lingbotvla
    model_path: <base_checkpoint>
    is_lora: false             # true for LoRA recipes
    openpi:
      assets_dir: <norm_stats_root>
      asset_id: <norm_stats_subdir>
```

DreamZero SFT planning fields:

- `actor.model.model_path` for a full checkpoint, or component paths for cold start.
- `actor.model.metadata_json_path` or equivalent normalization metadata.
- `data.train_data_paths` can be a list for mixture SFT; each entry may include dataset path, embodiment tag, metadata, and weight.
- Action horizon and temporal block count must match dataset chunking.

Qwen-VL SFT planning fields:

- `model_type` among supported Qwen-VL variants.
- `data.train_data_paths` / `val_data_paths` and dataset key mapping (`prompt`, choices/answers, image keys).
- `actor.training_backend` (`fsdp` or `megatron` where configured).
- Conversion to HuggingFace format is an operations/checkpoint task, not this sub-skill.

## Common data mistakes

- Raw pickle episodes contain no `main_images`; reward preprocessing produces empty splits.
- `only_success: true` was used for a binary reward dataset, causing no negatives.
- Train/eval windows from the same episode are split across VLM Trend train/eval; keep split by episode.
- VLM Trend windows lack a second view; update collection keys or choose ResNet reward instead.
- RECAP/STEAM tag mismatch: CFG cannot find sidecar advantages.
- OpenPI/DreamZero normalization stats come from a different embodiment or action dimension.
- Real-world replay buffer and online config disagree on gripper or dual-arm action shape.

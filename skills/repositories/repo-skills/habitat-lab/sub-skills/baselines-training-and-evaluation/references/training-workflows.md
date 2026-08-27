# Training And Evaluation Workflows

Habitat-Baselines training is usually a Hydra config plus overrides. The active trainer is selected by `habitat_baselines.trainer_name`, looked up through `baseline_registry`, instantiated with the composed config, then run via `trainer.train()` or `trainer.eval()`.

## Decision Tree

1. Identify the task family.
   - PointNav: start with `pointnav/ppo_pointnav_example.yaml` for samples, `pointnav/ppo_pointnav.yaml` or `pointnav/ddppo_pointnav.yaml` for larger runs.
   - ImageNav/ObjectNav/InstanceImageNav: start from the matching `imagenav/`, `objectnav/`, or `instance_imagenav/` config.
   - Rearrangement/HRL: start with `rearrange/rl_skill.yaml`, `rearrange/rl_rearrange.yaml`, or `rearrange/rl_hierarchical.yaml` depending on the task.
   - SocialNav/SocialRearrange: start with `social_nav/social_nav.yaml`, `social_rearrange/pop_play.yaml`, or `social_rearrange/plan_pop.yaml` and expect Habitat 3 assets.
   - EQA imitation learning: start with `eqa/il_eqa_cnn_pretrain.yaml`, then `eqa/il_vqa.yaml` or `eqa/il_pacman_nav.yaml`.
2. Choose train versus eval.
   - Training is the default: `habitat_baselines.evaluate=False`.
   - Evaluation: `habitat_baselines.evaluate=True` plus a valid checkpoint or explicit no-checkpoint evaluator setting.
3. Decide run scale.
   - Smoke/sanity: reduce `habitat_baselines.num_environments`, `habitat_baselines.num_updates`, and visual resolution if the config permits.
   - Research-scale: verify CUDA, dataset locations, process counts, checkpoint directories, and wall-clock expectations before launching.
4. Decide trainer.
   - `ppo`: single-process PPO trainer registered by `PPOTrainer`.
   - `ddppo`: distributed PPO path registered by the same `PPOTrainer` class and configured for distributed training.
   - `ver`: variable-experience rollout trainer for straggler-heavy workloads.
   - IL names such as `eqa-cnn-pretrain`, `vqa`, and `pacman`: EQA supervised/imitation workflows.

## RL Training Patterns

Minimal sample PointNav training:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ppo_pointnav_example.yaml
```

Switch to VER:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ppo_pointnav_example.yaml \
  habitat_baselines.trainer_name=ver
```

Bound a smoke run:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ppo_pointnav_example.yaml \
  habitat_baselines.num_environments=1 \
  habitat_baselines.num_updates=2 \
  habitat_baselines.total_num_steps=-1 \
  habitat_baselines.num_checkpoints=1
```

Important config constraints from `BaseRLTrainer`:

- Exactly one of `habitat_baselines.num_updates` and `habitat_baselines.total_num_steps` should drive training; set the unused one to `-1` or `-1.0`.
- Exactly one of `habitat_baselines.num_checkpoints` and `habitat_baselines.checkpoint_interval` should drive checkpoint cadence; set the unused one to `-1`.
- GPU-GPU paths, Habitat-Sim CUDA support, and distributed DD-PPO are environment-sensitive; inspect first rather than assuming they are available.

## IL / EQA Workflows

EQA IL workflows use the same CLI but different config groups and trainers:

```bash
python -u -m habitat_baselines.run --config-name=eqa/il_eqa_cnn_pretrain.yaml
python -u -m habitat_baselines.run --config-name=eqa/il_vqa.yaml
python -u -m habitat_baselines.run --config-name=eqa/il_pacman_nav.yaml
```

Evaluation uses the same flag:

```bash
python -u -m habitat_baselines.run \
  --config-name=eqa/il_pacman_nav.yaml \
  habitat_baselines.evaluate=True \
  habitat_baselines.eval_ckpt_path_dir=data/eqa/nav/checkpoints/epoch_5.ckpt
```

EQA configs often assume Matterport3D scenes, task datasets, and staged checkpoints from earlier EQA components.

## Checkpoints, Resume, And Evaluation

Training checkpoint outputs default to `habitat_baselines.checkpoint_folder`, commonly `data/checkpoints`. Evaluation reads `habitat_baselines.eval_ckpt_path_dir`, which can be a checkpoint file or a directory polled for multiple checkpoints.

Use a single checkpoint file:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ddppo_pointnav.yaml \
  habitat_baselines.evaluate=True \
  habitat_baselines.eval_ckpt_path_dir=data/checkpoints/ckpt.0.pth
```

Evaluate with new eval-time overrides instead of checkpoint-saved config:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ddppo_pointnav.yaml \
  habitat_baselines.evaluate=True \
  habitat_baselines.load_resume_state_config=False \
  habitat_baselines.eval.video_option='["disk"]' \
  habitat_baselines.video_dir=video_eval
```

`load_resume_state_config=True` means the original saved config can override new command-line changes during resume/eval. Set it to `False` when the user's explicit eval overrides should win.

## Output Directories

Common outputs are controlled by these keys:

| Key | Purpose |
| --- | --- |
| `habitat_baselines.log_file` | Training/eval log file path |
| `habitat_baselines.tensorboard_dir` | TensorBoard event output |
| `habitat_baselines.video_dir` | Disk video output when enabled |
| `habitat_baselines.checkpoint_folder` | Training checkpoints |
| `habitat_baselines.eval_ckpt_path_dir` | Checkpoint file or folder to evaluate |
| `habitat_baselines.eval.video_option` | Video destinations such as `[]`, `["disk"]`, or TensorBoard options |
| `habitat_baselines.test_episode_count` | Number of eval episodes when supported by the evaluator |

For video output, make sure video options and directories match. `disk` requires a non-empty `video_dir`; TensorBoard video requires a non-empty `tensorboard_dir`.

## Trainer And Registry APIs

Useful inspection snippets:

```python
from habitat_baselines.common.baseline_registry import baseline_registry
from habitat_baselines.config.default import get_config

cfg = get_config("pointnav/ppo_pointnav_example.yaml")
trainer_cls = baseline_registry.get_trainer(cfg.habitat_baselines.trainer_name)
print(trainer_cls)
```

```python
from habitat_baselines.run import execute_exp

# Only call this after confirming data, simulator, and runtime safety.
execute_exp(cfg, "train")
```

Known trainer facts:

- `BaseTrainer()` has abstract `train()`, `eval()`, `save_checkpoint()`, and `load_checkpoint()` methods.
- `BaseRLTrainer(config)` asserts a non-null config and validates update/checkpoint scheduling.
- `PPOTrainer(config=None)` exists but real training requires a valid config before methods are used.
- `PPOTrainer` registers both `ppo` and `ddppo` trainer names.
- `VERTrainer` registers `ver` and inherits PPO behavior with variable-experience rollout features.

## CPU/GPU/Data Caveats

A CPU-only Python environment can inspect imports, config composition, CLI help, and many pure-Python APIs. Real training/evaluation often needs:

- Habitat-Sim with the right physics/graphics/CUDA features.
- Datasets and scenes matching the config's `habitat.dataset.*` paths.
- Downloaded checkpoints for evaluation or pretrained-policy tests.
- Sufficient GPU memory, CPU cores, shared memory, and multiprocessing support.
- Optional media dependencies for video writing and TensorBoard visualization.

Do not promise benchmark-equivalent speed or metrics from a local smoke run.

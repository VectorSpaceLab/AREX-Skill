# Training and evaluation API reference

This reference summarizes the CLI, Hydra config groups, classes, and export helpers used by HumanoidVerse training/evaluation in this checkout.

## Entry points

### `humanoidverse/train_agent.py`

Invocation shape:

```bash
python humanoidverse/train_agent.py +simulator=<backend> +exp=<experiment> +domain_rand=<choice> +rewards=<choice> +robot=<choice> +terrain=<choice> +obs=<choice> [overrides...]
```

Hydra annotation:

```python
@hydra.main(config_path="config", config_name="base", version_base="1.1")
```

Runtime sequence:

1. Reads `config.simulator._target_` and imports/launches backend-specific packages:
   - `IsaacSim`: builds an IsaacLab `AppLauncher` before importing Torch.
   - `IsaacGym`: imports `isaacgym` before importing Torch.
2. Imports Torch, W&B, `BaseTask`, `BaseAlgo`, preprocessing helpers, and logging bridge.
3. Writes `train.log` under `HydraConfig.get().runtime.output_dir`, which is `${save_dir}` from `base.yaml`.
4. Changes back to Hydra's original cwd. Use repo-root commands so relative paths like `robot.motion.motion_file` resolve correctly.
5. Selects `device` from `+device=...` when present, otherwise `cuda:0` if Torch CUDA is available, otherwise `cpu`.
6. Calls `pre_process_config(config)`, which computes observation dimensions and stores them in `config.robot.algo_obs_dim_dict`.
7. Sets `config.env.config.save_rendering_dir = <experiment_dir>/renderings_training`.
8. Instantiates `config.env`, creates `<experiment_dir>`, saves unresolved `config.yaml`, instantiates `config.algo`, calls `setup()`, optionally loads `config.checkpoint`, then calls `learn()`.
9. Closes the IsaacSim app when that backend was selected.

Important fields from `base.yaml`:

```yaml
seed: 0
headless: True
num_envs: 4096
checkpoint: null
project_name: TEST
experiment_name: TEST
base_dir: logs
timestamp: ${now:%Y%m%d_%H%M%S}
experiment_dir: ${base_dir}/${project_name}/${timestamp}-${experiment_name}-${log_task_name}-${robot.asset.robot_type}
save_dir: ${experiment_dir}/.hydra
output_dir: ${experiment_dir}/output
eval_overrides:
  headless: False
  num_envs: 1
  auto_load_latest: False
  use_wandb: False
```

`auto_load_latest` exists in config but is not implemented in `train_agent.py`; pass `checkpoint=<path>` explicitly when resuming.

### `humanoidverse/eval_agent.py`

Invocation shape:

```bash
python humanoidverse/eval_agent.py +checkpoint=<path/to/model_N.pt> [eval overrides...]
```

Hydra annotation:

```python
@hydra.main(config_path="config", config_name="base_eval")
```

Runtime sequence:

1. Writes `eval.log` under `logs_eval/${eval_name}/${eval_timestamp}`.
2. Returns to Hydra's original cwd.
3. Requires `override_config.checkpoint` for normal operation.
4. Searches for a saved training config at:
   - `<checkpoint_parent>/config.yaml`
   - `<checkpoint_parent_parent>/config.yaml`
5. If a training config is found, merges its `eval_overrides` into the training config and then merges CLI eval overrides.
6. Selects and launches simulator backend the same way as training.
7. Calls `pre_process_config(config)`, selects `device`, creates `eval_log_dir`, writes eval `config.yaml`, and sets:
   - `config.env.config.save_rendering_dir = <checkpoint_parent>/renderings/ckpt_<N>`
   - `config.env.config.ckpt_dir = <checkpoint_parent>`
8. Instantiates env/algo, loads the checkpoint, exports ONNX by default, and then enters `algo.evaluate_policy()`.

Evaluation base config:

```yaml
eval_timestamp: ${now:%Y%m%d_%H%M%S}
eval_name: TEST
eval_log_dir: logs_eval/${eval_name}/${eval_timestamp}
hydra.run.dir: ${eval_log_dir}
```

Because `base_eval.yaml` does not define `headless` or `num_envs`, pass eval-only additions with a leading `+`, for example `+headless=True` or `+num_envs=1`. If a training `config.yaml` is found, these additions override the merged training config.

## Hydra config groups

The verified `--help` output listed these groups for both entry points:

| Group | Choices relevant here | Use |
| --- | --- | --- |
| `algo` | `ppo`, `ppo_train_delta_a` | Algorithm class. Usually selected through `+exp`. |
| `domain_rand` | `NO_domain_rand`, `NO_domain_rand_finetune_with_deltaA`, `domain_rand_base` | Domain randomization and delta-A finetuning switches. |
| `env` | `locomotion`, `motion_tracking`, `delta_a_open_loop`, `delta_a_closed_loop`, plus bases | Environment class. Usually selected through `+exp`. |
| `exp` | `locomotion`, `motion_tracking`, `train_delta_a_open_loop`, `train_delta_a_closed_loop` | High-level experiment bundle. |
| `obs/loco` | `leggedloco_obs_singlestep_withlinvel`, `leggedloco_obs_history_wolinvel`, others | Locomotion observation schema. |
| `obs/motion_tracking` | `deepmimic_a2c_nolinvel_LARGEnoise_history`, `deepmimic_a2c`, `deepmimic`, `motion_tracking` | Motion-tracking observation schema. |
| `obs/delta_a` | `open_loop`, `train_policy_with_delta_a` | Delta-action observation schemas. |
| `opt` | `wandb`, `record`, `eval_analysis_plot_motion_tracking`, `eval_analysis_plot_locomotion` | Optional logging, recording, and callbacks. |
| `rewards/loco` | `reward_g1_locomotion` plus other robots | Locomotion rewards. |
| `rewards/motion_tracking` | `reward_motion_tracking_dm_2real`, `reward_motion_tracking_dm_simfinetuning`, `reward_motion_tracking_basic` | Motion tracking and finetuning rewards. |
| `rewards/motion_tracking/delta_a` | `reward_delta_a_openloop`, `reward_motion_tracking_use_deltaA_to_train_2real` | Delta-action rewards. |
| `robot/g1` | `g1_29dof_anneal_23dof` | G1 23-action/29-DOF humanoid config. |
| `simulator` | `isaacgym`, `isaacsim`, `genesis`, `mujoco` | Backend class selection. |
| `terrain` | `terrain_locomotion_plane`, `terrain_locomotion`, `terrain_base` | Terrain object consumed by simulator/env. |

Use leading `+` for group additions from the base config, e.g. `+exp=motion_tracking`. Use plain `key=value` for existing scalar fields like `num_envs=1`, `project_name=...`, and `experiment_name=...`. For keys absent from the current base config, such as `device` in training or `headless` in base eval, use `+device=cuda:0` or `+headless=True`.

## Experiment bundles

| `+exp` | Defaults selected | Intended workflow |
| --- | --- | --- |
| `motion_tracking` | `/algo: ppo`, `/env: motion_tracking`; `experiment_name: TEST_Motion_Tracking` | Phase-based motion tracking from a robot motion file. |
| `locomotion` | `/algo: ppo`, `/env: locomotion`; `experiment_name: TEST_Locomotion` | Locomotion command following. |
| `train_delta_a_open_loop` | `/algo: ppo`, `/env: delta_a_open_loop`; `experiment_name: Train_Delta_A` | Learn corrections around motion-file open-loop actions. |
| `train_delta_a_closed_loop` | `/algo: ppo_train_delta_a`, `/env: delta_a_closed_loop`; `experiment_name: Use_Delta_A_for_Finetuning` | Finetune using `PPODeltaA` and a loaded closed-loop policy. |

## Environment classes and key config effects

| Env config | `_target_` | Key behavior |
| --- | --- | --- |
| `env/motion_tracking.yaml` | `humanoidverse.envs.motion_tracking.motion_tracking.LeggedRobotMotionTracking` | Tracks a reference motion, can terminate on motion end/far conditions, resamples motions during training, sets `log_task_name: motion_tracking`. |
| `env/locomotion.yaml` | `humanoidverse.envs.locomotion.locomotion.LeggedRobotLocomotion` | Samples linear/yaw commands, uses locomotion observation/reward scales, sets `log_task_name: locomotion`. |
| `env/delta_a_open_loop.yaml` | `humanoidverse.envs.delta_a.delta_a_open_loop.DeltaA_OpenLoop` | Extends motion tracking, sets `add_extra_action: True`, uses open-loop motion actions. |
| `env/delta_a_closed_loop.yaml` | `humanoidverse.envs.delta_a.delta_a_closed_loop.DeltaA_ClosedLoop` | Extends motion tracking, stores `actions_closed_loop`, adds them to torque computation when enabled. |

Motion-tracking and delta-action environments use `robot.motion.motion_file`. The default G1 robot config points to `humanoidverse/data/motions/g1_29dof_anneal_23dof/v1/amass_all.pkl`, but README workflows override it with a single TairanTestbed motion.

## PPO behavior

Class: `humanoidverse.agents.ppo.ppo.PPO`

Important methods:

- `setup()`: creates actor/critic modules and rollout storage.
- `load(ckpt_path)`: loads `actor_model_state_dict`, `critic_model_state_dict`, optionally optimizer states when `algo.config.load_optimizer=True`, sets `current_learning_iteration`, and returns checkpoint `infos`.
- `save(path, infos=None)`: writes actor/critic states, actor/critic optimizer states, `iter`, and `infos` to `model_<iteration>.pt`.
- `learn()`: resets env, rolls out `num_steps_per_env`, updates PPO for `num_learning_epochs * num_mini_batches`, logs metrics, saves every `save_interval` iterations, and saves a final checkpoint.
- `_post_epoch_logging()`: writes TensorBoard scalars for losses, FPS, rewards, episode length, and env metrics; prints a Rich live training panel.
- `evaluate_policy()`: creates callbacks, sets eval mode, resets env, repeatedly runs inference and env steps forever until interrupted.
- `get_example_obs()`: prints observation keys/dim sources and returns CPU observations used by ONNX export.
- `inference_model`: returns `{"actor": self.actor, "critic": self.critic}`.

Default PPO config (`algo/ppo.yaml`):

```yaml
num_steps_per_env: 24
save_interval: 100
num_learning_iterations: 1000000
num_learning_epochs: 5
num_mini_batches: 4
clip_param: 0.2
gamma: 0.99
lam: 0.95
actor_learning_rate: 1.e-3
critic_learning_rate: 1.e-3
schedule: adaptive
desired_kl: 0.01
module_dict.actor.layer_config.hidden_dims: [512, 256, 128]
module_dict.critic.layer_config.hidden_dims: [512, 256, 128]
```

## PPODeltaA behavior

Class: `humanoidverse.agents.delta_a.train_delta_a.PPODeltaA`

Configuration source: `algo/ppo_train_delta_a.yaml`.

Required field for closed-loop finetuning:

```yaml
algo.config.policy_checkpoint: /path/to/delta_or_closed_loop_policy.pt
```

Runtime behavior:

1. `PPODeltaA.__init__()` calls `PPO.__init__()` for the trainable actor/critic.
2. It locates a `config.yaml` next to `algo.config.policy_checkpoint` or one directory above.
3. It applies that loaded policy's `eval_overrides` when present, preprocesses the policy config, instantiates a second `BaseAlgo`, loads the policy checkpoint, switches it to eval mode, freezes parameters, and stores `loaded_policy.eval_policy`.
4. During rollout, the trainable actor produces `actions`; the loaded policy produces `actions_closed_loop` from `obs_dict['closed_loop_actor_obs']`; both are passed to `DeltaA_ClosedLoop.step()`.
5. `DeltaA_ClosedLoop._compute_torques()` combines `actions_scaled + motion_action + default_dof_pos - simulator.dof_pos` for position control when `add_extra_action=True`, where `motion_action` is `actions_closed_loop` with optional domain-randomization scaling.

Failure-sensitive details:

- If `algo.config.policy_checkpoint` is omitted or its config cannot be found, `PPODeltaA` does not have a valid `policy_config` to instantiate the frozen policy.
- `+checkpoint=<policy_to_finetune>` and `algo.config.policy_checkpoint=<loaded_policy>` are different paths; do not swap them.

## Delta-action motion file behavior

`DeltaA_OpenLoop` depends on motion actions:

- `get_open_loop_action_at_current_timestep()` calls the motion library's `get_motion_actions(...)`.
- The motion library sets `self.has_action=True` when a loaded motion record contains `action`, stores `curr_motion.action`, and concatenates those actions into `_motion_actions`.
- Open-loop torque computation adds `motion_action` to the learned actor action before PD control.

Practical rule: for open-loop delta-action training, use a motion `.pkl` whose per-motion record contains an `action` array with the same action dimension as the robot (`23` for the G1 config here). Retargeted files produced by the SMPL pipeline typically contain kinematic keys but not `action`; evaluation recording with `+opt=record` can create action-bearing rollouts.

## ONNX and JIT export helpers

Source: `humanoidverse/utils/inference_helpers.py`.

| Helper | Used by default? | Behavior |
| --- | --- | --- |
| `export_policy_as_onnx(inference_model, path, exported_policy_name, example_obs_dict)` | Yes in `eval_agent.py` | Deep-copies `inference_model['actor']`, wraps `actor.act_inference(actor_obs)`, exports opset 13 with input `actor_obs` and output `action`. |
| `export_policy_as_jit(actor_critic, path, exported_policy_name)` | No (`EXPORT_POLICY=False`) | Deep-copies `actor_critic.actor`, scripts it, saves a TorchScript file. The current eval code references `algo.alg.actor_critic` in this disabled branch, so treat it as unverified. |
| `export_policy_and_estimator_as_onnx(...)` | No, commented out | Exports actor plus left/right force estimators with inputs `actor_obs` and `long_history_for_estimator`; not active for the force-control path. |

Export path formula in `eval_agent.py`:

```python
exported_policy_path = os.path.join(HV_ROOT_DIR, checkpoint_dir, 'exported')
exported_onnx_name = exported_policy_name.replace('.pt', '.onnx')
```

For a relative checkpoint path like `logs/MotionTracking/run/model_5800.pt`, the ONNX file is:

```text
logs/MotionTracking/run/exported/model_5800.onnx
```

## Output path formulas

Training:

```text
${base_dir}/${project_name}/${timestamp}-${experiment_name}-${log_task_name}-${robot.asset.robot_type}/
```

Key files:

```text
config.yaml
model_<iteration>.pt
.hydra/train.log
renderings_training/
output/
```

Evaluation:

```text
logs_eval/${eval_name}/${eval_timestamp}/config.yaml
logs_eval/${eval_name}/${eval_timestamp}/eval.log
<checkpoint_dir>/renderings/ckpt_<checkpoint_number>/
<checkpoint_dir>/exported/model_<checkpoint_number>.onnx
```

Evaluation motion recording with `+opt=record`:

```text
<checkpoint_dir>/motions/<save_note>_<eval_timestamp>.pkl
```

## Safe command builder API

Script:

```bash
python sub-skills/training-and-evaluation/scripts/build_training_command.py --repo-root <asap-checkout> --workflow <name> [options]
```

The builder validates the repo root and emits a self-contained shell snippet prefixed with `cd <repo-root> &&`.

Supported workflows:

```text
locomotion-smoke
locomotion-train
motion-tracking
delta-a-open-loop
delta-a-finetune
eval
export-onnx
eval-record-motion
```

Useful options:

- `--cfg-job`: append `--cfg job` to make the printed command a Hydra composition-only check.
- `--strict`: fail instead of printing placeholder paths.
- `--require-existing-paths`: check motion/checkpoint paths exist without importing the repo.
- `--extra KEY=VALUE`: append additional one-line Hydra overrides.
- `--simulator`, `--robot`, `--terrain`, `--device`: choose backend and hardware-relevant overrides.
- `--analysis motion_tracking|locomotion`: add the relevant eval callback config.

The builder validates that referenced Hydra group YAML files exist under `humanoidverse/config/` and prints warnings for workflow-specific traps; it never starts training.

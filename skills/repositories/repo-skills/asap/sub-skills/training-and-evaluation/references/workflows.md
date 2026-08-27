# Training and evaluation workflows

Run every command from the repository root unless stated otherwise. These recipes are designed for a future agent to select commands without reopening the source README.

Use the builder when a prompt is underspecified; it prints commands but never runs them. The printed command is self-contained and starts with `cd <repo-root> &&`:

```bash
python sub-skills/training-and-evaluation/scripts/build_training_command.py --help
```

Add `--cfg-job` to the builder when you want the printed command to run only Hydra composition (`--cfg job`) instead of launching a simulator.

## Shared runtime preflight

If you want one command instead of separate probes, run `python scripts/asap_doctor.py --repo-root <asap-checkout> --section core` from the generated ASAP skill root.

```bash
# Use the same Python environment that will run training/evaluation.
python - <<'PY'
import importlib.metadata as md
import torch
import humanoidverse
print('asap distribution:', md.version('asap'))
print('humanoidverse:', humanoidverse.__file__)
print('torch:', torch.__version__, 'cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())
PY

python humanoidverse/train_agent.py --help
python humanoidverse/eval_agent.py --help
```

Expected safe observations:

- `train_agent.py --help` lists config groups such as `simulator`, `exp`, `domain_rand`, `rewards`, `robot`, `terrain`, and `obs`.
- `eval_agent.py --help` lists the same groups and the base eval config (`eval_log_dir: logs_eval/${eval_name}/${eval_timestamp}`).
- These help checks do not prove that IsaacGym, IsaacSim, Genesis, or MuJoCo runtime dependencies are installed.

## Locomotion training and smoke test

Use this when the user asks for a locomotion policy or wants to smoke-test the IsaacGym install. The small smoke command uses one environment and a visible viewer; the full training command uses many environments and headless mode.

Build the smoke command:

```bash
python sub-skills/training-and-evaluation/scripts/build_training_command.py \
  --repo-root <asap-checkout> \
  --workflow locomotion-smoke \
  --simulator isaacgym
```

Smoke-test command:

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
  +simulator=isaacgym \
  +exp=locomotion \
  +domain_rand=NO_domain_rand \
  +rewards=loco/reward_g1_locomotion \
  +robot=g1/g1_29dof_anneal_23dof \
  +terrain=terrain_locomotion_plane \
  +obs=loco/leggedloco_obs_singlestep_withlinvel \
  num_envs=1 \
  project_name=TestIsaacGymInstallation \
  experiment_name=G123dof_loco \
  headless=False
```

Build a full locomotion training command:

```bash
python sub-skills/training-and-evaluation/scripts/build_training_command.py \
  --repo-root <asap-checkout> \
  --workflow locomotion-train \
  --simulator isaacgym \
  --num-envs 4096 \
  --device cuda:0
```

Full locomotion training command:

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
  +simulator=isaacgym \
  +exp=locomotion \
  +domain_rand=NO_domain_rand \
  +rewards=loco/reward_g1_locomotion \
  +robot=g1/g1_29dof_anneal_23dof \
  +terrain=terrain_locomotion_plane \
  +obs=loco/leggedloco_obs_singlestep_withlinvel \
  num_envs=4096 \
  project_name=Locomotion \
  experiment_name=G123dof_loco \
  headless=True \
  rewards.reward_penalty_curriculum=True \
  rewards.reward_initial_penalty_scale=0.1 \
  rewards.reward_penalty_degree=0.00003 \
  +device=cuda:0
```

Expected outputs:

```text
logs/Locomotion/<timestamp>-G123dof_loco-locomotion-g1_29dof_anneal_23dof/
├── config.yaml
├── model_<iteration>.pt
├── events.out.tfevents.*
└── .hydra/train.log
```

## Motion-tracking training

Use this for phase-based motion tracking: the policy imitates a retargeted robot motion `.pkl`. The README's CR7 example consumes an already-retargeted G1 motion.

Known checked motion file:

```text
humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl
```

Build the command:

```bash
python sub-skills/training-and-evaluation/scripts/build_training_command.py \
  --repo-root <asap-checkout> \
  --workflow motion-tracking \
  --motion-file humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl \
  --simulator isaacgym \
  --device cuda:0
```

Training command:

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
  +simulator=isaacgym \
  +exp=motion_tracking \
  +domain_rand=NO_domain_rand \
  +rewards=motion_tracking/reward_motion_tracking_dm_2real \
  +robot=g1/g1_29dof_anneal_23dof \
  +terrain=terrain_locomotion_plane \
  +obs=motion_tracking/deepmimic_a2c_nolinvel_LARGEnoise_history \
  num_envs=4096 \
  project_name=MotionTracking \
  experiment_name=MotionTracking_CR7 \
  robot.motion.motion_file="humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl" \
  rewards.reward_penalty_curriculum=True \
  rewards.reward_penalty_degree=0.00001 \
  env.config.resample_motion_when_training=False \
  env.config.termination.terminate_when_motion_far=True \
  env.config.termination_curriculum.terminate_when_motion_far_curriculum=True \
  env.config.termination_curriculum.terminate_when_motion_far_threshold_min=0.3 \
  env.config.termination_curriculum.terminate_when_motion_far_curriculum_degree=0.000025 \
  robot.asset.self_collisions=0 \
  +device=cuda:0
```

Use `env.config.resample_motion_when_training=False` when training against one specific clip. Use `True` and a large `env.config.resample_time_interval_s` when sampling across many clips.

Expected outputs:

```text
logs/MotionTracking/<timestamp>-MotionTracking_CR7-motion_tracking-g1_29dof_anneal_23dof/
├── config.yaml
├── model_0.pt
├── model_100.pt
├── ...
├── model_<final>.pt
└── .hydra/train.log
```

## Open-loop delta-action training

Use this when the user asks to train a delta-action model from a motion file that already contains per-frame actions. A normal retargeted motion file with only `dof`, `pose_aa`, `root_rot`, `root_trans_offset`, `smpl_joints`, and `fps` is not enough. The loaded motion record must contain an `action` key because `DeltaA_OpenLoop.get_open_loop_action_at_current_timestep()` reads motion actions from the motion library.

Build the command:

```bash
python sub-skills/training-and-evaluation/scripts/build_training_command.py \
  --repo-root <asap-checkout> \
  --workflow delta-a-open-loop \
  --motion-file /path/to/motion_with_action.pkl \
  --simulator isaacgym \
  --device cuda:0
```

Training command:

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
  +simulator=isaacgym \
  +exp=train_delta_a_open_loop \
  +domain_rand=NO_domain_rand \
  +rewards=motion_tracking/delta_a/reward_delta_a_openloop \
  +robot=g1/g1_29dof_anneal_23dof \
  +terrain=terrain_locomotion_plane \
  +obs=delta_a/open_loop \
  num_envs=5000 \
  project_name=DeltaA_Training \
  experiment_name=openloopDeltaA_training \
  robot.motion.motion_file="/path/to/motion_with_action.pkl" \
  env.config.max_episode_length_s=1.0 \
  rewards.reward_scales.penalty_minimal_action_norm=-0.1 \
  +device=cuda:0 \
  env.config.resample_motion_when_training=True \
  env.config.resample_time_interval_s=10000
```

Runtime behavior:

- `+exp=train_delta_a_open_loop` selects `+env=delta_a_open_loop` and regular `+algo=ppo`.
- `DeltaA_OpenLoop._compute_torques()` adds the motion-file open-loop action to the learned policy action before the PD controller when `env.config.add_extra_action=True`.
- `+obs=delta_a/open_loop` adds `actions_open_loop` to actor/critic observations.
- The reward config exposes `rewards.reward_scales.penalty_minimal_action_norm` for encouraging small learned corrections.

Expected checkpoint directory:

```text
logs/DeltaA_Training/<timestamp>-openloopDeltaA_training-delta_a-g1_29dof_anneal_23dof/
```

## Closed-loop delta-action finetuning

Use this after a delta-action checkpoint exists and the user wants to finetune a motion-tracking policy with a loaded closed-loop controller. This recipe has two checkpoint-like paths:

- `algo.config.policy_checkpoint=<PATH_TO_YOUR_DELTA_A_MODEL>`: loaded by `PPODeltaA` as a frozen policy used to produce `actions_closed_loop`.
- `checkpoint=<PATH_TO_YOUR_POLICY_TO_BE_FINETUNED>`: loaded by `train_agent.py` through `algo.load(...)` as the policy being finetuned.

Build the command:

```bash
python sub-skills/training-and-evaluation/scripts/build_training_command.py \
  --repo-root <asap-checkout> \
  --workflow delta-a-finetune \
  --motion-file /path/to/motion.pkl \
  --delta-policy-checkpoint /path/to/delta_a_model.pt \
  --checkpoint /path/to/policy_to_finetune.pt \
  --simulator isaacgym \
  --device cuda:0 \
  --wandb
```

Finetuning command:

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
  +simulator=isaacgym \
  +exp=train_delta_a_closed_loop \
  algo.config.policy_checkpoint="/path/to/delta_a_model.pt" \
  +domain_rand=NO_domain_rand_finetune_with_deltaA \
  +rewards=motion_tracking/reward_motion_tracking_dm_simfinetuning \
  +robot=g1/g1_29dof_anneal_23dof \
  +terrain=terrain_locomotion_plane \
  +obs=delta_a/train_policy_with_delta_a \
  num_envs=4096 \
  project_name=DeltaA_Finetune \
  experiment_name=finetune_with_deltaA \
  robot.motion.motion_file="/path/to/motion.pkl" \
  +opt=wandb \
  env.config.add_extra_action=True \
  checkpoint="/path/to/policy_to_finetune.pt" \
  domain_rand.push_robots=False \
  env.config.noise_to_initial_level=1 \
  rewards.reward_penalty_curriculum=True \
  +device=cuda:0 \
  algo.config.save_interval=5 \
  algo.config.num_learning_iterations=1000
```

Critical checkpoint rule: both checkpoint directories should contain the `config.yaml` saved by training. `PPODeltaA` looks next to `algo.config.policy_checkpoint` and one directory up for a config file before instantiating the frozen policy.

Runtime behavior:

- `+exp=train_delta_a_closed_loop` selects `+algo=ppo_train_delta_a`, whose `_target_` is `humanoidverse.agents.delta_a.train_delta_a.PPODeltaA`.
- `PPODeltaA._rollout_step()` calls the loaded policy with `obs_dict['closed_loop_actor_obs']` and passes its output to the environment as `actions_closed_loop`.
- `DeltaA_ClosedLoop._compute_torques()` adds `actions_closed_loop` to the current actor's actions before PD torque computation when `env.config.add_extra_action=True`.
- `NO_domain_rand_finetune_with_deltaA` adds delta-A finetuning switches such as `cotrain_with_without_delta_a` and `rescale_delta_a`, but they are off by default.

## Checkpoint evaluation

Use this when the user asks to visualize or score an existing checkpoint. The simplest path is to pass only `+checkpoint`: `eval_agent.py` loads the training `config.yaml` next to the checkpoint or one directory up, merges `eval_overrides`, then merges the CLI overrides.

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/eval_agent.py \
  +checkpoint=logs/MotionTracking/<timestamp>-MotionTracking_CR7-motion_tracking-g1_29dof_anneal_23dof/model_5800.pt \
  eval_name=MotionTracking_CR7_eval
```

Optional analysis callbacks:

```bash
# Motion-tracking plots/metrics callback.
HYDRA_FULL_ERROR=1 python humanoidverse/eval_agent.py \
  +checkpoint=logs/MotionTracking/<run>/model_5800.pt \
  +opt=eval_analysis_plot_motion_tracking \
  eval_name=MotionTracking_CR7_analysis

# Locomotion analysis callback.
HYDRA_FULL_ERROR=1 python humanoidverse/eval_agent.py \
  +checkpoint=logs/Locomotion/<run>/model_6600.pt \
  +opt=eval_analysis_plot_locomotion \
  eval_name=Locomotion_analysis
```

Expected evaluation outputs:

```text
logs_eval/<eval_name>/<eval_timestamp>/
├── config.yaml
└── eval.log

<checkpoint_dir>/renderings/ckpt_<checkpoint_number>/
```

Important: `PPO.evaluate_policy()` loops forever. Stop it manually after the desired rendering, export, or callback output is complete.

## ONNX export

Use the same entry point as evaluation. `eval_agent.py` sets `EXPORT_ONNX=True` and `EXPORT_POLICY=False`, exports ONNX immediately after `algo.load(...)` and `algo.get_example_obs()`, then enters `algo.evaluate_policy()`.

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/eval_agent.py \
  +checkpoint=logs/MotionTracking/<run>/model_5800.pt \
  eval_name=export_motion_tracking_5800
```

Expected export:

```text
logs/MotionTracking/<run>/exported/model_5800.onnx
```

The exporter wraps the actor and writes a single-input ONNX graph:

```text
input:  actor_obs
output: action
opset: 13
```

If the user's intent is export-only, wait for a log like:

```text
Exported policy as onnx to: <checkpoint_dir>/exported/model_5800.onnx
```

Then stop the process before or during the infinite evaluation loop.

## Record evaluation motion for delta-action datasets

Use this when a future delta-action workflow needs a motion file that includes an `action` key. The source retargeting scripts do not synthesize actions, but motion-tracking evaluation can dump policy rollouts with actions when `+opt=record` is enabled.

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/eval_agent.py \
  +checkpoint=logs/MotionTracking/<run>/model_5800.pt \
  +opt=record \
  env.config.save_motion=True \
  env.config.save_note=delta_a_source \
  env.config.save_total_steps=10000 \
  eval_name=record_delta_a_source
```

Expected output:

```text
logs/MotionTracking/<run>/motions/delta_a_source_<eval_timestamp>.pkl
```

The saved joblib data contains per-motion dictionaries with keys including `root_trans_offset`, `pose_aa`, `dof`, `root_rot`, `actor_obs`, `action`, `terminate`, `root_lin_vel`, `root_ang_vel`, `dof_vel`, `motion_times`, and `fps`.

## Checkpoint resume and short bounded tests

To resume a training run from a checkpoint, add `checkpoint=<path>` to the training command. For a bounded sanity run, lower both environments and learning iterations:

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
  +simulator=isaacgym \
  +exp=motion_tracking \
  +domain_rand=NO_domain_rand \
  +rewards=motion_tracking/reward_motion_tracking_dm_2real \
  +robot=g1/g1_29dof_anneal_23dof \
  +terrain=terrain_locomotion_plane \
  +obs=motion_tracking/deepmimic_a2c_nolinvel_LARGEnoise_history \
  num_envs=1 \
  project_name=SkillSmoke \
  experiment_name=MotionTrackingSmoke \
  robot.motion.motion_file="humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl" \
  algo.config.num_learning_iterations=1 \
  algo.config.save_interval=1 \
  headless=True \
  +device=cuda:0
```

This still launches the selected simulator. If backend packages are missing, use the composition-only form instead:

```bash
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
  +simulator=isaacgym \
  +exp=motion_tracking \
  +domain_rand=NO_domain_rand \
  +rewards=motion_tracking/reward_motion_tracking_dm_2real \
  +robot=g1/g1_29dof_anneal_23dof \
  +terrain=terrain_locomotion_plane \
  +obs=motion_tracking/deepmimic_a2c_nolinvel_LARGEnoise_history \
  num_envs=1 \
  project_name=SkillSmoke \
  experiment_name=MotionTrackingSmoke \
  robot.motion.motion_file="humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl" \
  algo.config.num_learning_iterations=1 \
  --cfg job
```

## Choosing simulator overrides

| Override | When to choose it | Runtime gate |
| --- | --- | --- |
| `+simulator=isaacgym` | README-aligned training examples and high-throughput CUDA RL. | IsaacGym Preview 4 Python package installed; import `isaacgym` works; CUDA Torch available. |
| `+simulator=isaacsim` | IsaacLab/IsaacSim runs. | `omni.isaac.lab` available and IsaacSim paths configured; entry point launches `AppLauncher`. |
| `+simulator=genesis` | Genesis environment. | `genesis-world` installed in the same env. |
| `+simulator=mujoco` | Only if the HumanoidVerse training task was adapted and verified for MuJoCo. | `mujoco` package installed; use sim2real sub-skill for deployment/control, not this training recipe. |

Do not change only `sim_type`; the scripts instantiate from `config.simulator._target_`, so the Hydra group `+simulator=<choice>` is the important selection.

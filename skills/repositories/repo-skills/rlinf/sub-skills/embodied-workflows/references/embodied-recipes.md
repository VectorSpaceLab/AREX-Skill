# Embodied recipes

This reference distills RLinf v0.4.0 embodied training patterns into reusable operating guidance. It intentionally gives **static planning and launch-shape recipes** rather than telling an agent to run repository example scripts.

## Universal embodied launch shape

Before any launch, run the bundled static checker:

```bash
python <skill-dir>/scripts/check_embodied_config.py <config.yaml>
```

A normal embodied training launch is a Hydra invocation of the embodied training entrypoint:

```bash
python <embodied-training-entrypoint> \
  --config-path <embodied-config-dir> \
  --config-name <config_name_without_yaml> \
  runner.logger.log_path=<run_log_dir> \
  runner.max_steps=<small_smoke_steps_or_-1> \
  runner.save_interval=<checkpoint_interval_or_-1> \
  cluster.num_nodes=<node_count>
```

A helper shell wrapper in the source tree follows this concept: it sets an embodiment config root, sets EGL rendering defaults, prepares selected dataset/model environment variables, creates a timestamped log directory, writes the exact command into `run_embodiment.log`, and pipes stdout/stderr through `tee`. Recreate that behavior in your own run harness instead of depending on the helper file path.

Useful Hydra override categories:

- **Logging:** `runner.logger.log_path=<dir>`, `runner.logger.experiment_name=<name>`, `runner.logger.logger_backends=[tensorboard]` or W&B/SwanLab if credentials are configured.
- **Fast smoke:** `runner.max_steps=1`, `runner.save_interval=-1`, `runner.val_check_interval=-1`, smaller `env.train.total_num_envs`, and shorter `env.train.max_steps_per_rollout_epoch` when the environment supports it.
- **Model paths:** `actor.model.model_path=<checkpoint_dir>`, `rollout.model.model_path=<checkpoint_dir>`, `actor.model.lora_path=<lora_dir>`, `actor.model.is_lora=True`.
- **Assets/data:** environment-specific asset roots, `data.train_data_paths=<dataset>`, `algorithm.demo_buffer=<replay_buffer_dir>`, reward model checkpoint fields, and world-model checkpoint/init-data fields.
- **Cluster:** `cluster.num_nodes=<N>` and placement overrides should be coordinated with the setup/cluster skill; this sub-skill only verifies that actor, rollout, env, and optional reward components are accounted for.

## Core runner mental model

For `runner.task_type: embodied`, the entrypoint validates Hydra config, creates a `Cluster`, derives `HybridComponentPlacement`, creates actor/rollout/env and optional reward worker groups, initializes workers, then the runner loops:

```text
sync actor weights to rollout
env workers interact with simulator/robot
rollout workers produce action chunks/logprobs/values
optional reward worker scores observations/history
actor receives trajectories
actor computes advantages/returns
actor trains and saves/evaluates at configured intervals
```

Async real-world/SAC/DAGGER/RLT configurations use a long-running variant of the same component graph: env, rollout, reward, and actor communicate through channels while the actor consumes replay/trajectory batches.

## Environment and simulator recipe families

| Family | Config naming pattern | Typical models | Required decisions before launch | Notes |
| --- | --- | --- | --- | --- |
| ManiSkill / ManiSkill-RLT | `maniskill_*`, `maniskill_rlt_*` | OpenVLA, OpenVLA-OFT, OpenPI, MLP, Flow, CNN, RLT MLP, Evo1 | ManiSkill assets, `MUJOCO_GL=egl`, `PYOPENGL_PLATFORM=egl`, obs mode, control mode, action chunk size, reset-state policy | GPU simulation can be memory heavy; `env.enable_offload` and smaller env counts are common smoke-test levers. |
| LIBERO | `libero_*` | OpenPI, OpenVLA-OFT, GR00T, StarVLA, DreamZero, Dexbotic, Evo1 | LIBERO asset/cache state, `ROBOT_PLATFORM` (`LIBERO` by default), `LIBERO_TYPE` for standard/pro/plus variants, model checkpoint/normalization key | Watch action dimension and `ROBOT_PLATFORM` whenever moving between LIBERO, ALOHA, BRIDGE, RoboTwin, or real-world data. |
| RoboTwin | `robotwin_*` | OpenPI, OpenVLA-OFT, LingbotVLA | `ROBOTWIN_PATH`, asset root, seed file choice, task name, robot platform/action interface | Large env counts are common in configs; smoke tests should shrink env counts and rollout horizon. |
| RoboCasa / RoboCasa365 | `robocasa*` | OpenPI | assets, task/split/task-soup selection, camera/state/action schema | RoboCasa365 uses benchmark registry concepts such as split and task soup; verify task filters before expensive training. |
| BEHAVIOR | `behavior_*` | OpenPI/OpenPI_RLinf | OmniGibson data paths/key path, Isaac Sim path, headless flags, R1Pro action/state dimensions | Often needs disaggregated rollout/env placement because the simulator is heavy. |
| CALVIN | `calvin_*` | OpenPI | CALVIN suite/split, horizon, task suite, asset/data availability | Long horizons and many eval envs make smoke overrides important. |
| MetaWorld | `metaworld_*` | OpenPI, OpenVLA-OFT | task set (`50`, OOD/ind variants), horizon, success metric interpretation | Lightweight compared with image-heavy simulators but still uses embodied runner. |
| IsaacLab | `isaaclab_*` | GR00T, OpenPI | IsaacLab task id, Isaac Sim compatibility, CPU thread tuning for rollout workers | `env_cfg.init_params.id` must map to a registered IsaacLab task. |
| Genesis / GSEnv | `genesis_*`, `gsenv_*` | CNN, OpenPI | Genesis install/assets, camera/state mode, rel-reward settings | Treat as simulator backend with high GPU/driver sensitivity. |
| FrankaSim | `frankasim_*` | CNN, MLP, Flow, OpenVLA | simulator dependency, image/state obs format, replay-buffer sizing | Useful bridge between pure sim and real-world Franka recipes. |
| RealWorld robots | `realworld_*`, `dosw1_*`, XSquare/GimArm style configs | CNN, Flow, OpenPI, RLT policies | operator approval, robot IP/serials, controller deps, camera/gripper type, target pose, demo buffer | Never casually run hardware checks. See real-world reference first. |
| D4RL | `d4rl_iql_*` | MLP policy | offline dataset/task name, no online train env, eval env optional | Uses `runner.task_type: offline`; it is embodied-adjacent but not an online embodied launch. |
| Polaris | `polaris_*` | OpenPI | `POLARIS_DATA_PATH`, task data availability, long horizon | Usually one/few envs and high-horizon manipulation traces. |
| World model envs | `opensora_*`, `wan_*` | OpenVLA-OFT | VLA checkpoint, world-model checkpoint, init dataset, reward model type, generated-video settings | These train closed-loop without a physics simulator; world model has its own failure modes and may lack proprio/wrist views. |
| EmbodiChain / RoboVerse / Habitat | matching family names | OpenPI, CNN/MLP where supported | backend package/assets, task id, observation/action schema | Use the config checker to confirm `env_type`, horizons, and model paths; defer source extension work to extension-development. |

## Model recipe families

| Model family | Use for | Required planning fields |
| --- | --- | --- |
| OpenVLA | VLA policy on ManiSkill/LIBERO-like tasks | `actor.model.model_path`, `rollout.model.model_path`, precision, action/logprob level, `ROBOT_PLATFORM` where applicable. |
| OpenVLA-OFT | VLA with LoRA/OFT adapters, GRPO/PPO, world-model envs | Base `model_path`, optional `lora_path`, `is_lora`, `unnorm_key`, OpenVLA-OFT runtime deps. |
| OpenPI / OpenPI_RLinf | Flow-matching VLA for LIBERO, RoboTwin, BEHAVIOR, real-world, SFT-to-RL | base checkpoint, repo/config name or self-contained RLinf model template, normalization stats/assets, action horizon/chunk size, platform-specific action dimension. |
| GR00T / GR00T N1D6/N1D7 | IsaacLab/LIBERO/embodied VLA recipes | external GR00T runtime, CPU thread planning, checkpoint path, chunk/logprob settings. |
| DreamZero | VLA SFT/deployment and world-model-style policy training | WAN component checkpoint or full checkpoint, metadata/normalization JSON, LeRobot data layout, action horizon vs temporal block size. |
| StarVLA / LingbotVLA / MolmoAct2 / ABot / Dexbotic / Evo1 | specialized VLA wrappers | model checkpoint and base VLM path, required observation keys, action head/unnormalization settings. |
| MLP / CNN / Flow / CMA | compact policies for state/image SAC, PPO, DAgger, real-world | obs format, action dimension, replay buffer parameters, critic/Q settings, entropy tuning for SAC. |
| ResNet reward / VLM reward / value models | reward or offline advantage workflows | reward dataset paths, reward model type, VLM prompt/parser, local-vs-API inference, value-model tags. |

## Algorithm choices and launch implications

- **PPO / actor-critic:** `algorithm.adv_type: gae`, `algorithm.loss_type: actor_critic`; value head/model fields must be compatible. `clip_ratio_*`, `value_clip`, `gamma`, and `gae_lambda` drive update behavior.
- **GRPO:** `algorithm.adv_type: grpo`, usually `loss_type: actor`; set `algorithm.group_size > 1` and make `env.train.group_size` match. Fixed reset state IDs are often needed so group comparisons are meaningful.
- **SAC / Flow / RLPD:** `loss_type: embodied_sac`; replay-buffer config, demo buffer, entropy tuning, critic/actor update ratios, and async runner are important. Use `runner.weight_sync_interval` deliberately.
- **DAgger/NFT/RLT:** specialized `loss_type` values select actor worker classes. Verify expert/intervention flags, reference-policy paths, and action switching semantics.
- **Offline IQL/D4RL:** `runner.task_type: offline`, `data.dataset_type`, and offline actor fields dominate; env/rollout are only needed for eval.
- **SFT intersections:** `runner.task_type: sft` uses SFT workers, but the output checkpoint often becomes an embodied RL `actor.model.model_path` or LoRA path. Verify dataset normalization before using it online.

## Minimal preflight sequence

1. Identify config name, task type, env family, model family, algorithm, and whether reward/data/offline/SFT paths are involved.
2. Run `list_embodied_configs.py` to confirm the config appears as expected.
3. Run `check_embodied_config.py` on the exact YAML after user-specified edits.
4. Confirm every placeholder (`/path/to/...`, `ROBOT_IP`, serials, dataset roots, model paths) is replaced or intentionally supplied through environment variables.
5. Confirm optional assets and dependencies are installed for **the selected model+env pair only**.
6. For real-world/hardware, stop and follow the real-world safety gates before suggesting a launch.

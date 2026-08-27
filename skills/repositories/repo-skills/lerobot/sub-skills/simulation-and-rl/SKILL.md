---
name: simulation-and-rl
description: "Route LeRobot Gymnasium simulation, benchmark evaluation, and
  bounded RL or HIL-SERL configuration work with explicit dependency, asset,
  backend, and safety gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simulation and RL

Use this skill when a task mentions `env.type`, Gymnasium, PushT, LIBERO,
LIBERO-plus, MetaWorld, RoboTwin/RobotWin, VLABench, RoboCasa, RoboMME,
IsaacLab Arena, RL, HIL-SERL, actor/learner, or a reward model. This skill
routes environment construction and evaluation; it does not silently turn a
configuration check into a simulator rollout or a real-robot action.

## Route first

- Route generic policy training, processors, checkpoints, and inference to
  `policy-training-inference`.
- Route physical robot control, teleoperation, recording, and hardware safety
  to `robot-control-data-collection`.
- Route remote jobs, hosted services, gRPC service deployment, and extension
  authoring to `extensions-and-services`.
- Keep this skill responsible for simulation dispatch, benchmark evaluation,
  RL data flow, and reward integration.

## Inputs and gates

Collect before changing a command or config:

1. `env.type`, task/suite, observation mode, action mode, episode horizon,
   environment count, async preference, policy checkpoint, and evaluation
   episode count.
2. Whether the request is a **config/registry check**, a CPU smoke, or an
   actual rollout. A config check must not call `make_env()` or `reset()`.
3. Platform, Python version, Gymnasium/NumPy versions, simulator package,
   asset-pack status, rendering mode, CUDA/Vulkan/MuJoCo backend, and any
   Hub credential or remote-code consent.
4. For RL: actor/learner topology, `algorithm` (currently `sac`), policy
   action/state features, replay capacity, batch size, online/offline ratio,
   warmup threshold, device, and whether human intervention is intended.

Use `scripts/environment_probe.py` for dispatch-only inspection and
`scripts/rl_config_check.py` for bounded RL config validation. Both are
network-free, asset-free, non-actuating, and non-training.

## Environment dispatch contract

`make_env_config(type, **kwargs)` resolves the registered `EnvConfig` choice.
The config owns `create_envs(n_envs, use_async_envs)` and
`get_env_processors()`. `make_env(config)` returns:

```text
{suite_name: {task_id: gymnasium.vector.VectorEnv}}
```

The base config uses `gym_<type>/<task>` and imports the package only if that
Gym ID is absent. Benchmark configs override creation for multi-task or
third-party simulators. `SyncVectorEnv` is the conservative default; async
workers are opt-in and are only selected for more than one environment. GPU,
EGL, Vulkan, MuJoCo, SAPIEN, and asset initialization are not proved by config
construction or registry inspection.

Raw environment observations use `pixels`, nested camera dictionaries,
`agent_pos`, `environment_state`, or `robot_state`. `preprocess_observation`
normalizes these to LeRobot observation keys; `env_to_policy_features` and the
config `features_map` must agree with the policy. Evaluation depends on
`task`, `task_description`, `_max_episode_steps`, and `info["is_success"]`.

## Benchmark routing

| Trigger | Config route | Required gate |
|---|---|---|
| PushT | `pusht`, `PushT-v0` | `gym-pusht` and Pymunk; CPU smoke is reasonable |
| Aloha | `aloha` | `gym-aloha`; verify simulator import before rollout |
| LIBERO | `libero` | Linux, `hf-libero`, MuJoCo assets, render backend |
| LIBERO-plus | `libero_plus` | Plus fork/assets; do not mix with vanilla LIBERO |
| MetaWorld | `metaworld` | MetaWorld 3.0.0 and compatible Gymnasium |
| RobotWin/RoboTwin | `robotwin` | external RoboTwin tree, SAPIEN/CuRobo assets, NVIDIA GPU |
| VLABench | `vlabench` | external package, MuJoCo/dm-control, mesh assets, Linux |
| RoboCasa | `robocasa` | editable external packages, MuJoCo, kitchen/object assets |
| RoboMME | `robomme` | isolated Linux ManiSkill/SAPIEN/Vulkan environment |
| IsaacLab Arena | `isaaclab_arena` | Hub access plus explicit trusted remote-code consent |
| HIL simulation | `gym_manipulator` | `hilserl` extra, `gym_hil`, input device, usually NVIDIA GPU |

Use the detailed matrix and known conflicts in
[environment-overview.md](references/environment-overview.md) and
[compatibility.md](references/compatibility.md). Do not claim a runnable
rollout from a present Python module alone.

## Configuration decisions

Read [configuration.md](references/configuration.md) before editing nested
fields. Validate task names, observation/action dimensions, camera keys,
`n_envs >= 1`, positive FPS/horizon, and policy feature alignment. Keep
`hard_reset=false` for LIBERO only when fixed initial states are enabled and
reproducibility trade-offs are accepted. Use `use_async_envs=false` for the
first smoke when a simulator has fragile rendering or fork behavior.

Hub environment strings or `HubEnvConfig.hub_path` are a separate path:
`make_env` downloads/imports remote `env.py` only with
`trust_remote_code=true`. Treat this as code execution and a credential/network
boundary, never as a local registry result.

## Evaluation workflow

1. Run `environment_probe.py --env-type ...` and save its JSON output.
2. Resolve missing extras, version conflicts, backend, credentials, and assets;
   stop on a required gap rather than substituting an unrelated simulator.
3. For a CPU dispatch smoke, call `make_env` only for a known installed,
   lightweight candidate; reset at most one bounded episode and close it.
4. For a real benchmark evaluation, use `lerobot-eval` with the matching
   policy feature names, `--eval.batch_size=1` first, explicit task and
   episode count, and the benchmark's render/backend settings.
5. Verify success information and observation/action shapes before increasing
   parallelism. Record whether the result is config-only, partial smoke, or
   full rollout; do not label substitution as benchmark recovery.

See [workflows.md](references/workflows.md) for safe command patterns and
simulation-specific evaluation notes.

## RL and reward boundaries

The gRPC-free RL core exposes `ReplayBuffer`, `OnlineOfflineMixer`,
`RLTrainer`, `RLAlgorithmConfig`, and SAC. `RLTrainer.training_step()` asks the
algorithm for data, and SAC consumes batches containing state, action, reward,
next state, done, and truncation flags. `online_ratio` must be in `[0, 1]`;
SAC's `policy_config` must be populated before `make_algorithm`.

HIL-SERL actor/learner mode is different from a local RL smoke: the actor
collects transitions and interventions, queues them, receives weights, and
requires a learner service; the learner fills replay, delays updates until
`online_step_before_learning`, trains, checkpoints, and periodically pushes
weights. It requires the `hilserl` extra and hardware or `gym_hil` simulation.
Do not start actor/learner processes merely to validate JSON.

Reward configs route through `make_reward_model_config`,
`make_reward_model`, and `make_reward_pre_post_processors`. Supported built-in
names are `reward_classifier`, `sarm`, `robometer`, and `topreward`. Reward
models consume preprocessed tensor batches and emit per-sample rewards;
classifier threshold/success-reward settings affect HIL transition processing.
Transformer/VLM-backed models may need model weights, credentials, network, and
GPU memory. Zero-shot reward inference is not the same as trainable reward
model fitting.

## Recovery and handoff

On failure, classify it as missing package, version conflict, missing asset,
backend/display failure, credential/remote-code refusal, policy feature
mismatch, or actual simulator/runtime failure. Follow
[troubleshooting.md](references/troubleshooting.md); do not hide the class by
switching benchmarks. Report the exact command, status (`config`, `dispatch`,
`CPU smoke`, `GPU rollout`, or `none`), unresolved gates, and whether any
substitution was used.

## Bundled tools

- [environment_probe.py](scripts/environment_probe.py): registry/config and
  package-presence inspection; never downloads, creates, resets, or closes an
  external simulator.
- [rl_config_check.py](scripts/rl_config_check.py): bounded JSON schema/value
  checks; never trains, contacts an actor/learner, downloads weights, or
  initializes a simulator.

# Environment and RL configuration

This reference describes the safe configuration surface. Use it to decide
whether a field is a dispatch fact, a policy contract, or a runtime gate.

## Environment config lifecycle

The normal sequence is:

```python
from lerobot.envs.factory import make_env_config, make_env

cfg = make_env_config("pusht", task="PushT-v0")
# Inspect cfg.type, cfg.gym_id, cfg.gym_kwargs, cfg.features, cfg.features_map.
# Only after dependency/backend/asset approval:
envs = make_env(cfg, n_envs=1, use_async_envs=False)
```

`make_env_config` performs registry lookup and dataclass construction. It does
not download assets or create a simulator. `make_env` accepts an `EnvConfig` or
a Hub reference string. For local configs it checks `n_envs >= 1` and delegates
to `cfg.create_envs`; for Hub configs it requires explicit remote-code trust.
Do not call `make_env` from a config-only validation.

`EnvConfig.type` is the registered lowercase name. `package_name` and `gym_id`
are meaningful for base Gym-package environments, but custom benchmark
configs may override `create_envs` and leave `gym_kwargs` empty. The public
factory does not need a new `if/elif` branch for a registered config.

## High-value fields

| Field | Meaning | Validation / decision |
|---|---|---|
| `env.type` | registry key | must be a visible registered choice |
| `env.task` | task, suite, group, or comma-separated tasks | validate against the selected benchmark's task surface; group shortcuts are benchmark-specific |
| `env.fps` | simulator/control frequency | positive; LIBERO passes it as `control_freq` |
| `env.obs_type` | usually `pixels` or `pixels_agent_pos` | match declared features and checkpoint inputs; some wrappers reject `state` |
| `env.features` | raw feature shapes/types | action dimension must match action mode |
| `env.features_map` | raw-to-policy key mapping | image names must match dataset/policy normalization keys |
| `env.episode_length` | explicit horizon when supported | positive; `None` can mean benchmark task horizon |
| `env.task_ids` | selected suite/episode IDs | list values are benchmark-specific; do not assume task IDs equal names |
| `env.use_async_envs` / eval equivalent | worker strategy | start with false and `batch_size=1`; async may expose fork/render issues |
| `env.render_mode` | usually `rgb_array` | headless backends still need valid simulator setup |
| `env.control_mode` | LIBERO relative/absolute | match policy action parameterization |
| `env.action_mode` | RoboTwin joint/ee or VLABench eef | changes action dimension and optional dependencies |
| `env.camera_names` | RoboTwin camera list | each camera must exist in assets and policy features |
| `env.obj_registries` | RoboCasa object sources | use only registries whose packs are present; default lightwheel is safer |
| `env.dataset_split` | RoboMME split | one of train, val, test; still needs simulator episode data |
| `env.trust_remote_code` | Hub execution consent | false by default; never infer consent from a public repo ID |

Some benchmark task fields are not validated until the wrapper's custom
creator or worker imports the third-party package. Preserve that distinction
in the result.

## Observation and action alignment

For image environments, the wrapper generally emits HWC `uint8` arrays and
`preprocess_observation` returns BCHW float tensors. Do not pre-normalize the
raw image in a custom policy or rename camera keys casually. A policy trained
with `observation.images.camera1` will not automatically consume
`observation.images.image` unless a rename map or processor explicitly maps it.

Representative action/state contracts:

| Benchmark | Action | Common observation |
|---|---:|---|
| PushT | 2-D | pixel or 16-D environment state plus agent position |
| Aloha | 14-D | pixels and/or 14-D agent position |
| LIBERO | 7-D | two images plus an 8-D processor-produced state |
| MetaWorld | 4-D | one 480x480 image plus 4-D state |
| RoboTwin | 14-D joint or 16-D end-effector | three cameras plus 14-D state |
| VLABench | 7-D end-effector | three images plus 7-D state |
| RoboCasa | 12-D | three cameras plus 16-D state |
| RoboMME | 8-D joint or 7-D pose | two cameras plus 8-D state |

Use `env_to_policy_features(cfg)` to inspect visual channel-first shapes that a
policy should receive. LIBERO's environment processor is special: it flattens
the nested robot state into position, axis-angle orientation, and gripper
values. IsaacLab Arena's processor selects comma-separated `state_keys` and
`camera_keys`; at least one of those groups must be present.

## Evaluation config

Start with an explicit policy and a bounded command:

```bash
lerobot-eval \
  --policy.path=<compatible-checkpoint> \
  --env.type=<type> \
  --env.task=<one-task> \
  --eval.batch_size=1 \
  --eval.n_episodes=1 \
  --env.use_async_envs=false
```

The exact evaluation option name for async mode may be surfaced by the
installed CLI as `--eval.use_async_envs`; inspect `lerobot-eval --help` rather
than guessing. Use a matching `--rename_map` when a released checkpoint uses
canonical camera names different from the raw wrapper keys.

A successful configuration check means only that dataclass construction and
static values are coherent. A dispatch smoke means the factory returned the
expected nested mapping. A rollout smoke additionally requires reset, image
rendering, one or more action steps, success reporting, and clean close.

## HIL-SERL configuration

`HILSerlRobotEnvConfig` is registered as `gym_manipulator`. It carries
`robot`, `teleop`, and `HILSerlProcessorConfig`. The processor sub-configs
include:

- `control_mode`: commonly `gamepad` or `leader`;
- `observation`: joint velocity/current/EE pose toggles;
- `image_preprocessing`: crop and resize settings;
- `gripper`: enablement and movement penalty;
- `reset`: pose, reset/control durations, and terminate-on-success;
- `inverse_kinematics`: URDF, frame, bounds, and step sizes;
- `reward_classifier`: local pretrained path, threshold, and success reward.

`gym_manipulator` can create a real `RobotEnv`; it connects to hardware during
construction if the robot is not already connected. Treat any non-simulation
configuration as an actuation request and route it to the physical-control
skill for operator approval.

The simulation guide's `PandaPickCubeBase-v0`,
`PandaPickCubeGamepad-v0`, and `PandaPickCubeKeyboard-v0` names belong to the
external `gym_hil` package. A config import cannot prove these registrations.

## RL config surface

`TrainRLServerPipelineConfig` extends the ordinary training config with:

- optional `dataset` (RL can operate without an offline dataset);
- `algorithm` (`sac` is the registered built-in choice);
- `mixer` (currently `online_offline`);
- `online_ratio` in `[0, 1]`.

Validation fills a missing algorithm with SAC and attaches the policy config to
an algorithm whose `policy_config` is unset. `make_algorithm` still rejects a
config whose policy config is absent when called directly.

SAC fields with direct safety/shape implications include `actor_lr`,
`critic_lr`, `temperature_lr`, `discount`, `critic_target_update_weight`,
`num_critics`, `num_subsample_critics`, `temperature_init`, `target_entropy`,
`utd_ratio`, `policy_update_freq`, `grad_clip_norm`, and
`use_torch_compile`. Begin with defaults, CPU-compatible state features, and a
small bounded synthetic buffer; do not start an online actor merely to test
these values.

A replay transition contains `state`, `action`, `reward`, `next_state`,
`done`, `truncated`, and optional `complementary_info`. `ReplayBuffer` allocates
storage using the first transition's shapes. Keep storage on CPU when GPU
memory is constrained and move sampled batches to the learner device. The
`OnlineOfflineMixer` requires an online buffer and enforces the ratio range.

## Reward config surface

The built-in reward registry names are `reward_classifier`, `sarm`,
`robometer`, and `topreward`. All derive from `RewardModelConfig`, which
normalizes `device` and optionally stores a pretrained path and revision.

- `reward_classifier` is trainable and has CNN/transformer choices, camera
  count, optimizer settings, and feature validation.
- `sarm` is a temporal reward model with observation history, frame gap,
  annotation mode, and language/subtask fields; it is resource-heavy.
- `robometer` is a VLM reward model with progress/success output and an HF
  checkpoint by default; transformers, model files, and VRAM are gates.
- `topreward` is zero-shot in this release, uses a VLM identity and sampled
  frames, and is not equivalent to fitting a reward head.

Constructing a config is safe. `make_reward_model` loads/creates a torch module
and may load Hub/local weights; require explicit network/cache/VRAM approval.
`make_reward_pre_post_processors` must be selected together with the model's
input feature keys and dataset statistics. Keep reward scale, threshold, and
success semantics in the experiment record.

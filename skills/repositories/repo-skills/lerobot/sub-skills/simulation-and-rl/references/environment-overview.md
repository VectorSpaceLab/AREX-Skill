# Environment overview and evidence map

This reference is the self-contained environment map for LeRobot 0.6.2. It
separates **dispatch**, **dependency presence**, **assets**, and **runnable
rollout**. A row is not runnable merely because its config class can be
imported.

## Common Gymnasium contract

The public factory is `lerobot.envs.factory.make_env_config` followed by
`lerobot.envs.factory.make_env`. `EnvConfig` is a `draccus.ChoiceRegistry`.
The registered names in this release include `aloha`, `pusht`, `libero`,
`libero_plus`, `metaworld`, `robocasa`, `vlabench`, `isaaclab_arena`,
`robotwin`, `robomme`, and `gym_manipulator`.

A config declares `task`, `fps`, `features`, `features_map`,
`max_parallel_tasks`, and `disable_env_checker`. Its `gym_id` defaults to
`gym_<type>/<task>`, but multi-task integrations override `create_envs`.
The factory result is always a nested mapping from suite to task index to a
Gymnasium vector environment. Use `close()` on every vector environment after
a smoke or rollout.

The input convention consumed by `preprocess_observation` is:

| Raw key | Resulting policy key | Shape/dtype expectation |
|---|---|---|
| `pixels` as one HWC array | `observation.image` | HWC, `uint8` |
| `pixels` as a camera dict | `observation.images.<camera>` | each HWC, `uint8` |
| `agent_pos` | `observation.state` | numeric vector |
| `environment_state` | `observation.env_state` | numeric vector |
| `robot_state` | `observation.robot_state` | nested state; env processor may flatten it |

Image preprocessing transposes HWC to BCHW and scales `uint8` to float values
in `[0, 1]`. Every visual feature name in the policy must match the config's
`features_map` and the dataset/rename map. An environment should expose
`task_description`, `task`, `_max_episode_steps`, and `info["is_success"]`.

## Benchmark matrix

Status labels mean:

- **Dispatch**: the LeRobot config/factory path is present.
- **Install**: package or extra needed before importing/creating the actual
  simulator wrapper.
- **Assets**: external simulator files, meshes, initial states, or datasets;
  the bundled tools never download them.
- **Backend**: a rendering/compute/display requirement, not proved by config.
- **Credential**: Hub access or explicit trust/remote-code consent.

| Type | Dispatch | Install status | Asset status | Backend / platform | Credential / safety | First honest result |
|---|---|---|---|---|---|---|
| `pusht` | `PushtEnv`; base Gym ID `gym_pusht/PushT-v0` | `lerobot[pusht]` (`gym-pusht`, Pymunk) | package supplies the small task; no LeRobot asset gate | CPU-friendly; headless-safe for basic smoke | no credential; do not infer benchmark score from a config check | CPU reset smoke if extra is installed |
| `aloha` | `AlohaEnv`; Gym ID `gym_aloha/AlohaInsertion-v0` by default | `lerobot[aloha]` and its simulator package | package/task assets must be present | verify rendering and camera support; CPU dispatch may work | no credential; camera/actuation are separate gates | package import, then one bounded reset |
| `libero` | `LiberoEnv`; custom multi-suite creator | Linux `lerobot[libero]`, `hf-libero`, MuJoCo | LIBERO task files and initial states must resolve | MuJoCo; set a valid `MUJOCO_GL` such as `egl` for headless use | no Hub credential for local tasks; no real actuation | config/feature check, then one task reset |
| `libero_plus` | `LiberoPlusEnv`; reuses LIBERO interface | plus fork installed separately; vanilla `hf-libero` is not the plus fork | plus perturbation assets are required | Linux and MuJoCo; headless backend required on servers | no remote-code path; isolate fork | config-only until plus assets are proven |
| `metaworld` | `MetaworldEnv`; custom task/group creator | `lerobot[metaworld]`, MetaWorld `3.0.0`, SciPy | simulator package includes task definitions | rendering compatibility matters; Gymnasium `1.1.0` is the documented repair for a known assertion | no credential | config plus package import; rollout only after version check |
| `robotwin` / RobotWin | `RoboTwinEnvConfig`; custom creator | external RoboTwin tree, SAPIEN, CuRobo, mplib, PyTorch3D; no LeRobot extra | RoboTwin assets and task config must be provisioned | Linux; NVIDIA GPU and CUDA 12.1 are documented target; `PYTHONPATH` must expose the tree | no Hub credential; external code is executable, so pin/inspect it | config-only or import check unless all external gates pass |
| `vlabench` | `VLABenchEnv`; custom creator | external VLABench and RRT package; no PyPI/LeRobot extra; MuJoCo and dm-control pins | mesh/object assets are required | Linux; MuJoCo/dm-control; `MUJOCO_GL=egl` for headless; camera rendering | task code may use external services for some upstream capabilities; no automatic use here | config-only until package, meshes, and renderer pass |
| `robocasa` | `RoboCasaEnv`; custom creator | external editable RoboCasa and robosuite; no LeRobot extra because upstream pins an incompatible LeRobot version | kitchen macros, fixtures, textures, and object registry; default wrapper expects `lightwheel` | MuJoCo and offscreen rendering; headless backend required on servers | no Hub credential; external package code is a supply-chain boundary | config-only until assets and a single task reset pass |
| `robomme` | `RoboMMEEnv`; custom creator | external `robomme`; no extra because ManiSkill pins conflict with base NumPy | benchmark/SAPIEN episode assets and test split | Linux; SAPIEN/Vulkan; GPU recommended, CPU rendering is slow | no credential for local benchmark, but isolate the environment | config-only unless the isolated environment is active |
| `isaaclab_arena` | `IsaaclabArenaEnv`; `HubEnvConfig` | remote Hub environment rather than a local package | remote environment and its Isaac assets | Isaac/Omniverse GPU stack; default config requests `cuda:0` | `trust_remote_code=true` is explicit consent to execute Hub Python; private/gated repos also need credentials | metadata-only with trust off; rollout only with explicit approval |
| `gym_manipulator` | `HILSerlRobotEnvConfig`; HIL-SERL adapter | `lerobot[hilserl]`, including `gym-hil`, gRPC, and kinematics deps | simulator assets for `gym_hil`, or physical robot setup | simulator guide expects NVIDIA GPU; physical path needs cameras/motors/input device | physical path can actuate; require operator confirmation and route to robot-control | config-only or simulator-only smoke; never physical by default |

## Built-in simulation choices

### PushT and Aloha

These are the ordinary Gym-package path. The base `EnvConfig.create_envs`
checks the Gym registry, imports `gym_<type>` if needed, constructs one
`SyncVectorEnv` by default, and passes the config's `gym_kwargs`. PushT uses a
2-D action and supports pixel or environment-state observation variants.
Aloha defaults to a 14-D action and pixel/state variants. The testable property
is package/registry dispatch; a full rollout still requires simulator rendering.

### LIBERO and LIBERO-plus

`LiberoEnv` uses task suites and task IDs rather than a normal Gym registry.
The default task is `libero_10`; standard suites include `libero_spatial`,
`libero_object`, `libero_goal`, `libero_90`, and `libero_10`. Actions are 7-D
continuous values. Pixel observations use two cameras; `LiberoProcessorStep`
converts nested robot state into an 8-D state used by common policies.
`control_mode` is `relative` or `absolute` and must match the checkpoint.

`LiberoPlusEnv` has the same interface with `is_libero_plus=true`. It is a
robustness variant with perturbations, not a drop-in reason to silently use
vanilla tasks. The two package trees must not be installed together: verify
which `libero` import is active before evaluation.

### MetaWorld

Tasks can be a single task, a comma-separated list, or difficulty groups
`easy`, `medium`, `hard`, and `very_hard`. The wrapper uses a 4-D action and,
for pixel/state mode, one 480x480 camera plus a 4-D state. The implementation
creates each simulator lazily inside its worker to avoid stale rendering
contexts. This means an import/config check can succeed before reset fails.

### RoboTwin, VLABench, RoboCasa, and RoboMME

These wrappers deliberately defer heavy simulator creation until worker reset.
Their `create_envs` methods are useful dispatch evidence but are not external
asset checks. Start with one task, one environment, synchronous workers, and a
short episode. Preserve raw camera names when matching a checkpoint:
RoboTwin exposes `head_camera`, `left_camera`, and `right_camera`; VLABench
exposes `image`, `second_image`, and `wrist_image`; RoboCasa exposes its three
`robot0_*` names; RoboMME defaults to `camera1` and `camera2`.

RoboTwin defaults to dual-arm 14-D joint actions and supports 16-D `ee` pose
actions. RoboCasa uses a 12-D flattened action and 16-D state. VLABench uses a
7-D end-effector action/state. RoboMME uses 8-D `joint_angle` or 7-D `ee_pose`
actions and a 300-step default horizon. These dimensions are config facts;
policy compatibility is still required.

## IsaacLab and Hub environments

A string passed to `make_env` is interpreted as a Hub environment reference.
The factory resolves the Python file and calls its `make_env` function only
when `trust_remote_code` is true. A local config object with `hub_path` follows
the same path. Keep Hub cache and revision choices explicit. A registry result
cannot prove that a remote environment is safe, available, or compatible with
the requested GPU.

## What this map intentionally does not do

It contains no benchmark/asset downloader, no credential discovery, no remote
code execution, and no simulator rollout. Asset packs, exact upstream commits,
GPU driver versions, and external task correctness remain explicit handoff
items. Use the compatibility and troubleshooting references to classify those
limits rather than replacing a missing benchmark with a convenient one.

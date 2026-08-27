# Training configuration and task contract

## When to read

Read this before changing a task, device, environment count, action scale,
observation layout, reward term, or PPO setting. The configuration is Hydra-
composed and the values below are the contract expected by the generated
policy/checkpoint.

## Composition and supported tasks

The training entry point composes a root config named `config` from a `cfg`
directory and selects a task config with the `task=<name>` override. The
supported task names are exactly:

| Hydra task | Environment class | Asset family | Notes |
|---|---|---|---|
| `Aliengo` | `Aliengo` | Aliengo | README's primary training example |
| `A1` | `A1Task` | A1 | Same 48/12 task contract |
| `Go1` | `Go1` | Go1 | Same 48/12 task contract |

The task map also contains `ConfigPPO`, but it is a training-config class,
not a user-selectable robot task. Older documentation examples using `Ant`
are stale for this repository version and should not be copied.

The root config derives `task_name` from `${task.name}`. The main defaults are:

- `task=Aliengo`
- `num_envs=''`, resolved by each task to 32
- `seed=42`
- `torch_deterministic=False`
- `max_iterations=''`, leaving the PPO class default of 5000
- `physics_engine=physx`
- `pipeline=gpu`
- `sim_device=cuda:0`, `rl_device=cuda:0`, `graphics_device_id=0`
- `test=False`, `checkpoint=''`, `headless=False`
- `multi_gpu=False`, video capture disabled

The task resolver uses the default `32` when `num_envs` is empty; an explicit
positive `num_envs=N` overrides it. Keep `sim_device` and `rl_device` explicit
when reproducing a run.

## Hydra working-directory behavior

Use the working directory and public console/module entry point selected by the
current project package. The inspected entry point declares a local `cfg`
config path and `config` config name; Hydra consumes `key=value` overrides and
the root config sets `hydra.output_subdir: null` and `hydra.run.dir: .`.

The checkpoint override is converted with Hydra's `to_absolute_path` before
constructing the environment. Relative paths therefore mean paths relative to
the public command's launch context, not paths relative to this sub-skill.
Choose a user-owned working/run directory, pass an explicit existing checkpoint
path, and record the launch directory in experiment notes. Do not rely on a
source checkout's implicit current directory.

The resolved configuration is printed, then written as `config.yaml` in the
new timestamped run directory after the runner is created. This copy is useful
for auditing a run; it is not a substitute for validating the checkpoint or
backend.

## Override table

These are the public top-level overrides used by the entry point or its config.
Use the exact spelling on the left.

| Override | Type/examples | Effect |
|---|---|---|
| `task` | `A1`, `Aliengo`, `Go1` | Selects task config and environment class |
| `task_name` | task name | Used to select the task map and PPO experiment name; normally derived |
| `num_envs` | positive integer, e.g. `4` | Vectorized environment count |
| `headless` | `True`/`False` | Viewer rendering switch |
| `test` | `True`/`False` | Evaluation loop versus `learn` |
| `checkpoint` | existing relative/absolute file | Load model before test or resume |
| `seed` | integer; `-1` randomizes | Seeds the run through the utility helper |
| `torch_deterministic` | boolean | Requests deterministic Torch behavior through seed setup |
| `max_iterations` | positive integer | Overrides PPO runner update count |
| `sim_device` | `cuda:0`, `cpu` | Physics simulation device selector |
| `rl_device` | `cuda:0`, `cpu` | RSL-RL/policy device selector |
| `pipeline` | `gpu` or `cpu` | Controls `use_gpu_pipeline` resolver |
| `physics_engine` | `physx` or `flex` | Selects Isaac Gym physics backend |
| `graphics_device_id` | integer | Viewer graphics device |
| `num_threads` | integer | PhysX CPU worker threads |
| `solver_type` | `0` or `1` | PhysX solver selection |
| `num_subscenes` | integer | PhysX scene partitioning |
| `multi_gpu` | boolean | Config field; no custom multi-GPU logic is added in the entry point |

Nested `task.env.*` and `task.sim.*` values are Hydra configuration values,
but changing them changes the trained model contract. Make those changes only
with a fresh validation plan and a new checkpoint identity.

## Environment dimensions and observation order

All three robot task implementations set:

- `numObservations = 48`
- `numActions = 12`
- `clipObservations = 5.0`
- `clipActions = 1.0`

The simulator task observation concatenates the following in order, per
parallel environment:

1. base position: 3 values;
2. body-frame base linear velocity, multiplied by `linearVelocityScale`: 3;
3. body-frame base angular velocity, multiplied by `angularVelocityScale`: 3;
4. command `[linear_x, linear_y, yaw]`, scaled by the linear/linear/angular
   scales: 3;
5. joint position minus default joint position, multiplied by
   `dofPositionScale`: 12;
6. joint velocity multiplied by `dofVelocityScale`: 12; and
7. previous/current action buffer: 12.

The default normalization scales are all `1`. The command ranges are
`linear_x=[-2.5,2.5]`, `linear_y=[-1.0,1.0]`, and `yaw=[-2.5,2.5]`.

Important bridge distinction: `WeightPolicy.compute_observations` also
produces 48 values, but its third three-value block is `-ground_normal_yaw`
(projected gravity) rather than the simulator task's base-position block.
Its remaining blocks are body velocities, scaled commands, joint position
error, joint velocity, and the previous 12 weights. Treat this as a separate
inference-input contract. Do not silently replace one ordering with the other
for an existing checkpoint; verify or retrain if aligning them.

## Actions, bridge, and rewards

The policy emits 12 values. The environment clips them to `[-1, 1]` before
`pre_physics_step`. The training entry point sets the MPC bridge on, so the
12 values are affine-mapped to MPC parameters:

- indices 0-2: `4*a + 5`, range `[1, 9]`;
- indices 3-5: `20*a + 50`, range `[30, 70]`; and
- indices 6-11: `a + 1`, range `[0, 2]`.

The bridge appends a thirteenth zero weight after the 12 policy outputs and
passes the command vector `[linear_x, linear_y, yaw, weight_0..weight_12]` to
the lower-level controller. The controller returns one torque per joint. See
[api-reference](api-reference.md) and [mpc-control](../../mpc-control/SKILL.md)
for the cross-skill boundary.

The default task uses `dt=0.01`, `substeps=2`, z-up gravity `[0,0,-9.81]`,
GPU pipeline enabled when `pipeline=gpu`, and a 20-second episode. Reward
terms are velocity tracking for XY and yaw, penalties for vertical/angular
velocity, squared torques, and knee contacts; each configured reward scale is
multiplied by `dt`, and the summed reward is clipped below at zero. Resets are
triggered by base, knee, or hip contact above the contact threshold or by the
episode timeout. The default knee-contact scale is zero, but knee/hip/base
contacts still participate in reset logic.

When the bridge is disabled, the task uses clipped PD torque control from
`actionScale` and default joint positions instead. That is a different
control contract and must not be used with a bridge-trained checkpoint without
an explicit experiment change.

## PPO settings and checkpoints

The default `LeggedCfgPPO` values are:

- Actor and critic hidden layers: `[512, 256, 128]`;
- activation: `elu`;
- PPO learning rate `1e-3`, adaptive schedule, `gamma=0.99`, `lam=0.95`;
- 5 learning epochs, 4 mini-batches, clip parameter `0.2`, entropy coefficient
  `0.01`; and
- 24 rollout steps per environment, 5000 maximum iterations, save interval
  100.

`OnPolicyRunner` constructs `ActorCritic` with the environment's 48
observations and 12 actions. A saved runner checkpoint contains at least:
`model_state_dict`, `optimizer_state_dict`, `iter`, and `infos`. Loading is
strict for the actor state dict and also restores the optimizer by default;
there is no safe shape-adaptation mode in the source workflow.

The policy loader used by `WeightPolicy` also expects `model_state_dict` and
constructs the same 48-input/12-output actor with the PPO policy settings.
Validate task, observation ordering, action mapping, and hidden dimensions
before using a checkpoint outside the run that produced it.

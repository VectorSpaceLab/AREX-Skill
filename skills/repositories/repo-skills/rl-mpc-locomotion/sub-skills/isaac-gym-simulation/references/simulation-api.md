# Simulation API and data flow

This reference describes the project-facing Isaac Gym contract without
requiring access to implementation files. Isaac Gym Preview 4 exposes a
procedural API: `gymapi` owns handles and simulation operations, while
`gymtorch` can expose simulator buffers as PyTorch tensors.

## 1. Acquire and configure the simulation

Use this order and fail fast at each boundary:

1. `gym = gymapi.acquire_gym()`.
2. Allocate `sim_params = gymapi.SimParams()`.
3. Set `sim_params.dt` to the controller timestep, normally `0.01`, and set
   `substeps = 2`.
4. Select Z-up with `UP_AXIS_Z` and gravity `Vec3(0, 0, -9.81)`.
5. For PhysX set GPU use according to the selected `cuda:N` device, solver type
   `1` (TGS), six position iterations in the direct helper (four in the RL
   task configuration), one velocity iteration, contact offset `0.02`, rest
   offset `0.0`, bounce threshold `0.2`, and max depenetration velocity `100`.
   Preserve the configured value when reproducing an RL result rather than
   assuming the direct-launcher value.
6. Create PhysX with compute and graphics ids. A null result is a hard failure;
   do not continue to asset loading.
7. In the vector-task path, parse the task config first. `pipeline: gpu` and a
   CUDA simulation device select `use_gpu_pipeline`; a CPU simulation forces
   the pipeline back to CPU. The configured RL device may still differ from
   the simulation device, so make transfers explicit.

`graphics_device_id = -1` is appropriate for a headless vector task when
camera sensors are disabled. A viewer path needs a real graphics device and a
valid display/runtime. GPU PhysX, GPU pipeline, and rendering are independent
checks; report each one separately.

## 2. Add world geometry before actors

For a flat world, create `PlaneParams`, use normal `Vec3(0, 0, 1)`, and set the
configured static/dynamic friction and restitution before `gym.add_ground`.
For a mesh terrain, create the height field, convert it with
`convert_heightfield_to_trimesh`, fill `TriangleMeshParams` vertex/triangle
counts and transform, and call `gym.add_triangle_mesh` before environment
creation. See [assets-and-terrains.md](assets-and-terrains.md) for the
project's terrain variants and coordinate offsets.

Do not add a flat plane and assume it is the same experiment as the RL terrain
path. The interactive launcher adds a plane and then two demonstration meshes;
the RL task chooses a plane or a random mesh based on its flat-ground setting.
That difference affects contacts and rewards.

## 3. Load and instantiate actors

Configure `AssetOptions` before loading the URDF. The project uses floating
bases (`fix_base_link: False`), mesh materials, flipped visual attachments,
zero linear/angular damping, and `armature: 0.01`. The RL task also starts
from `DOF_MODE_NONE` and then sets per-DOF effort properties. Loading returns
an asset handle; inspect:

- `get_asset_dof_count` and `get_asset_rigid_body_count`;
- `get_asset_dof_names` and `get_asset_rigid_body_names`;
- the expected body names, especially `trunk`, names containing `foot`,
  `thigh`, and `hip`.

Create a grid with lower/upper bounds and `num_per_row`, then for each
environment create one actor at its configured base height. Cache both handles.
Use distinct actor names and collision group/filter values consistently. The
project's direct helper uses actor name `MyActor`, group equal to the env index,
and filter `1`; the RL tasks use `robot`, the env index, filter `1`, and a
zero additional argument. Those conventions are not interchangeable with a
multi-actor scene without checking collision behavior.

After creating actors, set the copied DOF property array on each actor. For
force control, use `driveMode = DOF_MODE_EFFORT`, `stiffness = 0`, and
`damping = 0`. Position-target control is an alternate commented design, not
the verified project default.

## 4. Prepare, acquire, and refresh state

The vector task calls `prepare_sim` after its subclass creates the sim and
before it allocates state buffers. Follow that order for tensor access:

```text
create sim -> create ground/terrain -> create envs/actors -> prepare_sim
-> acquire buffers -> wrap buffers -> refresh before first read
```

The one-actor-per-environment tensor contracts are:

| Buffer | Raw/project view | Meaning |
|---|---:|---|
| actor root state | `(num_envs, 13)` | position 3, quaternion 4, linear velocity 3, angular velocity 3 |
| DOF state | `(num_envs * num_dof, 2)` | position and velocity per DOF |
| DOF position/velocity | `(num_envs, num_dof)` | views of the two DOF columns |
| net contact force | `(num_envs, num_bodies, 3)` | XYZ force per rigid body |
| commands | `(num_envs, 3)` | x velocity, y velocity, yaw rate |
| actions | `(num_envs, 12)` | normalized policy actions |
| observations | `(num_envs, 48)` | policy input after clipping/scaling |

The root tensor's first 13 values are ordered `x,y,z,qx,qy,qz,qw,vx,vy,vz,
wx,wy,wz`. Raw global tensors can contain all actors, so only reshape to the
projected view when the one-actor-per-env invariant is true.

Call `refresh_dof_state_tensor`, `refresh_actor_root_state_tensor`, and
`refresh_net_contact_force_tensor` after a physics step and before consuming
those values. A wrapped tensor is a view, not a snapshot; stale reads are a
common source of apparently one-step-lagged observations. Use
`gymtorch.unwrap_tensor` only for tensors on the simulator's expected device.
A deliberate `.detach().cpu().numpy()` round trip is used by the MPC bridge,
but it is a performance boundary and must not be hidden in a high-frequency
path.

## 5. Step an interactive simulation

The direct controller launcher follows this lifecycle:

```text
acquire gym
  -> create sim
  -> add plane and demonstration terrain
  -> create envs and actors
  -> create viewer
  -> set each actor's effort properties
  -> construct and initialize one controller per actor
  -> loop until viewer closes:
       simulate
       fetch_results(sim, True)
       read gamepad command (or keep zero command)
       read DOF and selected rigid-body states
       run controller
       apply_actor_dof_efforts
       optionally draw debug lines
       periodically step_graphics/draw_viewer
       sync_frame_time
  -> stop gamepad
  -> destroy viewer
  -> destroy sim
```

The controller should receive the structured DOF state and selected trunk
rigid-body state, then return one effort per DOF. Efforts must be applied every
frame. `render-fps` controls how often graphics are drawn relative to the
controller loop; it does not change the physics timestep. Validate that
`num-envs` is positive before taking its square root for the grid.

For a new loop, use `try/finally`: stop input workers, draw no more frames after
viewer destruction, destroy the viewer before the simulation, and release the
simulation even on a keyboard interrupt or controller exception. Never create
a viewer in a safe diagnostic or headless check.

## 6. Step a vectorized RL task

The base vector task allocates observation, reward, reset, timeout, progress, and
randomization buffers. A task subclass then creates the simulation, allocates
wrapped simulator tensors, initializes commands/default DOF positions, and
resets all environment ids.

A call to `env.step(actions)` performs:

1. Optional action randomization and clipping to `clipActions` (normally `1`).
2. `pre_physics_step`, which sends batched torques through
   `set_dof_actuation_force_tensor`; with the MPC bridge enabled, normalized
   actions are rescaled, states/commands cross to CPU, each controller runs,
   and the torque matrix returns to the simulation device.
3. `controlFrequencyInv` simulation substeps. The renderer may fetch results;
   CPU simulation explicitly fetches results after the loop.
4. Timeout calculation, `post_physics_step`, reset of finished envs, tensor
   refresh, reward and observation computation.
5. Observation randomization, timeout metadata in `extras`, clipping, and move
   to `rl_device`.

The return is five values, in order: observations, privileged observations
(`None` in these tasks), rewards, reset flags, and an extras dictionary. A
reset performs a zero-action step, then returns the current observations and
privileged observations.

The task's reset path randomizes DOF positions around the default pose and
velocities in a small range, writes root and DOF state with indexed setters,
randomizes x/y/yaw commands, resets progress, and marks the selected ids. Do
not treat a reset flag as a global stop: it is one flag per environment.

## 7. Read sensors and apply torques

For structured API access, `get_actor_dof_states(..., STATE_ALL)` yields
`pos` and `vel` arrays in meters/radians and per-second units. Rigid-body state
contains `pose.p`, `pose.r`, `vel.linear`, and `vel.angular`. Resolve a body
index in `DOMAIN_ACTOR` before indexing the actor body-state array.

For contact sensing, the vector tasks use the batched net contact-force tensor.
The reward path treats forces over magnitude `1` as contact for the base,
knees, and hips. DOF force sensors are not enabled in the shipped RL task.
If joint forces are needed, enable them for every actor before stepping and
retrieve the per-actor DOF force array. Asset force sensors must instead be
created on the asset before actor instantiation; the direct helper's foot
sensor utility targets the documented foot body indices and reads force/torque
records per actor.

The non-bridge RL branch computes clipped PD-like efforts:
`Kp * (actionScale * action + default_dof_pos - dof_pos) - Kd * dof_vel`,
clipped to `[-55, 55]`. The bridge branch delegates effort generation to the
MPC controller. These paths have different latency and numerical contracts;
route controller questions to [mpc-control](../../mpc-control/SKILL.md).

## 8. Verification without a viewer

The bundled diagnostic checks package discoverability, importability of the
public Isaac Gym modules without acquiring a gym, PyTorch/CUDA visibility, and
optional asset presence. It intentionally does not call `acquire_gym`,
`create_sim`, `create_viewer`, or a native test. A passing diagnostic is only a
prerequisite check; a real rollout remains a separate required-backend test.
For training and checkpoint behavior, use [rl-training](../../rl-training/SKILL.md)
so RL algorithm evidence is not confused with simulator evidence.

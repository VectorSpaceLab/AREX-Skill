---
name: isaac-gym-simulation
description: "Operate the Isaac Gym Preview 4 simulation, vectorized locomotion
  environments, robot assets, terrain, state tensors, effort control, and
  interactive MPC launcher for this project."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Isaac Gym simulation

Use this sub-skill when the task involves Isaac Gym setup, PhysX simulation,
URDF loading, env/actor creation, terrain, state or force data, vectorized RL
stepping, or the interactive `RL_MPC_Locomotion` launcher. It is a procedural,
data-oriented guide: handles create the simulation, while NumPy or PyTorch
arrays/tensors carry state and commands.

## Required-backend gate

**RL and simulation execution is currently blocked.** The closed-source Isaac
Gym Preview 4 package was unavailable in the construction environment. The
partial handoff records PyTorch 1.10/CUDA 11.3, an A100 allocation, repository
imports, `rsl_rl`, and `mpc_osqp` as passing checks; those results do **not**
prove that Isaac Gym is installed or usable. From this sub-skill's directory, run the bundled diagnostic first:

```bash
python scripts/check_isaacgym.py
```

Do not claim that an RL rollout, viewer run, terrain run, or Isaac Gym import
passed until this gate is cleared with the vendor package and a compatible
GPU/runtime. The diagnostic never creates a viewer or simulation.

## Route quickly

- Need the exact lifecycle, API calls, tensor shapes, or viewer loop: read
  [references/simulation-api.md](references/simulation-api.md).
- Need robot selection, URDF/mesh caveats, ground, or terrain generation: read
  [references/assets-and-terrains.md](references/assets-and-terrains.md).
- Need a failure diagnosis or a safe stop condition: read
  [references/troubleshooting.md](references/troubleshooting.md).
- Need the PPO/Hydra task, checkpoint, observation, or training contract: route
  to [rl-training](../rl-training/SKILL.md).
- Need MPC state conversion, controller modes, gait, or solver behavior: route
  to [mpc-control](../mpc-control/SKILL.md).

## Setup contract

Use Python 3.8 with PyTorch 1.10.0 and CUDA 11.3, Isaac Gym Preview 4, NumPy,
Hydra/OmegaConf, and the pinned `rsl_rl` integration. A compatible NVIDIA
GPU/driver is required for the configured PhysX GPU pipeline; the upgrade notes
call out driver 470 or newer. The project normally uses `cuda:0` for both
simulation and RL, `physics_engine: physx`, Z-up gravity `[0, 0, -9.81]`,
`dt: 0.01`, and two substeps. Keep the setup sequence and backend verdict
explicit; CUDA-visible PyTorch alone is insufficient.

## Canonical procedural order

1. Acquire a gym handle, create `SimParams`, and set the control timestep,
   substeps, up-axis, gravity, and PhysX options.
2. Create the PhysX simulation with compute and graphics device ids. Stop on a
   null simulation handle.
3. Add exactly the intended ground plane or triangle terrain before creating
   environments. Do not silently combine terrain conventions from the
   interactive and RL paths.
4. Select one supported URDF, configure `AssetOptions`, load it, inspect DOF
   and rigid-body names/counts, and configure effort properties.
5. Create the environment grid and one actor per environment. Cache env and
   actor handles and resolve the `trunk`, foot, thigh, and hip body handles.
6. Prepare the simulation before acquiring/wrapping GPU state tensors. Refresh
   every tensor immediately before reading it.
7. Create a viewer only when rendering is requested. In each loop apply
   controls, simulate, fetch results as required by the pipeline, read state,
   update graphics, and synchronize frame time.
8. On every exit path stop the gamepad thread, destroy the viewer if created,
   then destroy the simulation. Use `try/finally` in new integrations.

## Control and data rules

- Effort mode is the project default. Set each DOF `driveMode` to
  `DOF_MODE_EFFORT` and stiffness/damping to zero, then apply a complete effort
  vector every physics frame. Missing a frame does not preserve a safe command.
- The direct launcher uses structured NumPy state (`pos`, `vel`; body pose,
  quaternion, linear and angular velocity) and applies per-actor efforts. The
  RL tasks use `gymtorch` wrappers and batched tensors; do not mix the two
  contracts without an explicit CPU/GPU conversion.
- With one actor per env, root state is `(num_envs, 13)` in the order position
  3, quaternion 4 `(x,y,z,w)`, linear velocity 3, angular velocity 3. DOF state
  is flattened as `(num_envs * num_dof, 2)` and reshaped to positions and
  velocities `(num_envs, num_dof)`. Net contacts are `(num_envs, num_bodies,
  3)`.
- RL actions are `(num_envs, 12)` and clipped to `[-1, 1]`; observations are
  `(num_envs, 48)`, commands are `(num_envs, 3)`, rewards/resets are per-env.
  The vector task returns `(obs, privileged_obs, rewards, resets, extras)`.
- The RL observation is base position, body-frame linear/angular velocity,
  scaled velocity command, offset DOF position, scaled DOF velocity, and the
  previous action. The standard simulator must refresh DOF, root, and contact
  tensors before computing it.

## Interactive launcher contract

The supported robots are `Aliengo`, `A1`, and `Go1`. The launcher accepts
`--robot`, `--mode {Fsm,Min,Policy}`, `--num-envs`, `--render-fps`,
`--disable-gamepad`, and `--checkpoint`. `Policy` consumes a checkpoint; if it
is omitted, the policy runner resolves the latest project run. `Fsm` is the
normal hierarchical controller and `Min` is the minimal MPC runner.

Without `--disable-gamepad`, an Xbox-like device is required. The left stick
commands forward/lateral velocity, the right stick commands yaw, LB cycles
Trot/Walk/Bound, and RB cycles Locomotion/Recovery Stand. LB+RB requests an
emergency stop; press the left stick to release it. For unattended or
headless automation, disable the gamepad and do not create a viewer. The
interactive launcher still renders and therefore remains backend-blocked here.

## Completion criteria

A simulation task is complete only when the backend diagnostic passes, asset
paths and names resolve, the simulation is stepped in the documented order,
state refreshes and tensor shapes are checked, and cleanup is observed. If the
backend is absent, provide the exact blocked prerequisite and stop; do not
substitute a CPU-only import or a successful MPC build as Isaac Gym evidence.

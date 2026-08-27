---
name: rl-mpc-locomotion
description: "Guide quadruped locomotion workflows built from Python convex MPC,
  FSM and gait control, NVIDIA Isaac Gym simulation, Hydra/RSL-RL training,
  learned MPC-weight policies, robot assets, and CUDA or solver
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RL-MPC Locomotion

Use this repo skill when a task involves the `rl_mpc_locomotion` package, its
`MPC_Controller` and `RL_Environment` modules, quadruped torque control, Isaac
Gym locomotion simulation, or learned MPC-weight policies. This is a router,
not a replacement for the focused workflow references.

## Gate before acting

1. Read [repository provenance](references/repo-provenance.md) when checking
   whether the guidance matches the source revision.
2. Use [setup-and-diagnostics](sub-skills/setup-and-diagnostics/SKILL.md) first
   for an isolated Python 3.8-era environment, pinned native inputs,
   `mpc_osqp`, CUDA, Isaac Gym, asset, and checkpoint probes.
3. Treat Isaac Gym Preview 4 as a required external backend for simulation,
   RL training/evaluation, and the interactive launcher. The construction
   evidence verified PyTorch 1.10/CUDA 11.3, CUDA allocation, repository
   imports, `rsl_rl`, and `mpc_osqp`, but did not verify Isaac Gym. Do not
   substitute a CUDA tensor or CPU import for that gate.

## Route by task

- **MPC, gait, FSM, state estimation, robot model, torque arrays, or solver
  binding:** read [mpc-control](sub-skills/mpc-control/SKILL.md).
- **Hydra training, evaluation, task YAML, observations/actions/rewards,
  checkpoints, policy bridge, or TensorBoard:** read
  [rl-training](sub-skills/rl-training/SKILL.md), then route low-level torque
  questions to `mpc-control`.
- **Isaac Gym setup, PhysX, URDF/assets, terrains, state tensors, effort
  control, viewer lifecycle, or gamepad launcher:** read
  [isaac-gym-simulation](sub-skills/isaac-gym-simulation/SKILL.md).
- **Installation order, submodules, PyTorch/CUDA conflicts, compiled
  extension, optional solver, missing config/asset, or backend diagnosis:**
  read [setup-and-diagnostics](sub-skills/setup-and-diagnostics/SKILL.md).

For shared concepts and cross-route boundaries, read
[the architecture overview](references/architecture-overview.md). For a
cross-cutting failure, read [troubleshooting](references/troubleshooting.md).

## Minimal public package check

In a current project copy, install the package after its documented native
inputs are present:

```bash
python -m pip install -e .
python -c "import MPC_Controller, RL_Environment, mpc_osqp; print('MPC package imports passed')"
```

Run the bundled checks from the generated skill root (or enter the setup
sub-skill directory). Set `PROJECT_COPY` to the current user-supplied project
copy when validating its native layout/config/assets; it is not a path inside
this skill bundle. The checks are read-only unless `--build` is passed
explicitly to the extension checker:

```bash
PROJECT_COPY=/path/to/current/project-copy
python sub-skills/setup-and-diagnostics/scripts/check_environment.py --pip-check
python sub-skills/setup-and-diagnostics/scripts/check_mpc_extension.py --repo-root "$PROJECT_COPY" --check-submodules --strict
python sub-skills/setup-and-diagnostics/scripts/validate_config.py --repo-root "$PROJECT_COPY" --all-tasks --strict
```

The setup sub-skill documents the explicit project-root argument needed when
checking a particular checkout. These commands do not prove Isaac Gym or a
stable gait.

## Safety and handoff

Never start a viewer, gamepad reader, training run, or policy deployment as an
installation smoke test. Confirm robot/task, device, checkpoint, run directory,
backend availability, and cleanup behavior first. The project supports
`Aliengo`, `A1`, and `Go1` in the public runtime selection; the bundled Mini
Cheetah assets are not a launcher robot choice. Sim-to-real operation is outside
this repository's verified contract.

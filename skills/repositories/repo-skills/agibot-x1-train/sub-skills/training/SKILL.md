---
name: "training"
description: "Route X1 DH stand PPO training, configuration inspection,
  checkpoint lifecycle, and algorithm-only shape checks with explicit Isaac Gym
  backend limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# X1 DH training

Use this sub-skill for the registered `x1_dh_stand` task: installing the
training stack, inspecting its configuration and observation contract, building
a bounded training command, running DH PPO, resuming from a checkpoint, and
triaging runner or tensor-shape failures.

## Backend boundary

The environment is an Isaac Gym Preview 4 task and its native environment,
terrain, asset, and `train.py` execution require Isaac Gym plus a compatible
CUDA/PhysX setup. Isaac Gym Preview 4 is unavailable in the current Creator
environment. Mark native training as
**BLOCKED_REQUIRED_BACKEND: Isaac Gym Preview 4 unavailable** unless the user
provides and verifies that dependency. Never replace it with a fake simulator.
CPU/Torch checks in this route validate only configuration arithmetic, policy
wiring, and rollout-buffer shapes; they do not validate Isaac Gym behavior.
MuJoCo playback is outside this route; after a checkpoint, hand off to
[playback](../playback/SKILL.md) or [sim2sim](../sim2sim/SKILL.md). For JIT or
ONNX artifacts, use [export](../export/SKILL.md).

## Start here

1. Read [workflows](references/workflows.md) for install, bounded launch,
   resume, checkpoint, and logging procedures.
2. Read [configuration](references/configuration.md) before changing any
   dimension, history stack, command, gait, terrain, PD, reward, or
   randomization field.
3. Read [algorithm API](references/algorithm-api.md) for DH actor/critic,
   `DHPPO`, runner, and `RolloutStorage` contracts.
4. Use [troubleshooting](references/troubleshooting.md) for backend, import,
   shape, OOM, checkpoint, and logging symptoms.
5. Run the safe helper first:
   `python scripts/training_preflight.py --help`, then
   `python scripts/training_preflight.py --print-command --num-envs 1 --max-iterations 1`.
   The helper never starts training. `--shape-smoke` is a CPU-only algorithm
   check; `--check-config` attempts a real config import and may report the
   required-backend block.

## Task and install contract

- The only registered training task covered here is `x1_dh_stand`; pass it
  explicitly because the generic parser's default task is not this task.
- The README's intended stack is Python 3.8, PyTorch 1.13.1 with CUDA 11.7,
  NumPy 1.23.x, Isaac Gym Preview 4, and `pip install -e .`. The package
  metadata also requests TensorBoard and several playback/export dependencies.
  Treat exact legacy versions as compatibility requirements, not as proof that
  they are installed.
- Install Isaac Gym Preview 4 separately according to its license/distribution
  instructions, install its Python package, verify an Isaac Gym example, and
  only then install this package. If that artifact is absent, stop at static
  inspection or the CPU algorithm smoke.
- The native command is `python humanoid/scripts/train.py --task=x1_dh_stand
  --run_name=<run_name> --headless` from the repository root. Isaac Gym's
  `gymutil` parser supplies simulator flags in addition to the custom flags;
  keep `--rl_device` and simulator device choices explicit on multi-device
  systems.

## Operating rules

- Treat `env.frame_stack=66`, `short_frame_stack=5`, and
  `c_frame_stack=3` as coupled invariants. The actor consumes 66 frames of 47
  features; the critic consumes 3 frames of 73 privileged features.
- Keep `env.num_single_obs=47`, `num_observations=3102`,
  `num_privileged_obs=219`, and `num_actions=12` aligned with the network and
  rollout storage. See the full feature accounting in [configuration](references/configuration.md).
- Raw commands are four values `(lin_vel_x, lin_vel_y, ang_vel_yaw, heading)`;
  this task uses `heading_command=False`, so the effective commanded triple is
  `(x, y, yaw)`. The five command-related observation values are gait sine,
  gait cosine, and the three scaled velocity commands—not five user commands.
- Use bounded command ranges and preserve the stand threshold. Do not invent a
  fifth action or bypass the policy's action clipping and PD torque limits.
- Keep domain randomization enabled unless an experiment explicitly studies a
  controlled ablation. Record changes to friction, pushes, mass/COM, gains,
  torque, joint friction/damping/armature, motor offsets, Coulomb friction, and
  action/DOF lag because they change the sim-to-real assumptions.
- Do not call `task_registry.make_env` merely to inspect a config on a machine
  without Isaac Gym: environment construction creates a PhysX simulation and
  loads the X1 asset. Prefer the bundled helper and static values first.
- Do not treat a successful CPU network/storage smoke as native training
  verification. Record backend status separately in any handoff.

## Checkpoints and handoff

The runner writes TensorBoard and checkpoint files under the project log root,
by default in `logs/x1_dh_stand/exported_data/<timestamp><run_name>/`.
Checkpoints are `model_<iteration>.pt`; the runner saves at iteration 0 and
then every `save_interval=100`, and saves one final checkpoint after the loop.
Each checkpoint contains `model_state_dict`, optimizer states, estimator
optimizer state, `iter`, and `infos`. `--resume --load_run <run> --checkpoint
<N>` selects a run/checkpoint. In the config object `load_run=-1` means latest,
but the source CLI declares `--load_run` as a string and can pass literal `-1`
as a directory name; omit that flag for configured latest behavior or pass an
exact run name. `--checkpoint=-1` is an integer sentinel for the latest model.
Resume loading intentionally omits optimizer state in the registry path, so
report that when comparing resumed runs.

After training, route only the resulting artifact to playback, export, or
sim2sim. Do not make this sub-skill perform interactive playback, export, or
MuJoCo behavior.

## Verification and hard cases

Run static frontmatter/link checks, the preflight `--help` and invariant output,
and `--shape-smoke` when Torch is available. A native train command is a
required-backend candidate and must be labeled blocked when Isaac Gym Preview 4
is unavailable. Proposed difficult usability cases for verification are:

1. A user requests `num_single_obs=48` or `frame_stack=5`: the agent must
   detect the 47/66/5 observation and CNN reshape contract, explain every
   dependent field, and refuse to launch until all dimensions are reconciled.
2. A user resumes with `--load_run -1 --checkpoint -1` after a run directory
   contains `model_0.pt`, sparse periodic checkpoints, and a stale `exported`
   directory: the agent must select the sorted latest model, distinguish the
   model's stored `iter` from its filename, and explain the optimizer-state
   omission before continuing.

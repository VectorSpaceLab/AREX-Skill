---
name: rl-training
description: "Routes Hydra and RSL-RL policy training, evaluation, checkpoint
  loading, task configuration, observation and action contracts, WeightPolicy
  bridging, and TensorBoard workflows for this quadruped MPC project."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RL training

Use this sub-skill when the task involves training or evaluating the learned
MPC-weight policy, selecting A1/Aliengo/Go1, loading or resuming a checkpoint,
checking observations/actions/rewards, or viewing RSL-RL TensorBoard logs.

## Read first

1. Read [workflows](references/workflows.md) for the public package/repository
   installation, Hydra overrides, and the train/test/resume/checkpoint
   decision.
2. Read [configuration](references/configuration.md) before changing task,
   device, environment count, or learning settings.
3. Read [API and bridge contracts](references/api-reference.md) before wiring a
   policy to an MPC runner or diagnosing tensor shape errors.
4. From this installed sub-skill directory, run the bundled safe
   command/config checker when planning a run:

   ```bash
   python scripts/validate_rl_config.py --task Aliengo --num-envs 1
   python scripts/run_training.py --help
   ```

   The installed-package launcher is a dry run unless `--run` is supplied.

5. Read [troubleshooting](references/troubleshooting.md) when an import,
   Hydra resolution, checkpoint, device, or logging step fails.

## Hard backend gate

RL environment construction, training, evaluation, and `WeightPolicy` import
require NVIDIA Isaac Gym Preview 4 in addition to the documented Python,
PyTorch/CUDA, and RSL-RL stack. The current inspection handoff proved
PyTorch 1.10/CUDA 11.3 on an A100, package imports, and `mpc_osqp`, but did not
prove Isaac Gym; `isaacgym` is unavailable. Treat all RL/simulation execution
as **blocked until the official SDK is installed and imported**. Do not
substitute a CPU import or a CUDA tensor smoke test for this gate. Use
[isaac-gym-simulation](../isaac-gym-simulation/SKILL.md) for SDK/API and
hardware diagnosis, and [mpc-control](../mpc-control/SKILL.md) for the
controller side of the bridge.

## Scope and routing

- **Training/evaluation:** Hydra overrides select `task`, `headless`,
  `num_envs`, `checkpoint`, `test`, devices, `seed`, and `max_iterations`.
  Use the bundled launcher only after the backend gate passes; public commands
  and fallback behavior are in [workflows](references/workflows.md).
- **Task/config contract:** valid task names, defaults, observation/reward
  layout, and PPO settings are in [configuration](references/configuration.md).
- **Policy API and bridge:** the 48-value observation and 12-value action
  contracts, policy architecture, checkpoint keys, and MPC weight mapping are
  in [api-reference](references/api-reference.md).
- **Low-level controller math/FSM:** do not duplicate it here; route to
  [mpc-control](../mpc-control/SKILL.md).
- **Isaac Gym lifecycle, assets, viewer, PhysX, and GPU pipeline:** route to
  [isaac-gym-simulation](../isaac-gym-simulation/SKILL.md).

## Safe operating rules

- Install the current project package through its public interface, then use
  the bundled `scripts/run_training.py` launcher. It resolves the installed
  training entry point and does not require opening a checkout-local script.
  Hydra uses `key=value` overrides, not an argparse option catalog.
- Choose a user-owned working directory and explicit run root for every
  experiment. Keep checkpoints under user-supplied paths; do not rely on a
  default run directory from a source checkout.
- Prefer an explicit absolute checkpoint file. A missing explicit file causes
  the source loader to try its configured latest-run fallback, which can select
  an unintended run or fail if no model exists. The bundled checker validates
  paths without importing or deserializing a checkpoint.
- Keep `num_obs=48` and `num_actions=12`. A checkpoint with incompatible
  actor/critic dimensions is not made safe by changing `num_envs`.
- Training uses the MPC bridge by default in the public training entry point:
  policy actions are transformed into 12 MPC parameters and the controller
  produces torques. This is not the same as direct joint-position control.
- Do not change observation ordering, action scaling, robot task, or policy
  hidden dimensions for an existing checkpoint without treating it as a new
  model and validating it from scratch.
- Training is long-running and evaluation loops for ten episode horizons; do
  not use either as a smoke test. Use the bundled checker and the
  setup/backend route first.

## Completion checklist

Before handing off a requested run, confirm:

- the task is exactly `A1`, `Aliengo`, or `Go1`;
- Isaac Gym is importable on the requested GPU, or the request is explicitly
  reported as blocked;
- `num_envs` is positive and fits GPU memory;
- an explicit user-supplied checkpoint exists and is structurally compatible
  when loading;
- `test=True` is used only for evaluation and `test=False` for training/resume;
- the user-owned run directory and TensorBoard log directory are unambiguous;
  and
- any MPC deployment request is cross-linked to the controller bridge route.

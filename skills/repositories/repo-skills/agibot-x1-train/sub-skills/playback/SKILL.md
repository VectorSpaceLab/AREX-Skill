---
name: playback
description: "Prepare, locate, and safely route interactive Isaac Gym playback
  of trained AgiBot X1 locomotion checkpoints, including viewer and Logitech
  F710 control diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# X1 Policy Playback

Use this route to inspect and then interactively run a **training checkpoint**
for the registered `x1_dh_stand` task in Isaac Gym. Do not use it to train,
export JIT/ONNX, or run MuJoCo sim2sim.

## Hard Backend Boundary

`humanoid/scripts/play.py` requires NVIDIA CUDA plus **Isaac Gym Preview 4**.
It is an interactive GPU/viewer workflow, not a CPU workflow. Preview 4 was
unavailable during skill construction, so native playback is
`BLOCKED_REQUIRED_BACKEND` and was not claimed as executed. A modern PyTorch
or CUDA installation alone does not prove compatibility.

Before playback, require all of the following:

- Python 3.8, the repository's documented PyTorch 1.13.1/CUDA 11.7 stack, and
  NumPy 1.23.x;
- Isaac Gym Preview 4 installed from its vendor archive and its own example
  passing on the intended GPU;
- this repository installed editable so `import humanoid` resolves;
- runtime imports `pygame`, `cv2`, `wandb`, and `tensorboard` available;
- an NVIDIA GPU, a working graphics/display session, and a full runner
  checkpoint under the expected log tree.

See [workflows.md](references/workflows.md#install-and-import-contract) for the
installation and import contract. Never substitute a fake simulator backend.

## Route By Intent

| Intent | Route |
|---|---|
| Select a trained run/checkpoint and open Isaac Gym viewer | Stay here |
| Diagnose axes, F710 directions, or policy input history | [joystick-and-observation.md](references/joystick-and-observation.md) |
| Diagnose imports, model lookup, CUDA, viewer, or shutdown | [troubleshooting.md](references/troubleshooting.md) |
| Produce or resume a checkpoint | Hand off to the `training` sub-skill |
| Turn a runner checkpoint into JIT or ONNX | Hand off to the `export` sub-skill after validating the checkpoint here |
| Run an exported policy in MuJoCo | Hand off to the `sim2sim` sub-skill; do not pass a runner checkpoint as an exported model |

## Safe Procedure

1. **Stay at repository root.** Confirm the package and robot resources are
   installed and the trained run is present. Playback reads a full runner
   checkpoint, not an exported actor file.
2. **Select explicitly.** The default experiment is `x1_dh_stand`. Use the run
   directory name with `--load_run`; use the integer suffix from
   `model_<iteration>.pt` with `--checkpoint`.
3. **Preflight without launching.** From this sub-skill directory, run:

   ```bash
   python scripts/playback_preflight.py \
     --repo-root /path/to/agibot_x1_train \
     --load-run '<date_time><run_name>' \
     --checkpoint 1000 \
     --require-joystick
   ```

   The helper performs only filesystem, module-spec, CUDA metadata, display,
   and joystick-device checks. It never imports Isaac Gym, deserializes the
   checkpoint, opens a viewer, starts `pygame`, or launches playback. Read its
   [CLI help](scripts/playback_preflight.py) with `--help`.
4. **Inspect the emitted command.** A normal interactive command is:

   ```bash
   python humanoid/scripts/play.py \
     --task=x1_dh_stand \
     --load_run='<date_time><run_name>' \
     --checkpoint=1000 \
     --num_envs=1 \
     --rl_device=cuda:0 \
     --sim_device=cuda:0
   ```

   Do not add `--headless` for viewer playback. Do not add `--resume`:
   `play.py` forces the runner's resume setting before policy creation.
5. **Center the controller before launch.** The implementation has no deadzone,
   no command clamping, and no implemented button-4 gate. Begin with one
   environment and small stick motion. Use the exact mapping in
   [joystick-and-observation.md](references/joystick-and-observation.md#logitech-f710-map).
6. **Operate the viewer.** `Esc` requests quit. `V` toggles synchronized drawing.
   The environment updates graphics from `env.step`; optional video rendering
   is disabled by the script constant `RENDER = False`.
7. **Record provenance.** Capture experiment, run directory, checkpoint number,
   task, devices, and any local code changes. Treat behavior as unverified if
   the backend, viewer, or controller checks were skipped.

## Flag Decisions That Matter

- `--task=x1_dh_stand` is the only registered X1 playback task in this graph.
- `--load_run=NAME` selects a directory below
  `logs/<experiment>/exported_data/`. `--run_name` does **not** select it.
- To choose the latest run, **omit** `--load_run`. Do not pass literal
  `--load_run=-1`: the parser stores it as a string while model discovery
  compares against integer `-1`, causing lookup of a directory literally named
  `-1`.
- `--checkpoint=-1` validly selects the latest model candidate. Omit it for the
  same configured default. A nonnegative `N` selects exactly `model_N.pt`.
- `--experiment_name=NAME` changes the log root used for loading. It must match
  where the run was trained.
- `--num_envs` is applied after the script's `min(..., 10)` override, so an
  explicit value can exceed 10. Use `1` initially and never assume the script
  will clamp the CLI value.
- `--run_name` only affects the newly constructed playback log/video name; it
  does not replace `--load_run`.
- `--headless` suppresses the viewer, conflicts with this interactive route,
  and still reaches an unconditional camera-setting call. Do not use it as a
  workaround for a broken display.

The complete project/custom argument table and exact discovery behavior are in
[workflows.md](references/workflows.md#playback-arguments).

## Playback Invariants

Reject or stop the run if any invariant fails:

- model path resolves to a readable, nonempty `model_<integer>.pt` file;
- checkpoint is a runner dictionary with a compatible `model_state_dict`, not
  a JIT/ONNX policy;
- policy input is `[num_envs, 3102]` = 66 history frames × 47 values;
- short policy history is 5 frames × 47 = 235 values;
- policy output is 12 actions in the configured X1 joint order;
- command channels are forward velocity, lateral velocity, and yaw velocity;
- viewer playback has a live display and graphics device;
- controller axes are centered and confirmed before commanding motion.

Use [joystick-and-observation.md](references/joystick-and-observation.md) for
input/action details and [troubleshooting.md](references/troubleshooting.md) for
fail-closed recovery.

## Bundled Runtime Material

- [workflows.md](references/workflows.md): install, CLI, run discovery, policy
  loading, playback lifecycle, and handoffs.
- [joystick-and-observation.md](references/joystick-and-observation.md): F710
  mapping, source/documentation discrepancy, observation history, and actions.
- [troubleshooting.md](references/troubleshooting.md): symptom-driven backend,
  checkpoint, viewer, joystick, and shutdown diagnosis.
- [playback_preflight.py](scripts/playback_preflight.py): safe parser and static
  preflight; it never starts interactive playback.

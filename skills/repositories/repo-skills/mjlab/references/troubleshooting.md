# Cross-cutting troubleshooting

## Import or install fails

1. Confirm the environment uses a supported Python version (`>=3.10,<3.14`).
2. Use the same dependency variant as the intended backend. CPU packages can
   inspect configs but do not validate CUDA training.
3. Run a package smoke check:

   ```bash
   uv run python path/to/mjlab_environment_smoke.py --json
   ```

4. If `mujoco`, `mujoco_warp`, `warp`, or `torch` import fails, solve the
   backend package issue before debugging mjlab code.

## CUDA or GPU problems

- Training is intended for Linux with NVIDIA GPUs.
- A visible GPU is not enough; the installed `torch` build must report CUDA and
  allocate a tiny tensor.
- `CUDA_VISIBLE_DEVICES` changes the physical GPUs visible to the process;
  mjlab's `--gpu-ids` values are interpreted relative to that visibility.
- To keep Warp away from GPUs entirely, hide devices before launch rather than
  relying only on a CLI CPU flag.
- Multi-GPU training uses data parallelism and increases total experience per
  iteration. Do not compare multi-GPU and single-GPU runs without accounting for
  total samples.

## CLI parsing surprises

- Tyro requires explicit boolean values: `--video True`, not `--video`.
- Use Python literal syntax for collections: `--gpu-ids "[0, 1]"`.
- CLI flags use hyphens even when Python fields use underscores.
- Use `uv run train <TASK> --help` or `uv run play <TASK> --help` for exact
  nested paths before constructing a long command.

## Rendering and viewers

- On Linux, mjlab defaults `MUJOCO_GL` to `egl` at import if unset.
- `play --viewer auto` chooses native if a display is present and Viser
  otherwise.
- Offscreen video and camera sensors depend on graphics backend availability.
- If a native viewer fails on a headless machine, try Viser or avoid opening an
  interactive viewer during automated checks.

## W&B and networked artifacts

- W&B run paths usually take the form `entity/project/run_id`.
- Tracking tasks often need a local `--motion-file` or a W&B motions registry
  artifact.
- `demo` downloads pretrained assets and should not be treated as a no-network
  smoke test.
- Cloud launchers, sweeps, and benchmark jobs can create cost or mutate remote
  state; ask before running them.

## NaNs and unstable simulation

- Use `--enable-nan-guard True` on training commands to capture instability.
- Inspect saved dumps with `viz-nan`.
- A `nan_detection` termination can keep a run from crashing, but it should not
  replace fixing reward/action/contact instability.
- If a derived state appears stale after writing simulation state, call or wait
  for the appropriate `forward()`/manager lifecycle point before reading it.

## Where to route deeper issues

- Manager lifecycle and term dictionaries: environment-configuration.
- Entity/MJCF/variant/export issues: scene-simulation-assets.
- Actions, actuators, rewards, commands: mdp-components.
- Sensors, terrains, and domain randomization: perception-terrain-randomization.
- CLI, training, playback, checkpoints, W&B, motion data: training-evaluation-cli.

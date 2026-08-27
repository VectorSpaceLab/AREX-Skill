# RoboVerse Cross-Cutting Troubleshooting

## Installation and import

- `No module named metasim`: install the RoboVerse package with the chosen
  backend extra; MetaSim is a required upstream dependency and is not bundled
  as a second local package.
- `No module named roboverse_pack` after install: check that the distribution
  installed into the active environment, run `python -m pip check`, and import
  the package before starting a script. Do not rely on the checkout being the
  current directory.
- Editable install resolves an unexpected MetaSim revision: record the public
  MetaSim revision/version and use a compatible pinned checkout or package for
  reproducible work. Do not copy MetaSim internals into RoboVerse skill content.
- An optional package raises `ImportError`: identify the owning extra (`learn`,
  `vla`, `mujoco`, or a simulator/integration extra), install only that variant,
  and rerun its minimal import. Preserve a CPU fallback only when behavior is
  actually equivalent.

## Config, data, and API boundaries

- Unknown task/robot/backend values must produce a clear supported-values error.
  Do not turn unsupported paths into quiet no-ops.
- Validate task registration, config fields, asset paths, body/joint/site names,
  data keys, shapes, dtypes, units, and episode boundaries before rendering or
  training.
- If a change requires a new simulator handler, registry behavior, or config
  type, route it to MetaSim. If it changes a task, robot, scene, reward,
  observation, asset adapter, or learning workflow, keep it in RoboVerse.

## Backend and runtime

- A CPU import proves only importability. It does not prove MuJoCo rendering,
  Isaac/Genesis/Newton/SAPIEN/PyBullet/MJX support, VLA inference, or native
  benchmark integrations.
- GPU errors should name torch build, CUDA/driver availability, device, and
  memory. Display/EGL failures should be separated from Python assertions.
- For a simulator failure, reduce to one headless environment, reset, and one
  bounded step; add cameras, rendering, multiple envs, policy, and external
  assets incrementally.

## Parity and reporting

Run the task end-to-end before numerical comparison. Align reset state, seed,
assets, action scale/order, timestep, control frequency, observation keys,
reward terms, and termination. Report backend names and max/mean deltas. Do not
claim closed-loop transfer or visual parity from observation agreement alone.

## Safety stops

Stop and ask for an explicit environment/data/credential/hardware decision when
a workflow requires real-robot control, external credentials, destructive asset
writes, large downloads, long training, a display/GPU not prepared for the
route, or an unavailable required backend. Record the limitation rather than
calling it a normal test failure.

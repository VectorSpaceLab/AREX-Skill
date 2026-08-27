# SMARTS cross-cutting troubleshooting

Read this reference when a failure is not owned by one workflow or when the
first diagnostic must distinguish package, optional dependency, path, process,
and lifecycle errors.

## Install and import

- **`ModuleNotFoundError: smarts` or `scl: command not found`:** use the same
  interpreter for installation and execution (`python -m pip install ...`),
  confirm `python -m pip show smarts`, and run
  `scripts/check_smarts_install.py`. Do not rely on a shell activation from a
  different environment.
- **Editable/local install appears to import the wrong code:** run from a
  neutral working directory, inspect `smarts.__file__`, and compare the
  installed distribution version with the intended checkout or release. Do
  not publish a local checkout path in a reusable workflow.
- **Dependency resolver or binary import failure:** install only the selected
  extra in an isolated environment. SMARTS's broad pinned requirements file
  is not a universal requirement for every workflow; compiled packages such as
  PyBullet, SciPy, Panda3D, and spatial-index libraries must match Python and
  platform.
- **`pip check` reports conflicts:** stop before simulation, record the exact
  conflicting distributions, and repair a private environment or create a
  clean one. Do not silently upgrade an existing user environment.

## Optional capabilities

- **Camera/grid/RGB/occlusion failure:** core CPU simulation does not prove
  rendering. Install the `camera-obs` extra, verify Panda3D and glTF support,
  and provide X11/Xvfb or another supported offscreen display. Reduce image
  dimensions while diagnosing.
- **Envision connection or replay failure:** verify the Envision extra, a free
  and reachable websocket endpoint, and a directory containing valid JSONL
  records. A client import is not a running server; use the visualization route
  for record format and the CLI route for command spelling.
- **Ray/RLlib/Torch/TensorFlow failure:** these are optional stacks with their
  own compatibility matrix. Probe imports before loading `RLlibHiWayEnv`; a
  core SMARTS import does not verify training or inference.
- **SUMO/TraCI, ROS, Waymo, Argoverse, or Visdom failure:** check the external
  executable, Python package, dataset format, service, and port separately.
  Preserve the failure as an optional integration limit instead of changing
  map engines or data formats without consent.

## Data, path, and configuration failures

- **Scenario not found or missing generated files:** pass an explicit scenario
  directory and validate source/build layout. Regenerate after changing
  `scenario.py` or a map; do not hand-edit generated XML, pickle, database, or
  mesh artifacts.
- **Map/traffic engine mismatch:** use SUMO traffic only with a SUMO-compatible
  network. Select the SMARTS engine for supported non-SUMO maps and verify the
  optional map parser before claiming the route works.
- **Unexpected agents or empty observations:** agents can start/end at
  different times. Step only active ids and treat an empty dictionary as a
  possible intermediate state; inspect `__all__` termination flags.
- **Reproducibility mismatch:** pass an explicit seed at the first reset and
  keep policy actions deterministic. Select sequential scenario ordering when
  shuffled iteration would change the experiment.
- **Environment setting appears ignored:** inspect SMARTS configuration
  precedence (environment variables, INI file, defaults), spelling, and the
  process that actually launches SMARTS. Avoid copying machine-specific INI
  paths into a reusable instruction.

## CLI and process failures

- Run `scl --help` and the relevant subcommand help before a full command.
  `--clean`, `--auto-install`, scenario generation, zoo installation, server
  startup, and benchmark commands may mutate files, install code, or spawn
  processes; use disposable paths and explicit approval.
- **Port conflict:** identify the owning process and choose an explicit free
  port. Do not kill unknown services. SUMO central mode requires the same host,
  port, and serve-mode settings on the allocator and clients; Envision defaults
  to a different service/port.
- **Child experiment fails under `scl run`:** check the script's own argument
  parser and scenario paths. `scl run` forwards remaining arguments; it does
  not repair the child program's imports, policy, or environment.

## Lifecycle cleanup

Always close `HiWayEnvV1`, parallel workers, Envision clients, and any service
that the user intentionally started. On exceptions, preserve the original
traceback or failure stage, then inspect lingering ports/processes before a
retry. Do not treat a successful `close()` as proof that the preceding episode
or optional backend was valid.

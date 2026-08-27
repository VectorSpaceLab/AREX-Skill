# Sensors and visualization troubleshooting

## Install and import

- **`ModuleNotFoundError: panda3d` or `gltf`:** the CPU package is usable, but
  camera observations are not. Install the project's camera extra in the
  active environment, then rerun `check_rendering.py`; do not silently replace
  a missing renderer with a claimed pass.
- **Envision import fails for `tornado`, `websocket`, or `ijson`:** install the
  Envision extra in the environment approved for the project. Core CPU sensors
  do not require it.
- **Visdom is missing:** it is an optional, unverified integration. Keep it
  disabled while checking observations or Envision JSONL.
- **Wrong interpreter:** run `python -m pip show smarts` and the helper with
  the same `python`; inspect package version and `pip check`. An editable
  checkout import is not a portable runtime dependency.

## Display, Panda3D, and camera failures

- **Panda3D imports but camera creation fails:** distinguish import from a
  usable graphics pipe. Check `DISPLAY`, run under a project-approved Xvfb,
  and try the bounded `--probe-offscreen` helper. Do not run full renderer
  tests until this probe and a small map-backed case are available.
- **`No display`, `Could not open display`, or black/empty images:** verify the
  X11 environment, software/OpenGL backend, map build artifacts, and camera
  dimensions. A CPU-only environment cannot produce a camera image.
- **`occlusion_map` assertion:** enable `occupancy_grid_map` and use exactly
  the same OGM width and height. Surface noise is another shader pass; disable
  it while isolating a basic path.
- **custom render assertion or shader error:** ensure shader file readability,
  unique dependency variable names, valid built-in camera names, and that each
  referenced built-in camera is attached. Add one pass/dependency at a time.
- **steps become very slow or memory grows:** lower width/height, remove image
  sensors not consumed by the policy, reduce lidar range/rays, and avoid
  rendering plus Envision recording during a timing diagnosis.

## Data and configuration

- **Optional observation is `None`:** inspect the interface used to build the
  agent, not only the policy. Boolean false disables a field; `True` resolves
  defaults. Confirm the agent id exists in the observation dictionary.
- **Unexpected waypoint count or empty road map:** path lengths depend on map,
  route, lane spacing, and current pose. Assert non-empty structure only when
  the scenario guarantees a lane; handle an empty road-waypoint mapping.
- **Neighbor list is unexpectedly large:** `radius=None` is unlimited. Set a
  finite radius and do not assume ego is included.
- **Lidar alignment failure:** check all points/hits/rays together and treat
  infinite points as misses. Custom `SensorParams` changes ray count.
- **signal tuple empty:** the current lane may be absent or no signal is inside
  the configured route/lookahead. An empty tuple is valid.
- **recording files are absent:** ensure `output_dir` is writable, the owning
  client/environment is torn down, and the run actually produced a state. The
  writer creates a timestamped subdirectory and client-named JSONL file.

## API and CLI misuse

- **Passing a flat NumPy action/observation assumption:** SMARTS observations
  are named records with nested lists/tuples and optional render records.
  Inspect the per-agent spaces and fields before writing a policy adapter.
- **Using deprecated aliases:** prefer `top_down_rgb`, `occupancy_grid_map`,
  `lidar_point_cloud`, `waypoint_paths`, and
  `neighborhood_vehicle_states`.
- **Wrong replay arguments:** the Python primitive takes a JSONL file, endpoint,
  and positive fixed timestep. A recording directory must first be expanded to
  its JSONL files. Delegate exact `scl` spelling to `cli-integrations`.
- **Trying to clean/build as a sensor check:** scenario generation and CLI
  cleanup belong to their sibling routes and may mutate files. The helpers in
  this route are read-only.

## Envision, replay, and service failures

- **No server at localhost:8081:** a non-headless client logs a warning and may
  retry, making runs slow. Use `envision=None` or headless mode for CPU tests;
  do not start a long-lived service from a diagnostic helper.
- **JSONL inspection succeeds but browser is blank:** local file syntax does
  not prove server protocol, map assets, browser connection, or frontend
  availability. Check the server endpoint and scenario map resources.
- **Replay is slow:** `read_and_send` sleeps for the configured timestep and
  sends every line. Use a bounded test file and positive timestep; do not
  mistake the replay delay for simulation performance.
- **Records are malformed or truncated:** stop the producer cleanly, inspect
  the first and last lines, and use a new output directory. Do not edit a
  recording in place during diagnosis.
- **Server history is sparse:** Envision has a bounded in-memory capacity and
  can discard middle frames when large streams exceed it. Reduce image/actor
  payloads before increasing capacity.

## Verification language

Report three statuses separately: `cpu import/observation`, `software
rendering`, and `Envision service`. A passed CPU check cannot upgrade the other
two. The prepared baseline verified Panda3D and renderer imports under Xvfb,
but did not verify full renderer tests, a live Envision server, or Visdom.

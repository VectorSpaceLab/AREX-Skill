# Cross-cutting troubleshooting

Read this when a failure crosses launcher, package, ROS, and asset boundaries.

## Isaac package or import failure

- **Symptom:** `ModuleNotFoundError: isaaclab`, an Isaac extension import error,
  or a launcher stops before `all imports complete`.
- **Likely cause:** wrong Isaac Sim/IsaacLab pair, missing IsaacLab package,
  Python version mismatch, or a partial installation.
- **Recovery:** run the bundled prerequisite checker; compare the installation
  against the documented version matrix; use a private Python 3.11 environment
  for Isaac Sim 5/Jazzy; do not substitute a CPU-only package or current
  IsaacLab release without compatibility evidence.
- **Stop condition:** the repository-required IsaacLab 0.54.3 is unavailable.
  Record the route as blocked rather than claiming a successful simulation.

## ROS ABI and typesupport failure

- **Symptom:** `rclpy` shared-library errors, duplicate `rcl_interfaces`
  assertions, or `rosidl_typesupport_c` import failures.
- **Likely cause:** host ROS Python libraries were sourced into Isaac's Python,
  or a legacy custom interface is being expected from the bundled runtime.
- **Recovery:** use the version-matched launcher; avoid sourcing `/opt/ros/*`
  for the modern path; inspect the telemetry and legacy-interface references.
  Build custom interfaces only in a separately matched ROS workspace.

## Checkpoint or asset failure

- **Symptom:** checkpoint lookup fails, G1 USD cannot be opened, or custom
  environment loading falls back/fails.
- **Likely cause:** external policy checkpoints, local G1 asset path, or
  downloaded custom USDs are absent or mismatched.
- **Recovery:** start with Go2 flat terrain and a known checkpoint; confirm the
  G1 asset is available to the selected runtime; treat custom environment and
  cloud asset downloads as explicit prerequisites. Do not fabricate a checkpoint
  or silently run a different robot.

## Headless/render/capture failure

- **Symptom:** display/window errors, camera extension errors, shader-cache
  stalls, or capture produces no PNGs.
- **Likely cause:** missing `--headless`/camera flags, first-run shader/cache
  compilation, unsupported Isaac camera API, or unavailable remote assets.
- **Recovery:** prove a minimal headless flat launch first; add
  `--enable_cameras` and `--capture` only afterward; allow bounded first-run
  cache work; record camera/LiDAR as optional if the extension is unavailable.

## ROS graph or DDS failure

- **Symptom:** expected `robot0/*` or `/real_dog/*` topics are absent.
- **Likely cause:** the sim has not reached its main loop, topic namespace/QoS
  differs, RMW/domain/interface selection is inconsistent, or the twin bridge
  is not running on its two intended sides.
- **Recovery:** inspect topic names/types before changing code; keep
  `ROS_DOMAIN_ID` and Fast DDS settings aligned for shared standard messages;
  use the digital-twin route for CycloneDDS-to-FastDDS diagnosis.

## Safety boundary

Never respond to an import or topic failure by sending robot commands, changing
network interfaces, disabling safety systems, or copying private credentials.

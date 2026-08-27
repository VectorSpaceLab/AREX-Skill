# Troubleshooting

## Install and import

- **`ModuleNotFoundError: alpasim_grpc`**: install the gRPC package or enable
  the workspace gRPC extra, then verify the active interpreter with
  `python -c 'import sys; print(sys.executable)'`. Do not fix it by adding a
  checkout directory to `PYTHONPATH`.
- **Version lookup fails during `import alpasim_grpc`**: the package metadata
  is not installed in the active environment. Repair the installation and
  check the package version; generated files alone are not a complete install.
- **`grpc_tools`/`pkg_resources` errors**: install the package's declared build
  dependencies and keep the supported `setuptools` upper bound. Do not mix
  generated files from another protobuf or grpcio-tools version without a
  compatibility check.
- **Generated import fails**: regenerate all imported schemas together and
  check that `alpasim_grpc.v0` is on the interpreter's package path.

## Optional dependencies and backends

- **`alpasim-info` lists fewer plugins than expected**: inspect the entry-point
  group first. Registry loading logs import failures and skips failed optional
  plugins; install the plugin's declared extras and backend, then retry.
- **The model registry hangs or times out**: optional model imports may probe
  large frameworks or assets. Use metadata-only entry-point inspection, then
  route model/runtime diagnosis to `drivers-and-plugins`.
- **A map test fails on Qt, parquet, trajdata, or artifact imports**: this is
  an optional map-tool dependency/backend gap. Use a headless plotting backend
  and a tiny fixture, or route the analysis to `evaluation-and-logs`; do not
  claim the gRPC package is broken.

## Data and configuration

- **`UNIMPLEMENTED`/`UNAVAILABLE` from a stub**: distinguish a generated stub
  mismatch from a missing or incompatible endpoint. Confirm the service name,
  host/port, server version, and session lifecycle; a stub import does not
  start a server.
- **Invalid scene, empty camera list, or missing model**: the request may be
  structurally valid but require scene cache, calibration, model assets, or a
  deployment config. Route acquisition and Hydra setup to `simulation-wizard`.
- **Coordinate-looking output is wrong**: inspect active transform direction,
  frame endpoints, and estimated/noised versus ground-truth data. Do not
  repair signs or inverses by trial and error.

## CLI and API misuse

- **`RenderRequest` cannot be imported**: use the generated name
  `sensorsim_pb2.RGBRenderRequest` (or the matching LiDAR/aggregated request).
- **A request serializes but the RPC rejects it**: check required semantic
  fields, timestamps, session UUID, camera calibration, and coordinate frames;
  protobuf construction only checks types and field names.
- **A plugin name is “not found”**: use the exact entry-point name and group,
  call `get_names()`, and confirm the providing distribution is installed.
  Do not add a second compatibility alias without a current contract.
- **A generated module has stale methods**: compare the proto declaration to
  the descriptor and generated stub after recompilation. Remove stale output
  only with the compiler's explicit clean option, then regenerate and review
  the diff.

## Workflow failures

- **Proto compilation deletes or changes unexpected files**: stop, restore the
  disposable output, and rerun the bundled compiler with explicit roots. Its
  default mode is non-destructive; review `--clean` use before enabling it.
- **A schema edit compiles but native tests fail**: treat this as a contract or
  caller regression, not a compiler success. Review field numbers, imported
  descriptors, endpoint method names, and logging/replay consumers.
- **Slurm/telemetry check starts external infrastructure**: stop the operation
  and classify it as an unsafe boundary. Use help output or the fixture-based
  unit test instead; ask the simulation owner for an approved deployment run.
- **Pre-commit changes generated code or unrelated files**: inspect the diff,
  keep only intended changes, and rerun the focused checks. Do not hide lint
  failures with broad formatting or compatibility shims.

When reporting an unresolved issue, include the package version, Python
version, exact generated module/service, command (without credentials),
backend/asset status, and the last safe check that passed.

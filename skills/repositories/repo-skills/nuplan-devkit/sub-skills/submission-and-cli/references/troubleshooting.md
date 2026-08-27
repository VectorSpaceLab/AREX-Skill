# Troubleshooting

Use the smallest safe diagnostic first. Preserve the original error and label
the failure as **help/CLI**, **data**, **Hydra/planner**, **protocol/runtime**,
**container**, or **remote/EvalAI**. Never modify protected protocol or server
files as a first response.

## Help unexpectedly touches data

**Symptom:** `nuplan_cli --help` or `nuplan_cli db --help` fails because a DB,
map, or sensor file is absent.

**Diagnosis:** Help should only construct Typer commands. A query command with
no explicit DB path can enter `_ensure_file_downloaded` and the package data
helper. Check that the user did not invoke `db info`, `duration`,
`log-duration`, `log-vehicle`, or `scenarios` when they wanted syntax only.

**Recovery:** rerun the exact `--help` command. For a query, first test the
explicit local path with a shell `-f` guard, then pass that path as `DB_VERSION`
and the appropriate `--data-root`. Do not download data in a help-only path.

## DB file not found or query fails

**Symptom:** a DB subcommand reports a missing path, download failure, SQLite
error, missing table, or `None`/integer conversion failure.

**Diagnosis:** confirm the path is a file, not a directory; inspect the data
root and split/version layout; then distinguish a valid empty result from a
schema mismatch. `duration` needs `lidar_pc.timestamp`; log duration needs
`log`, `scene`, and `lidar_pc`; vehicles need `log.vehicle_name`; scenarios
need `scenario_tag.type`.

**Recovery:** use `db info` on the same explicit file. If it cannot describe
the file, stop and repair data selection or schema compatibility. Do not point
the command at a map directory or sensor blob. The CLI query layer is not a
migration tool and does not validate arbitrary SQL identifiers.

## `nuplan_cli` command or option mismatch

**Symptom:** “No such command,” an unexpected option error, or a positional DB
path is rejected.

**Diagnosis:** the supported surface is `nuplan_cli db <command>`, not a flat
`nuplan_cli info`. `DB_VERSION` is positional; `--data-root` is an option.
Confirm the installed package rather than assuming a newer nuPlan release.

**Recovery:** run the relevant `--help`, copy the displayed spelling
(`log-duration`, `log-vehicle`, `scenarios`), and avoid adding options from
another release. The root help currently exposes only the `db` group.

## Hydra cannot compose the submission planner

**Symptoms:** missing mandatory `planner` or `output_dir`, unknown config,
`_target_` import failure, constructor argument error, or an unexpected
working-directory error.

**Diagnosis:** the launcher composes `default_submission_planner`, requires a
planner override, and resolves its config path from the package/default or
`NUPLAN_HYDRA_CONFIG_PATH`. Verify the config is included in the image, the
`_target_` is importable, and its keys match the planner constructor. Check
that `entrypoint_submission.sh` selects the intended config and does not point
at a host-only path.

**Recovery:** start from a minimal config with a fully qualified target and
explicit `output_dir`, then run a local config/help smoke test. Use
`planner=simple_planner` only as a wiring baseline, not as evidence that a
custom planner works. Do not edit `SubmissionPlanner` or generated protocol
files.

## Server exits before listening

**Symptoms:** missing-port runtime error, map DB exception, import error, or
container exits immediately.

**Diagnosis:** check `SUBMISSION_CONTAINER_PORT`, `NUPLAN_DATA_ROOT`,
`NUPLAN_MAP_VERSION`, and the expected maps directory. The server binds
`[::]:<port>` and initializes its map manager before serving. A missing map
root can fail before the first RPC. Check image logs and the entrypoint
command; the image must run the submission launcher.

**Recovery:** set a valid positive port and make the maps available at the
container path expected by the image. Keep the map mount read-only where
possible. Verify dependency installation and module inclusion. Do not change
bind addresses, gRPC service names, or container startup code to mask a data
failure.

## `InitializePlanner` fails

**Symptoms:** RPC unavailable/deadline, map lookup error, assertion that the
configuration builds more than one planner, or planner initialization error.

**Diagnosis:** the remote client defaults to localhost, retries initialization
for up to five seconds, and sends route roadblock IDs, mission goal, and map
name. The server expects exactly one planner and initializes all map layers.
Confirm the port is published consistently and the map name exists in the
mounted map DB. Confirm the planner accepts `PlannerInitialization` and does
not require a scenario.

**Recovery:** test port reachability only in the local composition, inspect
server logs, and use a minimal deterministic planner config. If the map is
missing, fix the map root/version. If planner construction fails, fix its
config or dependency. Never alter the `.proto` or generated gRPC stubs.

## `ComputeTrajectory` fails or times out

**Symptoms:** “Planner has not been initialized,” gRPC deadline exceeded,
serialization errors, empty response, or a planner exception.

**Diagnosis:** `ComputeTrajectory` is invalid until `InitializePlanner` has
completed. The client sends pickled history bytes, then only the newest state
and observation after the first call; the server maintains a rolling history.
The default compute timeout is one second. Inspect whether the planner is
re-entrant/stateful as expected, whether history elements match the selected
observation type, and whether traffic-light data is optional/empty rather
than malformed.

**Recovery:** initialize exactly once per server lifecycle, run a minimal local
request, and profile model loading outside the per-iteration call. Keep
computation below the one-second budget. Fix pickling/importable class paths in
the planner package rather than changing converters or protocol fields.

## Trajectory rejected by validation or challenge

**Symptoms:** a planner returns an empty/too-short trajectory, interpolation
fails, timestamps go backward or repeat, or the challenge marks output invalid.

**Diagnosis:** inspect the returned sampled states. Every point needs global
rear-axle x/y, heading, and time in microseconds. The horizon must reach at
least 8 seconds and include at least two points. Timestamps must be finite and
strictly increasing; do not mistake a count of points for a time horizon.
Check that the first future point is not accidentally earlier than the current
simulation iteration.

**Recovery:** reject the trajectory in the planner before serialization; fix
sampling period/count and timestamp units. Use the bundled checker with a
manifest containing representative timestamps. A static pass does not prove
state values are physically valid, so also exercise the planner in simulation.
Do not relax the minimum by editing a validator or `.proto`.

## Protected-file drift

**Symptoms:** a review or remote run reports protocol incompatibility even
though a local client/server pair works.

**Diagnosis:** compare the submission against the base package for the five
protected paths: protocol source, both generated Python files, submission
container, and submission server. Local client/server tests can pass together
with a mutually changed protocol, so they are not sufficient.

**Recovery:** restore the protected files from the exact base package, remove
any generated descriptor edits, and keep changes in the planner/config,
requirements, assets, or marked entrypoint selection. Run the static checker;
it rejects protected entries listed in `changed_files`.

## Container build or Compose failure

**Symptoms:** build cannot resolve dependencies, target/config is absent, GPU
runtime is unavailable, bind mount is empty, or Compose cannot start the
simulation.

**Diagnosis:** the submission Dockerfile uses a CUDA runtime and Conda/Python
3.9-era dependency set. Compose uses host networking, GPU reservation, and
host-root mounts. Check build-context inclusion, dependency compatibility,
image tag, environment variables, map/data permissions, and Docker/NVIDIA
runtime support separately.

**Recovery:** first run a dependency/config-only check without claiming a full
submission test. Then build with the documented Dockerfile and use a tiny
local scenario if all required data and GPU tooling are available. Treat
Docker, CUDA, full dataset, and S3 paths as optional/unverified unless they
were actually run. Do not add network downloads or credentials to the image's
serve path.

## Leaderboard/result formatting failure

**Symptoms:** leaderboard writer cannot read metadata, cannot find challenge
parquet columns, or EvalAI rejects a status payload.

**Diagnosis:** the writer requires `submission_metadata.json`; stdout/stderr
logs are optional. Successful formatting expects one result table for each of
`open_loop_boxes`, `closed_loop_nonreactive_agents`, and
`closed_loop_reactive_agents`, each with a `scenario == final_score` row and
its challenge-specific metric columns. Network update additionally requires
challenge and personal auth environment variables.

**Recovery:** inspect local metadata and parquet schema without calling the
network interface. For a failed simulation, use the failed-status path and
include logs. Never put auth tokens in a manifest or ask the safe checker to
upload. Confirm phase/submission identifiers in the current remote UI before
any external update.

## Report unresolved limits

If no dataset or map is present, say “data unavailable” rather than “protocol
broken.” If Docker, CUDA, EvalAI, S3, or full challenge execution was not run,
record it as unverified. The native tests cover CLI mocks, submission Hydra
wiring, protocol conversion, container helpers, and leaderboard formatting;
they do not prove remote organizer compatibility or a complete challenge run.

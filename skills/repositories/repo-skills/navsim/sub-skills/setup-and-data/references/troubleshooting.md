# Setup and data troubleshooting

## Install and import

**`ModuleNotFoundError: nuplan` or `navsim.common.dataclasses` fails at
import.** NAVSIM imports nuPlan and map/geometry dependencies transitively.
Activate the intended environment, install the declared requirements, and run
`python -m pip check`. Verify `python -c "import nuplan; import navsim"` before
blaming data paths. Do not work around this by shadowing `nuplan` with a stub:
Scene and map contracts need the real compatible dependency.

**Torch/torchvision or NumPy ABI errors.** Compare the active versions with the
NAVSIM 2.0.0 baseline, reinstall the pair from one compatible channel, and
rerun the three import probes. A CUDA availability warning is acceptable for
metadata-only work but blocks a CUDA-required learned agent. Do not silently
upgrade the pinned Torch/NumPy pair during a reproduction.

**Optional dependency errors.** Notebook, dashboard, rendering, geospatial,
Ray, and browser-export packages are not needed for the no-sensor workspace
check. Install the package required by the requested route and re-run its
import probe. Do not mark a missing optional visualization dependency as a
missing dataset; conversely, missing `nuplan`/map dependencies is blocking for
Scene construction.

## Environment and paths

**Validator reports a missing variable.** Export all five required variables:
`NUPLAN_MAP_VERSION`, `NUPLAN_MAPS_ROOT`, `NAVSIM_EXP_ROOT`,
`NAVSIM_DEVKIT_ROOT`, and `OPENSCENE_DATA_ROOT`. Use absolute paths and avoid
trailing whitespace. `NUPLAN_MAP_VERSION` should be `nuplan-maps-v1.0` for this
release.

**Map API says the map name/version is invalid or cannot open a map.** Check
that `NUPLAN_MAPS_ROOT` points to the extracted map database itself, not its
parent download directory, and that the map version is compatible. A maps
folder is separate from `OPENSCENE_DATA_ROOT`; setting one to the other can
make both metadata and map lookups fail.

**Logs are found but sensor files are missing.** Metadata paths are relative
to the matching original or synthetic sensor root. Check the selected
`data_split` and pair `navsim_logs/<split>` with
`sensor_blobs/<split>`. For a two-stage view, separately check the matching
synthetic pickle and sensor directories. Do not “fix” the error by pointing a
warmup or private run at the navhard bundle.

**Warmup selected with a missing synthetic scene directory.** The warmup
filter includes synthetic scenes. Provide the warmup bundle's
`synthetic_scene_pickles` (and paired sensor root), or stop with a clear setup
error. Do not set `include_synthetic_scenes=False` merely to make the loader
start; that changes the experiment and invalidates stage-two results.

**`NAVSIM_EXP_ROOT/metric_cache` missing.** This is expected for initial setup
and no-sensor checks. Evaluation routes may require a cache. Create/populate it
only through an explicitly reviewed evaluation workflow, then confirm its
scene tokens and map/data version match the selected split.

## Split and configuration validation

**A filtered split returns zero scenes.** Confirm the underlying data split:
`navtrain -> trainval`, `navtest/navhard/warmup -> test`, and private challenge
-> `private_test_hard`. Check `has_route`, log names, tokens, history/future
counts, and `frame_interval`; a filter can legitimately remove short or
route-less frames. Do not change the filter to hide missing data.

**`include_synthetic_scenes=True` assertion.** `SceneLoader` requires a
non-null synthetic scene path when that flag is enabled. Check the config's
explicit synthetic path overrides and the matching bundle. The generic
navhard-oriented default must not be assumed for warmup/private.

**Hydra interpolation is unresolved.** The environment variable is read when
configuration is composed. Export variables in the same shell that launches
the runner, quote values, and check the rendered values before a data run.
Avoid replacing `${oc.env:...}` with a hard-coded machine path in a shared
configuration.

**Competition policy violation.** Never train on the test, filtered test,
two-stage warmup, or private challenge views. These are evaluation/submission
assets. If a training configuration accidentally selects one, stop and fix
its split before reading the data.

## CLI and API misuse

**`SceneLoader` token assertion.** Use `loader.tokens` or one of the stage
properties and pass a scene token, not a log filename or filesystem path.
`get_scene_from_token` returns privileged future/map/annotation content;
`get_agent_input_from_token` is the correct boundary for an agent.

**History index or missing sensor.** Sensor list indices are zero-based history
iterations. A list such as `[0, 3]` loads only those history frames; it does
not mean camera IDs. Keep each enabled index within the configured history
window and make sure the sensor root contains all referenced blobs.

**Trajectory length/coordinate mismatch.** History and future trajectories
are local `(x, y, heading)` poses at 0.5-second intervals. Do not pass global
poses to an agent that expects `AgentInput`, and do not request more future
frames than the filter loaded. Scene contains privilege; AgentInput does not.

**Running a destructive helper as a health check.** Download helpers perform
network, extraction, and archive deletion. They are reference-only. Use
`validate_workspace.py`, `md5sum -c` on an already present archive, and small
import/API checks instead.

## Workflow-specific failures

- **Training starts but workers fail to read data:** validate the parent process
  environment, worker-visible absolute paths, complete trainval logs, and the
  selected navtrain sensor subset. Start with `build_no_sensors()` to separate
  metadata/filter problems from image/LiDAR I/O.
- **Metric caching fails in map preprocessing:** check maps and map version,
  then verify original logs and route-bearing scenes. A cache path is an
  experiment output, not a replacement for raw data.
- **Two-stage evaluation has only stage one:** check synthetic scene pickles,
  synthetic sensors, explicit stage-two token/mapping config, and the original
  final-frame tokens. A nonempty original test root alone is insufficient.
- **Warmup result differs from local expectation:** ensure the warmup split and
  warmup synthetic assets are selected, not navhard; compare sensor history
  selection and stage-two tokens before comparing scores.
- **Private submission data is unavailable:** stop at metadata/config
  validation. Do not fabricate private frames or attempt an upload from this
  route.

When reporting a failure, include the selected split, the validator output,
which root is missing, and whether the failing operation was import, metadata
filtering, map construction, original sensor loading, synthetic loading, or
cache/evaluation. Never include private absolute paths in a shared report.

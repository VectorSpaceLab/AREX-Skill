# Data-preparation workflows and CLI semantics

## Preconditions

Run commands from a project environment that contains the Diffusion Planner
package and nuPlan-devkit. The verified inspection environment had
`diffusion_planner` 1.0.0, `nuplan-devkit` 1.2.2, Python 3.9-compatible
packages, PyTorch 2.0.0+cu118, NumPy 1.23.4, Shapely 2.0.7, GeoPandas 1.0.1,
and Rasterio 1.3.10. These versions establish the observed API facts; they do
not make an external nuPlan dataset available.

Before any real run, validate:

```bash
python -c 'import diffusion_planner, nuplan; print("imports ok")'
python scripts/run_preprocessing.py --help
python scripts/validate_preprocessed_data.py --help
```

Use absolute paths for data, maps, output, and the normalization file. Check
that the data and map roots are readable directories, the output directory is
writable, and the map release matches the DB release. The observed builder is
constructed with map version `nuplan-maps-v1.0`.

## Preprocessing CLI

The bundled path-explicit adapter has this shape:

```bash
python scripts/run_preprocessing.py \
  --data-path /abs/path/to/nuplan/trainval \
  --map-path /abs/path/to/nuplan/maps \
  --save-path /abs/path/to/processed \
  --log-names /abs/path/to/log-names.json \
  --manifest-output /abs/path/to/processed/diffusion_planner_training.json \
  --scenarios-per-type ... \
  --total-scenarios ... \
  --shuffle-scenarios ... \
  --agent-num 32 --static-objects-num 5 \
  --lane-num 70 --lane-len 20 \
  --route-num 25 --route-len 20
```

This bundled adapter creates `save_path` if needed, reads the explicitly
provided log-name JSON, builds a `NuPlanScenarioBuilder`, constructs a
`ScenarioFilter`, processes scenarios with a process-pool
`SingleMachineParallelExecutor`, and writes one `.npz` per scenario. It writes
the manifest to the explicit `--manifest-output` path, avoiding the
checkout-relative manifest behavior of the source template. It still requires
real nuPlan data/maps and is therefore not a safe synthetic smoke.

### Arguments

| Argument | Observed meaning and safe use |
| --- | --- |
| `--data-path` | Raw nuPlan data/DB root; must be an existing readable directory. |
| `--map-path` | nuPlan map root; it must match the DB/map version expected by the builder. |
| `--save-path` | Processed `.npz` directory; created if absent. Use a dedicated empty or versioned directory. |
| `--log-names` | Explicit JSON array of training log names; avoids an implicit current-working-directory file. |
| `--manifest-output` | Explicit JSON filename-list destination; defaults inside `save-path`. |
| `--scenarios-per-type` | Optional per-scenario-type cap forwarded to `ScenarioFilter`. |
| `--total-scenarios` | Total cap forwarded to the filter; start small before increasing it. |
| `--shuffle-scenarios` | Explicit true/false value passed to the filter. |
| `--agent-num` | Fixed agent slots; default 32. Agent rows are selected by current distance, with at most 10 pedestrian/bicycle rows before filling remaining slots. |
| `--static-objects-num` | Fixed static-object slots; default 5. Rows are selected by current distance. |
| `--lane-num`, `--lane-len` | Maximum lane and boundary elements, and points per element; defaults 70 and 20. |
| `--route-num`, `--route-len` | Maximum route-lane elements and points per element; defaults 25 and 20. |

The scenario filter is initialized with no scenario-type, map-name, or token
filter, the loaded training log names as `log_names`, `expand_scenarios=True`,
`remove_invalid_goals=False`, and the chosen shuffle and limits. The builder
requires the raw data root, map root, optional sensor root/DB files (both
`None` in this workflow), and the map version. If the builder cannot discover
DBs or maps, stop and fix the paths instead of lowering caps or bypassing map
features.

## Shell workflow meaning

The supplied shell workflow is only a parameter template. Its two nuPlan
variables and its training output variable are deliberately placeholders, and
its `--total_scenarios 1000000` setting is expensive. Replace them with
absolute, verified paths, add a small limit for the first run, and invoke the
CLI explicitly. Check the shell with `bash -n`; do not run it merely to test
that placeholders parse.

A recommended staged run is:

1. Create a fresh output directory and select an explicit log-name JSON.
2. Run the bundled adapter and validator `--help` checks.
3. Process one or a few scenarios with the default feature caps.
4. Validate the resulting manifest and every listed record; inspect the first
   record's keys and shapes.
5. Only then increase `--total-scenarios`, retaining the same cap values and
   normalization file.

## DataProcessor behavior

The processor uses a 2-second history and 8-second future at ten samples per
second. It queries a 100 m radius around the initial ego pose and extracts
lane centerlines, left/right boundaries, and route lanes. All coordinates and
velocities are transformed into the initial ego frame. Agents are limited to
vehicles, pedestrians, and bicycles; static rows are limited to zone signs,
barriers, traffic cones, and generic objects. Missing rows are zero-padded.

For each scenario, the processor obtains past/future ego and tracked-object
trajectories, current traffic lights, route roadblock IDs, lane speed limits,
and map vectors. It saves metadata (`map_name`, `token`) in addition to the
model arrays. A route can be empty or disconnected; route correction and
connectivity pruning may therefore produce zero-padded route slots without
indicating a malformed `.npz`.

The package-level `DataProcessor` also has an inference adapter that returns
batched tensors. That adapter is not a substitute for offline extraction and
is outside this sub-skill's real-data workflow.

## Manifest and dataset handoff

The dataset loader receives three independent values: processed data
`data_dir`, JSON `data_list`, and the configured past/predicted neighbor counts
and future length. It opens each manifest entry by joining it to `data_dir`,
then exposes a tuple in this order:

1. `ego_current_state`
2. `ego_future_gt`
3. `neighbor_agents_past`
4. `neighbors_future_gt`
5. `lanes`
6. `lanes_speed_limit`
7. `lanes_has_speed_limit`
8. `route_lanes`
9. `route_lanes_speed_limit`
10. `route_lanes_has_speed_limit`
11. `static_objects`

The loader slices the first axis of neighbor arrays to the configured
neighbor count and retains the generated fixed shapes otherwise. A manifest
entry must therefore be a basename such as `map_token.npz`, not a path to a
raw DB, a directory, or another manifest.

## Bundled preprocessing adapter and validator

`run_preprocessing.py` is the self-contained replacement for the source
launcher: it makes all input/output paths explicit and writes the manifest to a
chosen location. It is still an expensive, data-backed command. Use it only
after the validator and external-prerequisite checks pass.

## Safe bundled validator

Use the helper without nuPlan or PyTorch:

```bash
python scripts/validate_preprocessed_data.py \
  --data-dir /abs/path/to/processed \
  --manifest /abs/path/to/diffusion_planner_training.json \
  --normalization /abs/path/to/normalization.json \
  --raw-data-path /abs/path/to/nuplan/trainval \
  --map-path /abs/path/to/nuplan/maps \
  --save-path /abs/path/to/processed
```

It checks directory kinds and permissions when supplied, manifest JSON shape
and safe filenames, listed-file existence, required arrays, expected caps and
sample dimensions, finite floating values, and normalization vector lengths
and positive finite standard deviations. It returns nonzero with actionable
errors and does not invoke a process pool. To exercise the validator safely:

```bash
python scripts/validate_preprocessed_data.py --make-fixture ./.dp-fixture
python scripts/validate_preprocessed_data.py \
  --data-dir ./.dp-fixture/data \
  --manifest ./.dp-fixture/diffusion_planner_training.json \
  --normalization ./.dp-fixture/normalization.json
```

The fixture is intentionally synthetic and must never be reported as a
successful nuPlan preprocessing run.

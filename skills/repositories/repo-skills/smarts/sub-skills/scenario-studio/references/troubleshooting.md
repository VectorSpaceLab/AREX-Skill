# Scenario Studio troubleshooting

## Install and import

**`No module named smarts` or `No module named smarts.sstudio`**

- Run the helper with the same Python that will run SMARTS (`python -c
  'import smarts, smarts.sstudio'`).
- Install the SMARTS package in an isolated environment, then check the
  installed version. This route was inspected with SMARTS 2.0.1 and Python
  3.11; do not assume a different release has identical signatures.
- Do not make the source checkout the runtime dependency. Ensure the installed
  package and the user's scenario module are importable from the intended
  `PYTHONPATH`.

**OpenDRIVE import error**

Install the package's optional OpenDRIVE extra and rerun a small map import.
The core CPU package can import Scenario Studio while the OpenDRIVE parser is
absent; that is an optional capability, not a scenario DSL failure.

**SUMO import error or `SUMO_HOME`/`sumolib` failure**

The inspected environment did not have the SUMO Python modules. Install and
verify the selected SUMO integration separately, then check `scl`/runtime
configuration. Do not silently change `engine="SUMO"` to `SMARTS` unless the map
and intended behavior support it. Live SUMO/TraCI belongs to `cli-integrations`.

**Waymo, Argoverse, or history importer error**

Treat these as optional packages plus external data. Verify the dataset format,
local input path, source type spelling, map alignment, and package version.
Network downloads and credentials are outside this route. A descriptor with no
`input_path` is a placeholder and will be skipped, not imported.

## Data and configuration

**`No valid scenarios found` / `is_valid_scenario` is false**

Check that the scenario root exists and contains a recognized map source or a
prebuilt `build/map/map_spec.pkl` whose builder is available. Unknown map
extensions need a custom `builder_fn`; an arbitrary custom file is not detected
as a road map. Run the layout validator, then test `Scenario.build_map` with the
same Python.

**`map.glb` or `map_spec.pkl` is missing**

Run the authoring `scenario.py` (which calls `gen_scenario`) and, when needed,
the public `scl scenario build --clean --seed <n> <scenario>` command. Use an
empty or backed-up output directory for experiments. Do not hand-create pickles
or copy an artifact from a different map.

**`build.db` is stale or outputs disagree after a source edit**

Generation caches object/map hashes. Use one explicit seed and regenerate; if a
map or builder changed, use the public clean build. A second build can be
faster because the cache is valid, so a fast no-op is not necessarily failure.

**Traffic route files are absent**

Confirm `Scenario.traffic` is non-empty, each group has a valid non-reserved
name, the route's roads and lanes exist, and the selected engine has a usable
map. A nonempty DSL object can still produce no file if route resolution or the
map builder failed first. Inspect the generator error rather than bypassing it.

## API misuse

**`TypeError` constructing a core DSL type**

Inspect the installed signature. In the verified release: `Traffic` takes
`flows` first, `Flow` requires `route` and `rate`, `Route` requires `begin` and
`end`, `Mission` requires `route`, and `MapSpec` requires `source`. Use the
public `types` alias and avoid copying signatures from another SMARTS release.

**Route cannot be resolved**

Check the exact road IDs, lane indexes, and offsets in the chosen map. Use
`RandomRoute()` only when the map/traffic generator supports random generation.
`via` entries are road IDs, not lane tuples. For a custom map, make sure the
builder returns a real `RoadMap` object and a stable hash.

**Mission starts in the wrong place or immediately collides**

Studio does not perform an ego/social/traffic occupancy collision check. Move
one start to another lane/offset, stagger departure/entry times, change flow
begin/end, or use a deliberate entry tactic. Also ensure a trap entry zone's
edge matches its mission begin edge.

**Social actor or bubble fails**

Resolve `agent_locator` as `module:registered-locator`, make actor names unique
across groups, and verify the social package can be imported at runtime. For a
bubble, use a valid zone, nonnegative margin, one follow id at most, and an
explicit offset for traveling bubbles. A `keep_alive` bubble requires a boid
actor in this release.

## CLI and workflow failures

**`scl scenario build` fails before generation**

Run `scl scenario --help` and `scl scenario build --help` with the target
installation. Pass an existing scenario path and an integer seed. The command
executes `scenario.py`; syntax/import errors are source errors. `--clean` removes
generated caches and route/build artifacts, so review the target and keep source
files outside the clean scope.

**Build succeeds but runtime cannot discover traffic**

Check the generated file extensions and locations: `.rou.xml` and `.smarts.xml`
under `build/traffic/`. `discover_traffic` combines both families. Validate
that the runtime has the same map/engine optional packages used to generate the
files.

**Custom `builder_fn` works during generation but not in a new process**

The callable must be importable in the new process. Serialized `MapSpec` may
contain executable Python; never transfer it from an untrusted source. Put the
builder in an application package, not an ephemeral interactive session.

**History appears spatially shifted**

Compare dataset coordinates with the map, then check `x_margin_px`,
`y_margin_px`, `swap_xy`, `flip_y`, lane width scaling, and heading inference.
Do not combine `shift_to_origin` with histories without explicitly validating
alignment.

## Script failures

`validate_scenario_layout.py` is intentionally read-only. It exits nonzero for
missing roots/maps, malformed path arguments, missing required build assets, or
an unknown map type. `generate_minimal_scenario.py` refuses nonempty output
unless `--force` is supplied and does not install anything or call network
services. If generation fails, retain the error and inspect the explicit
output; do not retry destructive clean operations blindly.

# Data-preparation troubleshooting

Use the smallest reproducer that distinguishes an environment/path failure
from an expensive data failure. Preserve the exact command, working directory,
selected caps, builder map version, and manifest path in the handoff.

## Missing nuPlan devkit or imports

**Symptoms:** `ModuleNotFoundError: nuplan`, failure importing
`NuPlanScenarioBuilder`, or an API/signature mismatch during startup.

**Action:** Run the import probe from the workflow reference in the same
interpreter that will run preprocessing. Install or activate the compatible
nuPlan-devkit environment, then rerun `--help`. Do not solve this by importing
only `diffusion_planner`: the processor directly depends on nuPlan actor-state,
map, tracked-object, and scenario APIs. If the installed version differs from
the verified 1.2.2 environment, recheck `ScenarioFilter` and builder signatures
before a real run.

## Invalid raw, map, or save paths

**Symptoms:** builder discovers zero DBs, map lookup errors, permission errors,
or the process creates an apparently successful empty directory.

**Action:** Check each path as the exact kind the CLI expects:

```bash
test -d "$NUPLAN_DATA_PATH" && test -r "$NUPLAN_DATA_PATH"
test -d "$NUPLAN_MAP_PATH" && test -r "$NUPLAN_MAP_PATH"
mkdir -p "$TRAIN_SET_PATH"
test -d "$TRAIN_SET_PATH" && test -w "$TRAIN_SET_PATH"
```

Use absolute paths, confirm the DB and map releases correspond, and ensure the
working directory also contains the intended training-log JSON. A writable
save directory does not prove that the raw DB root or maps are discoverable.
Run the bundled validator with `--raw-data-path`, `--map-path`, and
`--save-path` to make these checks repeatable.

## Missing or wrong manifest

**Symptoms:** `FileNotFoundError` for the training-log JSON, scenario count is
zero, the dataset loader cannot open a listed record, or validation says a
manifest entry is missing.

**Action:** Separate the two JSON roles:

- The input log-name list is read relative to the preprocessing working
  directory and is passed as `log_names` to `ScenarioFilter`.
- The generated filename list is written relative to the working directory
  after processing and contains `.npz` basenames.

Do not pass the raw log-name JSON to `DiffusionPlannerData`. Locate the actual
generated manifest, make its `data_dir` agree with the `.npz` directory, remove
absolute/path-traversal entries, and check for duplicates. If the manifest is
empty, investigate scenario discovery/filter limits rather than treating it as
an empty but valid training set.

## Empty output after a successful-looking run

**Symptoms:** no `.npz` files, a zero scenario count, or a manifest with zero
entries.

**Action:** First run a one-scenario limit with shuffling disabled only if the
entry-point's bool parsing has been verified. Check the data root, map root,
log names, map version, DB permissions, and scenario-filter limits. Confirm
that the process was run from the directory containing the input log JSON and
that the output scan is looking in the directory where records were saved.
Do not use an empty output as a schema fixture.

## Feature-shape mismatch

**Symptoms:** DataLoader collation errors, model linear-layer/broadcasting
errors, or a validator report such as `(70, 20, 12)` expected but `(64, 20,
12)` found.

**Action:** Compare the preprocessing cap arguments, dataset-loader neighbor
counts/future length, and model configuration. The default contract is:

```text
neighbor_agents_past    (32, 21, 11)
neighbor_agents_future  (32, 80, 3)
static_objects          (5, 10)
lanes                   (70, 20, 12)
route_lanes             (25, 20, 12)
*_speed_limit           (cap, 1)
*_has_speed_limit       (cap, 1) boolean
```

Also check `ego_current_state (10,)` and `ego_agent_future (80, 3)`. Pass
custom caps explicitly to the validator if a deliberate non-default dataset
was generated. Do not pad a mismatched dataset in the training loop without
checking type codes, availability semantics, and normalization.

## Normalization mismatch or NaN

**Symptoms:** shape/broadcasting errors in `ObservationNormalizer` or
`StateNormalizer`, exploding loss, NaNs, or nonzero padded rows after
normalization.

**Action:** Check the normalization JSON keys, vector lengths, finite values,
and strictly positive standard deviations. Match lengths to the feature table
in `data-formats.md`: 10 for ego current state, 11 for neighbor history, 10
for static objects, 12 for lane vectors, and 1 for speed limits; `ego` and
`neighbor` are 4-value target statistics. Verify that training converts future
heading to cos/sin before applying the state normalizer. Check units and the
ego-centric anchor; do not normalize global-coordinate records with this file.
If the file was edited or generated for another cap/feature order, regenerate
or version it with the corresponding data rather than suppressing the error.

## Real-data cost and partial runs

**Symptoms:** preprocessing is slow, consumes substantial disk, worker errors
appear late, or an interrupted run leaves a partial directory.

**Action:** Treat map queries and scenario history/future extraction as
expensive. Start with one or a few scenarios, monitor disk space, and use a
fresh versioned output directory. A partial directory can contain valid files
but an incomplete manifest; validate the manifest and record count before
training. Do not launch the million-scenario shell template on a shared host
without an explicit budget and storage estimate.

## Route/map edge cases

A scenario may have no route roadblock IDs or a disconnected route. The
processor has route correction and connectivity pruning, so zero route slots
can be legitimate. Conversely, a lane traffic-light count that does not match
lane coordinates is a processing error. Inspect `lanes`, route arrays, speed
masks, and finite values together; do not infer route validity from a nonempty
lane array alone.

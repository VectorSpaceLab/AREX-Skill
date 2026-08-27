# Data and evaluation troubleshooting

## Missing or malformed keys

- **`vehicles` missing or not a mapping**: the file is probably a scenario
  configuration, an empty YAML document, or an incomplete frame. Point
  `--input-root` at the dumped frame tree rather than the configuration tree.
- **`location`, `center`, `angle`, or `speed` missing**: the trajectory tuple
  cannot be reconstructed safely. Repair or exclude the frame; do not invent
  zeros because that changes the target state.
- **Vehicle id type mismatch**: YAML commonly loads an unquoted numeric key as
  an integer. The helper accepts the integer and string forms of the same id.
  If an id is absent in a later frame, it stops that vehicle's trajectory at
  the first missing frame instead of crossing to a different vehicle.
- **Dumper assertion on `carla_id == -1`**: the source dumper requires real
  CARLA ids for dumped perceived vehicles. Disable the incompatible perception
  dumping mode or provide valid source records; this is not an offline label
  generation problem.

## Horizon truncation and timing

- A short `predictions` or `observations` list is expected at a sequence edge.
  The helper uses 10 records per second, excludes the current frame, and does
  not pad, extrapolate, or interpolate.
- A shorter-than-requested prediction in the middle of a sequence usually means
  the target id disappeared at that horizon. Inspect neighboring `vehicles`
  mappings and actor lifecycle events before treating it as a model failure.
- The first 60 simulation steps are ignored by `DataDumper`; afterward every
  second step is dumped at 10 Hz for a 0.05 second simulation tick. Evaluation
  manager plots skip 60 20 Hz samples. Do not compare those warm-ups without
  converting the time base.
- If frame filenames do not sort chronologically, rename them to stable
  zero-padded names or supply a pre-sorted input tree. The helper intentionally
  uses deterministic lexical ordering and does not infer timestamps from YAML.

## Output writes and non-destructive processing

- `--output-root` must be distinct from `--input-root` unless `--in-place` is
  explicitly supplied. Roots that contain one another are rejected to avoid
  recursively consuming a generated tree.
- A separate output tree is not overwritten by default. Add `--overwrite` only
  after checking the target; otherwise choose a new empty output root.
- `--in-place` is the explicit source mutation switch. Use a backup or versioned
  input when the original dump is evidence for a later comparison.
- The helper validates and builds each sequence before writing. A malformed
  YAML file raises an error rather than writing a guessed record. Only YAML
  files are emitted; images and point clouds are not copied or changed.
- If a write fails, check parent-directory permissions, free space, and whether
  another process holds the destination. The helper writes a temporary file in
  the destination directory and atomically replaces the target after a
  successful serialization.

## Plotting backend and evaluation failures

- **`cannot connect to display` / GUI hangs**: set `MPLBACKEND=Agg` before the
  first matplotlib import, or run in a desktop backend intentionally. Save the
  returned figure and close it rather than relying on `plt.show()`.
- **No figure or empty axes**: check that the debug helper received at least one
  update and that the relevant history lists are non-empty. The native helper
  tests use synthetic one-step updates for this reason.
- **`EvaluationManager` import or construction fails**: it imports CARLA and
  expects compatible manager objects. An installed client library is not a
  running CARLA server and does not prove that route/sensor evaluation can run.
- **Evaluation stops in one module**: run the modules separately against the
  available manager state and retain `log.txt` plus the actor/platoon id. A
  missing sensor queue, route, or platoon is an external-data precondition,
  not a reason to fabricate output.

## Reproducibility checklist

Record the source revision/version, input and output roots, horizon arguments,
frame ordering rule, number of frames per vehicle, missing-id truncations,
matplotlib backend, and whether the operation was in-place. Keep review logs
and synthetic test reports outside the runtime skill directory.

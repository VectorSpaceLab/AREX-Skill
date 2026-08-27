# Processed data formats and normalization

## Scenario record

Each saved record is an `.npz` containing these metadata and model arrays:

| Key | Expected default shape | Meaning |
| --- | --- | --- |
| `map_name` | scalar string | nuPlan map identifier used in the output filename. |
| `token` | scalar string | Scenario token used in the output filename. |
| `ego_current_state` | `(10,)` | Ego-centric x/y, cos/sin heading, vx/vy, ax/ay, steering angle, and yaw rate. |
| `ego_agent_future` | `(80, 3)` | Ego future x/y/heading at 10 Hz over 8 seconds. Training converts heading to cos/sin before state normalization. |
| `neighbor_agents_past` | `(32, 21, 11)` | Up to 32 current agents, 21 samples covering 2 seconds of history plus present, and x/y, cos/sin heading, vx/vy, width/length, and a 3-way vehicle/pedestrian/bicycle type code. |
| `neighbor_agents_future` | `(32, 80, 3)` | Future x/y/heading for the selected agents; zero rows represent unavailable agents. |
| `static_objects` | `(5, 10)` | Up to 5 static objects: x/y, cos/sin heading, width/length, and a 4-way sign/barrier/cone/generic type code. |
| `lanes` | `(70, 20, 12)` | Fixed lane vectors: point, local tangent vector, offsets to left/right boundaries, and 4-way traffic-light encoding. |
| `lanes_speed_limit` | `(70, 1)` | Lane speed limits, with zero where unavailable. |
| `lanes_has_speed_limit` | `(70, 1)` boolean | Speed-limit availability mask. |
| `route_lanes` | `(25, 20, 12)` | Lane vectors selected from the connected route subset, zero-padded. |
| `route_lanes_speed_limit` | `(25, 1)` | Route-lane speed limits. |
| `route_lanes_has_speed_limit` | `(25, 1)` boolean | Route-lane speed-limit availability mask. |

The first dimension of agent/static/map arrays is a cap, not a guarantee that
all slots contain real objects. Map availability is represented by zero
padding and the corresponding lane availability is implicit in the vector
construction; speed-limit masks distinguish an absent speed limit from a
present one. Do not interpret an all-zero slot as a valid object at the ego
origin.

The actual output names are generated from `map_name` and `token`; collisions
are possible if the same pair is processed more than once. Use a fresh or
versioned save directory and inspect duplicate basenames before combining
runs.

## Coordinate and temporal assumptions

The processor anchors all ego, agent, static, and map coordinates at the
scenario's initial ego rear axle pose. Agent and static rows are sorted by
current distance and then clipped; pedestrian/bicycle rows have an additional
cap of 10 before remaining slots are filled. The history is 20 past samples
plus the current sample (`21`), and the future is `80` samples. The generated
future trajectory retains heading in radians until training converts it to
`[cos(heading), sin(heading)]`.

If a custom invocation changes any of `agent_num`, `static_objects_num`,
`lane_num`, `lane_len`, `route_num`, or `route_len`, pass the same values to
the validator and to the eventual training configuration. A record with
shape `(64, 21, 11)` is not compatible with a consumer configured for 32
agents merely because it is otherwise well formed.

## Normalization relationship

The supplied normalization JSON has these entries and vector lengths:

| Entry | Length | Consumer |
| --- | ---: | --- |
| `ego` | 4 | `StateNormalizer`: ego target `[x, y, cos, sin]`. |
| `neighbor` | 4 | `StateNormalizer`: repeated for configured predicted neighbors. |
| `ego_current_state` | 10 | `ObservationNormalizer`. |
| `neighbor_agents_past` | 11 | `ObservationNormalizer`. |
| `static_objects` | 10 | `ObservationNormalizer`. |
| `lanes` | 12 | `ObservationNormalizer`. |
| `lanes_speed_limit` | 1 | `ObservationNormalizer`. |
| `route_lanes` | 12 | `ObservationNormalizer`. |
| `route_lanes_speed_limit` | 1 | `ObservationNormalizer`. |

`ObservationNormalizer` ignores `ego` and `neighbor`, normalizes only keys
present in the input, and restores an all-zero row after normalization so
padding remains zero. `StateNormalizer` uses only `ego` and `neighbor` and
expects the heading-converted four-channel target. Consequently:

- Verify every mean/std vector's length against the final feature dimension;
  PyTorch broadcasting can otherwise fail late or normalize the wrong axis.
- Require finite means and strictly positive finite standard deviations.
- Keep the normalization file with the dataset/config version. Changing
  feature order, heading representation, caps, or units requires a matching
  normalization update and a fresh validation.
- Do not use the 4-value `ego`/`neighbor` vectors directly on the raw 3-value
  future arrays before heading conversion.

The normalizer source accepts a file path or an argument object containing the
normalization path. A valid JSON file is necessary but not sufficient: the
record shapes, feature order, and ego-centric coordinate convention must also
match.

## Manifest contract

The generated filename list is a JSON array of strings. Each string must be a
safe `.npz` basename in the processed directory. Validate all of the following
before dataset construction:

- JSON parses to a non-empty list for a non-empty training run.
- Entries are strings, end in `.npz`, are not absolute, and do not contain
  `..` path components.
- Every entry exists exactly where the dataset loader will join it.
- There are no duplicate entries; duplicates silently oversample a record.
- Every listed record contains all required keys and default/custom expected
  shapes.
- The manifest is not accidentally the raw training-log list. A log name such
  as `2021.05...` is an input selector and is not a processed filename.

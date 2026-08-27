# HighwayEnv observation types

The observation type is selected by `config["observation"]["type"]`. These type
strings are case-sensitive and are the public names to put in configs:

- `Kinematics`
- `OccupancyGrid`
- `TimeToCollision`
- `LidarObservation`
- `KinematicsGoal`
- `GrayscaleObservation`
- `AttributesObservation`
- `MultiAgentObservation`
- `TupleObservation`
- `ExitObservation`

## `Kinematics`

Purpose: a fixed-size table of nearby vehicle features.

Important parameters:

| Key | Meaning |
| --- | --- |
| `features` | Feature names to include. Default is `presence`, `x`, `y`, `vx`, `vy`. |
| `vehicles_count` | Number of rows, including ego vehicle. Missing traffic rows are zero-filled. |
| `features_range` | Per-feature `[min, max]` ranges used for normalization to `[-1, 1]`. |
| `absolute` | If false, non-ego coordinates/velocities are relative to ego. |
| `order` | `sorted` for distance order, `shuffled` for randomized non-ego rows. |
| `normalize` / `clip` | Normalize and clip range-managed features. |
| `see_behind` | Include vehicles behind the observer when searching nearby objects. |
| `observe_intentions` | Include destination direction features when vehicles expose them. |
| `include_obstacles` | Include road objects/obstacles as observable objects. |

Space shape: `(vehicles_count, len(features))`, dtype `float32`. The ego vehicle
is always the first row. Use `presence` to distinguish a real all-zero vehicle
state from a padded row.

Common feature names include `presence`, `x`, `y`, `vx`, `vy`, `heading`,
`cos_h`, `sin_h`, `cos_d`, `sin_d`, `long_off`, `lat_off`, and `ang_off`.
`long_off`, `lat_off`, and `ang_off` are useful in continuous intersection
variants because they describe offsets to the closest lane.

## `OccupancyGrid`

Purpose: a channel-first grid around the ego vehicle, useful for spatial policies
or local-map features.

Important parameters:

| Key | Meaning |
| --- | --- |
| `features` | Grid channels. Defaults to `presence`, `vx`, `vy`, `on_road`. |
| `grid_size` | `[[x_min, x_max], [y_min, y_max]]` local bounds in meters. |
| `grid_step` | `[x_step, y_step]` cell size. Use this singular key. |
| `features_range` | Ranges used to normalize vehicle features before filling cells. |
| `absolute` | Must normally stay `False`; absolute occupancy grids are not implemented. |
| `align_to_vehicle_axes` | Rotate grid axes into the observer vehicle frame. |
| `clip` | Clip values to `[-1, 1]`. |
| `as_image` | Return `uint8` image-like values instead of float features. |

Space shape is `(len(features), x_cells, y_cells)` where each cell count is
`floor((max - min) / step)`. For example, four features, `grid_size=[[-300, 300],
[-10, 10]]`, and `grid_step=[2, 2]` produce shape `(4, 300, 10)`.

Notes:

- The implementation is channels-first, not `height x width x channels`.
- `on_road` is a synthetic road layer; other channels are vehicle features.
- `absolute=True` raises `NotImplementedError` for this observation type.
- `as_image=True` maps clipped values to `[0, 255]` and changes dtype to
  `uint8`.

## `TimeToCollision`

Purpose: compact risk representation of predicted time-to-collision on nearby
lanes and speed hypotheses.

Important parameters:

| Key | Meaning |
| --- | --- |
| `horizon` | Prediction horizon in seconds. Default is `10`. |

Space shape is usually `(3, 3, horizon * policy_frequency)`, dtype `float32`.
The first axis corresponds to ego speed hypotheses, the second to lanes around
the current lane, and the third to time bins. `two-way-v0` defaults to this
observation with horizon 5; `u-turn-v0` defaults to horizon 16.

## `LidarObservation`

Purpose: angular sectors around the observer, with nearest-object distance and
relative velocity along each sector.

Important parameters:

| Key | Meaning |
| --- | --- |
| `cells` | Number of angular sectors. Default is `16`. |
| `maximum_range` | Maximum trace distance. Default is `60`. |
| `normalize` | Divide distances and relative speeds by `maximum_range`. |

Space shape: `(cells, 2)`, dtype `float32`. Column 0 is distance; column 1 is the
relative speed component along the sector direction. Use `normalize`, not the
British spelling `normalise`.

## `KinematicsGoal`

Purpose: goal-conditioned observation for parking-style tasks.

Important parameters:

| Key | Meaning |
| --- | --- |
| `features` | Usually `x`, `y`, `vx`, `vy`, `cos_h`, `sin_h`. |
| `scales` | Per-feature divisors applied to current and goal values. |
| `normalize` | Often `False` for parking because scaling is explicit. |

Space: `Dict` with keys `observation`, `achieved_goal`, and `desired_goal`. Each
value is a vector with length `len(features)` and dtype `float64`. Parking uses
this internally to compute reward and `info["is_success"]`.

## `GrayscaleObservation`

Purpose: stacked grayscale images rendered from the simulator.

Important parameters:

| Key | Meaning |
| --- | --- |
| `observation_shape` | `(width, height)` image size. |
| `stack_size` | Number of frames in the returned stack. |
| `weights` | RGB-to-grayscale weights, for example `[0.2989, 0.5870, 0.1140]`. |
| `scaling` | Optional viewer scaling for the observation renderer. |
| `centering_position` | Optional viewer centering for the observation renderer. |

Space shape: `(stack_size, width, height)`, dtype `uint8`. Rendering mechanics,
video recording, and headless display troubleshooting are owned by the simulation
and training sub-skills; this sub-skill only records the observation config.

## `AttributesObservation`

Purpose: expose named attributes from the environment as a dict observation.
`lane-keeping-v0` uses this for `state`, `derivative`, and `reference_state`.

Important parameter: `attributes`, a list of attribute names to read from the env.
Space is a `Dict` keyed by those names. Use only attributes that the environment
maintains at reset and step time.

## `MultiAgentObservation`

Purpose: one observation per controlled vehicle.

Important parameter: `observation_config`, a nested single-agent observation
config. The nested observation is cloned for each controlled vehicle and its
observer is set to that vehicle. Space is a `Tuple` with one subspace per
controlled vehicle; observations are returned as tuples in the same order.

## `TupleObservation`

Purpose: combine several observation views for the same observer.

Important parameter: `observation_configs`, a list of observation config dicts.
Space and returned observations are `Tuple`s in the same order. Use this when a
consumer intentionally expects multiple observation modalities.

## `ExitObservation`

Purpose: exit-env-specific kinematics. It behaves like `Kinematics`, but the ego
row's `x` value is replaced with longitudinal distance along the next exit lane.
It is intended for `exit-v0` and connected-lane exit variants.

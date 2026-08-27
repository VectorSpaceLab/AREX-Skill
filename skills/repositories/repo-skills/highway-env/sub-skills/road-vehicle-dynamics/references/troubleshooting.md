# Troubleshooting road, vehicle, and custom-environment issues

Use this reference for lower-level HighwayEnv scenario failures. If the failure is about `gym.make`, environment IDs, rendering, vectorization, or wrapper operation, use the simulation sub-skill. If it is about observation/action configuration or reward component interpretation, use the observations/actions/rewards sub-skill.

## Import or optional-dependency failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'highway_env'` | The package is not installed/importable in the active Python environment. | Install `highway-env` in the environment that will run the scenario, then retry a basic import before using this sub-skill. |
| `ModuleNotFoundError: No module named 'gymnasium'` while importing HighwayEnv | A partial install omitted required runtime dependencies. | Install the package with its declared dependencies rather than copying only source files. |
| `ImportError` for `scipy` when running interpolation checks | SciPy is optional for `check_spline_interp.py`; it is only used as a comparison reference. | The helper will fall back to deterministic expected-value checks when SciPy is absent. If a SciPy comparison is required, install SciPy explicitly in the inspection environment. |

## Lane and road-network issues

### `KeyError` in `RoadNetwork.get_lane(...)`

Likely causes:

- the `(from_node, to_node, lane_id)` tuple does not exist;
- lane IDs were assumed before checking append order;
- nodes were misspelled or reused for unrelated graph segments;
- a route points to a downstream node that has not been added.

Recovery:

```python
print(sorted(net.graph.keys()))
print({src: sorted(dsts.keys()) for src, dsts in net.graph.items()})
print(list(net.lanes_dict().keys()))
```

Then use one of the printed lane indexes exactly. If only one lane exists on an edge, `get_lane(("a", "b", None))` can resolve to lane 0, but explicit lane IDs are clearer in generated scenarios.

### Vehicles spawn off-road or immediately select the wrong lane

Likely causes:

- world coordinates were passed directly instead of `lane.position(longitudinal, lateral)`;
- `heading` does not match `lane.heading_at(longitudinal)`;
- a `CircularLane` phase or `clockwise` flag is reversed;
- a `SineLane` amplitude/phase places the lane somewhere unexpected;
- a `PolyLane` has too few or poorly ordered points.

Recovery:

```python
lane = road.network.get_lane(lane_index)
pos = lane.position(longitudinal, 0)
heading = lane.heading_at(longitudinal)
s, r = lane.local_coordinates(pos)
assert lane.on_lane(pos, s, r, margin=0.5)
vehicle = Vehicle(road, pos, heading=heading, speed=target_speed)
```

For curves, sample several `longitudinal` values and check positions/headings before adding vehicles.

### Lane changes never happen

Likely causes:

- the vehicle is a base `Vehicle`, not a `ControlledVehicle`/`MDPVehicle`/behaviour class;
- the action config disables lateral actions;
- target side lane does not exist or is not reachable from current position;
- the target lane has `forbidden=True`;
- an `IDMVehicle` has `enable_lane_change=False` or MOBIL rejects the change as unsafe.

Recovery:

- Check `type(vehicle)`, `vehicle.lane_index`, and `vehicle.target_lane_index`.
- Check `road.network.side_lanes(vehicle.lane_index)`.
- For direct controller tests, call `vehicle.act("LANE_RIGHT")`, then repeat `vehicle.act(); vehicle.step(dt)` for several seconds.
- For action-space routing, use the observations/actions/rewards sub-skill.

### Routes fail at intersections

Likely causes:

- `plan_route_to(destination)` was called before the vehicle had a valid `lane_index`;
- the destination node is not reachable by graph search;
- the current route contains `(from, to, None)` and lane ID inference chooses an unexpected lane;
- `set_route_at_intersection(...)` is called before the route reaches a branching node.

Recovery:

```python
print(vehicle.lane_index)
print(road.network.shortest_path(vehicle.lane_index[1], destination_node))
vehicle.plan_route_to(destination_node)
print(vehicle.route)
print(vehicle.get_routes_at_intersection())
```

If the graph has asymmetric lane counts, explicitly set lane IDs in planned route entries when lane choice matters.

## `Road.neighbour_vehicles` misses a vehicle near a segment boundary

Likely causes:

- `road.neighbour_vehicles_connected_lanes` is false, preserving legacy same-segment search;
- the environment ID is a legacy `*-v0` variant rather than a connected-lane version;
- connected segments have mismatched lane counts and the fallback lane is not the intended one;
- the candidate vehicle is not actually on the searched lane according to `lane.on_lane(..., margin=1)`;
- the candidate is a `Landmark`, which neighbour search intentionally ignores.

Recovery:

1. Print the flag and lane indexes:
   ```python
   print(road.neighbour_vehicles_connected_lanes)
   print(ego.lane_index, other.lane_index)
   ```
2. For custom roads, set `neighbour_vehicles_connected_lanes=True` on `Road(...)` and keep `config["neighbour_vehicles_connected_lanes"]` consistent.
3. Verify the geometry:
   ```python
   lane = road.network.get_lane(ego.lane_index)
   print(lane.local_coordinates(ego.position))
   candidate_lane = road.network.get_lane(other.lane_index)
   s_other, r_other = candidate_lane.local_coordinates(other.position)
   print(s_other, r_other, candidate_lane.on_lane(other.position, s_other, r_other, margin=1))
   ```
4. For registered scenarios, select the connected-lane version ID where available, such as `merge-v1`, `roundabout-v1`, `racetrack-v1`, `u-turn-v1`, `exit-v1`, or `intersection-v2`.

## Vehicle dynamics and collision surprises

### Speed or position does not change as expected

Likely causes:

- `Vehicle.act(...)` was not called with a new action, so the previous action is repeated;
- a crashed vehicle overrides actions with braking;
- speed is clipped by `MIN_SPEED`/`MAX_SPEED`;
- `ControlledVehicle.act(action)` converted a high-level action into low-level commands, overwriting manual low-level commands.

Recovery:

- For base kinematics, pass dictionaries: `{"acceleration": value, "steering": value}`.
- For controllers, pass high-level strings (`"FASTER"`, `"SLOWER"`, `"LANE_LEFT"`, `"LANE_RIGHT"`) and then continue calling `act()` each simulation tick.
- Step with a small `dt`, commonly `1 / simulation_frequency`.

### Collision with a goal crashes the vehicle

Likely cause: the goal was implemented as `Obstacle` or another solid object.

Recovery: use `Landmark` for non-solid goals. `Landmark` sets `solid=False`; contact can mark the landmark as hit without crashing the vehicle.

### Obstacles are ignored by close-neighbour logic

`road.close_vehicles_to(...)` deliberately returns only vehicles. Use `road.close_objects_to(..., vehicles_only=False)` when obstacles should be considered. `Road.neighbour_vehicles` includes obstacles but skips landmarks.

### `BicycleVehicle` behaves unstably

Likely causes:

- steering command too large for the dynamic model;
- very low speed combined with lateral dynamics;
- large integration timestep;
- expecting exact equality with kinematic `Vehicle` behaviour.

Recovery:

- Keep `dt` small and bounded.
- Start with low steering magnitude and moderate speed.
- Use `Vehicle` or `ControlledVehicle` for basic scenario validation, then switch to `BicycleVehicle` only when dynamic bicycle effects are necessary.

## Custom environment reset/step failures

### `NotImplementedError: The road and vehicle must be initialized...`

Likely causes:

- `_reset()` did not set `self.road`;
- `_reset()` created controlled vehicles but did not set `self.vehicle` or `self.controlled_vehicles`;
- the controlled vehicle was not appended to `self.road.vehicles`.

Recovery checklist:

```python
assert self.road is not None
assert self.vehicle is not None
assert self.vehicle in self.road.vehicles
```

For multi-agent or multiple controlled vehicles, ensure `self.controlled_vehicles` is non-empty and every controlled vehicle is also in `self.road.vehicles`.

### Observation/action spaces fail after reset

Likely causes:

- observation/action config is incomplete or nested incorrectly;
- `_create_vehicles()` uses `self.action_type.vehicle_class` before `define_spaces()` has been called by the base reset;
- custom `define_spaces()` forgot to call `super().define_spaces()`.

Recovery:

- Keep custom observation/action configs complete.
- Let `AbstractEnv.reset()` call `define_spaces()` before `_reset()`; do not bypass the base reset.
- Route detailed config diagnosis to `../observations-actions-rewards/SKILL.md`.

### `reset(seed=...)` is not deterministic

Likely causes:

- scene code uses `np.random` or `random` directly instead of `self.np_random`;
- vehicle creation uses a separate RNG;
- dynamic spawn code ignores the environment seed.

Recovery: use `self.np_random` for all random choices in `_create_road`, `_create_vehicles`, and spawn/cleanup methods. Pass it to `Road(..., np_random=self.np_random)`.

### Immediate collision on reset

Likely causes:

- vehicles were spawned too close;
- the ego vehicle was added after random traffic without clearing nearby vehicles;
- obstacles or walls were placed with incorrect dimensions;
- lane coordinates were computed on the wrong lane index.

Recovery:

- Add the ego vehicle first, then reject traffic within a fixed Euclidean or lane-distance threshold.
- For every new object, check distance to all existing vehicles before appending.
- If changing `Obstacle.LENGTH` or `Obstacle.WIDTH`, recompute `obstacle.diagonal`.

## Interpolation and spline checks

`PolyLane` and `LinearSpline2D` rely on `numpy_interp1d`, a SciPy-free replacement for one-dimensional linear interpolation with extrapolation. If custom spline lanes produce unexpected coordinates:

1. Run the bundled smoke helper:
   ```bash
   python scripts/check_spline_interp.py
   ```
2. Confirm the JSON summary reports `"ok": true`.
3. If `"used_scipy": true`, the helper compared against SciPy's `interp1d(fill_value="extrapolate")` on a deterministic fixture.
4. If `"used_scipy": false`, the helper compared against internal expected values for exact knots, interpolation, extrapolation, and scalar input.

If the helper fails, check that `highway-env` and its runtime dependencies are installed in the active Python environment before debugging custom lane points.

## Quick triage table

| Task/failure | Read next |
|---|---|
| Environment ID not found or registration import order is wrong | `../simulation-environments/SKILL.md` |
| Reset/step/render loop shape is unclear | `../simulation-environments/SKILL.md` |
| Observation shape or action dimension mismatch | `../observations-actions-rewards/SKILL.md` |
| Reward components missing from `info` | `../observations-actions-rewards/SKILL.md` |
| Custom road/lane/vehicle construction issue | `references/road-vehicle-api.md` |
| Custom env lifecycle or registration pattern issue | `references/custom-environments.md` |
| RL training or evaluation is unstable/too slow | `../training-and-evaluation/SKILL.md` |

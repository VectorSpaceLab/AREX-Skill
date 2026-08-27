# Road, lane, vehicle, and object API guide

This reference distills the lower-level HighwayEnv APIs used to build custom driving scenarios. It assumes the `highway-env` package imports successfully and focuses on runtime construction patterns rather than high-level Gymnasium operation.

## Core imports

```python
import numpy as np

from highway_env import utils
from highway_env.road.lane import (
    AbstractLane,
    CircularLane,
    LineType,
    PolyLane,
    PolyLaneFixedWidth,
    SineLane,
    StraightLane,
)
from highway_env.road.regulation import RegulatedRoad
from highway_env.road.road import LaneIndex, Road, RoadNetwork
from highway_env.vehicle.behavior import IDMVehicle, LinearVehicle
from highway_env.vehicle.controller import ControlledVehicle, MDPVehicle
from highway_env.vehicle.dynamics import BicycleVehicle
from highway_env.vehicle.kinematics import Vehicle
from highway_env.vehicle.objects import Landmark, Obstacle, RoadObject
```

## Road-network graph model

A `RoadNetwork` is a directed graph. Each edge is a road segment and stores one or more lane geometries. A lane is addressed by a `LaneIndex` tuple:

```python
lane_index = ("origin-node", "destination-node", lane_id)
```

Where `lane_id` is the integer index among parallel lanes on that edge. Common APIs:

| API | Use |
|---|---|
| `RoadNetwork()` | Start an empty graph. |
| `net.add_lane(_from, _to, lane)` | Append a lane geometry to the edge `_from -> _to`. The lane ID becomes the append order. |
| `net.get_lane((_from, _to, _id))` | Return the lane geometry for a `LaneIndex`. If `_id is None` and the edge has exactly one lane, lane 0 is used. |
| `net.get_closest_lane_index(position, heading=None)` | Find the closest lane by geometric distance and optional heading penalty. |
| `net.all_side_lanes(lane_index)` | Return all lane indexes on the same road segment. |
| `net.side_lanes(lane_index)` | Return adjacent left/right lane indexes on the same segment. |
| `net.next_lane(current_index, route=None, position=None, np_random=np.random)` | Choose the next lane after a vehicle reaches the end of its current lane. Follows a route when possible, otherwise chooses a downstream road. |
| `net.shortest_path(start, goal)` | Breadth-first node path for route planning. |
| `net.random_lane_index(np_random)` | Sample a random lane index from the graph. |
| `net.to_config()` / `RoadNetwork.from_config(config)` | Serialize/deserialize lane graph configurations. |
| `RoadNetwork.straight_road_network(...)` | Build parallel straight lanes with conventional nodes and line types. |

### Straight road helper

```python
net = RoadNetwork.straight_road_network(
    lanes=3,
    start=0.0,
    length=500.0,
    angle=0.0,
    speed_limit=30.0,
    nodes_str=("a", "b"),
)
lane = net.get_lane(("a", "b", 1))
```

The helper creates parallel `StraightLane` objects separated by `StraightLane.DEFAULT_WIDTH` and marks outside borders as continuous lines. Pass an existing `net=` to append another segment:

```python
net = RoadNetwork.straight_road_network(2, length=80, nodes_str=("a", "b"))
net = RoadNetwork.straight_road_network(2, start=80, length=60, nodes_str=("b", "c"), net=net)
```

## Lane geometry and coordinate APIs

All lanes implement `AbstractLane` methods:

| Method/property | Meaning |
|---|---|
| `lane.position(longitudinal, lateral)` | Convert Frenet lane coordinates to world `[x, y]`. |
| `lane.local_coordinates(position)` | Convert world `[x, y]` to `(longitudinal, lateral)`. |
| `lane.heading_at(longitudinal)` | Lane tangent heading in radians. |
| `lane.width_at(longitudinal)` | Lane width in meters. |
| `lane.on_lane(position, longitudinal=None, lateral=None, margin=0)` | True when a point lies on the lane, allowing a margin. |
| `lane.is_reachable_from(position)` | True when a vehicle may reasonably change/reach the lane and it is not forbidden. |
| `lane.after_end(position, longitudinal=None, lateral=None)` | True when a vehicle has passed near the lane end. |
| `lane.distance(position)` | L1-style distance to lane bounds/endpoints. |
| `lane.local_angle(heading, long_offset)` | Heading error relative to lane tangent. |
| `lane.to_config()` and `lane_from_config(...)` | Serialization helpers for supported lane classes. |

### Lane classes

| Class | Best use | Key constructor parameters |
|---|---|---|
| `StraightLane` | Straight road segments and parking spots. | `start`, `end`, optional `width`, `line_types`, `forbidden`, `speed_limit`, `priority`. |
| `SineLane` | Smooth merge ramps or sinusoidal connectors based on a straight centerline. | `start`, `end`, `amplitude`, `pulsation`, `phase`, plus common lane options. |
| `CircularLane` | Roundabouts, U-turns, and intersection turn arcs. | `center`, `radius`, `start_phase`, `end_phase`, `clockwise`, plus common lane options. |
| `PolyLaneFixedWidth` | Piecewise-linear lane from centerline points with fixed width. | `lane_points`, optional `width`, `line_types`, `forbidden`, `speed_limit`, `priority`. |
| `PolyLane` | Piecewise-linear lane with left/right boundaries and sampled width. | `lane_points`, `left_boundary_points`, `right_boundary_points`, plus common options. |

`LineType` values are integers exposed as constants: `LineType.NONE`, `LineType.STRIPED`, `LineType.CONTINUOUS`, and `LineType.CONTINUOUS_LINE`.

### Coordinate sanity check

```python
lane = StraightLane([0, 0], [100, 0], speed_limit=25)
pos = lane.position(20.0, 1.0)
longitudinal, lateral = lane.local_coordinates(pos)
assert abs(longitudinal - 20.0) < 1e-9
assert abs(lateral - 1.0) < 1e-9
assert lane.on_lane(pos, longitudinal, lateral)
```

For `CircularLane`, remember that `start_phase` and `end_phase` are radians and `clockwise` changes the sign convention. Check `lane.length`, `position`, and `heading_at` before placing vehicles on arcs.

## Road container and simulation stepping

A `Road` binds a network, moving vehicles, static/goal objects, and a random generator:

```python
road = Road(
    network=net,
    vehicles=[],
    road_objects=[],
    np_random=np.random.RandomState(42),
    record_history=False,
    neighbour_vehicles_connected_lanes=True,
)
```

Important methods:

| API | Use |
|---|---|
| `road.vehicles` | List of `Vehicle`/controller/behaviour instances that move and collide. |
| `road.objects` | List of `RoadObject` instances such as `Obstacle` and `Landmark`. |
| `road.act()` | Ask every vehicle to decide/store its next action. |
| `road.step(dt)` | Integrate every vehicle and handle vehicle/object collisions. |
| `road.close_objects_to(vehicle, distance, count=None, see_behind=True, sort=True, vehicles_only=False)` | Find nearby vehicles and optionally objects. |
| `road.close_vehicles_to(...)` | Vehicle-only shortcut. |
| `road.neighbour_vehicles(vehicle, lane_index=None)` | Return `(front_vehicle, rear_vehicle)` on a lane. |

`RegulatedRoad` extends `Road` for intersections where `lane.priority` controls right-of-way. It periodically detects possible conflicts and sets yielding `ControlledVehicle` target speeds to zero until the conflict is resolved. Use it when priority-aware intersection behaviour matters; otherwise use `Road`.

## Connected-lane neighbour detection

`Road.neighbour_vehicles(vehicle, lane_index=None)` searches the ego lane and returns the closest front and rear neighbours. With `road.neighbour_vehicles_connected_lanes=False`, only the current lane segment is searched. With it enabled, direct downstream and upstream connected segments are also searched:

- downstream lanes are taken from `road.network.graph[current_to]`;
- upstream lanes are any edges ending at `current_from`;
- matching lane ID is preferred; when a connected segment has fewer lanes, lane 0 is used as fallback;
- `Landmark` objects are skipped, but `Obstacle` objects participate as non-landmark road objects;
- each connected lane's longitudinal coordinate is offset into the ego lane frame so vehicles near segment boundaries can be ordered correctly.

### Version mapping for registered environments

Legacy `*-v0` IDs preserve same-segment neighbour search. New connected-lane IDs enable connected-lane search by default through `ConnectedLaneNeighboursMixin`.

| Scenario | Legacy search | Connected-lane search |
|---|---|---|
| Exit | `exit-v0` | `exit-v1` |
| Merge | `merge-v0`, `merge-generic-v0` | `merge-v1`, `merge-generic-v1` |
| Roundabout | `roundabout-v0`, `roundabout-generic-v0` | `roundabout-v1`, `roundabout-generic-v1` |
| Racetrack | `racetrack-v0`, `racetrack-large-v0`, `racetrack-oval-v0` | `racetrack-v1`, `racetrack-large-v1`, `racetrack-oval-v1` |
| U-turn | `u-turn-v0` | `u-turn-v1` |
| Intersection | `intersection-v0`, `intersection-multi-agent-v0` | `intersection-v2`, `intersection-multi-agent-v2` |

`intersection-v1` and `intersection-multi-agent-v1` are not the connected-lane variants; they are separate continuous-action/multi-agent variants.

### Minimal connected-lane scenario

```python
net = RoadNetwork()
net.add_lane("a", "b", StraightLane([0, 0], [50, 0]))
net.add_lane("b", "c", StraightLane([50, 0], [100, 0]))
road = Road(network=net, np_random=np.random.RandomState(42), neighbour_vehicles_connected_lanes=True)

ego_lane = ("a", "b", 0)
front_lane = ("b", "c", 0)
ego = Vehicle.make_on_lane(road, ego_lane, longitudinal=48.0, speed=10.0)
front = Vehicle.make_on_lane(road, front_lane, longitudinal=5.0, speed=8.0)
road.vehicles.extend([ego, front])

front_found, rear_found = road.neighbour_vehicles(ego, ego_lane)
assert front_found is front
assert rear_found is None
```

If the same scenario sets `neighbour_vehicles_connected_lanes=False`, the next-segment `front` is not detected.

## Vehicles and controllers

### Base `Vehicle`

`Vehicle` implements the modified kinematic bicycle model. It stores `position`, `heading`, `speed`, `lane_index`, `lane`, `action`, `crashed`, and trajectory history. Use low-level action dictionaries:

```python
vehicle = Vehicle(road, position=[0, 0], heading=0.0, speed=20.0)
vehicle.act({"acceleration": 1.0, "steering": 0.0})
vehicle.step(1 / 15)
```

Useful constructors and helpers:

| API | Use |
|---|---|
| `Vehicle.create_random(road, speed=None, lane_from=None, lane_to=None, lane_id=None, spacing=1)` | Spawn a vehicle behind existing traffic with randomized speed/position constrained to a lane. |
| `Vehicle.make_on_lane(road, lane_index, longitudinal, speed=None)` | Inherited from `RoadObject`; place a vehicle exactly on a lane. |
| `Vehicle.create_from(other)` | Copy a vehicle's dynamic state into a fresh instance of the class. |
| `vehicle.lane_distance_to(other, lane=None)` | Signed distance to another object along a lane. |
| `vehicle.predict_trajectory(...)` | Simulate a copied vehicle through a sequence of low-level actions. |
| `vehicle.to_dict(origin_vehicle=None, observe_intentions=True)` | Convert state to feature dictionary used by observations. |

Low-level action keys are exactly `"acceleration"` and `"steering"`. `Vehicle.step(dt)` clips acceleration when speed exceeds `MIN_SPEED`/`MAX_SPEED`, updates lane membership from the road network, and applies collision impact when needed.

### `ControlledVehicle`

`ControlledVehicle` adds target speed/lane controllers. High-level actions are strings:

- `"FASTER"` / `"SLOWER"`: change `target_speed` by `DELTA_SPEED`.
- `"LANE_RIGHT"` / `"LANE_LEFT"`: select an adjacent lane if reachable.
- `None` or `"IDLE"`-like control loops: continue following `target_lane_index` and `target_speed`.

Important methods:

| API | Use |
|---|---|
| `plan_route_to(destination_node)` | Compute a route from the current lane's destination node to a target node. |
| `follow_road()` | At a lane end, switch `target_lane_index` using `RoadNetwork.next_lane`. |
| `steering_control(target_lane_index)` | Return a steering command for lane following. |
| `speed_control(target_speed)` | Return proportional acceleration command. |
| `get_routes_at_intersection()` | Enumerate possible routes at the next intersection. |
| `set_route_at_intersection(_to)` | Pick a route at the next intersection; `_to` may be an index or `"random"`. |
| `predict_trajectory_constant_speed(times)` | Predict positions/headings along the route using constant speed. |

For controlled ego vehicles inside environments, instantiate `self.action_type.vehicle_class`, not necessarily `ControlledVehicle` directly, because the configured action type may select `MDPVehicle` or a dynamics-aware class.

### `MDPVehicle`

`MDPVehicle` is a `ControlledVehicle` with discrete target speeds. It maps `"FASTER"` and `"SLOWER"` to indexes in `target_speeds` (default `np.linspace(20, 30, 3)`). Use `index_to_speed`, `speed_to_index`, and `get_speed_index` when reward code needs a normalized speed index.

### Behaviour vehicles

| Class | Use | Notes |
|---|---|---|
| `IDMVehicle` | Autonomous traffic with IDM longitudinal acceleration and MOBIL lane changes. | Uses `road.neighbour_vehicles(...)` for front/rear vehicles, so connected-lane settings affect behaviour near segment boundaries. `enable_lane_change=False` can freeze lane changes. |
| `LinearVehicle` | Linear approximation of longitudinal/lateral behaviour; can collect feature/output data. | Exposes `acceleration_features`, `steering_features`, `longitudinal_structure`, and `lateral_structure`. |
| `AggressiveVehicle` / `DefensiveVehicle` | Parameter variants of `LinearVehicle`. | Useful for traffic heterogeneity. |

Typical traffic creation:

```python
other_type = utils.class_from_path("highway_env.vehicle.behavior.IDMVehicle")
traffic = other_type.create_random(road, lane_from="a", lane_to="b", lane_id=0, spacing=1.0)
traffic.randomize_behavior()
road.vehicles.append(traffic)
```

### `BicycleVehicle`

`BicycleVehicle` uses a dynamic bicycle model with lateral speed and yaw rate, integrated with RK4. It is useful when continuous steering dynamics or tire/friction effects matter. It exposes `state`, `derivative`, `derivative_linear`, `lateral_lpv_structure`, `lateral_lpv_dynamics`, `full_lateral_lpv_structure`, and `full_lateral_lpv_dynamics`. Keep first checks short and deterministic because dynamics are more sensitive than the base kinematic `Vehicle`.

## Road objects: obstacles and landmarks

`RoadObject` provides the common rectangular collision interface. Vehicles inherit from it; `Obstacle` and `Landmark` are static subclasses.

| Class | Collision behaviour | Use |
|---|---|---|
| `Obstacle` | `solid=True`; a colliding vehicle and obstacle crash. | Walls, lane ends, blocked spots, hazards. |
| `Landmark` | `solid=False`; colliding vehicle does not crash, landmark `hit=True`. | Goals and target areas, especially goal-based parking scenarios. |

Objects are usually appended to `road.objects`:

```python
lane = road.network.get_lane(("a", "b", 0))
road.objects.append(Obstacle(road, lane.position(lane.length, 0)))
road.objects.append(Landmark(road, lane.position(lane.length / 2, 0)))
```

`Road.neighbour_vehicles` ignores `Landmark` objects but includes obstacles/vehicles when searching for front/rear objects. `Road.step(dt)` checks collisions between every pair of vehicles and between each vehicle and every object.

## Practical scenario-construction checklist

- Choose stable node names; avoid reusing one node name for unrelated geometry because route planning depends on graph connectivity.
- Add lanes in the intended lane-ID order; lane IDs are append indexes.
- Confirm each segment's lane count before relying on same-lane connected-neighbour matching.
- Set `forbidden=True` on lanes that should not be used for lane changes but may still be driven as route segments.
- Use `speed_limit` on lanes when random vehicle speed should be tied to road geometry.
- For intersections, set `priority` on lanes and use `RegulatedRoad` if right-of-way must affect vehicle decisions.
- Spawn ego vehicles before dense traffic when using random placement; then reject or remove near-colliding traffic.
- Keep `simulation_frequency` and `dt` consistent: `road.step(1 / simulation_frequency)` for lower-level loops.
- Validate connected-lane behaviour with a tiny two-segment fixture before scaling to merge/roundabout/racetrack geometry.
- For custom observations/actions/rewards, route to `../observations-actions-rewards/SKILL.md`; this reference only covers the road/vehicle mechanics those configs consume.

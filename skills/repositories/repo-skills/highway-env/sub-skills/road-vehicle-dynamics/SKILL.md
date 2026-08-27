---
name: road-vehicle-dynamics
description: "Use HighwayEnv road, lane, vehicle, object, and custom-environment
  APIs to build and troubleshoot lower-level driving scenarios."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Road vehicle dynamics sub-skill

Use this sub-skill when an agent needs to build or inspect HighwayEnv road networks, lanes, vehicles, road objects, connected-lane neighbour detection, controller/behaviour classes, or a custom environment class.

## Routing boundaries

- For high-level Gymnasium operation (`gym.make`, registration/import fixes, reset/step/render loops, vectorization, multi-agent wrappers, finite-MDP helpers), read `../simulation-environments/SKILL.md`.
- For observation/action/reward configuration details, spaces, `info["rewards"]`, goal observations, or action-space mismatches, read `../observations-actions-rewards/SKILL.md`.
- For RL training, evaluation rollouts, videos, optional Stable-Baselines3/Torch usage, or long-run safety limits, read `../training-and-evaluation/SKILL.md`.
- Use this sub-skill for lower-level scenario construction: road topology, lane geometry, object placement, vehicle dynamics/behaviour, custom environment internals, and connected-lane neighbour semantics.

## Runtime references and helper

- Read `references/road-vehicle-api.md` when constructing `RoadNetwork` graphs, converting lane coordinates, adding vehicles/objects, choosing vehicle classes, or diagnosing `Road.neighbour_vehicles` results across connected lane segments.
- Read `references/custom-environments.md` when implementing a new `AbstractEnv` subclass, overriding scene/reward/termination methods, registering an environment ID, or checking the custom-environment lifecycle.
- Read `references/troubleshooting.md` when vehicles spawn off-lane, lane indexes are wrong, neighbour detection misses vehicles near segment boundaries, controller actions do not change speed/lane, collisions behave unexpectedly, custom environments fail during reset/step, or interpolation/spline checks fail.
- Run `scripts/check_spline_interp.py` as a tiny deterministic smoke check for HighwayEnv's SciPy-free `numpy_interp1d` helper before relying on `PolyLane`/`LinearSpline2D` geometry in a custom scenario.

## Safe default workflow

1. Build a `RoadNetwork` first, using node names plus lane IDs as stable `LaneIndex` tuples such as `("a", "b", 0)`.
2. Verify each lane with `lane.position(longitudinal, lateral)`, `lane.local_coordinates(position)`, `lane.heading_at(longitudinal)`, and `lane.on_lane(position, ...)` before spawning vehicles.
3. Create a `Road(network=net, np_random=env.np_random, record_history=..., neighbour_vehicles_connected_lanes=...)`, then append vehicles to `road.vehicles` and obstacles/landmarks to `road.objects`.
4. Prefer `self.action_type.vehicle_class` for controlled ego vehicles inside custom environments; use `other_vehicles_type`/`utils.class_from_path(...)` only for non-controlled traffic.
5. If a scenario has several connected lane segments, set `neighbour_vehicles_connected_lanes=True` intentionally and document whether old `*-v0` legacy behaviour must be reproduced.
6. For custom environments, implement `default_config`, `_reset`, road creation, vehicle creation, `_reward`, optional `_rewards`, `_is_terminated`, and `_is_truncated`; then run one bounded reset/step smoke test.

## Handoff contract

A successful use of this sub-skill should produce one or more of:

- a self-contained road-network and vehicle/object construction snippet;
- an explanation of which lane indexes, longitudinal coordinates, and connected-lane neighbour settings drive the scenario;
- a custom environment skeleton with registration and bounded smoke-test guidance;
- a route to another sub-skill if the blocker is Gymnasium operation, observation/action/reward configuration, or RL training rather than road/vehicle dynamics.

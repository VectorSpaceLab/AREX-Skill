# HighwayEnv environment catalog

HighwayEnv registers built-in Gymnasium environments when `highway_env` is imported. Use this catalog to choose a scenario family before routing into the simulation, configuration, dynamics, or training sub-skills.

## Scenario families

| Family | Primary env IDs | Typical action style | Use when the task needs |
| --- | --- | --- | --- |
| Highway | `highway-v0`, `highway-fast-v0` | Discrete meta-actions | Multilane driving, speed/lane trade-offs, fast DQN/PPO smoke tasks. |
| Merge | `merge-v0`, `merge-v1`, `merge-generic-v0`, `merge-generic-v1` | Discrete meta-actions | Highway merging and connected-lane merge variants. |
| Roundabout | `roundabout-v0`, `roundabout-v1`, `roundabout-generic-v0`, `roundabout-generic-v1` | Discrete meta-actions | Roundabout navigation with merging/exiting traffic. |
| Parking | `parking-v0`, `parking-ActionRepeat-v0`, `parking-parked-v0` | Continuous actions | Goal-conditioned parking, HER-style tasks, collision/success signals. |
| Intersection | `intersection-v0`, `intersection-v1`, `intersection-v2` | Discrete or continuous depending version | Crossing an unsignalized intersection; `intersection-v1` is continuous-control and `intersection-v2` uses connected-lane neighbour search. |
| Multi-agent intersection | `intersection-multi-agent-v0`, `intersection-multi-agent-v1`, `intersection-multi-agent-v2` | Multi-agent wrapper/action tuple | Multiple controlled vehicles with tuple observations/actions/rewards. |
| Racetrack | `racetrack-v0`, `racetrack-v1`, `racetrack-large-v0`, `racetrack-large-v1`, `racetrack-oval-v0`, `racetrack-oval-v1` | Continuous actions | Continuous-control racetrack following, large/oval variants. |
| Lane keeping | `lane-keeping-v0` | Continuous actions | Bicycle-dynamics lane following on a sine-wave lane. |
| Two-way | `two-way-v0` | Discrete meta-actions | Overtaking and risk management with oncoming traffic. |
| Exit | `exit-v0`, `exit-v1` | Discrete meta-actions | Navigating across lanes to an exit ramp; `v1` uses connected-lane neighbour search. |
| U-turn | `u-turn-v0`, `u-turn-v1` | Discrete meta-actions | Overtaking blocking vehicles in a U-turn; `v1` uses connected-lane neighbour search. |

## Version suffixes and connected-lane variants

Several families have legacy `v0` IDs and newer connected-lane variants. Connected-lane variants enable `neighbour_vehicles_connected_lanes`, so neighbour detection can include adjacent connected segments instead of only the current road segment.

Known version pairs:

- `exit-v0` → `exit-v1`
- `merge-v0` → `merge-v1`
- `merge-generic-v0` → `merge-generic-v1`
- `roundabout-v0` → `roundabout-v1`
- `roundabout-generic-v0` → `roundabout-generic-v1`
- `racetrack-v0` → `racetrack-v1`
- `racetrack-large-v0` → `racetrack-large-v1`
- `racetrack-oval-v0` → `racetrack-oval-v1`
- `u-turn-v0` → `u-turn-v1`
- `intersection-v0` → `intersection-v2`
- `intersection-multi-agent-v0` → `intersection-multi-agent-v2`

Use legacy IDs when reproducing old baselines. Prefer connected-lane IDs for new tasks whose lane-neighbour semantics near intersections or connected road segments matter.

## Common configuration keys

Many environments inherit these cross-cutting keys from the abstract environment:

- `observation`: nested observation config, default `{"type": "Kinematics"}` for many environments;
- `action`: nested action config, often `DiscreteMetaAction` or `ContinuousAction` depending scenario;
- `simulation_frequency`: low-level vehicle simulation frequency;
- `policy_frequency`: agent decision frequency;
- `duration`: maximum task duration in seconds when the environment implements an internal truncation;
- `screen_width`, `screen_height`, `scaling`, `centering_position`: rendering geometry;
- `show_trajectories`: record recent vehicle history for display;
- `manual_control`, `real_time_rendering`: interactive local-viewing options;
- `neighbour_vehicles_connected_lanes`: connected-segment neighbour search toggle.

Environment-specific keys include lane counts, vehicle counts/densities, reward weights, speed ranges, parking goal weights, and scenario geometry choices. Use the observations/actions/rewards sub-skill for config-space details and the road/vehicle sub-skill for custom geometry.

## Quick selection guide

- Need a fast discrete-action smoke or training target: start with `highway-fast-v0`.
- Need goal-conditioned continuous control: start with `parking-v0`.
- Need a continuous-control road-following benchmark: start with `racetrack-v0`, `racetrack-oval-v0`, or `lane-keeping-v0`.
- Need multi-agent tuple semantics: start with `intersection-multi-agent-v1` or `intersection-multi-agent-v2`.
- Need connected-lane neighbour behavior near segment joins: prefer `v1`/`v2` connected variants.
- Need old-baseline compatibility: keep the documented legacy ID and record the version choice.

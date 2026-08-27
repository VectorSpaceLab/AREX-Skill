# Traffic-agent policies

Traffic policy changes the environment in which the same ego trajectory is
scored. Record it with the experiment name and do not compare CSVs as if policy
were a harmless implementation detail.

## Policy choices

| Policy | Reactive? | Simulated objects | Use |
|---|---|---|---|
| Log replay (`non_reactive`) | No | Replays cached detections for the horizon | NAVSIM v1-like and controlled comparisons |
| Constant velocity | No | Current vehicles extrapolated with constant velocity/heading | Debugging only |
| NAVSIM IDM (`reactive`) | Yes for vehicles | Vehicles respond to simulated ego and map; non-vehicles remain log based | NAVSIM v2 two-stage behavior and reactive experiments |

The ego planner is always non-reactive: it commits one plan for the horizon and
is not called again after simulated observations. “Reactive traffic” means
background vehicles react to the simulated ego, not that the planner closes the
loop.

## One-stage selection

The one-stage runner chooses between the configured `non_reactive` and
`reactive` policy with the `traffic_agents` override:

```bash
python -m navsim.planning.script.run_pdm_score_one_stage \
  train_test_split=navtest \
  agent=constant_velocity_agent \
  traffic_agents=non_reactive \
  experiment_name=cv-log-replay \
  metric_cache_path="$NAVSIM_EXP_ROOT/metric_cache"
```

For a reactive run, change only the policy override after recording the
comparison intent:

```bash
python -m navsim.planning.script.run_pdm_score_one_stage \
  train_test_split=navtest \
  agent=constant_velocity_agent \
  traffic_agents=reactive \
  experiment_name=cv-idm \
  metric_cache_path="$NAVSIM_EXP_ROOT/metric_cache"
```

The default common setting is `traffic_agents: non_reactive`. The constant
velocity traffic class is not the default and is intended for debugging; use it
only with an explicit policy configuration and label.

## Two-stage selection

The standard two-stage runner and submission scorer instantiate the reactive
policy for both stage one and stage two. Do not assume that adding
`traffic_agents=non_reactive` to a two-stage command changes the implementation;
verify the runner/config combination before using it for a comparison. If a
custom two-stage configuration intentionally changes this behavior, document
that deviation and treat scores as a separate protocol.

## IDM-specific prerequisites

Reactive IDM needs the map API, current vehicle tracks, interpolated future
tracks, and a valid simulated ego state at each step. Its configuration
includes target velocity, minimum gap, headway, acceleration/deceleration
limits, map radius, open-loop object types, and a snap threshold. The default
configuration simulates vehicles within a 100 m radius. Non-vehicle objects,
parked objects, pedestrians, and static objects not handled by IDM continue to
use log/replayed data according to the policy implementation.

IDM state is copied per simulation. If it appears to leak between proposals,
stop and investigate policy construction or a custom policy rather than
reusing a mutable policy object across worker tasks.

## Interpretation rules

- Log replay is the correct baseline for a v1-like non-reactive comparison.
- Reactive IDM can change collision/TTC/comfort outcomes even with identical
  ego poses; compare only runs with the same map, cache, split, and sampling.
- Constant velocity is useful for a synthetic sanity check but is not a
  realistic leaderboard protocol.
- A policy failure is an invalid evaluation, not evidence that the planner
  trajectory is safe. See [troubleshooting](troubleshooting.md).

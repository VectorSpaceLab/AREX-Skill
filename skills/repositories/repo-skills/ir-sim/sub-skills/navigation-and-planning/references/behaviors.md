# Individual behaviors and line obstacles

## Install and dispatch

The base distribution is `ir-sim` 2.10.2 and requires Python `>=3.10`. The
runtime dependencies include NumPy, SciPy, Shapely, Matplotlib, PyYAML,
ImageIO, and Loguru:

```bash
python -m pip install ir-sim
python - <<'PY'
import irsim
import irsim.lib.behavior.behavior_methods  # registers built-ins
from irsim.lib.behavior.behavior_registry import behaviors_map
print(irsim.__version__)
print(sorted(behaviors_map))
PY
```

`irsim.make(scene, display=False, save_ani=False, disable_all_plot=True,
seed=...)` loads a scene. `Behavior.gen_vel(ego_object,
external_objects=None)` dispatches an individual behavior by the pair
`(kinematics, behavior.name)`. The registry is populated by importing the
built-in behavior methods; users normally do not call the dispatcher directly.

A missing behavior is not silently converted to a different algorithm. The
supported built-in matrix is:

| Kinematics | Individual behavior values |
| --- | --- |
| `diff` | `dash`, `rvo`, `sfm` |
| `omni` | `dash`, `rvo`, `sfm` |
| `omni_angular` | `dash` |
| `acker` | `dash` |

Thus `acker+rvo`, `acker+sfm`, `omni_angular+rvo`, and
`omni_angular+sfm` are unsupported built-in pairs. The missing pair is not
adapted automatically: when the behavior is dispatched, the registry raises a
lookup error. Use the extension route for a custom pair rather than changing
the YAML name and hoping it is adapted.

A robot without a behavior is static unless an external action is supplied.
All built-ins return a zero action while the goal is `None`. `target_roles` can
be `all`, `robot`, or `obstacle` and filters the external objects passed to an
individual behavior. `wander`, `loop`, and their range fields control goal
renewal/waypoint cycling in the object lifecycle; they do not change the
avoidance algorithm.

## Dash

Use:

```yaml
behavior: {name: dash, angle_tolerance: 0.1}
```

`diff` and `acker` receive a two-component command (forward/linear and
angular or steering); `omni` receives `[vx, vy]`; `omni_angular` receives
`[forward, lateral, yaw_rate]`. The command is clipped to the object's velocity
range. `angle_tolerance` is the angular alignment tolerance for `diff`/`acker`
(and is accepted by the omni-angular implementation). Dash does not inspect
neighbors or linestring obstacles.

## RVO, VO, and HRVO

Use the same behavior name and select the algorithm mode:

```yaml
behavior:
  name: rvo
  mode: rvo                 # rvo, hrvo, or vo
  vxmax: 1.5
  vymax: 1.5
  acce: 1.0
  factor: 1.0
  neighbor_threshold: 3.0
```

The behavior methods use `vxmax=1.5`, `vymax=1.5`, `acce=1.0`, `factor=1.0`,
and `neighbor_threshold=3.0` when these fields are absent. `mode` is passed to
`reciprocal_vel_obs.cal_vel(mode)`, whose accepted values are exactly
`rvo`, `hrvo`, and `vo`; an invalid value logs an error and is not a supported
configuration. `factor` weights the fallback penalty when every sampled
velocity is inside a velocity obstacle. `acce` limits the reachable velocity
sample around the current velocity, while `vxmax`/`vymax` bound the sampled
components. A larger neighbor threshold considers more objects but costs more
and can make a crowded scene more conservative.

RVO is local and reactive. It receives circular neighbors as states
`[x, y, vx, vy, radius]` and separates linestrings into line segments. It does
not replace a global map planner. The `diff` adapter converts the selected
holonomic velocity to `[linear, angular]`; a goal behind a diff robot has a
special rotate-in-place fallback only when no neighbor/line obstacle is
present. `omni` receives the selected world-frame pair directly.

The standalone live constructor is:

```python
from irsim.lib.algorithm.rvo import reciprocal_vel_obs

solver = reciprocal_vel_obs(
    state, obs_state_list=[], vxmax=1.5, vymax=1.5,
    acce=0.5, factor=1.0, line_obs_list=[]
)
velocity_xy = solver.cal_vel("rvo")
solver.update(state, obs_state_list, line_obs_list)
```

The standalone constructor's `acce` default is `0.5`; the registered behavior
passes its own behavior default of `1.0`. Do not conflate those two surfaces.

## SFM

Use SFM for reactive, anisotropic, pedestrian-like motion:

```yaml
behavior:
  name: sfm
  vmax: 1.0
  neighbor_threshold: 5.0
  relaxation_time: 0.5
  force_factor_desired: 1.0
  force_factor_social: 2.1
  force_factor_obstacle: 10.0
  sigma_obstacle: 0.8
  lambda_importance: 2.0
  gamma: 0.35
  n_angular: 2.0
  n_velocity: 3.0
  safety_radius: 0.05
```

The registered SFM defaults are `vmax=1.5`, `step_time` from the world,
`neighbor_threshold=10.0`, `relaxation_time=0.5`, desired/social/obstacle
force weights `1.0/2.1/10.0`, `sigma_obstacle=0.8`,
`lambda_importance=2.0`, `gamma=0.35`, `n_angular=2.0`, `n_velocity=3.0`, and
`safety_radius=0.0`.

Interpret the main controls as follows:

- `force_factor_desired` pulls velocity toward the goal; increasing it makes
  goal tracking dominate.
- `force_factor_social` increases anisotropic neighbor repulsion. Front and
  side interactions need not match because the implementation uses the
  Moussaid-Helbing velocity-aware interaction direction.
- `force_factor_obstacle` and `sigma_obstacle` increase wall repulsion and its
  decay range. The implementation sums nearby line-segment forces within
  `5*sigma_obstacle + robot_radius`.
- `relaxation_time` is the desired-velocity time constant: smaller values
  react faster. It must be positive.
- `lambda_importance` weights relative velocity in the interaction direction;
  `gamma` sets `B = gamma * ||t||` and must be positive.
- `n_angular` and `n_velocity` sharpen lateral and velocity-dependent angular
  effects. `neighbor_threshold` filters neighbors before the solver and is
  also the solver's interaction range.
- `safety_radius` shifts the social-force decay inward to model personal
  space; it is not a collision checker or a substitute for robot geometry.

The live algorithm surface is:

```python
from irsim.lib.algorithm.social_force_model import social_force_model

solver = social_force_model(
    state=[x, y, vx, vy, radius, vx_des, vy_des, theta],
    neighbor_list=[[x2, y2, vx2, vy2, radius2]],
    line_obs_list=[[x1, y1, x2, y2]],
    vmax=1.5,
    step_time=0.1,
)
new_vx, new_vy = solver.cal_vel()
solver.update(state, neighbor_list, line_obs_list)
```

`relaxation_time`, `gamma`, and `sigma_obstacle` reject non-positive values.
The `diff` behavior maps SFM's world-frame `[vx, vy]` back to a differential
command; the `omni` behavior returns the pair directly. SFM is behavioral and
reactive: it can produce more human-looking brush-bys or hesitations and must
not be described as a formal collision-free guarantee. Prefer RVO/ORCA when
collision avoidance under their assumptions is the priority.

## Linestring obstacles

Configure a polyline obstacle with vertices. Each consecutive pair becomes a
line segment in `ObjectBase.rvo_line_segments`:

```yaml
obstacle:
  - shape:
      name: linestring
      vertices: [[-4, 2], [0, 2], [0, 5]]
    state: [0, 0, 0]
    unobstructed: true
```

For RVO and SFM, line objects are collected separately from circular neighbor
states. A two-vertex line therefore produces one segment and a three-vertex
polyline produces two. Zero-length segments are ignored by the RVO cone
builder. Non-linestring obstacles continue through the circular-neighbor path.
Use a sufficiently detailed polyline for corners; local avoidance does not
create a route around a wall that fully encloses the goal.

`unobstructed` and `world.collision_mode` affect collision/status handling, but
they do not turn a linestring into a global planner. Keep the obstacle geometry,
robot footprint, and kinematics consistent; see
[scene-configuration](../../scene-configuration/SKILL.md). For map-based
planning, see [path-planners.md](path-planners.md) and
[sensing-and-mapping](../../sensing-and-mapping/SKILL.md).

## Individual versus group behavior

`behavior` is evaluated per object. `group_behavior` is evaluated once for an
`ObjectGroup`, and its returned actions are aligned with group members. The
built-in group registry contains `orca` for `omni` and `diff`; ORCA's optional
runtime gate is documented separately in [optional-orca.md](optional-orca.md).
Do not use `group_behavior: {name: rvo}` as a substitute for individual RVO.

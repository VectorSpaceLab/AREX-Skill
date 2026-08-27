# YAML scene schema

`EnvConfig` parses a YAML mapping with at most four root keys: `world`,
`robot`, `obstacle`, and `gui`. A misspelled root key raises `KeyError` with a
suggestion. Nested world/object keys are passed to `World`/`ObjectBase`; those
classes warn about unknown keyword arguments rather than consistently raising,
so use the bundled checker to make typos fail before construction.

The checker is intentionally a portable subset: it validates structure,
component names, dimensions, and the difficult list/shape cases. It does not
load image maps, import custom registries, or prove that footprints are
collision-free.

## World mapping

| Key | Meaning and constraints |
|---|---|
| `name` | Label; default `world`. |
| `height`, `width` | Positive extents; defaults `10`. Coordinates span `offset` to `offset + extent`. |
| `step_time` | Positive simulation interval; default `0.1`. |
| `sample_time` | Positive plotting/sample interval; defaults to `step_time`. |
| `offset` | Two-number `[x, y]` origin offset; default `[0, 0]`. |
| `step_mode` | `internal` (IR-SIM advances objects) or `external` (caller owns state); default `internal`. |
| `control_mode` | `auto` or `keyboard`; default `auto`. Keyboard is interactive/optional. |
| `collision_mode` | `stop`, `reactive`, `unobstructed`, or `unobstructed_obstacles`; default `stop`. In this release `reactive` follows the unobstructed branch rather than running a distinct controller. |
| `status` | Initial display label only; it does not pause execution. |
| `obstacle_map` | `null`, a caller-relative image path, a programmatic ndarray, or a generator mapping with `name`; map details belong to [sensing and mapping](../../sensing-and-mapping/SKILL.md). |
| `mdownsample` | Positive integer map stride; default `1`. |
| `fog_map`, `fog_map_resolution` | Optional fog overlay and positive cell size; map/sensor behavior is in the sensing sub-skill. |
| `plot` | Matplotlib world options such as `saved_figure`, `figure_pixels`, `show_title`, `title`, `no_axis`, `tight`, and `viewpoint`. Rendering belongs to [simulation environments](../../simulation-environments/SKILL.md). |

A portable world-only fragment is:

```yaml
world:
  width: 10
  height: 8
  offset: [0, 0]
  step_time: 0.1
  step_mode: internal
  collision_mode: stop
```

`obstacle_map` image paths are resolved by the caller's environment, not
relative to this skill. Do not put a source-checkout path in a reusable scene.

## Robot and obstacle groups

`robot` and `obstacle` may be one mapping or a list of mappings. Each mapping is
an object group. `number` defaults to `1`; objects are expanded by
`ObjectFactory.create_object`. The same object keys are available in both
sections; the section supplies the role. Do not add `role` in YAML.

Common keys:

| Key | Meaning and constraints |
|---|---|
| `name` | Optional object identifier. Omitted names become `<role>_<id>`. Explicit names must be unique across robots and obstacles. For `number > 1`, use a list of exactly `number` names. |
| `number` | Positive integer count. |
| `distribution` | `{name: manual}`, `{name: random, ...}`, or `{name: circle, ...}`; see [distributions](distributions-and-randomness.md). `uniform` and `3d: true` are not implemented. |
| `shape` | One shape mapping, or exactly `number` shape mappings for a heterogeneous group. See [geometry](geometry-and-kinematics.md). Omitting it invokes the runtime's radius-1 fallback; `{name: circle}` has radius `0.2`, so be explicit. |
| `kinematics` | One mapping or exactly `number` mappings. Supported names are `diff`, `omni`, `omni_angular`, and `acker`; absent kinematics makes the object static. |
| `state` | Initial pose, normally `[x, y, theta]`; Ackermann objects use a four-row state and pad a three-entry input with zero steer. The factory's random/circle distributions generate three-entry poses. |
| `velocity` | Initial control-space vector; dimensions are 2 for `diff`, `omni`, and `acker`, and 3 for `omni_angular`. |
| `goal` | One goal vector, or a per-object list. The object API supports sequential goal vectors; YAML nesting is easy to confuse with a per-object list, so use the explicit extra outer list shown below for one object with waypoints. `goal: null` is not a clear-goal escape through the YAML factory: `ObjectFactory` substitutes its manual default; clear goals with `obj.set_goal(None)`. |
| `vel_min`, `vel_max` | Absolute control limits with the selected action dimension. |
| `acce` | Per-control acceleration limit; `[inf, ...]` is the default. |
| `angle_range` | Two-number orientation interval, normally `[-pi, pi]`. |
| `goal_threshold` | Positive arrival distance; default `0.1`. |
| `arrive_mode` | `position` compares `x,y`; `state` compares the first three state components. |
| `behavior` | Per-object behavior mapping; built-in compatibility is in [navigation](../../navigation-and-planning/SKILL.md). |
| `group_behavior` | Group-level mapping, currently `orca` and optional `pyrvo`; route to navigation. |
| `static` | `true` freezes an object even when kinematics exist. No kinematics also forces static behavior. |
| `group`, `group_name` | Integer group id and optional label. `group_name` defaults to `<role>_<group>` and is used by group queries. |
| `unobstructed` | Per-object collision-stopping exemption; it does not delete geometry. |
| `state_dim`, `vel_dim` | Advanced overrides. Do not use them to hide a wrong vector dimension. |
| `sensors` | Sensor mapping list; contract belongs to [sensing and mapping](../../sensing-and-mapping/SKILL.md). |
| `fov`, `fov_radius` | Optional non-LiDAR field-of-view detection values; sensor/map details belong to sensing. |
| `color`, `description`, `plot` | Visualization/description options; `plot` details belong to simulation. |

### Per-object list rules

Flat numeric vectors are shared values, while nested numeric vectors are
per-object values. A mapping is shared; a list of mappings is expanded per
object. The runtime compatibility helpers repeat the final item when a list is
short and truncate when it is long. The bundled checker rejects those ambiguous
lengths for names, kinematics, state/goal/control vectors, shapes, behaviors,
and sensors.

For example:

```yaml
robot:
  - number: 2
    name: [r0, r1]
    distribution: {name: manual}
    kinematics: {name: diff}
    shape: {name: circle, radius: 0.25}
    state: [[1, 1, 0], [1, 3, 0]]
    goal: [[8, 7, 0], [8, 5, 0]]
    velocity: [0, 0]
    behavior: {name: dash}
```

For one object with sequential waypoints, preserve the per-object wrapper that
the factory expects:

```yaml
robot:
  - number: 1
    kinematics: {name: diff}
    shape: {name: circle, radius: 0.25}
    state: [1, 1, 0]
    goal:
      - [[3, 1, 0], [3, 4, 1.57], [7, 4, 0]]
    behavior: {name: dash, loop: true}
```

If a program constructs an object directly, `obj.set_goal([[...], [...]])`
expresses sequential goals without the YAML factory layer.

## Kinematics and behavior compatibility

| `kinematics.name` | State model | Control/velocity vector | Built-in `behavior.name` |
|---|---|---|---|
| `diff` | `[x, y, theta]` | `[linear, angular]` | `dash`, `rvo`, `sfm` |
| `omni` | `[x, y, theta]`; theta is preserved | body-frame `[forward, lateral]` | `dash`, `rvo`, `sfm` |
| `omni_angular` | `[x, y, theta]` | body-frame `[forward, lateral, yaw_rate]` | `dash` |
| `acker` | `[x, y, theta, steer]` | `[linear, steer]` in `steer` mode or `[linear, angular]` in `angular` mode | `dash` |

`noise: true` enables motion noise. `alpha` is passed to the selected
kinematics implementation; keep it model-appropriate and leave noise off for a
deterministic preflight. A `kinematics` mapping may contain `name`, `noise`,
`alpha`, and for Ackermann `mode: steer|angular`. The live
`KinematicsFactory` also accepts `wheelbase` programmatically, but do not put
`wheelbase` in YAML `kinematics`: `ObjectBase` obtains it from the shape and
passes its own value to the factory. Put an explicit positive wheelbase under
a circle or rectangle `shape` for Ackermann.

An object with no `behavior` is expected to stay still when `env.step()` has no
external action. A behavior is not a shape selector; route behavior parameters
to [navigation](../../navigation-and-planning/SKILL.md).

## GUI mapping

`gui` is optional and has `keyboard` and `mouse` mappings. Keyboard accepts
`backend: pynput|mpl`, `global_hook`, `key_lv_max`, `key_ang_max`, `key_lv`,
`key_ang`, `key_rot`, and `key_id`; mouse accepts `zoom_factor`. `pynput` is
optional and falls back to Matplotlib when unavailable. Use `display=False` and
avoid live input for batch checks.

## Object API examples

```python
obj.state          # NumPy column vector
obj.velocity       # current control-space column vector
obj.goal           # current goal as a column vector, or None
obj.geometry       # transformed Shapely geometry
obj.get_info()     # ObjectInfo snapshot for behaviors/planners
obj.get_obstacle_info()  # center, vertices, velocity, radius, G/h metadata
obj.set_state([2, 2, 0])
obj.set_velocity([0.5, 0.0])
obj.set_goal([8, 8, 0], init=True)
```

`set_state` updates the object's transformed geometry; `set_velocity` only
updates stored control input; `set_goal` accepts one vector, a sequence, or
`None` when called directly. `init=True` changes the corresponding reset
snapshot. Call the environment refresh/spatial-index path after direct mutation
when collision or sensing consumers need a synchronized scene.

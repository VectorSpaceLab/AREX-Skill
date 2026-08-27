# Geometry and kinematics

IR-SIM constructs an object through `ObjectFactory`, `GeometryFactory`, and
`KinematicsFactory`. A 2D geometry is a Shapely object in the body frame;
`geometry_handler.step(state)` applies the `[x, y, theta]` transform. Collision
checks use the transformed geometry, not only a radius approximation.

The live public signatures relevant to this route are:

```python
irsim.make(world_name=None, projection=None, step_mode=None, **kwargs)
ObjectFactory.create_object(obj_type="robot", number=1, distribution=None,
                            state=None, goal=None, **kwargs)
ObjectFactory.create_robot(kinematics=None, **kwargs)
ObjectFactory.create_obstacle(kinematics=None, **kwargs)
ObjectFactory.generate_state_list(number=1, distribution=None,
                                  state=None, goal=None)
GeometryFactory.create_geometry(name="circle", **kwargs)
KinematicsFactory.create_kinematics(name=None, noise=False, alpha=None,
                                    mode="steer", wheelbase=None, role="robot")
ObjectBase.set_state(state=None, init=False)
ObjectBase.set_velocity(velocity=None, init=False)
ObjectBase.set_goal(goal=None, init=False)
ObjectBase.get_info()
ObjectBase.get_obstacle_info()
ObjectBase.check_collision(obj)
```

## Shapes and exact collision geometry

| Shape | Configuration | Runtime geometry and caveat |
|---|---|---|
| `circle` | `radius` (default `0.2` when the mapping is explicit), optional body-frame `center`, `random_shape`, `radius_range` | A buffered point. A body-frame center rotates with heading. For Ackermann, the circle center is additionally shifted by `wheelbase / 2`. |
| `rectangle` | `length` and `width` (defaults `1.0`), optional `wheelbase` | A four-vertex polygon. With wheelbase, the x coordinates are shifted so the body is aligned to the rear axle. |
| `polygon` | explicit `vertices: [[x,y], ...]`, or random-generation parameters | A Shapely polygon. Invalid polygons are repaired by the runtime; for safety-critical footprints, use a simple ordered boundary and inspect validity. |
| `compound` | non-empty `parts` list of circle/rectangle/polygon mappings; optional part `pose: [x,y,theta]` | A union of rigid part geometries. Overlapping parts are unioned; disjoint parts form a `MultiPolygon`. Parts cannot be linestrings or carry individual colors. |
| `linestring` | `vertices: [[x,y], ...]`, or random-generation parameters | An exact Shapely line, not a filled wall. Consecutive segments are exposed to RVO line-obstacle handling. |

A missing top-level `shape` has a different default from an explicit circle:
`ObjectBase` creates a radius-1 circle when shape is omitted, while
`{name: circle}` uses the geometry handler's radius-0.2 default. Always write
shape explicitly in reproducible scenes.

Compound details:

- Each part's pose is fixed in the owning object's body frame. The owning state
  transforms the whole union and all `part_vertices` together.
- `obj.vertices` and `obj.original_vertices` are `None` for a compound; use
  `obj.part_vertices` or `obj.original_part_vertices` for per-part boundaries.
- The exact union is used for `obj.check_collision(other)`, so a body in the
  empty gap between two disjoint parts does not collide with the compound.
- Circle and convex polygon/rectangle handlers can expose a convex `G, h`
  representation. Compound and linestring handlers do not provide one. The
  geometry handler's `get_init_Gh()` and `get_Gh()` return four values:
  `(G, h, cone_type, convex_flag)`; unavailable representations are `None`.

## Kinematics matrix

| Name | Natural state rows | Action rows | Meaning |
|---|---:|---:|---|
| `diff` | 3 | 2 | `[linear, angular]`; integrates theta and can rotate in place. |
| `omni` | 3 | 2 | Body-frame `[forward, lateral]`; translates after body-to-world rotation and preserves theta. |
| `omni_angular` | 3 | 3 | Body-frame `[forward, lateral, yaw_rate]`; translates and integrates yaw. |
| `acker` | 4 | 2 | `[linear, steer]` for `mode: steer`, or `[linear, angular]` for `mode: angular`; stores steering in state row four. |

`velocity`, `vel_min`, `vel_max`, and `acce` are control-space vectors, not
state vectors. Use exact lengths: 2 for `diff`, `omni`, and `acker`; 3 for
`omni_angular`. `ObjectBase` pads or truncates an initial state to its selected
state dimension, but explicit natural dimensions avoid silent changes. A wrong
control vector can fail in `set_velocity` or kinematics stepping; the bundled
checker rejects it before construction.

`KinematicsFactory.create_kinematics` lowercases registered lookup names. Its
built-ins report these defaults:

- `diff`, `omni`, and `acker`: `vel_min=[-1,-1]`, `vel_max=[1,1]`,
  `acce=[inf,inf]`.
- `omni_angular`: `vel_min=[-1,-1,-1]`, `vel_max=[1,1,1]`,
  `acce=[inf,inf,inf]`.

The factory itself falls back to a differential handler when a name is absent or
unknown, but `ObjectFactory.create_robot/create_obstacle` checks the registry
and raises `NotImplementedError` for an unsupported named kinematics. Treat
unknown names as configuration errors rather than relying on the fallback.

Ackermann is the main geometry/kinematics coupling:

```yaml
kinematics: {name: acker, mode: steer}
shape: {name: rectangle, length: 2.0, width: 0.8, wheelbase: 1.4}
state: [1.0, 1.0, 0.0, 0.0]
velocity: [0.5, 0.0]
```

The live factory defaults a missing Ackermann wheelbase to `1.0`, but the
shape handler cannot align the footprint without an explicit shape wheelbase.
The checker therefore rejects missing/non-positive wheelbase on Ackermann
circle/rectangle shapes. This is deliberate: it catches a physically ambiguous
scene rather than hiding the runtime fallback.

## Limits, angles, arrival, and state API

`vel_min`/`vel_max` clip requested controls. `acce` limits the change per step;
`get_vel_range()` intersects absolute limits with current velocity plus or
minus `acce * world.step_time`. `angle_range` is a two-pi region used to wrap
orientation.

`goal` can be a single vector or a sequence of waypoints when set through the
object API. `obj.goal` returns the current goal as a NumPy column vector (or
`None`). When the current goal is reached, `check_arrive_status()` dequeues the
next waypoint; `obj.arrive` and `obj.collision` expose boolean flags.

- `arrive_mode: position` compares `state[:2]` and `goal[:2]`.
- `arrive_mode: state` compares the first three state components.
- `goal_threshold` defaults to `0.1` and uses a strict less-than comparison.
- `obj.set_state(value, init=True)` changes both current and reset state;
  without `init`, it changes only current state and refreshes object geometry.
- `obj.set_velocity(value, init=True)` follows the same reset convention but
  does not advance the object.
- `obj.set_goal(value, init=True)` accepts one vector, a list of vectors, a
  deque, or `None`; `init=True` changes the reset goal snapshot.
- `obj.reset()` restores the state, velocity, and goal snapshots. It does not
  rebuild the environment spatial tree by itself; use the environment reset or
  refresh path for synchronized collision/sensor data.

Useful read-only surfaces include `state`, `init_state`, `velocity`, `goal`,
`position`, `geometry`, `shape`, `kinematics`, `radius`, `length`, `width`,
`wheelbase`, `vertices`, `original_vertices`, and compound part vertices.
`get_info()` returns an `ObjectInfo` snapshot containing identity, role,
limits, goal threshold, wheelbase, and convex-geometry metadata. It is not a
live replacement for state/velocity. `get_obstacle_info()` returns center,
vertices, velocity, radius, and `G/h` metadata for collision-aware consumers.

## Collision policy

The default world `collision_mode` is `stop`. During status checking, exact
Shapely intersections populate `obj.collision_obj` and `obj.collision`; in
stop mode, colliding objects stop unless the relevant object is marked
`unobstructed`.

- `unobstructed`: skip collision stopping globally.
- `unobstructed_obstacles`: obstacle-obstacle contacts do not stop obstacles;
  robot contacts remain relevant.
- `reactive`: this release currently follows the unobstructed branch; it is not
  a separate reactive controller.
- `unobstructed: true` is an object-level stopping exemption. It does not
  remove the object's Shapely geometry from queries or sensors.

Check initial transformed geometries before stepping. An initial overlap can
set collision immediately and make a behavior look broken. For navigation
behavior choice and line-obstacle semantics, follow
[the navigation sub-skill](../../navigation-and-planning/SKILL.md).

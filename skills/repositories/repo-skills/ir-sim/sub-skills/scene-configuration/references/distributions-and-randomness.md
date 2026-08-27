# Distributions and reproducibility

`ObjectFactory.create_object()` calls `generate_state_list()` before creating
objects. It produces one initial state and one goal per expanded object, then
uses `convert_list_length`/`convert_list_length_dict` to broadcast shape,
behavior, color, sensor, and other configuration values. The runtime repeats
the final list item when a list is short; the bundled checker rejects ambiguous
per-object lengths so experiments remain explicit.

## `manual`

`manual` is the default. Give a flat vector to share it across a group, or a
nested vector list with exactly one entry per object:

```yaml
robot:
  - number: 2
    distribution: {name: manual}
    name: [r0, r1]
    state: [[1, 1, 0], [2, 1, 0]]
    goal: [[8, 8, 0], [8, 2, 0]]
```

A flat numeric `state`/`goal` is interpreted as one vector and is broadcast.
An object-level `goal` sequence is a separate concept: one object may have
sequential waypoints when the YAML nesting makes the extra object wrapper
unambiguous, or by calling `obj.set_goal([[...], [...]])` directly.

## `random`

```yaml
obstacle:
  - number: 3
    distribution:
      name: random
      range_low: [1, 1, -3.141592653589793]
      range_high: [9, 7, 3.141592653589793]
      min_distance: 1.0
    shape: {name: circle, radius: 0.3}
```

`range_low` and `range_high` are three-entry `[x, y, theta]` bounds. If
omitted, the factory derives them from the attached world: each xy bound is
inset by `0.5` from `offset`/`offset + extent`, and theta is `[-pi, pi]`.
`min_distance` defaults to `1.0` and is applied to xy points. States and goals
are sampled independently, so a random goal can still lie in an obstacle or
outside a footprint-safe area.

Sampling is rejection-based with up to 1000 attempts per point. A crowded or
impossible range can therefore return the last candidate after the attempt
budget; it is not a hard collision-free guarantee. It also does not account for
shape radius or obstacle geometry. Lower `number`/`min_distance`, widen the
range, or place objects manually when spacing matters.

`distribution: {name: uniform}` raises `NotImplementedError`; an unknown name
raises `ValueError`. `distribution: {name: ..., 3d: true}` raises
`NotImplementedError` because 3D state generation is not implemented by this
factory.

## `circle`

```yaml
robot:
  - number: 4
    distribution: {name: circle, center: [5, 4, 0], radius: 2.5}
    kinematics: {name: diff}
    shape: {name: circle, radius: 0.2}
```

The default center is `[offset_x + width/2, offset_y + height/2, 0]`; the
default radius is `min(width, height)/2 - 0.5`. For object index `i`, the
factory uses `theta = 2*pi*i/number`, puts the state at
`center + radius*[cos(theta), sin(theta)]`, faces it with orientation
`theta - pi`, and puts the goal at the opposite point. `center[2]` is accepted
by the documented form but the placement code uses the xy components for
position and generates its own orientations. A custom radius can place a body
outside the world; check the full footprint rather than only the center.

## Random shape and random goals

Geometry handlers use the same package RNG proxy for `circle.random_shape` and
random polygon/linestring generation. Keep generation bounds and vertex counts
small for smoke checks; explicit vertices are easier to audit.

For a constructed object with existing goals:

```python
obj.set_random_goal(
    obstacle_list,
    free=True,
    goal_check_radius=0.2,
    range_limits=[[1, 1, -3.14], [9, 7, 3.14]],
    max_attempts=100,
)
```

The live signature is
`set_random_goal(obstacle_list, init=False, free=True, goal_check_radius=0.2,
range_limits=None, max_attempts=100)`. It samples one replacement for each
existing goal. With `free=True`, each candidate is checked against obstacle
geometries using a temporary circle; after `max_attempts`, IR-SIM logs a
warning and commits the last candidate. Verify the resulting geometry if a
hard free-space guarantee is required. Calling it when the object has no goal
is invalid because the method iterates the existing goal deque.

`behavior: {name: dash, wander: true}` also renews a random goal after arrival;
its bounds come from the behavior's `range_low`/`range_high`. `loop: true`
cycles waypoints, and `wander` takes priority if both are enabled. These
behavior controls belong to [navigation and planning](../../navigation-and-planning/SKILL.md),
but they consume the same package randomness.

## Central RNG

IR-SIM exposes one proxy over `numpy.random.Generator`:

```python
from irsim.util.random import set_seed

set_seed(42)
```

`irsim.make(..., seed=42)` calls `set_seed` before loading and constructing a
scene. Random placement, random geometry, random goals, wandering, and motion
or sensor noise route through package RNG paths. To compare two scenes, reset
the seed immediately before each construction and compare states, goals, and
geometry properties rather than object ids.

`set_seed(None)` creates a fresh non-deterministic generator. Do not substitute
`numpy.random.seed`; it does not reset IR-SIM's generator. A seed makes the
sampling sequence repeatable, not an impossible placement constraint solvable,
a live GUI deterministic, or an external controller reproducible. For
lifecycle random resets, use the environment reset contract described in
[simulation environments](../../simulation-environments/SKILL.md), not private
fields.

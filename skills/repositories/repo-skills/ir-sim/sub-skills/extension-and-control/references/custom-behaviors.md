# Custom behaviors and registries

This reference records the extension contracts that are actually used by the
2.10.2 dispatch code. Registry entries live in the Python process; importing a
module is the operation that registers its decorators. Use a unique key in a
smoke test and remove it or run the test in a fresh process.

## Individual behavior functions

Import the decorator from either public location:

```python
from irsim.lib import register_behavior
# or:
from irsim.lib.behavior.behavior_registry import register_behavior
```

Register the exact pair used by the object's YAML:

```python
@register_behavior("diff", "dash_custom")
def dash_custom(ego_object, external_objects, **kwargs):
    # Return a (2, 1) array for diff; use the matching action dimension.
    return make_command(ego_object, external_objects, **kwargs)
```

The dispatch contract is important:

- The key is `(kinematics, action_name)`, for example `("diff", "dash_custom")`.
  Behavior names are not made portable across kinematics and the behavior
  registry does not normalize their spelling.
- `Behavior.gen_vel()` passes `ego_object=...`,
  `external_objects=...`, and every key in the configured behavior mapping as
  keyword arguments. Include the literal `external_objects` parameter or
  accept `**kwargs`; documentation examples using an `objects` parameter alone
  do not match this call and can raise an unexpected-keyword `TypeError`.
- `external_objects=None` is normalized to an empty list. If
  `target_roles` is `robot` or `obstacle`, the list is filtered before the
  custom function is called. The default is `all`.
- Return a NumPy array with one column and the object's action dimension:
  `diff`, `omni`, and `acker` normally use 2; `omni_angular` uses 3. The
  object layer applies velocity and acceleration-range clipping afterward.
  A behavior that returns the wrong dimension fails later, so validate it in
  the extension's own smoke test.
- If no behavior mapping is configured, the object is static and the behavior
  facade returns zeros. A custom behavior does not replace an explicit action
  passed to internal `env.step()`.

The normal load sequence is:

```python
import irsim

env = irsim.make("scene.yaml", display=False)
env.load_behavior("my_behavior_module")  # importable module name, not a path
try:
    env.step()
finally:
    env.end(0)
```

`EnvBase.load_behavior()` calls `importlib.import_module()` and then
reinitializes registered individual and group **class** handlers for existing
objects/groups. The module must already be on `sys.path`; placing a file beside
a script only works when that directory is importable. Load before the first
step and before any YAML object needs a custom map generator.

## Stateful individual handlers

Use `register_behavior_class` when setup is needed once or state must persist:

```python
from irsim.lib.behavior.behavior_registry import register_behavior_class

@register_behavior_class("diff", "smooth_custom")
def init_smooth(object_info, **kwargs):
    return SmoothHandler(object_info, **kwargs)

class SmoothHandler:
    def __init__(self, object_info, **kwargs):
        self.previous = np.zeros((2, 1))

    def __call__(self, ego_object, external_objects, **kwargs):
        return self.previous
```

The registered object is an initializer. The behavior facade calls it once as
`initializer(object_info, **behavior_dict)` and stores the returned callable.
On each step it calls that callable as
`handler(ego_object=..., external_objects=..., **behavior_dict)`. A class
constructor that expects only the object and does not accept the configured
keyword arguments will fail initialization; use `**kwargs` for extensible
parameters. If class initialization fails, IR-SIM logs the error and falls
back to the function map; it does not silently repair a bad handler.

## Group behavior functions and classes

Group behavior is separate from per-object behavior. The four decorators are:

| Decorator | Registered value | Call shape | Result |
| --- | --- | --- | --- |
| `register_behavior` | per-object function | `fn(ego_object, external_objects, **config)` | one action array |
| `register_behavior_class` | per-object initializer | `init(object_info, **config)` → callable | one action array per call |
| `register_group_behavior` | per-group function | `fn(members, **config)` | list aligned with `members` |
| `register_group_behavior_class` | per-group initializer | `init(members, **config)` → callable | list aligned with `members` |

A stateless group example is:

```python
@register_group_behavior("omni", "formation_custom")
def formation_custom(members, **kwargs):
    return [np.zeros((2, 1)) for _ in members]
```

For the class form, the initializer receives the initial members once. The
returned handler is called as `handler(current_members, **behavior_dict)`. A
`GroupBehavior.update_members()` call replaces the wrapper's member list but
does not force class re-instantiation; a stateful handler must handle changed
membership or rebuild its own state. The function result must contain one
action per member in the same order. Empty/no-configured groups use the
framework's `[None]` sentinel rather than an action list.

A `group_behavior` name is looked up using the first member's kinematics. ORCA
is implemented by this class-based route and requires `pyrvo`; custom group
functions do not acquire that dependency automatically. Route built-in
algorithm selection and ORCA trade-offs to
[the navigation skill](../../navigation-and-planning/SKILL.md).

## Custom kinematics

`register_kinematics(name)` lowercases the registry key and rejects a different
class under an existing key:

```python
from irsim.lib.handler.kinematics_handler import (
    KinematicsHandler, register_kinematics,
)

@register_kinematics("my_kinematics")
class MyKinematics(KinematicsHandler):
    action_dim = 2
    state_dim = 3
    min_state_dim = 3

    def step(self, state, velocity, step_time):
        return state
```

`KinematicsFactory.create_kinematics()` constructs a registered class as
`handler_cls(name, noise, alpha)` (the built-in Ackermann class is the special
case that receives `mode` and `wheelbase`). Therefore a custom constructor
must accept the base constructor arguments unless the factory is bypassed.
The abstract requirement is `step(state, velocity, step_time)`; override
`velocity_to_xy`, `compute_max_speed`, and `compute_heading` whenever the
custom action/state semantics differ from the differential-drive defaults.
Set accurate class metadata (`action_dim`, state dimensions, limits,
acceleration, and visualization flags) because scene parsing and object
clipping use it. `get_handler_class("MY_KINEMATICS")` is case-insensitive at
lookup time.

An unknown factory name is not a custom extension: for a robot the factory
warns and falls back to the differential handler. Do not rely on that fallback
for a working custom robot.

## Custom grid-map generators

Subclass and import `GridMapGenerator` before a YAML map is resolved:

```python
import numpy as np
from irsim.world.map.grid_map_generator_base import GridMapGenerator

class MyGenerator(GridMapGenerator):
    name = "my_generator"
    yaml_param_names = ("marker",)

    def __init__(self, width, height, marker=100, **kwargs):
        super().__init__()
        self.width, self.height, self.marker = width, height, marker

    def _build_grid(self):
        return np.full((self.width, self.height), self.marker)
```

`GridMapGenerator.__init_subclass__` adds any subclass with a non-empty
`name` to `GridMapGenerator.registry`; the name is used exactly (unlike the
kinematics registry). `build_grid_from_generator(spec, world_width,
world_height)` requires `spec["name"]` and `spec["resolution"]`, computes
`round(world_width / resolution)` and `round(world_height / resolution)`, and
injects those cell counts as `width` and `height`. Only keys listed in
`yaml_param_names` are forwarded from the spec; unknown YAML parameters are
ignored. The generator's `generate()` converts `_build_grid()` to a float64
array, and `.grid` generates lazily if needed.

Return occupancy values in the package convention (0–100, with values above
50 treated as occupied). A custom generator module must be imported before
`irsim.make()` or before `build_grid_from_generator()`; there is no filename
lookup hook in the map registry. The map's world dimensions, resolution, and
offset still belong to the scene/map contract; see
[scene configuration](../../scene-configuration/SKILL.md) and
[sensing and mapping](../../sensing-and-mapping/SKILL.md).

## Safe extension test pattern

Test registrations in a fresh process with a tiny fake object/member fixture:
assert the registry contains the exact key, invoke the function, check array
shape and member ordering, and remove temporary entries in `finally`. Then
construct only the smallest headless scene needed to check integration. The
bundled `scripts/custom_behavior_smoke.py` exercises process-local individual,
group, kinematics, and map registration without importing an original usage
file or opening a figure.

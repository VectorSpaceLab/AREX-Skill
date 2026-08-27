# Manipulation task reference

`dm_control.manipulation` exposes a structured registry of Jaco arm/hand manipulation environments. The public entry points are:

- `dm_control.manipulation.ALL`: tuple of all registered environment names.
- `dm_control.manipulation.TAGS`: tuple of tags, verified as `('features', 'vision', 'easy')`.
- `dm_control.manipulation.get_environments_by_tag(tag)`: return registered names for a tag.
- `dm_control.manipulation.load(environment_name, seed=None)`: construct a `composer.Environment` for one registered name.

The installed registry was verified with 25 manipulation tasks: 13 `features`, 12 `vision`, and 4 `easy` reach variants.

## Task catalog

Use exact names. Build validation around `name in manipulation.ALL`; do not guess alternate spellings.

| Family | Feature observations | Vision observations | Notes |
|---|---|---|---|
| Reach Duplo | `reach_duplo_features` | `reach_duplo_vision` | `easy`; target is a moveable Duplo prop. |
| Reach site | `reach_site_features` | `reach_site_vision` | `easy`; target is a fixed site. |
| Lift brick | `lift_brick_features` | `lift_brick_vision` | Lift a brick prop. |
| Lift large box | `lift_large_box_features` | `lift_large_box_vision` | Larger prop than brick. |
| Place brick | `place_brick_features` | `place_brick_vision` | Place a brick at a target. |
| Place cradle | `place_cradle_features` | `place_cradle_vision` | Place into a cradle target. |
| Stack 2 bricks | `stack_2_bricks_features` | `stack_2_bricks_vision` | Stacking task. |
| Stack 2 bricks, moveable base | `stack_2_bricks_moveable_base_features` | `stack_2_bricks_moveable_base_vision` | Stacking with moveable base. |
| Stack 3 bricks | `stack_3_bricks_features` | `stack_3_bricks_vision` | Stacking task. |
| Stack 3 bricks, random order | `stack_3_bricks_random_order_features` | — | Feature-only registry entry. |
| Stack 2 of 3 bricks, random order | `stack_2_of_3_bricks_random_order_features` | `stack_2_of_3_bricks_random_order_vision` | Partial stack with randomized goal order. |
| Reassemble 3 bricks, fixed order | `reassemble_3_bricks_fixed_order_features` | `reassemble_3_bricks_fixed_order_vision` | Reassembly task. |
| Reassemble 5 bricks, random order | `reassemble_5_bricks_random_order_features` | `reassemble_5_bricks_random_order_vision` | Larger reassembly task. |

Tag shortcuts:

```python
from dm_control import manipulation

print(manipulation.TAGS)
print(manipulation.get_environments_by_tag('easy'))
print(manipulation.get_environments_by_tag('features'))
print(manipulation.get_environments_by_tag('vision'))
```

## Feature versus vision variants

Choose by observation contract, not by reward or action API:

- `*_features` enables proprioception, force/torque/touch readings, and object/target pose features; camera observations are disabled.
- `*_vision` keeps proprioception and force/torque/touch readings, disables direct prop-pose features, and enables camera observations at 84x84 by default.
- `*_vision` tasks may need a working MuJoCo/OpenGL rendering backend when camera observations are generated. Route backend setup and render failures to `../rendering-viewer-assets/SKILL.md`.
- Action specs still come from the Jaco arm/hand control interface. Always inspect `env.action_spec()` instead of hard-coding dimensions.

For fast non-rendering checks or low-dimensional RL baselines, start with a `*_features` task such as `reach_site_features`. Use `*_vision` only when the downstream policy or data collection explicitly needs pixels.

## Load and inspect workflow

```python
from dm_control import manipulation
import numpy as np

name = 'reach_site_features'
if name not in manipulation.ALL:
    raise ValueError(f'Unknown manipulation task {name!r}; use manipulation.ALL')

env = manipulation.load(name, seed=0)
observation_spec = env.observation_spec()
action_spec = env.action_spec()

print('observations:', list(observation_spec))
print('action shape:', action_spec.shape)
print('action min/max finite:', np.isfinite(action_spec.minimum).all(),
      np.isfinite(action_spec.maximum).all())

time_step = env.reset()
for key, spec in observation_spec.items():
    spec.validate(time_step.observation[key])

action = np.zeros(action_spec.shape, dtype=action_spec.dtype)
action = np.clip(action, action_spec.minimum, action_spec.maximum)
time_step = env.step(action)
print('reward:', time_step.reward, 'discount:', time_step.discount)
```

## Validation loop for future agents

1. Print `manipulation.TAGS` and reject tags not in it before calling `get_environments_by_tag`.
2. Print or search `manipulation.ALL` before calling `load`; suggest close exact names from the catalog if the requested name is invalid.
3. Prefer `seed=0` or a caller-provided seed for reproducible construction.
4. Run one `reset()` and one zero or random action `step()`; validate observations against `env.observation_spec()` and validate action bounds are finite.
5. For `*_vision`, verify rendering backend separately before treating a camera-observation failure as a task-registry failure.

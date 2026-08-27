# Third-Party Controllers

This reference describes the extension pattern for custom composite controllers.

## 1) The extension pattern

A third-party controller usually subclasses `CompositeController` or `WholeBody`.

Minimal shape:

```python
from robosuite.controllers.composite.composite_controller import WholeBody, register_composite_controller

@register_composite_controller
class WholeBodyMySolver(WholeBody):
    name = "WHOLE_BODY_MY_SOLVER"

    def _init_joint_action_policy(self):
        self.joint_action_policy = ...
```

Required steps:

1. Subclass one of the composite controller bases.
2. Decorate the class with `@register_composite_controller`.
3. Give the class a `name` that will become the controller `type` string.
4. Implement the composite-specific logic that produces low-level part actions.
5. Import the module so the decorator runs and the controller is added to the registry.
6. Ship a JSON config whose top-level `type` matches the controller `name`.

## 2) What usually changes in a `WholeBody` subclass

For whole-body controllers, the custom logic normally lives in:

- `_init_joint_action_policy`
- `setup_action_split_idx` only if the solver changes the action prefix
- `action_limits` only if the new solver has a different control space
- `set_goal` if the solver needs custom action parsing

The `composite_controller_specific_configs` section should still carry:

- `ref_name`
- `actuation_part_names`
- solver-specific tuning values

## 3) Optional Mink example

The bundled `WHOLE_BODY_MINK_IK` pattern is a good reference for a third-party whole-body solver.

It uses:

- a `WholeBody` subclass
- a registered controller name of `WHOLE_BODY_MINK_IK`
- an `IKSolverMink`-style joint-action policy
- solver-specific config fields such as `ik_input_ref_frame`, `ik_input_rotation_repr`, `ik_hand_pos_cost`, and `ik_hand_ori_cost`

Important runtime note:

- `mink` is optional and was not installed in the verified environment for this sub-skill draft.
- Treat Mink-based controllers as reference-only unless the dependency is present.

## 4) Configuration pairing

A custom controller config should look like:

```json
{
  "type": "WHOLE_BODY_MY_SOLVER",
  "composite_controller_specific_configs": {
    "ref_name": ["..."],
    "actuation_part_names": ["right", "left"]
  },
  "body_parts": {
    "arms": {
      "right": { "type": "JOINT_POSITION", "gripper": { "type": "GRIP" } },
      "left": { "type": "JOINT_POSITION", "gripper": { "type": "GRIP" } }
    }
  }
}
```

Use `scripts/validate_controller_config.py` to catch missing `type`, `body_parts`, `ref_name`, and `actuation_part_names` before trying the config in an env.

## 5) When to use the `skip_wbc_action` escape hatch

`skip_wbc_action` tells a whole-body controller to fall back to the base composite controller split logic.

Use it only when:

- you want to reuse the part-controller wiring
- you do not need the whole-body solver prefix in the action space

Otherwise, leave it off so the solver owns the action layout.

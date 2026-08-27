---
name: controllers
description: "Select, validate, and extend robosuite controllers, controller
  configs, action splits, and custom robot composition."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Controllers

Use this sub-skill for controller selection, controller-config validation, action-split inspection, custom robot composition, and third-party composite controller routing.

## Primary references

- `references/controller-configs-and-actions.md`
- `references/robots-grippers-and-bases.md`
- `references/third-party-controllers.md`
- `references/troubleshooting.md`

## Bundled helpers

- `scripts/print_action_info.py` — print JSON action splits for an env / robot / controller config
- `scripts/validate_controller_config.py` — validate composite controller JSON shape and common omissions

## Fast paths

- Default robot controller:
  `load_composite_controller_config(robot="Panda")`
- BASIC preset:
  `load_composite_controller_config(controller="BASIC")`
- Custom controller JSON:
  `load_composite_controller_config(controller="/path/to/controller.json")`
- Legacy part config:
  `load_part_controller_config(default_controller="OSC_POSE")`
- Action dict to vector:
  `robot.create_action_vector({"right": np.zeros(6), "right_gripper": np.array([0.0])})`
- Custom composite robot:
  `create_composite_robot("CustomPanda", robot="Panda", base="RethinkMount", grippers="PandaGripper")`

## Boundary

Included:
- `load_composite_controller_config`
- `load_part_controller_config`
- `BASIC`, `HYBRID_MOBILE_BASE`, `WHOLE_BODY_IK`
- part controllers and controller JSON structure
- robot / gripper / base registries
- `action_split_indexes`
- `robot.create_action_vector`
- `create_composite_robot`
- third-party composite controller extension pattern

Excluded:
- environment setup basics
- device-to-action conversion
- camera / rendering workflows
- MJCF world / object modeling

## Cross-links

- `../environments` for `suite.make(...)` examples
- `../teleoperation` for device-to-action conversion
- `../modeling` for custom robot XML checks

## Notes

- `WHOLE_BODY_MINK_IK` is optional and reference-only; current verification did not include `mink`.
- `robosuite_models` adds extra robots, grippers, and bases when installed, but it is optional.

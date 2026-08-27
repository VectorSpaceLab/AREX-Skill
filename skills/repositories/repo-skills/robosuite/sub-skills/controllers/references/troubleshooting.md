# Troubleshooting

Use these checks first:

```bash
python scripts/validate_controller_config.py /path/to/controller.json
python scripts/print_action_info.py --environment Lift --robots Panda --controller BASIC
```

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Controller ... not found in COMPOSITE_CONTROLLERS_DICT` | Type typo, or custom controller module was never imported | Use a registered name such as `BASIC`, `HYBRID_MOBILE_BASE`, or `WHOLE_BODY_IK`; for custom controllers, import the module before `suite.make(...)`. |
| `Missing top-level key: body_parts` | Composite config is malformed | Add a top-level `body_parts` mapping; raw part-only JSON is not a composite controller config. |
| Action dimension mismatch at `env.step(...)` | Wrong part names, wrong gripper dof, or a stale split map | Print the split map, check `right` / `left` / `base` / `torso` / `head` / `legs`, and rebuild the action vector with `robot.create_action_vector(...)`. |
| Extra or missing gripper dims | Gripper type does not match the robot, or a gripper config was omitted | Check the chosen gripper registry entry and whether the arm is supposed to have a gripper at all. |
| `base_mode` confusion | `HYBRID_MOBILE_BASE` appends one extra scalar | Include the trailing mode term when building the action vector. |
| Whole-body IK gives empty or wrong splits | `ref_name` or `actuation_part_names` is wrong | Ensure both keys exist and the site names / part names match the robot model. |
| `WHOLE_BODY_MINK_IK` fails to import | `mink` is not installed | Treat Mink-based controllers as optional; `GR1` / `GR1FixedLowerBody` defaults may resolve here, so use `WHOLE_BODY_IK`, choose a different robot/controller, or install `mink`. |
| `IK_POSE` fails on a robot that used to work elsewhere | The robot is not one of the supported IK robots | The current source only supports IK on `Baxter`, `Sawyer`, `Panda`, and `GR1FixedLowerBody`. |
| `JOINT_POSITION` / `JOINT_VELOCITY` works for one part but not another | Part-type mismatch | Base, torso, head, and legs have different supported controller families than arms. |
| `GR1` or `Jaco` appears fragile in tests | Current repo tests mark them as known caveats | Start with a tiny smoke run and the bundled action-info helper before relying on a custom config. |
| A robot or gripper name is missing entirely | Optional `robosuite_models` package is absent | Install the optional package or switch to a built-in registry entry. |

## Part naming reminders

- Arm parts: `right`, `left`
- Gripper parts: `right_gripper`, `left_gripper`
- Mobile parts: `base`, `torso`, `head`, `legs`
- `load_composite_controller_config` flattens `body_parts["arms"]` into the arm names above

## When in doubt

1. Validate the JSON.
2. Print the split map.
3. Compare the part names against the robot / gripper / base combination.
4. If the controller is custom, make sure its module was imported so registration happened.

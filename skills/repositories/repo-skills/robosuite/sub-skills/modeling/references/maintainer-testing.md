# Maintainer testing

Pick the narrowest test that exercises the modeling surface you changed.

## Recommended order

1. Compile the edited XML or generated MJCF first.
2. Check custom robot XML or a registered robot next.
3. Run the smallest pytest module that exercises the affected model registry.
4. Only widen to environment smoke tests if model composition or reset behavior changed.

## Change-to-test map

| Change type | First check | Focused pytest |
| --- | --- | --- |
| XML syntax, asset paths, or compiled MJCF output | `scripts/compile_mjcf_model.py` on the edited XML | None until the XML compiles cleanly |
| Custom robot XML, joint names, or mount bodies | `scripts/check_custom_robot_model.py --robot-xml-file <file>` | `tests/test_robots/test_all_robots.py` and, if composition changed, `tests/test_robots/test_composite_robots.py` |
| Registered robot sanity, including dynamic composite robots | `scripts/check_custom_robot_model.py --robot <name>` | `tests/test_robots/test_all_robots.py` or `tests/test_robots/test_composite_robots.py` depending on the change |
| Gripper XML or gripper mount / attachment changes | `scripts/check_custom_robot_model.py --robot <name>` when the robot uses the gripper | `tests/test_grippers/test_all_grippers.py` plus `tests/test_robots/test_composite_robots.py` if mount geometry changed |
| Object, arena, or task composition | compile helper plus a tiny headless scene reset | `tests/test_environments/test_env_determinism.py` and `tests/test_environments/test_action_playback.py` |
| New environment wiring or broad registry impact | compile helper plus one reset smoke | `tests/test_environments/test_all_environments.py` |
| Camera, pose, or image-observation behavior | hand off to `../rendering` | `tests/test_environments/test_camera_transforms.py` only if the camera math itself changed |

## Why these tests

- `tests/test_robots/test_all_robots.py` catches broken robot registration and missing model properties.
- `tests/test_robots/test_composite_robots.py` catches robot / base / gripper composition problems.
- `tests/test_grippers/test_all_grippers.py` catches gripper registry and formatting regressions.
- `tests/test_environments/test_env_determinism.py` catches reset drift and object-placement changes.
- `tests/test_environments/test_action_playback.py` catches state replay and reset wiring regressions.
- `tests/test_environments/test_all_environments.py` is the broad smoke test when the change should apply everywhere.

## Practical workflow

- Start with `--help` on the bundled scripts when you are unsure which mode to use.
- Prefer one robot or one object in the first pass; do not start with a full benchmark sweep.
- If a change only affects display-dependent helpers, do not block on headless CI; treat those helpers as optional and environment-dependent.
- If the change reaches into camera projection or transform math, stop here and delegate the visual math to `../rendering`.

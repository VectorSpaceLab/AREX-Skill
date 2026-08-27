# Troubleshooting

Use the smallest fix that makes the MJCF model compile and the registered robot / environment smoke pass.

| Symptom | Likely cause | Fix | Follow-up check |
| --- | --- | --- | --- |
| XML parse error or MuJoCo refuses to load the file | Malformed tag, bad nesting, or an invalid asset path | Validate the XML structure, keep the object subtree under the expected `object` body, and resolve asset paths with `xml_path_completion(...)` | `scripts/compile_mjcf_model.py` |
| MuJoCo compile error mentions a mesh, inertia, or mass problem | Missing mesh file, bad mesh scale, or incomplete inertial values | Fix the mesh reference or scale, then make density / inertia explicit enough for MuJoCo to compile | `scripts/compile_mjcf_model.py` |
| Robot XML loads but joints are grouped or ordered incorrectly | Joint names do not follow the expected body-part convention, or a left arm appears before the right arm | Rename joints so torso / head / leg / gripper / base are explicit, keep arm joints in the expected right-first order, and rerun the robot checker | `scripts/check_custom_robot_model.py` and the robot tests |
| Gripper will not mount or the checker cannot find an end-effector body | The robot XML is missing the mount / eef body or `ManipulatorModel.eef_name` does not match the XML | Add the expected body, then realign the public end-effector name map with the XML asset | `scripts/check_custom_robot_model.py --robot <name>` |
| Objects spawn in collision or fall through the table at reset | Missing `bottom_site`, `top_site`, or `horizontal_radius_site`, or the placement sampler ranges are too tight | Add the placement sites, widen the sampler bounds, and recheck object offsets before environment wiring | `scripts/compile_mjcf_model.py` and a headless reset smoke |
| `browse_mjcf_model.py`, `tune_camera.py`, or `tune_joints.py` never opens or cannot read keys | No display, missing keyboard focus, or `pynput` is unavailable | Treat these helpers as display-dependent and optional; use the compile and checker scripts for headless validation | Help-only smoke or a local GUI session |
| A custom robot works in one session but not after composition | A dynamic composite robot was not registered under the name you are checking | Create it with `create_composite_robot(name, robot, base=None, grippers=None)`, verify the registered name, then rerun the checker | `scripts/check_custom_robot_model.py --robot <composite-name>` |

## Optional or environment-dependent capabilities

These are useful but not part of the core modeling contract:

- `robosuite_models`
- `mink`
- `hidapi` device hardware
- `usd-core`
- Isaac / Omniverse export workflows
- on-screen display

Document them as optional when you mention them, and do not make core modeling validation depend on them.

## When to hand off

- Camera observation, projection, or transform problems belong in `../rendering`.
- Controller semantics, action slicing, and gripper motion behavior belong in `../controllers`.
- Purely environmental runtime issues without a model change usually belong in the environment sub-skill instead of here.

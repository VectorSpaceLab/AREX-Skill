# YAML, URDF, and robot-builder decisions

Prefer an existing bundled robot YAML when the robot is already represented.
It supplies kinematic structure, joint limits, tool frames, collision sphere
parameters, and optional dynamics. Use an explicit URDF path only when creating
or adapting a new model; confirm mesh references are resolvable and that the
active joint order matches the intended control order.

`RobotBuilder` can fit link geometry with spheres and produce a self-collision
ignore map. More spheres improve collision fidelity but increase GPU memory and
pair count. The ignore map must contain only link pairs that are mechanically
safe to skip; do not remove pairs merely to make a difficult plan pass.
Validate the generated config by constructing `Kinematics` and checking DOF,
joint names, tool frames, limits, and a known-valid zero/default state.

Visualization is optional and should be treated as a separate Viser workflow.
Do not leave a model-building process alive in a batch job; use the builder's
non-interactive/configuration path and save outputs deliberately.

# Robot model API

`KinematicsCfg.from_robot_yaml_file(file_path, tool_frames=None,
 device_cfg=DeviceCfg(...), urdf_path=None, **kwargs)` accepts a bundled YAML
name or mapping. `Kinematics(config)` exposes `get_dof()`, `dof`, `joint_names`,
`tool_frames`, `default_joint_state`, `get_joint_limits()`,
`get_robot_as_spheres()`, and `compute_kinematics(joint_state, idxs_env=None)`.

`JointState.from_position(position, joint_names=None)` expects a tensor with the
last dimension equal to the active DOF; a single configuration is normally
`(1, dof)` rather than `(dof,)`. `Pose(position, quaternion, rotation=None,
 batch_size=1, name="ee_link", normalize_rotation=False)` uses position shape
`(B,3)` and quaternion shape `(B,4)`. cuRobo's quaternion convention is wxyz.

A kinematics result contains tool and link state. Use the named tool-frame
accessor rather than assuming the first frame when a robot has multiple tools.
Keep the input tensor on the configured CUDA device. FK uses differentiable
PyTorch operations, so a scalar derived from a position/orientation output can
be backpropagated to `q`.

For custom URDF construction, `RobotBuilder` and `UrdfRobotParser` produce or
inspect robot configuration data. The builder's sphere fitting and self-
collision pruning are configuration-generation operations; they are distinct
from runtime FK.

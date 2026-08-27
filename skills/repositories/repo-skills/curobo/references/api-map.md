# Public API map

| Task | Public entry points | Core input/output |
| --- | --- | --- |
| Kinematics | `KinematicsCfg.from_robot_yaml_file`, `Kinematics.compute_kinematics` | `JointState` → `KinematicsState` with tool/link poses and Jacobians |
| IK | `InverseKinematicsCfg.create`, `InverseKinematics.solve_pose` | `GoalToolPose`, optional current state/seeds → result with success, joint solution, errors |
| Trajectory optimization | `TrajectoryOptimizerCfg.create`, `TrajectoryOptimizer.solve_pose`, `solve_cspace` | start/goal state or tool poses → optimized and interpolated joint trajectories |
| Motion planning | `MotionPlannerCfg.create`, `MotionPlanner.plan_pose`, `plan_cspace`, `plan_grasp` | start state + pose/c-space/grasp goal → planner result combining IK, graph, trajopt |
| MPC | `ModelPredictiveControlCfg.create`, `ModelPredictiveControl.update_*`, `optimize_next_action`, `optimize_action_sequence` | current state and goal registry → next action or action sequence |
| Retargeting | `MotionRetargeterCfg.create`, `MotionRetargeter.solve_frame`, `solve_sequence` | tool-pose criteria and frame/sequence goals → retarget result/joint sequence |
| Scene data | `Scene`, `Cuboid`, `Sphere`, `Capsule`, `Cylinder`, `Mesh`, `VoxelGrid` | typed obstacle lists and poses |
| Collision | `RobotSceneCollisionCfg`, `RobotSceneCollision` | robot/scene configs and joint states → collision distances/costs |
| Perception | `MapperCfg`, `Mapper`, `FilterDepth`, `CameraObservation`, `LidarObservation` | depth/feature/sensor observations → TSDF/ESDF, mesh, occupied/matched voxels |
| Shared data | `JointState`, `Pose`, `GoalToolPose`, `ToolPoseCriteria`, `DeviceCfg`, `ContentPath` | CUDA tensors, frame names, config/content locations |

## Important verified defaults

- `KinematicsCfg.from_robot_yaml_file(file_path, tool_frames=None,
  device_cfg=CUDA float32, urdf_path=None, **kwargs)` accepts a bundled YAML name
  or a config dictionary.
- `InverseKinematicsCfg.create` defaults to 32 seeds, 5 mm position tolerance,
  0.05 orientation tolerance, self-collision enabled, CUDA graphs enabled,
  `max_batch_size=1`, and `max_goalset=1`.
- `TrajectoryOptimizerCfg.create` defaults to LBFGS B-spline trajectory config,
  four seeds, CUDA graphs enabled, interpolation `dt=0.025`, and a 1000-sample
  interpolation buffer.
- `MotionPlannerCfg.create` composes IK, trajectory optimization, graph planner,
  metrics rollout, transition models, scene collision config, and interpolation.
- `ModelPredictiveControlCfg.create` defaults to LBFGS MPC, `optimization_dt=0.02`,
  four interpolation steps, safe deceleration on failure, and CUDA graphs.
- `MotionRetargeterCfg.create` requires a robot and a dictionary of
  `ToolPoseCriteria`; it chooses global IK unless `use_mpc=True` and exposes
  global/local seeds, target stepping, tolerance, collision and timing controls.
- `MapperCfg` requires `extent_meters_xyz`; defaults include 5 mm TSDF voxels,
  5 cm ESDF voxels, 4 cm truncation, 10 cm minimum depth, 10 m maximum depth,
  block size 8, and `device="cuda:0"`.
- `Scene` is a typed collection of sphere/cuboid/capsule/cylinder/mesh/voxel
  obstacles. Obstacle poses use `[x, y, z, qw, qx, qy, qz]`.
- `Pose` quaternion values are **wxyz**. `GoalToolPose.from_poses` maps tool-frame
  names to `Pose` and can fix tool-frame ordering and a goalset dimension.

Use the owning sub-skill for exact workflow and troubleshooting; this table is
only a router.

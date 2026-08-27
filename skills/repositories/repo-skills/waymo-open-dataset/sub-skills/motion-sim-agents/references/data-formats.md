# Motion Data Formats

- `Scenario`: motion scene with tracks, map features, dynamic map states, timestamps, and prediction requirements.
- `JointScene`: simulated joint object states for a single rollout-like scene.
- `ScenarioRollouts`: a set of rollouts for a scenario; count must match the challenge config.
- Occupancy flow inputs: parsed tensors from TFExamples plus `OccupancyFlowTaskConfig`; predicted and true waypoint grids must share resolution and waypoint timing.
- WOMD camera features: scenario-like camera data plus codebook/token arrays.
- WOMD LiDAR features: compressed lidar payloads, frame pose, and laser calibration.

Do not mix Perception `Frame` protos with Motion `Scenario` protos without an explicit conversion or merge helper.

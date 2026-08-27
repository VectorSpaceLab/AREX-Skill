# Motion and Sim-Agent Workflows

## Validate sim-agent rollouts

```python
from waymo_open_dataset.utils.sim_agents import submission_specs
challenge = submission_specs.ChallengeType.SIM_AGENTS
config = submission_specs.get_submission_config(challenge)
submission_specs.validate_scenario_rollouts(scenario_rollouts, original_scenario, challenge)
```

Use `get_sim_agent_ids` to determine which tracks must be simulated. Wrong rollout count, wrong current-time index, missing tracks, or invalid ids should be fixed before metric computation.

## Convert a Scenario to a JointScene

```python
from waymo_open_dataset.utils.sim_agents import converters, submission_specs
joint_scene = converters.scenario_to_joint_scene(scenario, submission_specs.ChallengeType.SIM_AGENTS)
trajectories = converters.joint_scene_to_trajectories(joint_scene, scenario)
```

Use this for baseline rollouts, visualization, or conversion checks.

## Occupancy flow metrics

1. Parse serialized examples with `occupancy_flow_data.parse_tf_example`.
2. Build a task config proto.
3. Create ground-truth timestep grids and waypoints.
4. Provide predicted waypoint grids with matching resolution and horizon.
5. Call `compute_occupancy_flow_metrics`.

## WOMD camera and LiDAR feature merge

Camera feature merging requires a scenario carrying motion tracks plus camera tokens/codebook-derived embeddings. LiDAR merging requires compressed lidar protos and matching laser calibration. Keep the camera/LiDAR data scenario aligned with the original motion scenario before augmenting.

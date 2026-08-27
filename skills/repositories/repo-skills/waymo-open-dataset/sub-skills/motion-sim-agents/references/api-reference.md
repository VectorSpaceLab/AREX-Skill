# Motion and Sim-Agent API Reference

Verified signatures:

- `occupancy_flow_data.parse_tf_example(tf_example) -> dict[str, tf.Tensor]`
- `occupancy_flow_grids.create_ground_truth_timestep_grids(inputs, config) -> TimestepGrids`
- `occupancy_flow_metrics.compute_occupancy_flow_metrics(config, true_waypoints, pred_waypoints) -> OccupancyFlowMetrics`
- `submission_specs.get_submission_config(challenge_type) -> SubmissionConfig`
- `submission_specs.get_sim_agent_ids(scenario, challenge_type) -> Sequence[int]`
- `submission_specs.validate_joint_scene(joint_scene, original_scenario, challenge_type) -> None`
- `submission_specs.validate_scenario_rollouts(scenario_rollouts, original_scenario, challenge_type=ChallengeType.SIM_AGENTS) -> None`
- `converters.scenario_to_joint_scene(scenario, challenge_type=ChallengeType.SIM_AGENTS) -> JointScene`
- `converters.joint_scene_to_trajectories(joint_scene, scenario, use_log_validity=False) -> ObjectTrajectories`
- `womd_camera_utils.add_camera_tokens_to_scenario(scenario, camera_data) -> Scenario`
- `womd_camera_utils.get_camera_embedding_from_codebook(codebook, input_tokens) -> np.ndarray`
- `womd_lidar_utils.augment_womd_scenario_with_lidar_points(scenario, lidar_data) -> Scenario`

Challenge type enum values are `sim_agents` and `scenario_gen`. SubmissionConfig fields include `current_time_index`, `n_simulation_steps`, `n_rollouts`, and `step_duration_seconds`.

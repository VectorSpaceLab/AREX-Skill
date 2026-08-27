# Motion and Sim-Agent Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Rollout validation fails on count | `ScenarioRollouts` count differs from challenge config | Check `get_submission_config(challenge_type).n_rollouts`. |
| Invalid simulated agent ids | Submission contains tracks not required or misses required tracks | Use `get_sim_agent_ids(original_scenario, challenge_type)`. |
| Current time or horizon mismatch | Wrong challenge type or sequence length | Confirm `current_time_index`, `n_simulation_steps`, and `step_duration_seconds`. |
| Occupancy metric tensor shape error | Predicted waypoint grid shape/resolution differs from config | Build predictions from the same config used for ground truth grids. |
| Camera/LiDAR merge drops objects | Camera/LiDAR scenario is not aligned to the motion scenario | Match scenario ids, timestamps, and track ids before augmenting. |
| WDL-limited sim-agent metric import surprises | Extra license scope or optional dependencies | Read license terms and install only needed optional packages. |

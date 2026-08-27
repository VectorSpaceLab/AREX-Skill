# Simulation-data troubleshooting

## Symptoms, causes, and recovery

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `GLFWError: X11: The DISPLAY environment variable is missing` | The host is using offscreen MuJoCo rendering without configuring a GL backend. | Set `MUJOCO_GL=egl` on an EGL-capable machine before running sim reset/rollout code. |
| `AssertionError` on `BOX_POSE[0] is not None` during `sim_env` reset | Joint-space transfer-cube and insertion tasks expect the object pose to be seeded from outside the env. | Call `utils.sample_box_pose()` or `utils.sample_insertion_pose()` and assign the result to `sim_env.BOX_POSE[0]` before reset. |
| `Dataset does not exist` in replay/visualize/postprocess | The command was pointed at the wrong directory or wrong episode name. | Confirm `episode_<idx>.hdf5` or `mirror_episode_<idx>.hdf5` exists in the dataset directory. |
| Corrupt-looking mirrored images | Horizontal flip or compression metadata is mismatched. | Check that `/compress_len` exists and that the mirrored file was produced by the bundled mirror workflow. |
| No frames in the output video | The episode contained no frames or the camera names do not match the file layout. | Verify the task's camera list and that the HDF5 `/observations/images/<camera>` groups exist. |

## Common recovery order

1. Run [check_sim_backend.py](../scripts/check_sim_backend.py) for the target checkout and task.
2. Confirm `MUJOCO_GL=egl` or another valid offscreen renderer.
3. Confirm the episode file layout before replaying or visualizing.
4. Only after the simulator reset is healthy should you generate multiple episodes or batch-process whole directories.

# Troubleshooting

## Invalid env name
**Symptom**: `Environment X not found` or a similar lookup failure.

**Fix**:
- use a registered name from `suite.ALL_ENVIRONMENTS`
- check exact capitalization, such as `Lift` and `TwoArmLift`

## Invalid two-arm robot config
**Symptom**: two-arm env creation fails with a robot/configuration error.

**Fix**:
- use exactly 2 robots, or one bimanual robot when the task supports it
- for two separate robots, use `env_configuration="opposed"` or `"parallel"`
- for a single bimanual robot, let the task switch to `single-robot`

## Missing camera/offscreen renderer
**Symptom**: camera observations fail or a renderer error appears.

**Fix**:
- set `has_offscreen_renderer=True`
- provide at least one `camera_names` entry
- ensure the runtime has a working MuJoCo rendering backend
- for headless smoke tests, keep `use_camera_obs=False`
- for depth, segmentation, and backend-specific renderer issues, see `../rendering`

## Changed obs keys
**Symptom**: code expects a key that no longer appears.

**Fix**:
- inspect `obs.keys()` after `reset()`
- confirm whether `use_object_obs` or `use_camera_obs` is enabled
- check that the robot count matches your prefix expectations, such as `robot0_...`

## Reward/done confusion
**Symptom**: success happened but the env did not terminate.

**Fix**:
- remember that robosuite envs end on horizon unless `ignore_done=True`
- use reward or task success checks to detect completion, not `done` alone

## Gymnasium import/API mismatch
**Symptom**: `GymWrapper` import fails or step/reset unpacking looks wrong.

**Fix**:
- install `gymnasium` when possible
- if falling back to `gym`, ensure the version satisfies the wrapper's compatibility check
- expect `reset(seed=...) -> (obs, info)` and `step(...) -> (obs, reward, terminated, truncated, info)`

## Random rollout crashes
**Symptom**: a smoke loop fails immediately.

**Fix**:
- compare `action.shape` against `env.action_spec[0].shape`
- verify robot and gripper selection
- turn off camera obs first, then add pixels once the base env works

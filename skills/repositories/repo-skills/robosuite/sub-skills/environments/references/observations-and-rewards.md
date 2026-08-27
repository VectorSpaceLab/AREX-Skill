# Observations and rewards

## Observation families
robosuite observations are dict-like and may include:
- proprioception: `robot0_proprio-state`, `robot1_proprio-state`, ...
- object state: `object-state`
- camera state: `{camera_name}_image`, `{camera_name}_depth`, `{camera_name}_segmentation_*`
- fused modality entries: `image-state`, `object-state`, and `*-state` aggregates when enabled

## Shape expectations
- proprioception: flat 1D arrays
- object state: flat 1D arrays
- RGB images: `(H, W, 3)`
- depth maps: `(H, W)` or the wrapped sensor's channel format
- action vectors: flat 1D arrays whose length matches `env.action_dim`

## `use_object_obs`
Use this when you want low-dimensional task and object features for control or learning.
Typical Lift observations include object position, quaternion, and gripper-to-object offsets.

## `use_camera_obs`
Use this when you want pixels.
Requirements:
- `has_offscreen_renderer=True`
- at least one camera name
- camera dimensions specified

## Reward shaping
- `reward_shaping=False` gives the sparse completion-style reward.
- `reward_shaping=True` adds dense intermediate terms.
- task classes scale rewards with `reward_scale` when it is not `None`.

## Horizon and done
- Episodes end by horizon, not by success alone.
- `ignore_done=True` keeps the env from ending at the horizon.
- A success state can still coexist with a continuing episode until horizon is reached.

## Seeding and determinism
- pass `seed` to the env constructor
- compare reset state, XML, and the first observation across env instances
- if a rollout diverges, check action sampling, initialization noise, and environment configuration first

## Task-specific reward notes
### Lift
- sparse reward: success at lift completion
- shaping terms typically cover reach, grasp, and lift

### TwoArmLift
- sparse reward: success when the pot is lifted and level enough
- shaping terms typically cover per-arm reach, grasp, and lift

## Common misunderstanding
`done` is about episode length, not success semantics. Read reward and any task-specific success signal separately.

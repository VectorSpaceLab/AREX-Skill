# Workflows

## 1. Create a standard env
1. Pick `env_name` from the registered robosuite environments.
2. Choose `robots` that match the task family.
3. Set `has_renderer` / `has_offscreen_renderer` based on whether you need display or camera observations.
4. Decide whether to use `use_object_obs` or `use_camera_obs`.
5. Reset, inspect `action_spec`, and step a bounded number of actions.

## 2. Single-arm env workflow
Typical path:
- `env_name="Lift"`
- `robots="Panda"` or another single-arm robot
- `env_configuration="default"`
- `use_object_obs=True` for low-dimensional state learning
- `use_camera_obs=False` for pure state rollouts

Example: headless single-arm rollout.
```python
import numpy as np
import robosuite as suite

env = suite.make(
    "Lift",
    robots="Panda",
    use_object_obs=True,
    use_camera_obs=False,
    has_renderer=False,
    has_offscreen_renderer=False,
    reward_shaping=True,
)
obs = env.reset()
low, high = env.action_spec
action = np.random.uniform(low, high)
obs, reward, done, info = env.step(action)
```

Example: single-arm camera observations.
```python
import robosuite as suite

env = suite.make(
    "Lift",
    robots="Panda",
    use_object_obs=False,
    use_camera_obs=True,
    has_renderer=False,
    has_offscreen_renderer=True,
    camera_names="agentview",
    camera_heights=84,
    camera_widths=84,
)
obs = env.reset()
print(obs["agentview_image"].shape)
```

## 3. Two-arm env workflow
Typical path:
- `env_name="TwoArmLift"`
- `robots=["Sawyer", "Panda"]` for two separate arms, or one bimanual robot when the task allows it
- `env_configuration="opposed"` or `"parallel"`
- use the same-length `gripper_types` list if you need asymmetric grippers

Example: headless two-arm rollout.
```python
import numpy as np
import robosuite as suite
from robosuite.controllers import load_composite_controller_config

controller_config = load_composite_controller_config(controller="BASIC")
env = suite.make(
    "TwoArmLift",
    robots=["Sawyer", "Panda"],
    env_configuration="opposed",
    gripper_types="default",
    controller_configs=controller_config,
    use_object_obs=True,
    use_camera_obs=False,
    has_renderer=False,
    has_offscreen_renderer=False,
    reward_shaping=True,
)
obs = env.reset()
action = np.random.uniform(*env.action_spec)
obs, reward, done, info = env.step(action)
```

## 4. Camera-observation workflow
1. Enable `use_camera_obs=True`.
2. Enable `has_offscreen_renderer=True`.
3. Provide at least one `camera_names` entry.
4. Set `camera_heights` and `camera_widths`.
5. Inspect image keys such as `agentview_image` and optional depth keys when `camera_depths=True`.

## 5. Gymnasium workflow
1. Create the env with robosuite.
2. Wrap with `GymWrapper`.
3. Use `reset(seed=...)` and the Gymnasium step tuple.
4. Sample from `env.action_space` for a smoke test.

## 6. Random-policy smoke loop
1. Reset the env.
2. Read `env.action_spec` and infer the action shape.
3. Sample uniformly inside the action bounds.
4. Step until `done` or a small step cap.
5. Print the keys and array shapes that appear in the observation dict.

## 7. Reproducibility workflow
- Pass `seed` at env construction.
- Avoid hidden randomness in your own rollout code.
- Use the same seed for comparison runs.
- Compare both XML/state initialization and the first reset observation when validating determinism.

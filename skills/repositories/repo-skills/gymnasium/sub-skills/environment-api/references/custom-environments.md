# Custom Environments

Use this reference to design and validate a custom single-agent Gymnasium environment.

## Minimal Class Contract

A custom environment should subclass `gymnasium.Env` and provide:

- `metadata`, especially `render_modes` and optionally `render_fps`.
- `__init__(...)` with `self.action_space`, `self.observation_space`, and any constructor parameters.
- `reset(self, *, seed=None, options=None)` or a compatible signature with `seed` and `options`; return `(observation, info)`.
- `step(self, action)` returning `(observation, reward, terminated, truncated, info)`.
- `render(self)` if rendering is supported; use `self.render_mode` chosen at construction.
- `close(self)` if resources need cleanup.

A compact template:

```python
import numpy as np
import gymnasium as gym
from gymnasium import spaces

class TinyEnv(gym.Env):
    metadata = {"render_modes": ["ansi"], "render_fps": 4}

    def __init__(self, size=5, render_mode=None):
        self.size = int(size)
        self.render_mode = render_mode
        self.observation_space = spaces.Dict(
            {
                "agent": spaces.Box(0, self.size - 1, shape=(2,), dtype=np.int64),
                "target": spaces.Box(0, self.size - 1, shape=(2,), dtype=np.int64),
            }
        )
        self.action_space = spaces.Discrete(4)
        self._directions = {
            0: np.array([0, 1], dtype=np.int64),
            1: np.array([-1, 0], dtype=np.int64),
            2: np.array([0, -1], dtype=np.int64),
            3: np.array([1, 0], dtype=np.int64),
        }
        self._agent = np.zeros(2, dtype=np.int64)
        self._target = np.ones(2, dtype=np.int64)

    def _get_obs(self):
        return {"agent": self._agent.copy(), "target": self._target.copy()}

    def _get_info(self):
        return {"distance": int(np.abs(self._agent - self._target).sum())}

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._agent = self.np_random.integers(0, self.size, size=2, dtype=np.int64)
        self._target = self._agent.copy()
        while np.array_equal(self._target, self._agent):
            self._target = self.np_random.integers(0, self.size, size=2, dtype=np.int64)
        return self._get_obs(), self._get_info()

    def step(self, action):
        direction = self._directions[int(action)]
        self._agent = np.clip(self._agent + direction, 0, self.size - 1)
        terminated = bool(np.array_equal(self._agent, self._target))
        truncated = False
        reward = 1.0 if terminated else 0.0
        return self._get_obs(), reward, terminated, truncated, self._get_info()
```

## Design Checklist

Before coding, decide:

- Skill/task: what should the agent learn?
- Observation: what state information is necessary and sufficient?
- Action: which decisions are valid at each step?
- Reward: what signal encourages the intended behavior?
- Termination: what counts as task success or failure?
- Truncation: what external limits stop an otherwise continuing episode?
- Rendering: is visual or text output required, and which modes are supported?
- Randomness: which parts use `self.np_random` and must be reproducible?

Keep observations and actions inside declared spaces. If an observation/action space is complex, route design details to `../spaces-data/SKILL.md`.

## Reset Rules

Correct `reset` behavior:

```python
def reset(self, *, seed=None, options=None):
    super().reset(seed=seed)
    # initialize episode state using self.np_random
    return observation, info
```

Rules enforced by `check_env` and passive checkers:

- The signature should accept `seed` and `options` with defaults of `None`.
- The default `seed` must not be a fixed integer; fixed defaults make episodes deterministic by accident.
- `super().reset(seed=seed)` must be called so `self.np_random` and `self.np_random_seed` are initialized.
- The return value must be a tuple of length 2: `(obs, info)`.
- `obs` must be contained in `observation_space`.
- `info` must be a Python `dict`.
- `options` is for episode-specific configuration; document any supported keys.

## Step Rules

Correct `step` behavior:

```python
def step(self, action):
    assert self.action_space.contains(action)
    # update state
    return observation, reward, terminated, truncated, info
```

Rules:

- Return exactly five items: `(obs, reward, terminated, truncated, info)`.
- `terminated` and `truncated` must be Python or NumPy booleans.
- `reward` must be numeric and not NaN or infinity.
- `info` must be a Python `dict`.
- `obs` must match the declared `observation_space` keys, shape, dtype, and bounds.
- Use `terminated` for natural task endings and `truncated` for external cutoffs.
- If the environment has a registered `max_episode_steps`, prefer the `TimeLimit` wrapper to emit truncations instead of duplicating the same limit inside the raw env.

Do not return the old `(obs, reward, done, info)` tuple from a new Gymnasium environment.

## Rendering Contract

If rendering is supported:

```python
class MyEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array", "ansi"], "render_fps": 30}

    def __init__(self, render_mode=None):
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
```

Guidelines:

- Include every supported mode in `metadata["render_modes"]`; `None` does not need to be listed.
- `render_mode` should be fixed at construction time, not passed to `render()`.
- `human` rendering normally returns `None`.
- `rgb_array` should return a `np.ndarray` with dtype `np.uint8` and last dimension of size 3.
- `ansi` or `ascii` should return a string.
- Implement `close()` to clean up windows or renderer objects and tolerate repeated calls.

For video recording and render helper wrappers, route to `../wrappers-recording/SKILL.md`.

## Registration Recipe

For local scripts and tests, a class callable is enough:

```python
import gymnasium as gym

gym.register(
    id="demo/GridWorld-v0",
    entry_point=TinyEnv,
    max_episode_steps=100,
)

env = gym.make("demo/GridWorld-v0", size=7)
```

For packages, use a string entry point:

```python
gym.register(
    id="my_package/GridWorld-v0",
    entry_point="my_package.envs:GridWorldEnv",
    max_episode_steps=300,
    kwargs={"size": 5},
)
```

Recommendations:

- Use a namespace for package or organization ownership, e.g. `my_package/GridWorld-v0`.
- Use a version suffix such as `-v0` for APIs that may evolve.
- Avoid registering an unversioned env with the same name as versioned envs.
- Put default constructor parameters in `kwargs` when registering reusable packages.
- Override run-specific parameters through `gym.make("id", size=10)`.
- Use `max_episode_steps` to get the default `TimeLimit` truncation behavior.

## Validation Workflow

```python
from gymnasium.utils.env_checker import check_env

raw_env = TinyEnv(size=5)
check_env(raw_env, skip_render_check=True)

registered_env = gym.make("demo/GridWorld-v0")
obs, info = registered_env.reset(seed=123)
obs, reward, terminated, truncated, info = registered_env.step(
    registered_env.action_space.sample()
)
registered_env.close()
```

Use the raw environment for `check_env` when possible. If the environment is wrapped, the checker warns that wrappers may affect results. If rendering depends on optional GUI/media dependencies, use `skip_render_check=True` for headless CI and test render modes separately.

## Bundled Smoke Script

This sub-skill includes `scripts/check_custom_env.py`, adapted from the GridWorld custom environment tutorial into a self-contained, dependency-light checker. It:

- Defines a small GridWorld-like `gymnasium.Env`.
- Uses only base Gymnasium and NumPy.
- Supports `--help`.
- Optionally runs `gymnasium.utils.env_checker.check_env`.
- Registers a local demo ID.
- Runs one reset and one step.
- Prints concise success signals.

Run from this sub-skill directory:

```bash
python scripts/check_custom_env.py
python scripts/check_custom_env.py --skip-check-env --size 4 --seed 7
```

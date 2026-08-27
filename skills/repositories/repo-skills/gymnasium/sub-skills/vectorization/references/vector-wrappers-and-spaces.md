# Vector Wrappers and Vector Space Utilities

Use vector wrappers when the object being wrapped is a `gymnasium.vector.VectorEnv`. Use single-environment wrappers only before vectorization, through `make_vec(..., wrappers=[...])` or inside each factory passed to `SyncVectorEnv`/`AsyncVectorEnv`.

## Wrapper Placement

### Wrap each sub-environment before vectorization

```python
import gymnasium as gym
from gymnasium.wrappers import TimeAwareObservation

envs = gym.make_vec(
    "CartPole-v1",
    num_envs=4,
    vectorization_mode="sync",
    wrappers=(TimeAwareObservation,),
)
```

This pattern changes each individual env before observations/actions are batched. It is available for `"sync"` and `"async"`, but not for `"vector_entry_point"`.

### Wrap the vector environment after vectorization

```python
import gymnasium as gym
from gymnasium.wrappers.vector import FlattenObservation, RecordEpisodeStatistics

envs = gym.make_vec("CartPole-v1", num_envs=4, vectorization_mode="sync")
envs = FlattenObservation(envs)
envs = RecordEpisodeStatistics(envs)
```

This pattern transforms the batched vector API. The wrapper must come from `gymnasium.wrappers.vector` or subclass `gymnasium.vector.VectorWrapper`.

## Vector Wrapper Families

`gymnasium.wrappers.vector` exports these practical categories:

| Category | Wrappers | Use |
| --- | --- | --- |
| Vector-only adapters | `DictInfoToList`, `VectorizeTransformObservation`, `VectorizeTransformAction`, `VectorizeTransformReward` | Convert vector info format or adapt a single-item transform across a batch. |
| Observation transforms | `TransformObservation`, `FilterObservation`, `FlattenObservation`, `GrayscaleObservation`, `ResizeObservation`, `ReshapeObservation`, `RescaleObservation`, `DtypeObservation`, `NormalizeObservation` | Modify batched observations and update batched/single observation spaces as needed. |
| Action transforms | `TransformAction`, `ClipAction`, `RescaleAction` | Transform action batches before they reach sub-envs. |
| Reward transforms | `TransformReward`, `ClipReward`, `NormalizeReward` | Transform reward arrays from vector steps. |
| Episode/rendering helpers | `RecordEpisodeStatistics`, `RecordVideo`, `HumanRendering` | Track returns/lengths or render/record vector envs with render-mode constraints. |
| Array conversion | `ArrayConversion`, `JaxToNumpy`, `JaxToTorch`, `NumpyToTorch` | Convert batched data for array API/JAX/Torch workflows; optional packages may be required. |

Some wrappers have autoreset constraints. For example, stateful normalization and vector observation wrappers may require `AutoresetMode.NEXT_STEP` or reject `SAME_STEP`. Check `envs.metadata["autoreset_mode"]` before combining wrappers with custom autoreset modes.

## Info Format and `DictInfoToList`

Gymnasium vector infos are dictionaries of batched arrays plus masks:

```python
infos = {
    "score": np.array([10, 0, 12]),
    "_score": np.array([True, False, True]),
}
```

The mask means sub-env 1 did not provide `score`. For old code that expects a list of per-env dictionaries, wrap with `gymnasium.wrappers.vector.DictInfoToList`.

## Recording Statistics and Video

Use vector `RecordEpisodeStatistics` for batched episode returns and lengths. Its episode data appears in vector `infos` with masks, not as one scalar event.

For vector `RecordVideo`:

- Create the vector env with an image-compatible render mode such as `render_mode="rgb_array"`.
- Install the optional video dependency if `moviepy` is missing.
- Be explicit about triggers and output folders in user code.
- Expect limitations with `AsyncVectorEnv`, human rendering, and envs that return lists of frames instead of arrays.

For single-env recording details, use `../wrappers-recording/SKILL.md`; for vector placement and batched info interpretation, stay here.

## Vector Space Utilities

The vector utilities in `gymnasium.vector.utils` are useful when writing wrappers, custom vector envs, or tests:

| Utility | Purpose |
| --- | --- |
| `batch_space(space, n)` | Create a batched space from one single-env space. `Discrete(n)` becomes `MultiDiscrete`; `Box(shape=s)` becomes `Box(shape=(num_envs, *s))`. |
| `batch_differing_spaces(spaces)` | Batch spaces of the same type, shape, and dtype when bounds or discrete sizes differ across sub-envs. |
| `concatenate(space, samples, out)` | Combine per-env samples into a batched observation/action object. |
| `iterate(space, batch)` | Iterate a batched action/observation object into per-env items. |
| `create_empty_array(space, n, fn)` | Allocate an empty nested batched container for vector observations. |
| `create_shared_memory`, `read_from_shared_memory`, `write_to_shared_memory` | Back `AsyncVectorEnv(shared_memory=True)` observations with multiprocessing shared memory. |

For deep fundamental space design, route to `../spaces-data/SKILL.md`. Here, the key distinction is whether an object belongs to the single space or the batched vector space.

## Observation Modes

`SyncVectorEnv` and `AsyncVectorEnv` accept `observation_mode`:

- `"same"`: every sub-env observation space must equal the first sub-env's observation space; this is the default and most reliable mode.
- `"different"`: sub-env observation spaces may differ in values such as bounds, but must share compatible type, shape, and dtype.
- custom `(observation_space, single_observation_space)` tuple: advanced mode for explicit batching contracts.

Action spaces must match the first sub-env's action space in built-in vectorizers.

## Custom Vector Wrappers

Subclass vector wrapper bases for batched transformations:

```python
from gymnasium.vector import VectorRewardWrapper

class ScaleVectorReward(VectorRewardWrapper):
    def __init__(self, env, scale):
        super().__init__(env)
        self.scale = scale

    def rewards(self, rewards):
        return rewards * self.scale
```

Use `VectorObservationWrapper.observations`, `VectorActionWrapper.actions`, and `VectorRewardWrapper.rewards` for batch-level transformations. Update `observation_space`, `single_observation_space`, `action_space`, or `single_action_space` when a wrapper changes the public contract.

## Practical Checks After Wrapping

After applying wrappers, verify:

```python
observations, infos = envs.reset(seed=123)
assert observations in envs.observation_space
actions = envs.action_space.sample()
observations, rewards, terminations, truncations, infos = envs.step(actions)
assert rewards.shape == (envs.num_envs,)
```

If `observations in envs.observation_space` is too strict for complex object spaces, inspect the shapes, dtypes, and keys manually.

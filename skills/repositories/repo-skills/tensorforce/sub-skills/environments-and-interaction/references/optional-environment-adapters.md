# Optional environment adapters

Tensorforce includes a small built-in environment plus adapter classes for Gym and several optional simulators. Only the base Tensorforce API and `custom_cartpole` CPU smoke were part of the construction environment. Treat the simulator adapters below as public surfaces requiring user-provided dependencies/assets/services before claiming execution is verified.

## Adapter registry keys

| Registry keys | Adapter class | Typical requirement | Verification status |
|---|---|---|---|
| `custom_cartpole` | Tensorforce CartPole | Base Tensorforce install | CPU API smoke eligible |
| `gym`, `openai_gym`, `default` | OpenAI Gym adapter | `gym` plus any environment extras | Base Gym path eligible if compatible Gym is installed |
| `ale`, `arcade_learning_environment` | Arcade Learning Environment | `ale-py`, ROM file, possible SDL/system packages | Optional; not executed here |
| `retro`, `openai_retro` | OpenAI Retro | `gym-retro`, game data | Optional; not executed here |
| `osim`, `open_sim` | OpenSim | `osim-rl`/OpenSim stack | Optional; not executed here |
| `ple`, `pygame_learning_environment` | PyGame Learning Environment | `pygame`, PLE package, SDL/headless setup | Optional; not executed here |
| `vizdoom` | ViZDoom | `vizdoom`, config/WAD assets, system libraries | Optional; not executed here |
| `carla`, `carla_environment` | CARLA driving simulator | CARLA server, Python bindings, `pygame`, OpenCV | Optional external service; not executed here |

## Built-in `custom_cartpole`

Use this for fast local checks when Gym or external simulators are not needed:

```python
from tensorforce import Environment

env = Environment.create(environment='custom_cartpole', max_episode_timesteps=500)
try:
    print(env.states())   # float vector state
    print(env.actions())  # scalar int action with 2 or 3 values depending on constructor args
    states = env.reset()
    states, terminal, reward = env.execute(actions=0)
finally:
    env.close()
```

Useful constructor options include physics ranges, state flags, `action_continuous`, and `action_noop`. The built-in environment is vectorizable, so `reset(num_parallel=N)` can return `(parallel_indices, states)` for advanced workflows.

## Gym adapter

Create a Gym environment explicitly:

```python
env = Environment.create(environment='gym', level='CartPole-v1', max_episode_timesteps=500)
```

or use the fallback form:

```python
env = Environment.create(environment='CartPole-v1', max_episode_timesteps=500)
```

Important adapter arguments:

- `level`: Gym id, Gym `Env` instance, or Gym `Env` class.
- `visualize`: call render during `execute`.
- `import_modules`: module or list of modules to import before constructing the Gym level, useful for custom Gym registration.
- `min_value` and `max_value`: required together when unbounded Box observation values need clipping.
- `terminal_reward`: reward adjustment for early true terminal states when the Gym time limit is otherwise ambiguous.
- `reward_threshold`: custom Gym environment registration metadata.
- `drop_states_indices`: remove selected indices from a flat vector observation.
- `visualize_directory`: Gym monitor output directory for compatible Gym versions.
- Additional `**kwargs`: forwarded to Gym environment construction.

Space conversion summary:

- `gym.spaces.Discrete(n)` -> scalar int spec with `num_values=n`.
- `MultiBinary` -> bool spec.
- `MultiDiscrete` -> int spec when all entries have the same range; otherwise a dict of per-entry specs.
- `Box` -> float spec; infinite bounds may require explicit `min_value`/`max_value` or may be represented as infinities depending on adapter path.
- `Tuple` and `Dict` observations/actions are flattened into Tensorforce component names.
- Gym dict observations may carry action masks as `action_mask` or `<action_name>_mask`; the adapter preserves these mask keys before flattening other observations.

Gym API compatibility warning: Tensorforce 0.6.x expects the older Gym API where `reset()` returns only an observation and `step()` returns `(observation, reward, terminal, info)`. Newer Gym/Gymnasium versions may return `(observation, info)` and split termination/truncation into five return values; use a compatible Gym release or a compatibility wrapper.

## ALE adapter

Create with:

```python
env = Environment.create(environment='ale', level='path-or-rom-name')
```

Actual constructor arguments include:

- `level`: ALE ROM file path.
- `life_loss_terminal`: whether losing a life should signal terminal.
- `life_loss_punishment`: reward penalty on life loss when not terminal.
- `repeat_action_probability`: probability ALE repeats the last action.
- `visualize`: display screen.
- `frame_skip`: repeat each selected ALE action this many frames.
- `seed`: ALE random seed.

The state is an RGB screen normalized to `[0, 1]`; the action is a scalar int index into ALE's legal action set. This adapter needs ALE and ROM assets before any runtime claim can be made.

## Retro adapter

Create with:

```python
env = Environment.create(environment='retro', level='GameId')
```

Constructor arguments include `level`, `visualize`, `visualize_directory`, and Retro-specific `**kwargs`. It subclasses the Gym adapter, so Gym compatibility constraints also apply. Retro game data/assets must be installed separately.

## OpenSim adapter

Create with:

```python
env = Environment.create(environment='osim', level='Arm2D')
```

Recognized level names in the adapter are `Arm2D`, `L2M2019`, `LegacyArm`, and `LegacyRun`. It exposes float observations and float actions from the OpenSim environment. Treat this adapter as unverified unless the user provides a working OpenSim runtime and a bounded smoke passes.

## PyGame Learning Environment adapter

Create with:

```python
env = Environment.create(environment='ple', level='Catcher')
```

Constructor arguments include:

- `level`: PLE game class/name such as `Catcher`, `Pixelcopter`, `Pong`, `PuckWorld`, `Snake`, or `WaterWorld`, depending on installed PLE assets.
- `visualize`: display the game; when false, the adapter sets SDL to a headless/dummy mode.
- `frame_skip`: repeat selected action.
- `fps`: target frame rate.

State may be a screen image only, or a dict with screen plus game state if the PLE game exposes state dimensions. This adapter needs pygame/PLE and can be sensitive to headless display configuration.

## ViZDoom adapter

Create with:

```python
env = Environment.create(environment='vizdoom', level='scenario.cfg')
```

Constructor arguments include:

- `level`: ViZDoom config file.
- `include_variables`: include game variables alongside the screen.
- `factored_action`: use a bool vector over buttons instead of a discrete action index.
- `visualize`: visible async player mode versus headless player mode.
- `frame_skip`: repeated action frames.
- `seed`: ViZDoom seed.

State is a normalized RGB screen, optionally with variables. Actions are either a scalar int over all button combinations or a bool vector when factored. Requires ViZDoom and scenario assets.

## CARLA adapter

Create only when a CARLA simulator server and Python bindings are already available:

```python
env = Environment.create(environment='carla', address='localhost', port=2000, render=False)
```

Constructor arguments include `address`, `port`, `timeout`, `image_shape`, `window_size`, `vehicle_filter`, `sensors`, `route_resolution`, `fps`, `render`, and `debug`.

The adapter exposes a dict observation with image, vehicle features, road features, and previous actions. Actions are a float vector interpreted as vehicle controls. It also contains subclass hooks for custom sensors, reward functions, terminal conditions, and action-to-control mapping.

CARLA caveats:

- A CARLA server process must be running and compatible with the Python bindings.
- `pygame` and OpenCV are required by this adapter surface.
- The adapter's own comments state that the standard Tensorforce `Runner` is not compatible with this environment; use the adapter's manual training/direct interaction pattern unless you have proven a replacement workflow.
- Do not report CARLA execution as verified from this skill alone.

# RL API reference

Evidence baseline: source tree files listed in the construction request plus installed-package inspection facts for `gym-pybullet-drones` version 2.2.0 on Python 3.12.13. The package declares no console-script CLI entry points, so use Python imports or the bundled helper script.

## Package and dependency facts

| Fact | Evidence |
| --- | --- |
| Package name/version | `pyproject.toml`: `gym-pybullet-drones`, version `2.2.0` |
| Python support in project metadata | `pyproject.toml`: `python = "^3.12"`; CI uses Python 3.12 |
| RL dependencies | `torch`, `gymnasium`, `stable-baselines3`, `numpy`, `matplotlib`, `pybullet` |
| Native RL smoke | `tests/test_examples.py::test_learn` calls `learn.run(..., local=False)` |
| Source usage | README trains with `learn.py`, then plays `results/<latest>/best_model.zip` with `play.py` |

## Gymnasium environment registration

`gym_pybullet_drones/__init__.py` registers these RL IDs when `gym_pybullet_drones` is imported:

| Env ID | Entry point | Use |
| --- | --- | --- |
| `hover-aviary-v0` | `gym_pybullet_drones.envs:HoverAviary` | Single drone hover at target position near z = 1.0 |
| `multihover-aviary-v0` | `gym_pybullet_drones.envs:MultiHoverAviary` | Multi-drone hover / leader-follower-style joint task |

Minimal registration check:

```python
import gymnasium as gym
import gym_pybullet_drones
assert gym.spec("hover-aviary-v0").entry_point == "gym_pybullet_drones.envs:HoverAviary"
assert gym.spec("multihover-aviary-v0").entry_point == "gym_pybullet_drones.envs:MultiHoverAviary"
```

## RL environment constructors

### `BaseRLAviary`

```python
BaseRLAviary(
    drone_model=DroneModel.CF2X,
    num_drones=1,
    neighbourhood_radius=np.inf,
    initial_xyzs=None,
    initial_rpys=None,
    physics=Physics.PYB,
    pyb_freq=240,
    ctrl_freq=240,
    gui=False,
    record=False,
    obs=ObservationType.KIN,
    act=ActionType.RPM,
)
```

Operational facts:

- Base class for single- and multi-agent RL envs; future agents normally instantiate `HoverAviary` or `MultiHoverAviary` instead.
- Stores `OBS_TYPE` and `ACT_TYPE`, creates an action buffer of `ctrl_freq // 2` previous actions, and appends that buffer to kinematic observations.
- For `ActionType.PID`, `ActionType.VEL`, and `ActionType.ONE_D_PID`, it creates integrated `DSLPIDControl` controllers when using compatible Crazyflie models.
- Action space is a `gymnasium.spaces.Box` with shape `(NUM_DRONES, action_dim)` and bounds `[-1, 1]`.

### `HoverAviary`

```python
HoverAviary(
    drone_model=DroneModel.CF2X,
    initial_xyzs=None,
    initial_rpys=None,
    physics=Physics.PYB,
    pyb_freq=240,
    ctrl_freq=30,
    gui=False,
    record=False,
    obs=ObservationType.KIN,
    act=ActionType.RPM,
)
```

Operational facts:

- Concrete single-agent RL env behind `hover-aviary-v0`.
- Sets `num_drones=1`, `TARGET_POS = [0, 0, 1]`, and `EPISODE_LEN_SEC = 8`.
- Reward is positive near the target: `max(0, 2 - ||target - position||^4)`.
- Truncates if the drone moves too far, too high, too tilted, or exceeds the 8-second episode length.

### `MultiHoverAviary`

```python
MultiHoverAviary(
    drone_model=DroneModel.CF2X,
    num_drones=2,
    neighbourhood_radius=np.inf,
    initial_xyzs=None,
    initial_rpys=None,
    physics=Physics.PYB,
    pyb_freq=240,
    ctrl_freq=30,
    gui=False,
    record=False,
    obs=ObservationType.KIN,
    act=ActionType.RPM,
)
```

Operational facts:

- Concrete multi-agent RL env behind `multihover-aviary-v0`.
- Default `num_drones=2`; still exposed as one Gymnasium environment with joint Box observation/action spaces.
- Sets per-drone targets from initial positions plus `[0, 0, 1/(i+1)]` and sums per-drone hover rewards.
- Truncates if any drone moves too far, too high, too tilted, or the episode exceeds 8 seconds.

## Action and observation enums

Use enum objects, not raw strings, when instantiating env classes directly.

| Enum | Values | Notes |
| --- | --- | --- |
| `ObservationType` | `KIN`, `RGB`, `DEP`, `ALL` with values `"kin"`, `"rgb"`, `"dep"`, `"all"` | RL examples default to `ObservationType.KIN`; vision observations create image spaces and are heavier. |
| `ActionType` | `RPM`, `PID`, `VEL`, `ONE_D_RPM`, `ONE_D_PID` with values `"rpm"`, `"pid"`, `"vel"`, `"one_d_rpm"`, `"one_d_pid"` | RL examples default to `ActionType.ONE_D_RPM`; PID/velocity-like modes use integrated controllers. |

Action dimensions in `BaseRLAviary`:

| Action type | Per-drone action dimension |
| --- | --- |
| `RPM` | 4 |
| `VEL` | 4 |
| `PID` | 3 |
| `ONE_D_RPM` | 1 |
| `ONE_D_PID` | 1 |

## Source RL example entry points

### `learn.run`

```python
learn.run(
    multiagent=False,
    output_folder="results",
    gui=True,
    plot=True,
    colab=False,
    record_video=False,
    local=True,
)
```

Important defaults and behavior:

- `DEFAULT_OBS = ObservationType("kin")`.
- `DEFAULT_ACT = ActionType("one_d_rpm")`.
- `DEFAULT_AGENTS = 2` for multi-agent runs.
- Creates `output_folder/save-<timestamp>/`.
- Uses `make_vec_env(HoverAviary, ...)` or `make_vec_env(MultiHoverAviary, ...)` and SB3 `PPO("MlpPolicy", ...)`.
- `local=False` is the short training branch used by tests: `total_timesteps=int(1e2)`.
- `local=True` is full training: `total_timesteps=int(1e7)`.
- Attempts to load `best_model.zip` after training and then runs a playback-style evaluation/logging loop.

### `play.play`

```python
play.play(
    model_path="results/best_model.zip",
    multiagent=False,
    gui=True,
)
```

Important behavior:

- Checks `os.path.isfile(model_path)`; if missing, prints an error and returns.
- Loads with `PPO.load(model_path)`.
- Creates `HoverAviary` or `MultiHoverAviary` with the same default `ObservationType.KIN` and `ActionType.ONE_D_RPM`.
- Runs one episode-like loop, predicts deterministic actions, logs with `Logger`, calls `env.render()`, paces with `sync`, closes the env, and plots the logger output.

The bundled helper keeps these source decisions but makes model-path failure a non-zero exit and defaults playback to headless/no-plot for automation.

## Logger and sync pieces used by RL examples

```python
from gym_pybullet_drones.utils.Logger import Logger
from gym_pybullet_drones.utils.utils import sync
```

- `Logger(logging_freq_hz=int(env.CTRL_FREQ), num_drones=..., output_folder=..., colab=False)` creates the output folder if needed.
- `Logger.log(drone, timestamp, state, control=np.zeros(12))` expects a 20-value state vector and a 12-value control vector.
- `Logger.save()` writes a NumPy archive; `Logger.save_as_csv()` writes per-field CSV files; `Logger.plot()` opens or saves Matplotlib plots depending on Colab/display behavior.
- `sync(i, start_time, timestep)` sleeps to match simulation wall-clock pace; skip it for fast headless smoke checks and enable it for human-observable playback.

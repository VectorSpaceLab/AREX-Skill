# RL workflows

This sub-skill wraps the repository's PPO `learn.py` and `play.py` patterns into a skill-owned helper so future agents do not need to reopen the original checkout. Use the helper against an installed `gym-pybullet-drones` package.

## Workflow decision guide

| User intent | Use | Safe default |
| --- | --- | --- |
| "train a hover policy" | Train `HoverAviary` with SB3 `PPO` | headless, short timesteps, `ObservationType.KIN`, `ActionType.ONE_D_RPM` |
| "run a short PPO smoke" | Helper `train` or `train-play` | `--timesteps 256`, `gui=False`, save in a temporary output folder |
| "play a saved model" | Helper `play` | pass an existing `best_model.zip` or `final_model.zip`; keep `--gui` off unless a display exists |
| "compare single-agent and multi-agent hover" | Run the same train/play flow once without `--multiagent` and once with it | single-agent uses `HoverAviary`; multi-agent uses `MultiHoverAviary --num-drones 2` |
| "Gymnasium env ID" | Import `gym_pybullet_drones` before `gym.make(...)` | `hover-aviary-v0` or `multihover-aviary-v0` |

## Preflight import check

From the sub-skill directory:

```bash
python scripts/run_rl_workflow.py check-imports
```

Expected signal: JSON with package imports and registered env IDs. If it fails on `gymnasium`, `torch`, or `stable_baselines3`, fix the Python environment before training.

## Short headless training smoke

Use this before any long run. It creates a timestamped run folder and writes both `final_model.zip` and `best_model.zip` for easy playback.

```bash
python scripts/run_rl_workflow.py train \
  --output-folder /tmp/drones-rl-smoke \
  --timesteps 256 \
  --seed 0
```

Expected outputs:

```text
/tmp/drones-rl-smoke/save-<timestamp>/final_model.zip
/tmp/drones-rl-smoke/save-<timestamp>/best_model.zip
/tmp/drones-rl-smoke/save-<timestamp>/rl_workflow_summary.json
```

The summary JSON contains the chosen env, action/observation types, timesteps, model paths, and a small evaluation result when evaluation succeeds.

## Train and immediately play back

Use this for an end-to-end usability smoke. It is the quickest way to prove that training saved a loadable PPO model and playback can run headless.

```bash
python scripts/run_rl_workflow.py train-play \
  --output-folder /tmp/drones-rl-train-play \
  --timesteps 256 \
  --play-steps 60 \
  --seed 0
```

The helper trains first, selects the generated `best_model.zip`, then runs playback with `gui=False` unless `--gui` is passed.

## Play a saved model

Always pass the concrete model path from a previous run. Do not rely on the source example's placeholder default `results/best_model.zip`.

```bash
python scripts/run_rl_workflow.py play \
  --model-path /tmp/drones-rl-smoke/save-<timestamp>/best_model.zip \
  --output-folder /tmp/drones-rl-playback \
  --steps 120
```

Playback uses `PPO.load(model_path)`, creates the matching hover environment, predicts deterministic actions, steps the environment, logs the default kinematic/one-dimensional-RPM trajectory with `Logger`, and closes the PyBullet environment.

Use `--gui` only when a display/OpenGL context is available. Use `--realtime` when you want source-like `sync(i, start, env.CTRL_TIMESTEP)` wall-clock pacing; omit it for faster smoke checks.

## Multi-agent hover

The multi-agent task is still a single Gymnasium environment with joint observations/actions, not a PettingZoo-style separate-agent API. Use the same PPO workflow with `--multiagent`.

```bash
python scripts/run_rl_workflow.py train-play \
  --multiagent \
  --num-drones 2 \
  --output-folder /tmp/drones-rl-multi-smoke \
  --timesteps 256 \
  --play-steps 60
```

Default source behavior uses two agents (`DEFAULT_AGENTS = 2`). Increase `--num-drones` only when you have a reason to train a larger joint action/observation space.

## Gymnasium env IDs

The package registers RL env IDs in `gym_pybullet_drones/__init__.py`. Importing `gym_pybullet_drones` performs registration.

```python
import gymnasium as gym
import gym_pybullet_drones  # registers env IDs
from gym_pybullet_drones.utils.enums import ObservationType, ActionType

env = gym.make(
    "hover-aviary-v0",
    gui=False,
    obs=ObservationType.KIN,
    act=ActionType.ONE_D_RPM,
)
obs, info = env.reset(seed=0, options={})
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
```

Use `"multihover-aviary-v0"` plus `num_drones=2` for the multi-agent hover task.

## Source `learn.py` local mode vs helper smoke mode

The source `learn.run(...)` chooses training length with its `local` argument:

- `local=False`: `total_timesteps=int(1e2)`, used by `tests/test_examples.py::test_learn` for CI smoke training.
- `local=True`: `total_timesteps=int(1e7)`, intended for full local training and not safe as an accidental default.

The bundled helper makes the safety choice explicit with `--timesteps`; its default is a short smoke value. For a real training run, deliberately set a larger `--timesteps`, keep the output folder, and record the runtime budget.

## Plotting and logs

- Training writes model artifacts and `rl_workflow_summary.json` into the timestamped run folder.
- Playback writes logger outputs into `--output-folder`; use `--save-log` for a NumPy log file.
- Plotting can open a Matplotlib window; leave `--plot` off in headless automation.
- The source logger layout is best matched by the default `ObservationType.KIN` and `ActionType.ONE_D_RPM` combination. For other action types, the helper still plays the policy but skips source-shape logger entries if they do not fit `Logger.log`'s 20-value state contract.

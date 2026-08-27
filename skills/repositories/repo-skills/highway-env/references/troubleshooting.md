# HighwayEnv cross-cutting troubleshooting

Use this root troubleshooting reference before routing to a focused sub-skill when the failure spans install, import, Gymnasium registration, rendering, optional dependencies, config shape, or long-running rollouts.

## Import or environment registration fails

Symptoms:

- `ModuleNotFoundError: No module named 'highway_env'`
- `gymnasium.error.NameNotFound: Environment highway doesn't exist`
- `gym.make("highway-v0")` works in one process but fails in a subprocess/vector worker

Likely causes:

- `highway-env` is not installed in the active Python environment.
- The process did not import `highway_env` before Gymnasium looked up the ID.
- A spawned worker did not repeat registration/import logic.

Recovery:

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)
env = gym.make("highway-v0")
```

In subprocess/vector workers, put the import inside the factory function or use Gymnasium's module-qualified syntax when appropriate. Run `scripts/check_highway_env_install.py` to prove the active environment can create a selected ID.

## Step loop or API signature mismatch

Symptoms:

- code expects `obs = env.reset()` instead of `(obs, info)`;
- code expects four values from `env.step()`;
- Stable-Baselines3 or another library complains about Gym vs Gymnasium API values.

Recovery: use current Gymnasium signatures and verify that optional RL libraries support Gymnasium. Do not change HighwayEnv internals to satisfy an old wrapper until the wrapper version is checked.

## Rendering returns `None`, opens a window, or fails headlessly

Rules of thumb:

- `render_mode=None`: `env.render()` returns `None`.
- `render_mode="rgb_array"`: `env.render()` returns an RGB array and is the right choice for headless capture.
- `render_mode="human"`: opens a pygame window and returns `None`.

If rendering fails in a remote/headless environment, first run non-rendering smoke. If only rendering fails, route to the simulation or training rendering references. Avoid `human` mode in CI, vector workers, or server processes.

## Optional RL dependencies are missing

`highway-env` does not install Stable-Baselines3, Torch, rl-agents, old baselines/HER packages, Colab helpers, or display-server helpers. If a training example imports one of these libraries, install and verify it as a project dependency. For package-level validation, use the bundled random-policy helpers that do not import RL frameworks.

## Config dictionaries fail or spaces are surprising

Symptoms:

- unknown observation/action type;
- action dimension differs from what a policy outputs;
- observation shape changed after a config edit;
- reward components are missing from `info`;
- parking success or goal arrays are unclear.

Recovery:

1. Route to `sub-skills/observations-actions-rewards/SKILL.md`.
2. Run `sub-skills/observations-actions-rewards/scripts/inspect_spaces.py` with the exact env ID and config JSON.
3. Validate the observation/action space before constructing a policy.
4. If the config depends on road geometry or custom environment internals, route to the road/vehicle sub-skill.

## Rollouts, training, or videos run too long

HighwayEnv examples and RL tutorials can contain long training budgets or open-ended policy evaluation loops. For automation:

- use explicit `episodes` and `max_steps` caps;
- keep the first SB3/Torch run to a smoke budget;
- do not record every episode during long training;
- close environments and video wrappers;
- distinguish random-policy crash rate from package failure.

Route long-run training, evaluation, and recording tasks to `sub-skills/training-and-evaluation/SKILL.md`.

## Custom roads or vehicles behave incorrectly

If vehicles spawn off-lane, neighbour detection misses cars near segment joins, lane indexes are wrong, or custom environment reset/step fails, route to `sub-skills/road-vehicle-dynamics/SKILL.md`. That sub-skill covers `RoadNetwork`, lane coordinates, connected-lane neighbour settings, vehicle/controller classes, obstacles/landmarks, and custom `AbstractEnv` implementation.

## Quick triage commands

```bash
python scripts/check_highway_env_install.py --env-id highway-v0 --steps 3
python scripts/check_highway_env_install.py --env-id highway-v0 --steps 2 --render-rgb
```

If the first command passes and the second fails, treat it as a rendering/headless issue. If both fail, inspect the install/import/registration path first.

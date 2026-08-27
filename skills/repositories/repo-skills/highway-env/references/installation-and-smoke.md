# Installation and smoke checks

Use this reference when a task starts from a fresh Python environment, an import failure, or an uncertain HighwayEnv installation.

## Package names and dependencies

- Distribution name: `highway-env`
- Import package: `highway_env`
- Python support in the inspected package metadata: Python `>=3.10`
- Core dependencies: Gymnasium, NumPy, pygame-ce, matplotlib, pandas, farama-notifications
- Test-only dependencies: pytest, pytest-cov, diff-cover, scipy
- Optional RL/training libraries that are **not** installed by `highway-env`: Stable-Baselines3, Torch, rl-agents, old baselines/HER packages, pyvirtualdisplay, IPython/Colab helpers

Install for package use:

```bash
python -m pip install highway-env
```

or with uv in a project:

```bash
uv add highway-env
```

For local package development, use the project's normal tooling and install test dependencies separately. On Linux machines that build or use pygame from source, SDL development libraries may be needed; binary wheels usually avoid that on common platforms.

## Minimal import and registration check

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)
print(highway_env.__version__)
print(gym.spec("highway-v0"))
```

If `gym.spec("highway-v0")` fails, import `highway_env` in the same process and call `gym.register_envs(highway_env)` before creating the environment. The registration call is idempotent.

## Root smoke helper

Run the bundled helper from the root of this generated skill directory:

```bash
python scripts/check_highway_env_install.py --env-id highway-v0 --steps 3
```

Useful options:

```bash
python scripts/check_highway_env_install.py --env-id parking-v0 --steps 2
python scripts/check_highway_env_install.py --env-id highway-v0 --steps 2 --render-rgb
python scripts/check_highway_env_install.py --env-id intersection-multi-agent-v1 --steps 1
```

The helper prints JSON with:

- HighwayEnv version;
- registered HighwayEnv environment IDs;
- selected environment ID;
- observation and action space summaries;
- number of executed steps;
- final termination/truncation state;
- last reward and info keys;
- optional RGB render shape.

Use this helper before longer rollouts, training, videos, or custom environment work.

## When to use sub-skill helpers instead

- Need a full environment rollout smoke with config JSON and render-mode fallback: use `sub-skills/simulation-environments/scripts/smoke_env_rollout.py`.
- Need to inspect spaces, action labels, goal observation keys, or `info["rewards"]`: use `sub-skills/observations-actions-rewards/scripts/inspect_spaces.py`.
- Need to validate the SciPy-free spline interpolation helper: use `sub-skills/road-vehicle-dynamics/scripts/check_spline_interp.py`.
- Need episode-return summaries for random-policy evaluation: use `sub-skills/training-and-evaluation/scripts/random_policy_rollout.py`.

## Expected smoke signals

A healthy base install should be able to:

1. import `highway_env`;
2. register HighwayEnv Gymnasium specs;
3. create `highway-v0`;
4. reset with a seed;
5. sample and step at least one action;
6. close the environment cleanly.

Rendering is a separate capability. If non-rendering smoke passes but `--render-rgb` fails, route to rendering troubleshooting instead of treating the whole package as broken.

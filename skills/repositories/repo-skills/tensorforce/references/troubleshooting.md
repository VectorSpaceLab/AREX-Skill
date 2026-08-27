# Cross-Cutting Troubleshooting

## Import or install fails

Symptoms:

- pip reports incompatible `numpy` and `tensorflow` requirements;
- `ModuleNotFoundError: gym` or optional adapter modules;
- TensorFlow imports but Tensorforce fails on old NumPy/Gym API assumptions.

Recovery:

1. Use an isolated Python environment; avoid changing a shared base environment.
2. Prefer Python 3.8 for Tensorforce 0.6.x when exact old pins are important.
3. Read [installation and inspection](installation-and-inspection.md) for the known TensorFlow/NumPy resolver conflict.
4. Run `scripts/check_tensorforce_env.py --smoke-agent` after every dependency change.
5. Install optional extras only for selected workflows.

## TensorFlow warnings

Tensorforce may trigger warnings about moved TensorFlow internals or CPU/GPU device discovery. Treat warnings as informational only if import and a one-step smoke pass. Treat them as blocking when TensorFlow import fails, device placement fails for a required backend, or model construction crashes.

## Gym/Gymnasium mismatch

Tensorforce 0.6.x expects Gym-era APIs. If the user has Gymnasium-only environments, wrap them carefully or install a Gym-compatible adapter. For Tensorforce `Environment.create(environment='gym', level='CartPole-v1')`, verify the installed Gym package can create that level.

## Optional adapter unavailable

CARLA, ALE, Retro, ViZDoom, OpenSim/PLE, Box2D, and Atari workflows may require Python extras, non-Python assets, simulator processes, ROMs, displays, or native libraries. Keep the core Tensorforce workflow on CPU/custom CartPole until those prerequisites are explicitly available.

## Long or hanging runs

Most RL examples are training loops, not smoke tests. If a run hangs or takes too long, reduce `num_episodes`, set `max_episode_timesteps`, turn off visualization, avoid socket remote modes, and test with `agent='random'` before debugging PPO/DQN configuration.

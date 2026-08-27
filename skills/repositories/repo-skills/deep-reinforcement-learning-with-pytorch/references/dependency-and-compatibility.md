# Dependency and Compatibility Notes

## What the source checkout actually uses

- PyTorch for all neural RL workflows.
- Gym for environments.
- tensorboardX for some logging variants.
- pandas and matplotlib only for the tabular toy examples and curve plotting.
- pygame and box2d-py for BipedalWalker support.
- TensorFlow appears in `requirements.txt` but no discovered source file imports it.
- `gym[atari]` appears in `requirements.txt` but no Atari workflow was discovered.

## Modern inspection environment snapshot

The verification environment used for distillation was:

- Python 3.10.20
- torch 2.2.2+cu121
- gym 0.23.1
- tensorboardX 2.6.5
- numpy 1.26.4
- pandas 2.3.3
- matplotlib 3.10.9
- seaborn 0.13.2
- pygame 2.6.1
- box2d-py 2.3.8

## Legacy Gym conventions in the source

The repository was written against the older Gym API:

- `state = env.reset()`
- `next_state, reward, done, info = env.step(action)`
- `env.seed(seed)`

Gym 0.23.1 still supports the old 4-value step style for classic-control envs, but newer Gym or Gymnasium installs may not. If you modernize the code, update reset/step handling together instead of patching only one call site.

## Legacy env names and modern substitutes

The source scripts and README use legacy names such as:

- CartPole-v0
- MountainCar-v0
- Pendulum-v0
- BipedalWalker-v2

In the verified environment, the modern substitutes that work are:

- Pendulum-v1
- BipedalWalker-v3

CartPole-v0 and MountainCar-v0 still work in the inspection env, but they are also legacy IDs. Keep them as compatibility notes when explaining the repository.

## Backend expectations

- CPU is enough for understanding and routing every family in this repo.
- CUDA is optional. The scripts switch to CUDA when Torch sees it.
- Box2D is only relevant for the BipedalWalker variants.
- If you only need inspection or compatibility, do not install optional extras for unrelated families.

## Practical compatibility reminders

- DDPG, SAC, and TD3 build checkpoint directories from the script name plus the env name. Changing the env ID changes the expected checkpoint path.
- Older Gym code often relies on `env.render()` inside the training loop; keep that off for headless runs.
- NumPy 2 compatibility can matter for legacy code. The inspection env used NumPy 1.26.4 to avoid deprecated alias issues and to keep the old RL scripts closer to their source assumptions.

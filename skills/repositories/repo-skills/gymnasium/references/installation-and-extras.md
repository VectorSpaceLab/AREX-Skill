# Gymnasium Installation and Optional Extras

Gymnasium's base install covers the core API, spaces, wrappers, vectorization, Classic Control IDs without human rendering dependencies, Toy Text logic, and registry inspection. Optional extras are family- or workflow-specific; install the smallest extra that matches the task.

## Base Install

```bash
pip install gymnasium
```

Minimal import check:

```python
import gymnasium as gym
print(gym.__version__)
print(gym.spec("CartPole-v1"))
```

## Optional Extras

| Extra | Use when | Adds |
| --- | --- | --- |
| `gymnasium[classic-control]` or `gymnasium[classic_control]` | Classic Control rendering or PyGame-backed human windows | `pygame-ce` |
| `gymnasium[toy-text]` or `gymnasium[toy_text]` | Toy Text rendering assets or PyGame-backed display | `pygame-ce` |
| `gymnasium[box2d]` | `LunarLander`, `BipedalWalker`, `CarRacing` and Box2D physics/rendering | Box2D package, `pygame-ce`, `swig` |
| `gymnasium[mujoco]` | MuJoCo environments such as `Ant-v5`, `HalfCheetah-v5`, `Hopper-v5`, `Humanoid-v5` | `mujoco`, `imageio`, `packaging` |
| `gymnasium[atari]` | Atari/ALE plugin environments and `ALE/...` IDs | `ale_py` |
| `gymnasium[other]` | Video recording helpers and plotting/image utilities | `moviepy`, `matplotlib`, `opencv-python`, `seaborn` |
| `gymnasium[array-api]` | Array API conversion wrappers without committing to JAX or Torch workflows | `array-api-compat`, newer NumPy, `packaging` |
| `gymnasium[jax]` | JAX/Flax conversion or functional workflows | `jax`, `jaxlib`, `flax`, `array-api-compat` |
| `gymnasium[torch]` | Torch conversion wrappers | `torch`, `array-api-compat` |
| `gymnasium[all]` | Disposable broad test environments where every backend is intentionally needed | Most optional families and utility extras |

Avoid `gymnasium[all]` for ordinary agent tasks. It pulls multiple compiled or backend packages that are unnecessary for most environment loops, wrappers, and spaces work.

## Family Selection

- Use `CartPole-v1`, `MountainCar-v0`, `Pendulum-v1`, or `Acrobot-v1` for lightweight control examples.
- Use `Taxi-v4`, `FrozenLake-v1`, `Blackjack-v1`, or `CliffWalking-v1` for discrete debugging, tabular methods, or action-mask examples.
- Use Box2D or MuJoCo only when the task explicitly needs those physics families.
- Use Atari/ALE only when the task names Atari, ALE, ROMs, emulator preprocessing, or Atari-specific wrappers.

## Verification Commands

After installing an extra, verify only the targeted family:

```python
import gymnasium as gym

env = gym.make("CartPole-v1")
obs, info = env.reset(seed=123)
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
```

For vectorization:

```python
import gymnasium as gym

envs = gym.make_vec("CartPole-v1", num_envs=2, vectorization_mode="sync")
obs, info = envs.reset(seed=123)
obs, rewards, terminated, truncated, info = envs.step(envs.action_space.sample())
envs.close()
```

For optional media recording, verify that `moviepy` is importable before adding `RecordVideo` to longer workflows.

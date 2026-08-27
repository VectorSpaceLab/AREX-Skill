# Optional Dependencies and Minimal Extras

Gymnasium intentionally keeps the base install small. Most built-in environment families are discoverable from the registry, but optional simulators, renderers, media tools, and array frameworks are installed only when requested.

## Rule of Thumb

1. Start with `pip install gymnasium` for API work, Classic Control stepping, Toy Text stepping, registry inspection, spaces, wrappers, and vector basics.
2. Add exactly one family extra when an environment backend or renderer needs it.
3. Avoid `gymnasium[all]` for normal projects. It pulls broad simulator, media, array-framework, and visualization dependencies that are unnecessary for most tasks and can create platform-specific failures.
4. Verify with `gym.spec(...)` and one short reset/step before adding training, rendering, recording, or vectorization.

## Extras Map

| Extra | Installs / enables | Use when | Avoid when |
| --- | --- | --- | --- |
| `gymnasium[classic-control]` or `gymnasium[classic_control]` | `pygame-ce` | Rendering Classic Control with `human` or `rgb_array` | Only stepping `CartPole-v1` headlessly |
| `gymnasium[toy-text]` or `gymnasium[toy_text]` | `pygame-ce` | Graphical Toy Text rendering | Only using text/tabular stepping or Taxi masks without GUI |
| `gymnasium[box2d]` | Box2D bindings, `pygame-ce`, SWIG-related build support | `LunarLander`, `BipedalWalker`, or `CarRacing` | Classic Control, Toy Text, MuJoCo, wrappers, spaces |
| `gymnasium[mujoco]` | `mujoco`, `imageio`, `packaging` | MuJoCo locomotion/robotics IDs such as `Ant-v5` | Box2D or Atari tasks |
| `gymnasium[atari]` | `ale_py` | ALE/Atari plugin environments such as `ALE/...` IDs | Classic Control/Toy Text/Box2D/MuJoCo tasks |
| `gymnasium[jax]` | `jax`, `jaxlib`, `flax`, `array-api-compat`, newer NumPy | JAX functional/tabular/phys2d experiments or JAX array outputs | Ordinary NumPy environments |
| `gymnasium[torch]` | `torch`, `array-api-compat`, newer NumPy | Torch conversion wrappers or Torch array interop | Environment selection alone |
| `gymnasium[array-api]` | `array-api-compat`, newer NumPy, `packaging` | Array API conversion wrappers without committing to a full framework extra | Basic spaces/env loops |
| `gymnasium[other]` | `moviepy`, `matplotlib`, `opencv-python`, `seaborn` | Video saving/recording helpers, plotting/tutorial media utilities | Rendering an env window, non-video wrappers, backend installs |
| `gymnasium[testing]` | Pytest and test support packages | Running Gymnasium's own test suite | User projects that only consume environments |
| `gymnasium[all]` | Broad union of most optional dependencies | Disposable full-featured CI image or local experimentation across many families | Reproducible minimal projects, constrained machines, debugging one missing backend |

## Minimal Install Examples

Classic Control smoke without rendering:

```bash
pip install gymnasium
python - <<'PY'
import gymnasium as gym
env = gym.make("CartPole-v1")
obs, info = env.reset(seed=0)
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
print("ok")
PY
```

Classic Control or Toy Text rendering:

```bash
pip install "gymnasium[classic-control]"
pip install "gymnasium[toy-text]"
```

Box2D family:

```bash
pip install swig
pip install "gymnasium[box2d]"
```

MuJoCo family:

```bash
pip install "gymnasium[mujoco]"
```

Atari/ALE family:

```bash
pip install "gymnasium[atari]"
```

Recording videos or using media utilities:

```bash
pip install "gymnasium[other]"
```

## Verification Snippets

Check that an ID is registered before instantiating its backend:

```python
import gymnasium as gym

for env_id in ["CartPole-v1", "Taxi-v4", "LunarLander-v3", "Ant-v5"]:
    try:
        spec = gym.spec(env_id)
    except gym.error.Error as exc:
        print(env_id, "not registered:", exc)
    else:
        print(env_id, "registered via", spec.entry_point)
```

Check that a family backend can run a short episode:

```python
import gymnasium as gym

env = gym.make("CartPole-v1")
obs, info = env.reset(seed=7)
for _ in range(3):
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
    if terminated or truncated:
        obs, info = env.reset()
env.close()
```

## Backend-Specific Cautions

- `pygame-ce` is mainly a rendering dependency for Classic Control, Toy Text, Box2D, and related visual environments. Missing `pygame` errors usually mean the family render extra is absent, not that the environment API is broken.
- Box2D Python bindings may need SWIG at build time. Install `swig` before retrying the Box2D extra when wheels are unavailable.
- MuJoCo rendering failures may require selecting an OpenGL backend with `MUJOCO_GL`, even when `mujoco` imports successfully.
- Atari requires both Python package support and ROM/license availability. A missing `ALE/...` registry entry and a missing ROM are different failures.
- `moviepy` belongs to recording/video helpers, not to environment rendering in general. Route `RecordVideo` and `save_video` setup to `../wrappers-recording/SKILL.md`.
- JAX/Torch conversion wrappers are optional framework integrations. Do not install them solely to use standard NumPy observations from most built-in environments.

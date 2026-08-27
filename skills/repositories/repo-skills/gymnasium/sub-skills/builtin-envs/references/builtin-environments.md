# Built-in Environment Families

Gymnasium's base package registers a reference set of environment specs, but not every family can be instantiated without its optional backend. Treat the registry as an availability map, then choose the smallest family and extra for the job.

## Inspect the Registry First

```python
import gymnasium as gym

print(len(gym.registry))
print(gym.spec("CartPole-v1"))
print(sorted(env_id for env_id in gym.registry if env_id.startswith("CartPole")))
gym.pprint_registry()
```

Useful checks:

- `gym.spec(env_id)` proves the ID is registered and exposes `entry_point`, `max_episode_steps`, `reward_threshold`, `kwargs`, `nondeterministic`, and wrapper-related spec fields.
- `gym.make(env_id, disable_env_checker=True)` skips checker wrappers only when diagnosing a known checker issue; leave it at the default for normal use.
- A registered spec can still fail at `gym.make(...)` if the family backend is missing, such as Box2D, MuJoCo, `pygame`, or a plugin-provided Atari namespace.
- Environment IDs are versioned for reproducibility. Use the exact registered suffix such as `CartPole-v1`, `Taxi-v4`, `LunarLander-v3`, or `Ant-v5`.

## Family Selection Matrix

| Family | Typical IDs | Best use | Base install behavior | Minimal extra when needed |
| --- | --- | --- | --- | --- |
| Classic Control | `CartPole-v1`, `MountainCar-v0`, `MountainCarContinuous-v0`, `Pendulum-v1`, `Acrobot-v1` | Fast smoke tests, simple control, tutorials, regression checks | Non-rendered stepping is lightweight; human/rgb rendering needs `pygame-ce` | `gymnasium[classic-control]` for rendering |
| Toy Text | `Taxi-v4`, `FrozenLake-v1`, `FrozenLake8x8-v1`, `Blackjack-v1`, `CliffWalking-v1`, `CliffWalkingSlippery-v1` | Discrete debugging, tabular RL, deterministic/stochastic toy tasks, Taxi masks | Non-rendered stepping is lightweight; graphical rendering needs `pygame-ce`; text modes may be available for selected envs | `gymnasium[toy-text]` for graphical rendering |
| Box2D | `LunarLander-v3`, `LunarLanderContinuous-v3`, `BipedalWalker-v3`, `BipedalWalkerHardcore-v3`, `CarRacing-v3` | Physics-control toy benchmarks with visual rendering | Specs may be registered, but instantiation needs Box2D bindings and often `pygame-ce` | Install `swig`, then `gymnasium[box2d]` |
| MuJoCo | `Reacher-v5`, `Pusher-v5`, `InvertedPendulum-v5`, `HalfCheetah-v5`, `Hopper-v5`, `Swimmer-v5`, `Walker2d-v5`, `Ant-v5`, `Humanoid-v5`, `HumanoidStandup-v5` | Robotics/locomotion benchmarks and continuous-control evaluation | Specs may be registered, but instantiation needs `mujoco`; rendering needs a working OpenGL backend | `gymnasium[mujoco]` |
| Atari/ALE | Plugin IDs such as `ALE/Pong-v5` after ALE registration | Atari 2600 benchmark tasks | Base Gymnasium does not register ALE IDs by itself | `gymnasium[atari]` plus ALE ROM/license handling |
| Tabular/JAX | `tabular/Blackjack-v0`, `tabular/CliffWalking-v0` | Limited advanced tabular/JAX-compatible surfaces | May return JAX arrays or need conversion wrappers/framework extras in downstream code | `gymnasium[jax]`, `gymnasium[array-api]`, or framework-specific extras when converting arrays |
| Phys2D/JAX Classic Control | `phys2d/CartPole-v1`, `phys2d/Pendulum-v0` | Limited JAX/functional experiments and vectorized JAX surfaces | Advanced surface; render metadata is narrower and conversion wrappers may need extras | `gymnasium[jax]` and related conversion extras as needed |

## Classic Control Notes

- Registered base IDs include `CartPole-v0`, `CartPole-v1`, `MountainCar-v0`, `MountainCarContinuous-v0`, `Pendulum-v1`, and `Acrobot-v1`.
- These are good first smoke tests because base stepping is fast and does not require simulator backends.
- Use `CartPole-v1` as the default sanity check unless the task specifically asks for the older `v0` horizon.
- Rendering modes commonly include `human` and `rgb_array`; install the classic-control extra for `pygame-ce` when rendering.
- Some Classic Control specs provide vector entry points; route vectorized usage to `../vectorization/SKILL.md`.

## Toy Text Notes

- Registered IDs include `Blackjack-v1`, `FrozenLake-v1`, `FrozenLake8x8-v1`, `CliffWalking-v1`, `CliffWalkingSlippery-v1`, and `Taxi-v4`.
- These are best for discrete action/observation debugging and tabular examples.
- `Taxi-v4` returns `info["action_mask"]` from both `reset()` and `step()`; do not assume every Toy Text or discrete environment exposes a mask.
- Some environments support `render_mode="ansi"` for text output in addition to `human`/`rgb_array`; inspect `env.metadata["render_modes"]` for the actual modes.
- Long Blackjack/FrozenLake Q-learning tutorials are useful conceptually, but do not copy full training loops into quick diagnostics.

## Box2D Notes

- Registered IDs include `LunarLander-v3`, `LunarLanderContinuous-v3`, `BipedalWalker-v3`, `BipedalWalkerHardcore-v3`, and `CarRacing-v3`.
- Box2D imports fail early if the Box2D binding is unavailable. The relevant fix is not `gymnasium[all]`; install SWIG if needed and then the Box2D extra.
- Rendering depends on `pygame-ce`. Use non-rendered short episodes for backend verification before adding human rendering.
- Use `gym.spec("LunarLander-v3")` to confirm registration, then `env = gym.make("LunarLander-v3")` to confirm the backend is importable.

## MuJoCo Notes

- Prefer current `v5` IDs for new work unless a paper, benchmark, or reproducibility task names `v4`.
- Older `v2`/`v3` MuJoCo IDs are compatibility placeholders that raise an import error directing users to `gymnasium-robotics` for `mujoco-py`-based environments.
- `gymnasium[mujoco]` installs the Python MuJoCo binding plus support packages used by Gymnasium's MuJoCo environments.
- Render modes include image and depth variants for many MuJoCo envs. OpenGL backend selection uses `MUJOCO_GL=glfw`, `MUJOCO_GL=egl`, or `MUJOCO_GL=osmesa` depending on the machine.
- MuJoCo action spaces are continuous `Box` spaces; mis-shaped actions raise action-dimension errors rather than being silently accepted.

## Atari/ALE Plugin Notes

- Base Gymnasium does not register `ALE/...` IDs in the verified base install. If `gym.spec("ALE/Pong-v5")` fails, diagnose plugin/extra/ROM setup before changing RL code.
- Install the Atari extra for `ale_py`, then register plugin environments according to the ALE package behavior for the installed version.
- ROM availability and license acceptance are separate from installing the Python package. An ALE import can succeed while a specific ROM still fails.
- Multi-agent Atari belongs in PettingZoo or another Farama project, not in single-agent Gymnasium built-ins.

## Third-party Compatibility Signals

- Third-party packages may expose Gymnasium-compatible environments through their own registration side effects or package entry points.
- Check the third-party project's declared Gymnasium version. Older packages may target Gym or early Gymnasium APIs.
- If an old Gym environment needs compatibility wrapping, use the `shimmy` guidance in `references/troubleshooting.md` and route reset/step API migration details to `../environment-api/SKILL.md`.
- Do not assume third-party environment IDs exist in `gym.registry` until the package is installed and its registrations have run.

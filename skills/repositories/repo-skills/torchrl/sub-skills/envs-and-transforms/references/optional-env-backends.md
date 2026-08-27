# Optional environment backends

The CPU-verified operating floor for this sub-skill uses native TorchRL environments. Treat third-party simulators, rendering stacks, and pixel backends as optional until the exact dependency is installed and a local smoke check passes.

## Backend selection table

| Need | TorchRL surface | Dependency family | First smoke check |
| --- | --- | --- | --- |
| Classic Gym/Gymnasium task by id | `GymEnv("EnvName-vX")` | `gym` or `gymnasium` plus task extras | Construct one env, run `check_env_specs`, run `rollout(3)`. |
| Existing Gym/Gymnasium object | `GymWrapper(gym_env)` | Same as above | Wrap the object, inspect converted specs, run `check_env_specs`. |
| Continuous Gym MuJoCo tasks | `GymEnv` through Gymnasium | Gymnasium plus MuJoCo | Import backend, construct a non-pixel env first, then add rendering if needed. |
| DeepMind Control | `DMControlEnv` / wrapper | `dm_control` and MuJoCo runtime | Import backend before rendering config mistakes accumulate; run a tiny no-pixel rollout. |
| Native MuJoCo env families | TorchRL MuJoCo envs | MuJoCo or selected physics backend | Start with no rendering; validate specs and deterministic reset behavior. |
| VMAS/PettingZoo/OpenSpiel multi-agent | multi-agent wrappers | MARL or OpenSpiel packages | Inspect group keys, `action_key`, `reward_key`, `done_key`; then run `check_env_specs`. |
| Brax/Jumanji/JAX-backed envs | library wrappers | JAX plus backend package | Confirm compatible Python/JAX versions, then run a tiny CPU or accelerator smoke. |
| IsaacLab/Isaac simulation | `IsaacLabWrapper` | Isaac/Kit/Gymnasium stack | Launch simulator app before constructing envs; verify camera/rendering settings separately. |
| Pixel observations | `from_pixels=True`, image transforms | simulator render support plus image deps | Verify raw pixel key shape/dtype before TorchRL image transforms. |
| Video/rendering helpers | recorders/render CLI | rendering/video extras and codecs | Check CLI/help/import first; then run a tiny no-training render. |

## Gym and Gymnasium

TorchRL can select which backend powers `GymEnv` through `set_gym_backend`.

```python
from torchrl.envs.libs.gym import GymEnv, GymWrapper, set_gym_backend

with set_gym_backend("gymnasium"):
    env = GymEnv("Pendulum-v1")
```

If automatic construction by id fails but direct Gym/Gymnasium construction works, build the backend env yourself and pass it to `GymWrapper`.

```python
import gymnasium as gym
from torchrl.envs.libs.gym import GymWrapper

backend_env = gym.make("CartPole-v1")
env = GymWrapper(backend_env)
```

Failure triage:

- `ModuleNotFoundError: gym` or `gymnasium`: install the selected backend.
- Environment id not found: install the task extra package or register the custom env before `GymEnv` construction.
- Converted Dict/Tuple/Sequence observations look wrong: inspect converted specs and test `return_contiguous=False` for sequence-like data.
- Gym and Gymnasium both installed: wrap construction in `set_gym_backend(...)` so the intended package is unambiguous.

## MuJoCo and DM Control rendering

MuJoCo-style render failures are often platform/runtime problems rather than TorchRL spec problems. Use this order:

1. Verify import of the physics package.
2. Run a non-rendering env smoke.
3. Select the rendering backend before importing the simulator when headless rendering is needed.
4. Add pixel keys and image transforms only after raw pixels are visible.
5. For vectorized pixel environments, benchmark: rendering may serialize through a single graphics device even when many compute devices exist.

Common generic environment variables such as `MUJOCO_GL=egl`, `MUJOCO_GL=osmesa`, or `MUJOCO_GL=glfw` may be relevant for MuJoCo-family rendering. They must be set before the simulator import. Choose the value that matches the host graphics stack.

## IsaacLab and heavy simulators

Heavy simulators often have their own app launcher and import-order rules. For IsaacLab-style workflows:

- start the simulator app before importing or constructing simulator environments;
- use the simulator's Gymnasium registration after tasks are imported;
- remember that many Isaac environments are already internally batched;
- keep rendering/camera enablement separate from state-only control smokes;
- close the simulator app explicitly after a smoke or training run.

Do not turn a missing Isaac, Habitat, VMAS, PettingZoo, OpenSpiel, Brax, Jumanji, or rendering dependency into a required TorchRL failure unless the user's task explicitly selected that backend.

## Pixel and rendering dependencies

Pixel pipelines combine at least three layers: simulator rendering, TorchRL wrapper options, and transform dependencies.

Checklist:

```python
td = env.reset()
print(td.keys(True, True))
print(td.get("pixels").shape, td.get("pixels").dtype)
```

Then add transforms:

```python
from torchrl.envs.transforms import Compose, Resize, ToTensorImage

transform = Compose(
    ToTensorImage(in_keys=["pixels"]),
    Resize(64, 64, in_keys=["pixels"]),
)
```

Typical failures:

- no pixel key: backend env was not constructed with pixel/render mode enabled;
- empty/black frames: headless graphics backend not configured or camera not enabled;
- dtype mismatch: image transform order is wrong;
- codec error: rendering/video optional packages or system codecs are missing.

## Optional backend smoke template

Use this minimal pattern before adapting a larger example:

```python
from torchrl.envs import check_env_specs

# Construct the smallest version of the chosen backend env.
env = make_env_without_training_or_rendering()
try:
    check_env_specs(env, seed=0)
    rollout = env.rollout(max_steps=3)
    assert "next" in rollout.keys()
finally:
    env.close()
```

Only after this passes should you add transforms, vectorization, collectors, policies, pixels, rendering, or long training.

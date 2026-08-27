# Environment Integration

This reference covers built-in environment adapters, optional dependency
boundaries, custom environment checklists, and wrapper ordering for DreamerV3's
Embodied layer.

## Safe baseline: dummy environment

Use the dummy environment for dataflow checks that must not depend on optional
system packages:

```python
from embodied.envs import dummy

env = dummy.Dummy('disc', size=(64, 64), length=100)
print(env.obs_space)
print(env.act_space)
obs0 = env.step({'reset': True, 'act_disc': 0, 'act_cont': [0.0] * 6})
```

Contract properties:

- Observations include `image`, `vector`, `token`, `count`, two 2D test arrays,
  `reward`, `is_first`, `is_last`, and `is_terminal`.
- Actions include mandatory `reset`, discrete `act_disc`, and continuous
  `act_cont`.
- Reset returns an `is_first` observation. After `length` non-reset steps,
  `is_last=True` and `is_terminal=True`.

Use dummy for checker, replay, driver, and integration smoke before attempting
Atari, Mujoco, Minecraft, DMLab, or other optional adapters.

## Built-in adapter map

| Adapter | Dependency boundary | Input/task | Observation/action shape highlights | Notes |
| --- | --- | --- | --- | --- |
| `dummy.Dummy` | base package only | arbitrary task string ignored | `image` uint8, vector/token/count fixtures, `act_disc`, `act_cont`, `reset` | Safest contract reference and smoke target. |
| `from_gym.FromGym` | `gym` plus the requested Gym env package | env instance or env id string | Dict spaces are flattened with `/`; non-dict obs/action use keys such as `image` and `action`; adds `reward`, `is_first`, `is_last`, `is_terminal`, and `reset` | Uses `info.get('is_terminal', done)` when available. Close delegates to Gym env. |
| `from_dm.FromDM` | DM-style environment package | env instance with `observation_spec()` and `action_spec()` | Non-dict observations use `observation`; action key defaults to `action`; slashes in obs keys become `_`; `reward` observations are renamed `obs_reward` | Terminal is inferred from discount `0` on non-first time steps. Empty observation specs are dropped. |
| `atari.Atari` | `ale_py`, ROM availability/AutoROM, Pillow; optional OpenCV for resize | Atari game name | `image` uint8 `(H,W,1 or 3)`, discrete `action`, `reset` | Supports repeat, sticky actions, no-ops, life handling, action-set selection, reward clipping, ROM path via `ALE_ROM_PATH`. |
| `crafter.Crafter` | `crafter` | `reward` or `noreward` | `image`, `reward`, flags, discrete `action`, optional `log/achievement_*` | Can write Crafter stats JSONL when logging is enabled. |
| `dmc.DMC` | `dm_control`, Mujoco renderer/system libs | DM Control task string or env instance | Uses `FromDM`, optional proprio, rendered `image` or `log/image`, continuous actions | Sets `MUJOCO_GL=egl` if unset. Checks finite continuous actions and finite floating observations. |
| `dmlab.DMLab` | `deepmind_lab` and level assets | DMLab level | `image`, optional `instr` embedding, discrete `action` | Supports train/eval level handling, action-set presets, episodic/non-episodic terminal behavior. |
| `loconav.LocoNav` | `dm_control`, locomotion, labmaze, matplotlib, Mujoco renderer | walker/maze name | DMC-derived observations plus `log/coverage` | Applies weaker action scaling and maze coverage logs. |
| `minecraft.Minecraft` | MineRL stack, Java/Minecraft resources, many system deps | `wood`, `climb`, or `diamond` | `image`, inventory/equipped/health/hunger/breath features, discrete high-level action | Heavy integration. Treat import/runtime failures as optional env dependency issues. |
| `pinpad.PinPad` | base NumPy/elements only | `three` through `eight` | `image` uint8 `(64,64,3)`, discrete `action`, `reset` | Lightweight gridworld with long-horizon memory sequence. |
| `procgen.ProcGen` | `procgen`, Gym registration, Pillow or OpenCV | ProcGen task name | Gym-derived spaces with `image` resized to configured size | Uses step image at 64x64; otherwise fetches RGB from env info/render path. |
| `bsuite.BSuite` | `bsuite` and DM-style dependencies | BSuite checkpoint id or task name | DM-derived spaces | Stateful result logging; interruption/restart behavior can be surprising. If adapter-level wrappers differ across versions, use `FromDM` plus explicit local wrappers. |

Optional adapter failures should be isolated from the core DreamerV3 dataflow
contract. If `dummy`, custom Env, driver, and replay pass but an optional adapter
fails to import, route installation and system package diagnosis to `results-ops`.

## Custom environment checklist

Before training a custom environment, verify all of the following:

1. **Factory**: expose a zero-argument factory, for example `def make_env():
   return MyEnv(...)`. `Driver(parallel=True)` requires picklable factories and
   child-process-safe imports.
2. **Action reset**: `act_space` contains `reset: elements.Space(bool)`. The
   policy should not produce `reset`; the driver does.
3. **Mandatory observations**: every returned observation has `reward`,
   `is_first`, `is_last`, and `is_terminal`.
4. **Spaces match values**: every value returned by `step()` belongs to the
   corresponding `elements.Space` dtype, shape, and bounds.
5. **No key overlap**: observation and action key sets are disjoint.
6. **Reset step**: `step({'reset': True, ...})` resets internal state and returns
   an `is_first=True` observation without also setting `is_last=True`.
7. **Terminal step**: the final normal step of an episode sets `is_last=True`.
   Set `is_terminal=True` only for terminal environment endings, not every
   time-limit cut unless that is the task definition.
8. **Log keys**: put metrics not needed by the policy under `log/` prefixes.
9. **Close**: implement `close()` to release windows, processes, files, sockets,
   or simulator handles.
10. **Single-process first**: pass `Driver([make_env], parallel=False)` before
    enabling parallel workers.

A compact adapter skeleton:

```python
import elements
import embodied
import numpy as np

class MyEnv(embodied.Env):
  def __init__(self, length=100):
    self.length = length
    self.stepnum = 0
    self.done = True

  @property
  def obs_space(self):
    return {
        'vector': elements.Space(np.float32, (4,), -np.inf, np.inf),
        'reward': elements.Space(np.float32),
        'is_first': elements.Space(bool),
        'is_last': elements.Space(bool),
        'is_terminal': elements.Space(bool),
    }

  @property
  def act_space(self):
    return {
        'reset': elements.Space(bool),
        'action': elements.Space(np.int32, (), 0, 3),
    }

  def step(self, action):
    if bool(np.asarray(action['reset']).item()) or self.done:
      self.stepnum = 0
      self.done = False
      return self._obs(0.0, is_first=True)
    self.stepnum += 1
    self.done = self.stepnum >= self.length
    return self._obs(1.0, is_last=self.done, is_terminal=self.done)

  def _obs(self, reward, is_first=False, is_last=False, is_terminal=False):
    return {
        'vector': np.zeros(4, np.float32),
        'reward': np.float32(reward),
        'is_first': bool(is_first),
        'is_last': bool(is_last),
        'is_terminal': bool(is_terminal),
    }
```

Then run:

```bash
python scripts/check_embodied_contracts.py --mode env --factory my_pkg.envs:make_env
python scripts/check_embodied_contracts.py --mode driver --factory my_pkg.envs:make_env
```

## Wrapper responsibilities

| Wrapper | Use when | Important behavior |
| --- | --- | --- |
| `TimeLimit(env, duration, reset=True)` | Need to cut episodes/segments after a fixed number of non-reset steps. | With `reset=True`, forwards a reset to the inner env after limit/done. With `reset=False`, can mark the next observation `is_first=True` without inner reset. |
| `ActionRepeat(env, repeat)` | Need frame/action repeat with accumulated reward. | Bypasses repeat on reset. Stops early on `is_last` or `is_terminal`. |
| `NormalizeAction(env, key='action')` | Inner continuous action space has finite bounds but agent should operate in `[-1,1]`. | Exposes normalized finite dimensions and maps back before inner step; leaves non-finite dimensions unchanged. |
| `ClipAction(env, key='action', low=-1, high=1)` | Need a final safety clamp for continuous policy actions. | Clips the configured action key before inner step. Often placed outside `NormalizeAction`. |
| `DiscretizeAction(env, key='action', bins=5)` | Need an integer action over bins for a vector continuous action. | Converts integer bin ids to continuous values in `[-1,1]`; best for vector-shaped continuous spaces. |
| `ResizeImage(env, size=(64,64))` | Image observation spatial size differs from model/config expectation. | Resizes image-like observation keys with Pillow; updates obs space to uint8. |
| `UnifyDtypes(env)` | Backend returns float64/int64 but DreamerV3 expects normalized dtypes. | Converts floats to `np.float32`, integers to `np.int32` except uint8 stays uint8; applies to spaces and step values. |
| `CheckSpaces(env)` | Debugging custom adapters or wrappers. | Checks action and observation values against spaces and rejects obs/action key overlap. Keep it during development. |
| `RestartOnException(ctor, exceptions, window, maxfails, wait)` | Environment crashes transiently and can be reconstructed. | Wraps a constructor, catches selected exceptions, waits, rebuilds env, forces reset, and raises after too many failures. |

## Recommended wrapper order

Wrapper order depends on task, but a safe debugging stack is:

```python
def make_env():
  env = RawOrAdapterEnv(...)
  env = embodied.wrappers.TimeLimit(env, duration=1000)        # if needed
  env = embodied.wrappers.NormalizeAction(env, key='action')   # if continuous
  env = embodied.wrappers.ClipAction(env, key='action')        # clamp policy output
  env = embodied.wrappers.ResizeImage(env, size=(64, 64))      # if needed
  env = embodied.wrappers.UnifyDtypes(env)
  env = embodied.wrappers.CheckSpaces(env)
  return env
```

Read this as inner-to-outer construction. Put `RestartOnException` around a
constructor when the whole env may need recreation:

```python
def make_raw():
  return RawOrAdapterEnv(...)

env = embodied.wrappers.RestartOnException(make_raw, exceptions=(RuntimeError,))
```

If a wrapper changes spaces, inspect `env.obs_space` and `env.act_space` after
stack construction, not just on the raw adapter.

## Adapter-specific validation commands

Use the checker against the dummy default first:

```bash
python scripts/check_embodied_contracts.py --all
```

For a custom or optional adapter, expose a factory and then run:

```bash
python scripts/check_embodied_contracts.py --mode env --factory my_pkg.envs:make_env
python scripts/check_embodied_contracts.py --mode driver --factory my_pkg.envs:make_env --steps 8
```

If those pass but full training fails, preserve the checker output and route the
next investigation according to the failure: config/run-loop to
`train-configure`, JAX/model errors to `jax-models`, or optional package/system
setup to `results-ops`.

# Troubleshooting: Environments and Vectorization

## Install and Import

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: tianshou` | Package is not installed in the active environment | Install Tianshou and rerun a minimal `import tianshou` check before debugging env code. |
| `ModuleNotFoundError: gymnasium` | Core environment dependency missing | Install public Tianshou dependencies or Gymnasium directly. |
| Optional engine import fails | Extra was intentionally not installed | Install only the needed extra/backend, such as Atari, MuJoCo, VizDoom, EnvPool, Box2D, robotics, or Ray. |
| `RayVectorEnv` raises `Please install ray` | Ray is not a default runtime dependency | Install `ray` for supported platforms or use `DummyVectorEnv`/`SubprocVectorEnv`. |

## Data and Config Validation

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `The environment does not adhere to the Gymnasium's API` | `reset()` did not return `(obs, info)` | Update the env to Gymnasium API or add a compatibility wrapper. |
| `Tuple observation space is not supported` | Env reset returned tuple observations | Convert observations to arrays or dictionaries before vectorization. |
| Object-dtype batched observations | Variable-length observations cannot be stacked | Pad, flatten, or encode observations consistently before model/trainer work. |
| `Unsupported space type` from `SpaceInfo` | Space is not `Box` or `Discrete` | Inspect `Dict`, `Tuple`, `MultiDiscrete`, or custom spaces manually, or wrap/flatten before using `SpaceInfo`. |
| PettingZoo assertion about unequal spaces | Agents have different observation/action spaces | Apply SuperSuit padding wrappers before `PettingZooEnv`. |
| Illegal action selected in a PettingZoo game | Policy ignored `obs["mask"]` | Route mask use into the policy/action-selection layer and verify mask shape matches the action space. |

## CLI and API Misuse

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Passing env instances to vector env constructor fails later | Tianshou expects callables, not existing env objects | Pass `[lambda: gym.make(task) for _ in range(n)]` or top-level factories. |
| `action must be not-None for non-async` | `step(None)` used on a synchronous vector env | Pass one action per env, or use async mode intentionally with `wait_num`/`timeout`. |
| Assertion on action length | Number of actions does not match selected env ids | For synchronous mode, pass `len(actions) == len(ids)`; for async mode, follow returned `info.env_id`. |
| Methods assert after `close()` | Closed vector env reused | Recreate the vector env; `close()` is terminal. |
| `set_env_attr` appears ineffective | Attribute is looked up on `env.unwrapped` or a subprocess copy | Confirm the attribute exists on the unwrapped env and remember subprocess workers mutate worker-local envs. |

## Subprocess, Spawn, and Pickling

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Works in `DummyVectorEnv` but fails in `SubprocVectorEnv` | Factory, env class, wrapper, or captured object is not process-safe | Move definitions to importable top-level functions/classes and capture only simple serializable config. |
| Fails only with `context="spawn"` | Spawn cannot import `__main__` local definitions | Put factories/env classes in modules and guard scripts with `if __name__ == "__main__":`. |
| Hangs during subprocess reset/step | Worker process crashed or is waiting on external engine resources | Reproduce with one env, enable direct dummy mode, then inspect optional engine initialization and assets. |
| Shared-memory vector env crashes on observation buffer setup | Observation space has unsupported dtype/shape or custom objects | Use `SubprocVectorEnv(..., share_memory=False)` or simplify observations to fixed-shape NumPy arrays/dicts. |
| macOS/Linux multiprocessing behavior differs | Default multiprocessing context differs by platform and libraries | Try explicit `context="spawn"` or `context="fork"` based on library constraints and keep factories import-safe. |

## Workflow Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Env validation succeeds but training fails | Model/action head does not match space shape or masks | Use this sub-skill to verify spaces, then route model/policy/trainer construction to `../procedural-training/SKILL.md`. |
| EnvPool reset info format surprises wrappers | EnvPool may return vectorized info differently from Tianshou envs | Inspect reset output, set EnvPool Gymnasium flags when available, and keep normalization smoke tests small. |
| Atari/MuJoCo/VizDoom examples fail before Tianshou code runs | Native engines, ROMs/assets, licenses, display, or physics runtimes are missing | Treat those examples as optional backend integration, not default smoke validation. |
| PettingZoo example learns illegal behavior | Mask values are exposed but not enforced by the policy | Validate `mask` values from `PettingZooEnv`, then make the policy sample/select only legal actions. |

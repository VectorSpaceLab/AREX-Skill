# Embodied Dataflow Troubleshooting

Use this reference when dataflow errors occur before or during DreamerV3
training. Start with the smallest failing surface: custom env in single process,
then driver, then replay, then streams, then parallel workers.

## Quick triage

```bash
python scripts/check_embodied_contracts.py --mode env
python scripts/check_embodied_contracts.py --mode replay
python scripts/check_embodied_contracts.py --mode driver
```

For custom environments:

```bash
python scripts/check_embodied_contracts.py --mode env --factory my_pkg.envs:make_env
python scripts/check_embodied_contracts.py --mode driver --factory my_pkg.envs:make_env --steps 8
```

If the custom checker fails, fix the env contract before touching JAX, configs,
or training loops.

## Error matrix

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'reset'` or checker says action space lacks reset | Custom env omitted `act_space['reset']` or wrapper dropped it. | Add `reset: elements.Space(bool)` to `act_space`; ensure wrappers preserve it. Policy actions should not include `reset`. |
| Reset call does not produce `is_first=True` | `step()` ignores `action['reset']` or only resets in a separate method. | Make `step({'reset': True, ...})` reset state and return the first observation. |
| First transition is counted unexpectedly | Driver begins by sending `reset=True`, and the first observation is a callback transition. | Account for the reset observation. A length-10 dummy episode yields 11 callback transitions. |
| `CheckSpaces` reports dtype mismatch | Backend emits `float64`, `int64`, Python lists, or booleans with unexpected dtype. | Wrap with `UnifyDtypes` before `CheckSpaces`, or cast returned values explicitly to `np.float32`, `np.int32`, `np.uint8`, or `bool`. |
| `CheckSpaces` reports shape mismatch | Returned value shape differs from `elements.Space.shape`; common with missing channel dim or scalar/vector confusion. | Print `env.obs_space`/`env.act_space` after wrapper construction. Return exact shapes, for example images `(H,W,C)` and scalar flags `()`. |
| `Value for 'action' ... is not in Space` | Action out of declared bounds, unnormalized action sent to normalized env, or discrete id too high. | Add `ClipAction` outside `NormalizeAction`, check policy action key, and verify integer action bounds. |
| `assert not (env.obs_space.keys() & env.act_space.keys())` | Same key appears in both spaces. | Rename observation keys or action keys. Do not return an observation called `action` if action key is `action`. |
| Policy receives missing `log/` key | Driver strips `log/` observations before policy. | Use non-log keys for model inputs. Keep `log/` for callbacks/logger/replay-excluded metrics. |
| Callback transition lacks `log/` key in replay sample | Replay drops `log/` keys on `add()`. | Save logs separately in callback/logger; do not rely on replay to train on `log/` keys. |
| Driver assertion that action arrays are not NumPy arrays or have wrong leading dimension | Policy returned Python lists/scalars or unbatched actions. | Return NumPy arrays with leading dimension equal to number of envs for every non-reset action. |
| Driver error `outs` collides with action keys | Policy auxiliary outputs use same key as actions. | Rename policy output keys; action and `out` dictionaries must be disjoint. |
| Parallel driver says worker error or terminates workers | Env factory is not picklable, optional imports unavailable in child process, env crashed, or backend cannot run in process. | Reproduce with `parallel=False`; expose a top-level zero-arg factory; keep optional imports inside factory; use `RestartOnException` only for transient env crashes. |
| `Replay buffer ... is empty` or sampling waits forever | Fewer than `length` transitions were added per worker, callback not registered, driver did not run, or all transitions use a worker stream that has not reached length. | Check `len(replay)`, lower `length`, print callback counts, and run the bundled replay checker. |
| Replay samples appear to cross worker streams | Transitions from multiple envs were added with the same `worker` id or mixed after sampling. | Use `driver.on_step(lambda tran, worker: replay.add(tran, worker=worker))`. Add a `debug_worker` key and assert it is constant along each sampled sequence. |
| `replay.update()` asserts `stepid.ndim == 3` | Update data is unbatched, missing time dimension, or stepid was removed. | Pass `batch['stepid']` from `replay.sample()` unchanged; priority shape should be `(batch, length)`. |
| Priority updates ignored | Items were evicted before asynchronous update or selector does not support priorities. | Increase capacity, update sooner, or use `selectors.Prioritized`; tolerate stale updates. |
| Too many replay chunk files | `chunksize` is too small or save is called very often. | Increase `chunksize` for real runs. Keep small chunks only for tests. |
| Restored replay contains old and new items | `load()` does not clear an existing replay first. | Restore into a fresh `Replay` instance when you need exact state. |
| `Consec` assertion on available length | Source replay sample is shorter than `length * consec + prefix`, or `strict=True` expects exact length. | Increase replay/source length, lower `consec`, adjust `prefix`, or set `strict=False` when extra context is intentional. |
| `Prefetch` raises `RuntimeError` containing a string | Background worker raised an exception and forwarded it. | Re-run the source stream without prefetch to see the original stack, then re-enable prefetch. |
| `Mixer` fails on iteration or NumPy attribute | Stream implementation can be version-sensitive. | Prefer `Zip`/`Map`/separate streams, or smoke-test `Mixer` in the installed package before using it. |
| Optional adapter `ImportError` | Missing optional dependency, ROM, simulator, Java/MineRL stack, DMLab assets, Mujoco/GL, or Gym registration. | Validate dummy/custom dataflow first. Route installation/system work to `results-ops`. |
| DMC/Loconav rendering fails | Mujoco renderer/system libraries or `MUJOCO_GL` setup issue. | Confirm optional setup in `results-ops`; DMC sets `MUJOCO_GL=egl` if unset but host libraries still matter. |
| Atari ROM load fails | ROM package/path unavailable. | Install/authorize ROMs through the environment setup path; set `ALE_ROM_PATH` only if using local ROM files. |
| Image resize import error | `ResizeImage` or adapter resize path needs Pillow or OpenCV. | Use Pillow resize where available or install optional image dependency through `results-ops`. |

## Missing `reset` in a custom environment

This is the highest-priority custom env issue because DreamerV3's driver owns
reset scheduling. A backend might expose `env.reset()`, but Embodied still
expects reset through the action dictionary.

Bad pattern:

```python
@property
def act_space(self):
  return {'action': elements.Space(np.int32, (), 0, 4)}
```

Good pattern:

```python
@property
def act_space(self):
  return {
      'reset': elements.Space(bool),
      'action': elements.Space(np.int32, (), 0, 4),
  }

def step(self, action):
  if bool(np.asarray(action['reset']).item()) or self.done:
    return self._reset_obs()
  return self._normal_step(action['action'])
```

Run:

```bash
python scripts/check_embodied_contracts.py --mode env --factory my_pkg.envs:make_env
```

The checker fails before training if `reset` is absent.

## Replay samples crossing worker streams

Replay itself stores streams per worker id. It can only preserve this guarantee
if you add transitions with stable worker ids.

Correct callback:

```python
def add_transition(tran, worker):
  replay.add(tran, worker=worker)

driver.on_step(add_transition)
```

Debug callback:

```python
def add_transition(tran, worker):
  tran = dict(tran)
  tran['debug_worker'] = np.int32(worker)
  replay.add(tran, worker=worker)
```

After enough transitions:

```python
batch = replay.sample(batch=8)
assert (batch['debug_worker'] == batch['debug_worker'][:, :1]).all()
```

If this fails:

1. Confirm callback uses the `worker` parameter, not a constant.
2. Confirm each parallel env factory creates an independent env instance.
3. Check downstream streams: `Zip` concatenates batches, and custom `Map`
   transforms might mix rows.
4. Check `Consec` source length and row origins. `Consec` slices time windows
   from source rows; it does not repair mixed source rows.

## Wrapper order debugging

When a wrapper stack fails, inspect after every wrapper:

```python
env = RawEnv(...)
print('raw', env.obs_space, env.act_space)
env = embodied.wrappers.NormalizeAction(env)
print('normalized', env.obs_space, env.act_space)
env = embodied.wrappers.UnifyDtypes(env)
env = embodied.wrappers.CheckSpaces(env)
```

Guidelines:

- `CheckSpaces` should normally be outermost during debugging, so it validates
  the public wrapped interface.
- `UnifyDtypes` should be inside `CheckSpaces`, so values are converted before
  final checks.
- `ClipAction` is useful outside `NormalizeAction` to clamp policy outputs in
  normalized space before mapping to raw bounds.
- `ResizeImage` changes observation spaces; inspect shape after applying it.
- If `DiscretizeAction` fails on action shape, confirm the continuous action
  space is vector-shaped and not a scalar or multi-axis action that needs a
  custom discretizer.

## Parallel process failures

Parallel mode adds multiprocessing, pickling, and child-import constraints. Use
this sequence:

1. `python scripts/check_embodied_contracts.py --mode env --factory my_pkg.envs:make_env`
2. `python scripts/check_embodied_contracts.py --mode driver --factory my_pkg.envs:make_env --parallel-envs 1`
3. Only then try your training driver with `parallel=True`.

A valid parallel factory should be a top-level callable:

```python
def make_env():
  from my_pkg.envs import MyEnv
  return MyEnv(...)
```

Avoid lambdas that close over non-picklable handles, already-created simulator
instances, sockets, open files, or local nested classes.

## Optional environment ImportErrors

Do not let optional adapter setup obscure the core dataflow diagnosis:

1. Pass the bundled checker with the default tiny env.
2. Pass the checker with a custom lightweight factory if you have one.
3. Only then diagnose optional adapter installation.

Typical boundaries:

- Atari: `ale_py`, ROMs/AutoROM, Pillow/OpenCV.
- Crafter: `crafter` package.
- DMC/Loconav: `dm_control`, Mujoco/GL/system libraries.
- DMLab: `deepmind_lab` and assets.
- ProcGen: `procgen`, Gym registration, image resize dependency.
- Minecraft: MineRL, Java/Minecraft runtime, additional system packages.
- BSuite: `bsuite` and version-compatible DM wrappers.

Installation/backend actions belong to `results-ops`; this sub-skill only tells
you what the adapter must provide once it imports.

---
name: embodied-dataflow
description: "Build and troubleshoot DreamerV3 Embodied Env, Agent, Driver,
  Replay, Stream, wrapper, and custom environment dataflow contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Embodied Dataflow for DreamerV3

Use this sub-skill when a task is about the Embodied runtime layer that feeds
DreamerV3: environment adapters, custom `Env` contracts, `Agent.policy()` data
shapes, `Driver` stepping/callbacks, replay insertion/sampling, streams, and
wrappers. It is intentionally safe: it documents and checks data contracts, not
training quality.

## Route here for

- Building or validating a custom `embodied.Env` adapter.
- Explaining why `act_space` must include `reset`, why observations need
  `reward`, `is_first`, `is_last`, and `is_terminal`, or why `log/` keys do not
  reach the policy.
- Wiring `Driver(...).on_step(...)` callbacks into replay with stable worker ids.
- Debugging replay samples, selectors, chunk save/load, stream composition, and
  sequence contiguity.
- Choosing and ordering wrappers such as `NormalizeAction`, `ClipAction`,
  `UnifyDtypes`, `CheckSpaces`, `DiscretizeAction`, `ResizeImage`, `TimeLimit`,
  and `RestartOnException`.
- Using the safe dummy environment as a contract example before attempting
  optional Atari, Crafter, DMC, DMLab, Gym, Minecraft, ProcGen, PinPad, or
  BSuite integrations.

## Route elsewhere

- CLI flags, `configs.yaml`, run-loop selection, logging/checkpoints, and train
  smoke commands belong to sibling sub-skill `train-configure`.
- JAX, Ninjax, DreamerV3 model internals, optimizer state, sharding, and neural
  module debugging belong to sibling sub-skill `jax-models`.
- Installation, CUDA/system packages, optional environment dependency setup,
  Docker, plotting, score files, and metrics operations belong to sibling
  sub-skill `results-ops`.

## Fast operating path

1. Read [references/api-contracts.md](references/api-contracts.md) before
   implementing or reviewing any `Env`, `Agent`, `Driver`, `Replay`, or `Stream`
   code. It contains the exact key, shape, callback, and sample/update
   contracts.
2. Read [references/env-integration.md](references/env-integration.md) when
   adding a built-in or custom environment adapter, selecting wrappers, or
   deciding which optional dependency boundary applies.
3. Read [references/replay-and-streams.md](references/replay-and-streams.md)
   when replay sampling is empty, samples appear non-contiguous, priorities are
   updated, chunks are saved/loaded, or stream combinators are used.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when an
   error mentions `reset`, `CheckSpaces`, dtype/shape bounds, parallel workers,
   replay waiting, optional environment imports, or stream assertions.
5. Run [scripts/check_embodied_contracts.py](scripts/check_embodied_contracts.py)
   as a local contract smoke before training. It supports:

   ```bash
   python scripts/check_embodied_contracts.py --help
   python scripts/check_embodied_contracts.py --all
   python scripts/check_embodied_contracts.py --mode env
   python scripts/check_embodied_contracts.py --mode replay
   python scripts/check_embodied_contracts.py --mode driver
   python scripts/check_embodied_contracts.py --mode env --factory my_pkg.envs:make_env
   ```

   The checker uses a tiny dummy-like environment by default and can validate a
   user-provided zero-argument environment factory. It does not train.

## Common recipes

### Custom environment preflight

1. Implement `obs_space`, `act_space`, `step(action)`, and `close()`.
2. Include `act_space['reset'] = elements.Space(bool)` even if the wrapped
   backend resets internally.
3. Return `reward`, `is_first`, `is_last`, and `is_terminal` on every step.
4. Make `step({'reset': True, ...})` return the first observation of a new
   episode with `is_first=True`, `is_last=False`, and reward normally `0.0`.
5. Wrap with `UnifyDtypes` and then `CheckSpaces` during debugging.
6. Run the bundled checker in `env` mode before connecting a policy or replay.

### Driver to replay wiring

```python
import embodied
from embodied.envs import dummy

def make_env():
  return dummy.Dummy('disc', length=100)

env0 = make_env()
agent = embodied.RandomAgent(env0.obs_space, env0.act_space)
env0.close()

replay = embodied.Replay(length=16, capacity=1000)
driver = embodied.Driver([make_env, make_env], parallel=False)
driver.reset(agent.init_policy)
driver.on_step(lambda tran, worker: replay.add(tran, worker=worker))
driver(agent.policy, steps=64)
batch = replay.sample(batch=4, mode='train')
assert batch['is_first'].shape[:2] == (4, 16)
```

Keep the callback `worker` id when adding to replay. Worker ids keep sequences
from separate environment streams from crossing.

## Native verification candidates owned by this sub-skill

Use these as final native candidates after the whole DreamerV3 skill is
integrated and its verification plan allows native tests:

- `embodied/tests/test_driver.py::TestDriver::test_episode_length`: driver
  reset/episode-length semantics on the dummy environment.
- `embodied/tests/test_replay.py::TestReplay::test_sample_single`: replay
  single-worker contiguous sequence sampling.
- Optional if resources allow: `embodied/tests/test_parallel.py`, because it
  exercises parallel run-loop dataflow and save/load behavior but is longer and
  depends on additional runtime services.

Do not run those native tests while merely using this runtime sub-skill; use the
bundled checker for quick contract preflight.

## Known limits

- Optional environment adapters can require external packages, ROMs, system
  libraries, display/Mujoco setup, or Java/MineRL resources. This sub-skill only
  defines the dataflow contract and adapter boundaries; setup belongs to
  `results-ops`.
- The checker validates contract shape and safe replay/driver mechanics. It does
  not prove training performance, JAX model correctness, or distributed run-loop
  behavior.
- For environments with unusual constructor arguments, expose a small
  zero-argument factory and pass it via `--factory module:callable` to the
  checker.

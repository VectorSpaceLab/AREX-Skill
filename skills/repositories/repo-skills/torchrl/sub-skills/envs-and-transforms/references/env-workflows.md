# Environment workflows

## Core mental model

TorchRL environments are `EnvBase` modules that read and write `TensorDict` objects.

- `env.reset()` returns the initial root data: observations plus root done-family entries.
- `env.step(td)` reads root inputs such as `action` and writes transition outputs under `"next"`.
- `env.rollout(max_steps=N)` stacks transitions over a trailing time dimension and leaves next-step observations, rewards, and done-family entries under `("next", key)`.
- `step_mdp(td)` turns a single transition into the next-step root layout by moving selected `"next"` values to the root and dropping stale fields according to its options.

Important environment attributes:

| Attribute | Use |
| --- | --- |
| `env.batch_size` | Number of env instances batched together. Specs should include this leading shape. |
| `env.device` | Device expected for input/output TensorDict data; not necessarily where the simulator computes. |
| `env.observation_spec` | Leaf observation spec exposed to outside users. |
| `env.action_spec` | Action spec used by `rand_action`, policies, transforms, and collectors. |
| `env.reward_spec` | Reward spec. |
| `env.done_spec` | Done-family spec. |
| `env.input_spec` | Full state/action input spec. |
| `env.output_spec` | Full observation/reward/done output spec. |
| `env.action_key`, `env.reward_key`, `env.done_key` | Preferred keys for single main action/reward/done, especially after nesting or multi-agent grouping. |
| `env.action_keys`, `env.reward_keys`, `env.done_keys` | All matching keys; pass these to `step_mdp` for nested or multi-agent layouts. |

## CPU-native Pendulum workflow

Use native environments for core TorchRL checks because they avoid optional simulator dependencies.

```python
from torchrl.envs import PendulumEnv, TransformedEnv, check_env_specs, step_mdp
from torchrl.envs.transforms import StepCounter

base_env = PendulumEnv()
env = TransformedEnv(base_env, StepCounter(max_steps=200))

# Offline spec check: useful before collectors or ParallelEnv.
check_env_specs(env, seed=0)

rollout = env.rollout(max_steps=3)
transition = rollout[0]
next_root = step_mdp(
    transition,
    reward_keys=env.reward_keys,
    done_keys=env.done_keys,
    action_keys=env.action_keys,
)
```

Default `step_mdp` behavior keeps non-transition extras, moves next observations and done-family entries to the root, excludes reward, and excludes action. Set `exclude_reward=False` for losses or diagnostics that need the next reward in the next-root TensorDict; set `exclude_action=False` only when the next call explicitly reuses or inspects the previous action.

## Spec validation workflow

Use `check_env_specs` before vectorization, collectors, compiled stepping, or any custom `EnvBase` change.

```python
check_env_specs(
    env,
    return_contiguous=None,
    check_dtype=True,
    seed=0,
    break_when_any_done="both",
)
```

What it catches:

- real rollout keys differ from fake/preallocated spec keys;
- tensor shapes differ from specs;
- dtypes differ when `check_dtype=True`;
- dynamic specs that require non-contiguous rollout handling;
- done-family layout mismatches that would break buffers in vectorized envs or collectors.

Cautions:

- It runs a short random rollout and can call `set_seed`; use it as an offline construction check, not inside a hot training loop.
- If an env has dynamic shapes, leave `return_contiguous=None` or pass `False`; contiguous rollout can fail for heterogeneous shapes.
- For partially reset or auto-resetting envs, test both `break_when_any_done=True` and `False` when the downstream loop will use both modes.

## `step_mdp` transition movement

A TorchRL step result has the previous step at the root and the next step under `"next"`:

```text
root/action
root/observation
root/done
root/next/observation
root/next/reward
root/next/done
root/next/terminated
root/next/truncated
```

`step_mdp(td, ...)` builds a new root TensorDict for time `t+1`.

Options to decide deliberately:

| Option | Default | Effect |
| --- | --- | --- |
| `keep_other` | `True` | Keep root fields that are not action/reward/done/next, such as recurrent state or metadata. |
| `exclude_reward` | `True` | Drop next reward from the new root unless explicitly needed. |
| `exclude_done` | `False` | Keep next done-family entries at the root. |
| `exclude_action` | `True` | Drop stale previous action. |
| `reward_keys`, `done_keys`, `action_keys` | flat defaults | Pass env key lists for nested or multi-agent layouts. |
| `next_tensordict` | `None` | Optional preallocated destination. |

Nested-key example:

```python
next_root = step_mdp(
    transition,
    reward_keys=[("agents", "reward")],
    done_keys=["done", ("agents", "done")],
    action_keys=[("agents", "action")],
    exclude_reward=False,
)
```

If a transform renames action or observation keys, pass the keys visible at the level where `step_mdp` is called. For transformed env outputs, this is usually the outer policy-facing key set.

## Done, terminated, and truncated layout

TorchRL treats `done` as the union signal that tells rollouts and collectors an episode boundary was reached. `terminated` represents task termination; `truncated` represents time-limit or early-stop truncation when available. `StepCounter(max_steps=...)` writes a `truncated` entry and, with `update_done=True`, updates `done` at the same nesting level.

Rules of thumb:

- Keep `done`, `terminated`, and `truncated` shapes compatible with the environment batch and nesting level.
- If a backend has only one terminal signal, expect TorchRL to infer or pair the done-family fields.
- For multi-agent environments, root `done` can summarize the whole environment while per-agent rewards/actions/observations live under an agent group.
- Use `env.done_keys` rather than hard-coding `"done"` once nesting or transforms are involved.

## Serial and parallel vectorization

Use `SerialEnv` to debug vectorized semantics without subprocesses; use `ParallelEnv` only when specs and the factory are stable.

```python
from torchrl.envs import ParallelEnv, SerialEnv, TransformedEnv, check_env_specs
from torchrl.envs.transforms import StepCounter


def make_env():
    env = PendulumEnv()
    return TransformedEnv(env, StepCounter(max_steps=200))

check_env_specs(make_env(), seed=0)
serial_env = SerialEnv(4, make_env)
parallel_env = ParallelEnv(4, make_env)
try:
    serial_rollout = serial_env.rollout(max_steps=3)
    parallel_rollout = parallel_env.rollout(max_steps=3)
finally:
    serial_env.close()
    parallel_env.close()
```

Vectorization checklist:

1. Use a top-level factory function or a picklable callable. Avoid closing over large objects, file handles, or non-picklable simulator instances.
2. Run `check_env_specs(make_env())` before constructing `ParallelEnv`; buffers are allocated from specs.
3. Use `SerialEnv` first to verify batch shapes and transform behavior.
4. Guard process-spawning entry points with `if __name__ == "__main__":` in scripts and notebooks converted to scripts.
5. If warnings disappear inside workers, remember TorchRL filters some subprocess warnings by default.
6. Close vectorized environments explicitly to release worker processes and simulator resources.

## Custom `EnvBase` sketch

A custom environment normally implements `_reset`, `_step`, `_set_seed`, and specs. Keep all data in TensorDict form.

```python
from __future__ import annotations

import torch
from tensordict import TensorDict, TensorDictBase
from torchrl.data import Binary, Bounded, Composite, Unbounded
from torchrl.envs import EnvBase


class TinyCounterEnv(EnvBase):
    def __init__(self, max_count: int = 3):
        super().__init__(batch_size=[])
        self.max_count = max_count
        self.count = 0
        self.observation_spec = Composite(observation=Unbounded(shape=(1,)))
        self.action_spec = Bounded(low=-1.0, high=1.0, shape=(1,))
        self.reward_spec = Unbounded(shape=(1,))
        self.done_spec = Composite(done=Binary(shape=(1,), dtype=torch.bool))

    def _reset(self, tensordict: TensorDictBase | None = None) -> TensorDictBase:
        self.count = 0
        return TensorDict({"observation": torch.zeros(1)}, [])

    def _step(self, tensordict: TensorDictBase) -> TensorDictBase:
        self.count += 1
        done = torch.tensor([self.count >= self.max_count], dtype=torch.bool)
        return TensorDict(
            {
                "observation": torch.tensor([float(self.count)]),
                "reward": torch.ones(1),
                "done": done,
            },
            [],
        )

    def _set_seed(self, seed: int | None) -> int | None:
        return seed
```

After constructing any custom env, run `check_env_specs(env)` and a tiny rollout before connecting policies, collectors, or transforms.

## Multi-agent environment/spec grouping

TorchRL does not require a separate multi-agent container. Per-agent tensors are ordinary nested TensorDict entries, commonly under an `"agents"` group with shape `[num_envs, num_agents, ...]`; shared tensors stay at the root.

Typical layout:

```text
root/done                         # shared env-level done, shape [num_envs, 1]
root/agents/action                # per-agent action, shape [num_envs, num_agents, action_dim]
root/next/agents/observation      # per-agent next observation
root/next/agents/reward           # per-agent reward
```

Use the environment's resolved key attributes (`action_key`, `reward_key`, `done_key`, and plural forms) when handing keys to transforms, losses, and `step_mdp`. This avoids bugs where a flat default such as `"action"` misses `("agents", "action")`.

## Dynamic specs and non-contiguous rollout

Some wrappers and custom envs can emit variable-size tensors. Specs may mark dynamic dimensions with `-1`. In that case:

- call `rollout(..., return_contiguous=False)`;
- expect a lazy stacked TensorDict rather than a dense contiguous tensor for the dynamic branch;
- benchmark before using multiprocessing, because dynamic data prevents efficient shared-memory buffers;
- make keys stable across steps even when shapes vary. A key appearing in one step and disappearing in another is not a supported dynamic-spec pattern.

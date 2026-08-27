# Transform reference

## Construction pattern

`TransformedEnv(base_env, transform)` wraps an `EnvBase` and exposes transformed specs and TensorDict keys to the outside world. `Compose(t1, t2, ...)` applies multiple transforms in order.

```python
from torchrl.envs import PendulumEnv, TransformedEnv
from torchrl.envs.transforms import Compose, ObservationNorm, StepCounter

env = TransformedEnv(
    PendulumEnv(),
    Compose(
        ObservationNorm(in_keys=["th"], standard_normal=True),
        StepCounter(max_steps=200),
    ),
)
env.transform[0].init_stats(num_iter=32)
```

A transform attached to an env owns a parent pointer. If you want to reuse a transform object on another env, call `transform.clone()` or construct a fresh instance.

## Key routing vocabulary

Transforms see two perspectives:

- `in_keys`: keys read from the inner/base environment output during the forward path.
- `out_keys`: keys written to the outside/policy-facing TensorDict during the forward path.
- `out_keys_inv`: keys read from the outside/policy-facing TensorDict before an action reaches the base env.
- `in_keys_inv`: keys written for the inner/base environment input during the inverse action path.

Forward path example: base env emits `"observation"`, policy should see `"obs_norm"`.

```python
ObservationNorm(
    in_keys=["observation"],
    out_keys=["obs_norm"],
    standard_normal=True,
)
```

Inverse action path example: policy emits normalized `"scaled_action"`, base env receives `"action"`.

```python
from torchrl.envs.transforms import ActionScaling

ActionScaling(
    in_keys_inv=["action"],
    out_keys_inv=["scaled_action"],
    in_keys=["action"],
    out_keys=["scaled_action"],
)
```

If the error says a key is missing, first identify whether the failure is on the forward path (`reset`, `rollout`, replay-buffer sample) or inverse path (`step`, policy action before simulator call). Then compare the failing key against the inner and outer key names.

## Common transforms

| Transform | Typical use | Key notes |
| --- | --- | --- |
| `StepCounter(max_steps=None, truncated_key="truncated", step_count_key="step_count", update_done=True)` | Count steps and optionally time-limit episodes. | `truncated_key` and `step_count_key` are leaf strings; the transform mirrors them at each done nesting level. |
| `ObservationNorm(loc=None, scale=None, in_keys=..., standard_normal=False)` | Normalize observations or pixels. | In current APIs, pass `in_keys` explicitly. If `loc`/`scale` are uninitialized, call `init_stats` on the attached transform before training. |
| `RewardSum` | Track episode return as an observation-like running value. | Episode sums are not ordinary reward specs; be deliberate with `step_mdp(exclude_reward=...)`. |
| `ActionScaling` | Expose normalized continuous actions to policies and denormalize before the base env. | Supports one action key per instance; compose multiple instances for multiple action leaves. Requires bounded action spec unless explicit `loc` and `scale` are provided. |
| `RenameTransform`, `SelectTransform`, `ExcludeTransform`, `CatTensors`, `FlattenObservation`, `FlattenAction` | Key/layout adaptation. | Update policy/loss/collector keys after changing names or nesting. |
| `ToTensorImage`, `Resize`, `CenterCrop`, `GrayScale`, `PermuteTransform` | Pixel preprocessing. | Requires pixel/rendering backend to supply image observations; check dtype/shape after the transform. |
| `FiniteTensorDictCheck` | Fail fast on NaN/Inf observations, actions, or rewards. | Useful after custom envs, physics backends, or normalization. |
| `InitTracker`, `TensorDictPrimer` | Initialize recurrent state and mark episode starts. | Often inserted automatically when an env receives a recurrent policy, but manual wiring is safer when keys are renamed. |
| `ActionChunkTransform` | Build time-windowed action chunks for VLA-style training data. | Generic semantics are listed below; VLA workflows route to `llm-vla-and-services`. |

## `ObservationNorm` workflow

```python
from torchrl.envs import PendulumEnv, TransformedEnv, check_env_specs
from torchrl.envs.transforms import ObservationNorm

env = TransformedEnv(
    PendulumEnv(),
    ObservationNorm(in_keys=["th"], standard_normal=True),
)
env.transform.init_stats(num_iter=64)
check_env_specs(env, seed=0)
```

Rules:

- Do not leave `in_keys` implicit.
- Initialize stats before training if `loc` and `scale` were not supplied.
- With multiple input keys, initialize each transform separately or pass the `key=` argument to `init_stats`.
- For images, use shape-aware `keep_dims` so channel statistics broadcast correctly.

## `StepCounter` workflow

```python
from torchrl.envs.transforms import StepCounter

transform = StepCounter(max_steps=200)
```

Behavior:

- Adds `step_count` and `truncated` leaves at every done level.
- When `max_steps` is reached, marks `truncated=True`.
- With `update_done=True`, also updates `done=True` at the same level.
- For multi-agent or nested done keys, pass env-resolved `done_keys` to downstream `step_mdp` or losses rather than assuming flat `"done"`.

## `ActionScaling` workflow

```python
from torchrl.envs import PendulumEnv, TransformedEnv, check_env_specs
from torchrl.envs.transforms import ActionScaling

env = TransformedEnv(PendulumEnv(), ActionScaling())
check_env_specs(env, seed=0)
```

The default normalized policy action range is `[-1, 1]` for bounded continuous action specs. If the source spec is unbounded or partly unbounded, supply explicit `loc` and `scale` or choose a different transform. For datasets or replay buffers, a forward-only instance with `in_keys_inv=[]` normalizes samples without changing data written through `extend`.

## `ActionChunkTransform` routing note

`ActionChunkTransform(chunk_size=H, action_key="action", chunk_key=("vla_action", "chunk"), pad_key="action_is_pad", time_dim=-2, done_key="done")` builds fixed-length future action chunks from time-structured TensorDict data shaped like `[*B, T, action_dim]`.

Use it only as a data transform. It does not execute multiple environment actions. Execution-time multi-action behavior belongs to policy wrappers or action-execution transforms, and VLA-specific schema/loss work routes to `llm-vla-and-services`.

Checklist before using it:

1. Ensure the TensorDict sample is time-structured, not a flat `[B*T, ...]` sample.
2. Ensure the action dimension immediately follows the time dimension.
3. If the sample contains `("next", done_key)`, verify that its shape matches the action time layout; otherwise pass `done_key=None` only when crossing episode boundaries is intentionally acceptable.
4. Check the generated chunk key and pad mask before using a behavior-cloning loss.

## Custom transform checklist

When writing a new transform:

- Implement `_apply_transform` for independent tensor mapping.
- Implement `_call` when transformation needs access to the whole output TensorDict.
- Implement `_inv_apply_transform` or `_inv_call` for action-side transforms.
- Implement `_step` only when the transform needs both pre-step inputs and post-step outputs.
- Update specs through the appropriate `transform_*_spec` method.
- Add nested-key tests if the transform accepts `NestedKey` inputs.
- Verify with `check_env_specs` after attaching the transform to an env.

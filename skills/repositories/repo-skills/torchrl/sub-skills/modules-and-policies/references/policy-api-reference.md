# Policy API reference

This reference focuses on TensorDict-native module wiring. Treat every policy, critic, and distribution wrapper as a key-transforming operator over a `TensorDict`.

## Core key contract

| Wrapper | Typical inputs | Typical outputs | Notes |
| --- | --- | --- | --- |
| `TensorDictModule` | `in_keys` passed to a plain `nn.Module` in order | `out_keys` matched to returned tensors | Use when a PyTorch module does not know about TensorDicts. |
| `SafeModule` | Same as `TensorDictModule` | Same as `TensorDictModule` | Adds optional `spec` and `safe=True` projection. Spec keys must match out keys. |
| `SafeSequential` | Outputs from earlier modules feed later modules | Union of all written keys | Use for policy bodies built from multiple TensorDict modules. |
| `Actor` | Defaults to `['observation']` | Defaults to `['action']` | Deterministic policy wrapper; non-composite action specs are wrapped under `action`. |
| `ProbabilisticActor` | Distribution params (`loc`, `scale`, `logits`, etc.) | Defaults to `['action']`; optional log-prob key | Its `module` writes parameters first, then the probabilistic wrapper samples or selects an action. |
| `ValueOperator` | Defaults to `['observation']`, or include `action` | Defaults to `state_value`; `state_action_value` if `action` is in `in_keys` | Use explicit out keys if an objective expects a custom value key. |
| `QValueActor` | Observations or an existing `action_value` key | `action`, `action_value`, `chosen_action_value` | Requires an action spec or action-space declaration. Supports action masks. |

Nested keys are first-class keys. Use tuples such as `('agent', 'observation')` or `('next', 'recurrent_state')` when the data layout is nested. Keep the same key spelling across policy, collector/replay, and objective modules.

## Deterministic actor pattern

Use `Actor` when the network directly emits an action tensor.

```python
from tensordict import TensorDict
from torch import nn
from torchrl.data import Bounded
from torchrl.modules import Actor, MLP

obs_dim, action_dim = 4, 2
spec = Bounded(low=-1.0, high=1.0, shape=(action_dim,))
net = MLP(in_features=obs_dim, out_features=action_dim, num_cells=[32, 32])
actor = Actor(net, in_keys=[('obs', 'state')], out_keys=['action'], spec=spec, safe=True)

td = TensorDict({('obs', 'state'): ...}, batch_size=[...])
td = actor(td)
assert 'action' in td.keys()
```

Notes:

- `safe=True` projects out-of-domain outputs with the spec. It is useful at task boundaries, but costs extra checks.
- If the network returns multiple tensors, use a `Composite` spec whose keys match every `out_key`, or omit the spec for outputs that do not have domains.
- For nested observations, the `in_keys` sequence controls argument order into the underlying module.

## Probabilistic actor pattern

Use `ProbabilisticActor` when a network emits distribution parameters.

```python
from tensordict.nn import TensorDictModule
from tensordict.nn.distributions import NormalParamExtractor
from torch import nn
from torchrl.modules import ProbabilisticActor, TanhNormal

param_net = TensorDictModule(
    nn.Sequential(nn.Linear(obs_dim, 2 * action_dim), NormalParamExtractor()),
    in_keys=[('obs', 'state')],
    out_keys=['loc', 'scale'],
)
policy = ProbabilisticActor(
    module=param_net,
    in_keys=['loc', 'scale'],
    out_keys=['action'],
    spec=spec,
    distribution_class=TanhNormal,
    distribution_kwargs={'low': -1.0, 'high': 1.0},
    return_log_prob=True,
    log_prob_key='sample_log_prob',
)
```

Parameter rules:

- A list `in_keys=['loc', 'scale']` requires leaf key names to match the distribution constructor arguments.
- A dict `in_keys={'loc': ('policy', 'mu'), 'scale': ('policy', 'sigma')}` maps distribution argument names to arbitrary TensorDict keys.
- `return_log_prob=True` writes a log-prob key used by policy-gradient objectives. If an objective expects a specific key, set `log_prob_key` explicitly.
- `cache_dist=True` keeps distribution parameters available for later comparison or debugging.
- Interaction mode controls sampling vs deterministic selection. A collector normally samples randomly for exploration; evaluation usually uses deterministic/mode behaviour.

## Bounded continuous distributions

For continuous actions, prefer a squashed distribution over manually clamping unconstrained normals:

- `TanhNormal(loc, scale, low=..., high=...)` samples within bounds and computes consistent log probabilities.
- `NormalParamExtractor` splits a linear output into `loc` and positive `scale` tensors.
- `TanhDelta` can represent deterministic bounded actions in probabilistic wrappers.

Use `safe=True` as a domain guard, not as the primary way to make a probabilistic distribution valid. Spec projection can clamp gradients and hide poor parameterization.

## Masked discrete distributions

For discrete policies with illegal actions, use mask-aware distributions or Q-value actor masks.

- `MaskedCategorical(logits=..., mask=...)` accepts a boolean mask with the same last dimension as logits. Invalid entries are assigned a negative-infinity value before sampling/scoring.
- For `ProbabilisticActor`, either write `logits` and `mask` under keys whose leaf names match the distribution constructor, or pass an `in_keys` dict such as `{'logits': 'policy_logits', 'mask': 'action_mask'}`.
- For value-based policies, pass `action_mask_key='action_mask'` to `QValueActor` so invalid actions are not selected.

## Q-value actor pattern

Use `QValueActor` for DQN-style greedy policies.

```python
from torchrl.data import OneHot
from torchrl.modules import MLP, QValueActor

q_net = MLP(in_features=obs_dim, out_features=n_actions, num_cells=[64])
action_spec = OneHot(n_actions)
actor = QValueActor(
    module=q_net,
    spec=action_spec,
    action_mask_key='action_mask',
    strict_shape='auto',
)
```

Rules:

- If `module` is a plain `nn.Module`, it is wrapped with default `in_keys=['observation']` and writes `action_value`.
- If `module` is already a TensorDict module, its `out_keys` must include the chosen `action_value_key`.
- Provide either `spec` or `action_space` (`'one-hot'`, `'mult-one-hot'`, `'binary'`, or `'categorical'`). Specs are safer because they carry shape and dtype.
- `strict_shape='auto'` reshapes selected categorical actions to match spec shape when supported; `strict_shape=True` raises instead of silently reshaping.

## Actor and critic pairs

A common actor/critic TensorDict contract is:

```text
('obs', 'state') ── actor body ──> action, sample_log_prob
('obs', 'state') ── value head ──> state_value
('obs', 'state'), action ── q head ──> state_action_value
```

Guidelines:

- Keep actor and critic key names explicit when composing with losses.
- If a critic consumes the sampled action, ensure the action key written by the actor exactly matches the critic `in_keys`.
- For nested observation specs, use small adapter modules that concatenate or flatten only the inputs the model actually needs; keep the original nested keys present for env/loss code.
- If a loss module fails later with missing keys, inspect the policy output TensorDict before debugging the loss.

## Composite and multi-head actions

Composite policies write multiple action leaves, for example `('action', 'continuous')` and `('action', 'discrete')`. Use a parameter module that writes grouped distribution params and a `CompositeDistribution` name map to route distribution samples to action keys. The bundled [actor smoke script](../scripts/smoke_actor.py) includes a small deterministic example of this pattern.

## Exploration wrappers

TorchRL also includes exploration modules and wrappers for epsilon-greedy, Ornstein-Uhlenbeck noise, random policy behaviour, and multi-step actor wrappers. Treat them as TensorDict modules around the same action keys:

1. Build the base actor and prove it writes the expected action/log-prob keys.
2. Add the exploration wrapper with the same action spec/key.
3. Re-run a small TensorDict forward to confirm action shape, dtype, and bounds.
4. If a collector or evaluator changes interaction mode, confirm whether the probabilistic actor should sample randomly or use deterministic/mode actions.

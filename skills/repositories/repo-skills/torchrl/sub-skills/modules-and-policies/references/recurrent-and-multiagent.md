# Recurrent and multi-agent modules

This reference covers recurrent policy state wiring and multi-agent model grouping. Both areas are sensitive to TensorDict key layout: decide the layout first, then build modules around it.

## Recurrent modules at a glance

`LSTMModule` and `GRUModule` wrap PyTorch RNNs so they can read and write TensorDict entries.

| Module | Required input keys | Default hidden inputs | Default hidden outputs | Typical feature output |
| --- | --- | --- | --- | --- |
| `GRUModule` | observation/input, hidden state, `is_init` | `recurrent_state` | `('next', 'recurrent_state')` | `features` or `embed` |
| `LSTMModule` | observation/input, hidden h, hidden c, `is_init` | `recurrent_state_h`, `recurrent_state_c` | `('next', 'recurrent_state_h')`, `('next', 'recurrent_state_c')` | `features` or `embed` |

Use explicit keys for nontrivial policies:

```python
from torchrl.modules import GRUModule

gru = GRUModule(
    input_size=obs_dim,
    hidden_size=hidden_dim,
    in_keys=['embed', 'actor_rs', 'is_init'],
    out_keys=['actor_features', ('next', 'actor_rs')],
    recurrent_backend='pad',
)
```

For LSTMs, use a pair of hidden keys:

```python
lstm = LSTMModule(
    input_size=obs_dim,
    hidden_size=hidden_dim,
    in_keys=['embed', 'actor_h', 'actor_c', 'is_init'],
    out_keys=['actor_features', ('next', 'actor_h'), ('next', 'actor_c')],
)
```

The `('next', ...)` output convention is important: after an environment step, transition utilities and collectors can promote next-step hidden state to root hidden keys for the following policy call.

## `is_init` lifecycle

`is_init` is the reset boundary signal. It should be true on the first step of a fresh trajectory and immediately after a previous `done`.

Recurrent modules use it in both modes:

- Sequential collection mode: one step per call. The module reads root hidden state, zeros or resets it where `is_init=True`, processes the step, then writes next hidden state under `('next', ...)` keys.
- Recurrent training mode: a full time batch or contiguous sequence slice is processed in one call. The module uses `is_init` inside the batch to prevent hidden state from leaking across trajectory boundaries.

If `is_init` is missing, recurrent modules typically raise a key error. If `is_init` is present but always false, hidden state can leak silently across episodes.

## Primers and hidden-key setup

The safest environment/collector setup is to let TorchRL add recurrent policy transforms automatically when the collector supports it. In manual setups, add recurrent primers produced by the module:

```python
primer = gru.make_tensordict_primer()
# append the primer to the environment transform stack in env-building code
```

Primer responsibilities:

- Add hidden-state entries to reset TensorDicts.
- Register hidden-state specs so batched/process collectors know the extra keys.
- Ensure initial hidden state has shape compatible with the recurrent module.

When a recurrent module sits inside a larger policy, utility functions can collect primers from submodules. If manual TensorDicts are used in a smoke test or offline computation, create zero hidden tensors yourself and keep their shapes consistent with the module.

## Mode selection

Use `set_recurrent_mode` to switch execution paths:

```python
from torchrl.modules import set_recurrent_mode

with set_recurrent_mode(False):
    one_step_td = policy(one_step_td)

with set_recurrent_mode(True):
    sequence_td = policy(sequence_td)
```

Accepted values include booleans and the string aliases for sequential/recurrent modes. Built-in losses and value estimators often enter recurrent mode for their own forward computations; custom training code should be explicit so sequence forwards are easy to audit.

## Batch layout and `batch_first`

The default `batch_first=True` matches the common TensorDict batch layout where the last batch dimension is time during recurrent-mode calls, for example `[batch, time]` or `[time]`.

Hidden shapes follow the TensorDict batch shape plus recurrent dimensions:

```text
GRU hidden:  (*batch, num_layers, hidden_size)
LSTM hidden: (*batch, num_layers, hidden_size) for h and c
```

For a sequence TensorDict with `batch_size=[B, T]`, a GRU hidden tensor usually has shape `[B, T, num_layers, hidden_size]`. For a one-step TensorDict with `batch_size=[B]`, it has shape `[B, num_layers, hidden_size]`.

Common shape mistakes:

- Passing PyTorch RNN layout `[num_layers, batch, hidden]` directly as a TensorDict hidden key.
- Forgetting that a single unbatched step still needs the recurrent dimensions.
- Setting `batch_first=False` without updating every manual tensor shape and every comparison.

## Backend choices: `pad`, `scan`, `triton`, `auto`

| Backend | When to use | Constraints |
| --- | --- | --- |
| `pad` | Safest CPU/eager baseline and default. | Splits trajectories on `is_init`, pads chunks, and uses PyTorch RNN kernels. Can waste memory when there are many resets. |
| `scan` | Compile-friendly reset-aware path that avoids padding. | Supports a narrower set of RNN configurations; unsupported options raise in recurrent mode. |
| `triton` | Performance-oriented CUDA path for reset-heavy recurrent training. | Requires CUDA and Triton. Some LSTM/GRU variants fall back or are unsupported. Do not claim it is verified unless run on a matching backend. |
| `auto` | Chooses a baseline according to execution context. | Good for exploration, but explicit backend selection is easier to debug and benchmark. |

For safe CPU helpers and minimal reproducibility checks, use `recurrent_backend='pad'` and avoid Triton-specific precision knobs. Treat GPU/Triton behaviour as optional backend coverage unless it is separately provisioned and tested.

## Recurrent actor assembly recipe

1. Convert observations to an embedding with `TensorDictModule` or `MLP`.
2. Add `GRUModule` or `LSTMModule` with explicit hidden keys and `is_init`.
3. Add a deterministic head, `QValueModule`, or `ProbabilisticActor` distribution-parameter head.
4. Add recurrent primers to environments/collectors, or manually create hidden keys for synthetic TensorDicts.
5. During collection, run sequential mode. During sequence training or replayed slices, run recurrent mode.
6. Assert that output feature/action shapes preserve the TensorDict batch shape.

The bundled [recurrent actor smoke script](../scripts/smoke_recurrent_actor.py) intentionally demonstrates a missing reset-signal failure and then runs with manually primed hidden state.

## Multi-agent model grouping

TorchRL multi-agent models such as `MultiAgentMLP` and `MultiAgentConvNet` treat one tensor dimension as the agent dimension. The key questions are:

- `n_agents`: how many agents are in the group?
- `agent_dim`: which tensor dimension indexes agents?
- `centralized`: does each agent see all agents' observations/actions, or only its own slice?
- `share_params`: do agents share one network or own separate parameters?
- `vmap_randomness`: should stochastic layers use same or different randomness across agents?

Typical decentralized actor body:

```python
from torchrl.modules import MultiAgentMLP

model = MultiAgentMLP(
    n_agent_inputs=obs_per_agent,
    n_agent_outputs=actions_per_agent,
    n_agents=n_agents,
    centralized=False,
    share_params=True,
    agent_dim=-2,
    depth=2,
    num_cells=64,
)
```

Expected input tensor shape is usually `[..., n_agents, obs_per_agent]`; output shape is `[..., n_agents, actions_per_agent]`.

Centralized critics often set `centralized=True` so each agent's value head can see grouped information. Keep the same grouped tensor convention when handing values to multi-agent objectives.

## Multi-agent TensorDict key patterns

Two common layouts are valid, but mixing them causes bugs:

1. Grouped tensor layout:

```text
('agents', 'observation') -> tensor[..., n_agents, obs_dim]
('agents', 'action')      -> tensor[..., n_agents, action_dim]
```

2. Per-agent nested layout:

```text
('agent0', 'observation'), ('agent0', 'action')
('agent1', 'observation'), ('agent1', 'action')
```

`MultiAgentMLP` expects grouped tensors. If your environment emits per-agent nested keys, add a transform or adapter module that stacks agent observations before the multi-agent model, and unstack actions after the model if the environment expects per-agent leaves.

## Debugging recurrent multi-agent policies

For recurrent multi-agent models, keep both axes visible:

```text
batch/time dims ... x agent_dim x feature_dim x recurrent dims
```

Guidelines:

- Do not use one shared hidden key for actor and critic recurrent modules unless they intentionally share state.
- Include the group name in hidden keys, such as `('agents', 'actor_rs')`, when the policy operates on grouped agent tensors.
- Confirm `is_init` shape broadcasts across the agent dimension exactly as intended.
- When using decentralized parameter sharing, one hidden state per agent is often needed even when the network weights are shared.

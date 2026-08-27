# Network and MCTS Reference

## Purpose

Read this when inspecting or debugging MuZero General's network factory, inference APIs, MCTS root expansion, node statistics, search path traversal, value backup, or legal-action policy masking. The facts here are distilled from `models.py`, `self_play.py`, CartPole/TicTacToe configs, the README feature summary, and verified smoke/inspection runs.

## Verified public signatures

| Object | Verified signature | Notes |
| --- | --- | --- |
| `models.MuZeroNetwork` | `MuZeroNetwork(config)` | Factory object; returns a concrete `torch.nn.Module` subclass. |
| `model.initial_inference` | `initial_inference(observation)` | Expects a batched stacked observation tensor. |
| `model.recurrent_inference` | `recurrent_inference(encoded_state, action)` | Expects hidden state from the model and an action tensor shaped like `[[action_index]]` per batch item. |
| `models.support_to_scalar` | `support_to_scalar(logits, support_size)` | Decodes value/reward logits over `2 * support_size + 1` bins to scalar shape `(batch, 1)`. |
| `models.scalar_to_support` | `scalar_to_support(x, support_size)` | Encodes scalar targets to categorical support. |
| `self_play.MCTS.run` | `MCTS.run(model, observation, legal_actions, to_play, add_exploration_noise, override_root_with=None)` | Converts observation to the model device, expands root, runs `config.num_simulations`. |
| `self_play.GameHistory.get_stacked_observations` | `get_stacked_observations(index, num_stacked_observations, action_space_size)` | Builds channel-stacked current/past observations plus past action planes. |

## Network factory behavior

`MuZeroNetwork(config)` dispatches only on `config.network`:

- `"fullyconnected"` returns `MuZeroFullyConnectedNetwork`.
- `"resnet"` returns `MuZeroResidualNetwork`.
- Any other value raises `NotImplementedError('The network parameter should be "fullyconnected" or "resnet".')`.

The README advertises both residual and fully connected PyTorch networks. Verified smokes passed for the built-in CartPole FC configuration and TicTacToe ResNet configuration.

### Fully connected construction fields

The FC network consumes these config fields:

- `observation_shape`
- `stacked_observations`
- `action_space` length
- `encoding_size`
- `fc_reward_layers`
- `fc_value_layers`
- `fc_policy_layers`
- `fc_representation_layers`
- `fc_dynamics_layers`
- `support_size`

Implementation behavior:

- The representation network flattens the stacked observation to shape `(batch, flat_features)`.
- The encoded hidden state has shape `(batch, encoding_size)` and is normalized per sample to `[0, 1]`.
- Dynamics concatenates the encoded state with a one-hot action vector of width `len(action_space)`.
- Prediction emits `policy_logits` with width `len(action_space)` and value logits with width `2 * support_size + 1`.

Verified CartPole default smoke (`support_size=10`, `action_space=[0, 1]`, `encoding_size=8`) returned:

```text
initial_inference:   value (1, 21), reward (1, 21), policy_logits (1, 2), hidden_state (1, 8)
recurrent_inference: value (1, 21), reward (1, 21), policy_logits (1, 2), hidden_state (1, 8)
```

### ResNet construction fields

The ResNet network consumes these config fields:

- `observation_shape`
- `stacked_observations`
- `action_space` length
- `blocks`
- `channels`
- `reduced_channels_reward`
- `reduced_channels_value`
- `reduced_channels_policy`
- `resnet_fc_reward_layers`
- `resnet_fc_value_layers`
- `resnet_fc_policy_layers`
- `support_size`
- `downsample` (`False`, `"CNN"`, or `"resnet"`)

Implementation behavior:

- The representation input channel count is `observation_shape[0] * (stacked_observations + 1) + stacked_observations`.
- With `downsample=False`, hidden states keep the observation height and width and have shape `(batch, channels, height, width)`.
- With `downsample="CNN"` or `"resnet"`, the reward/value/policy head flatten sizes use `ceil(height / 16)` and `ceil(width / 16)`.
- Dynamics appends one action plane to the encoded state, scaled by `action / len(action_space)`.
- Prediction emits `policy_logits` with width `len(action_space)` and value logits with width `2 * support_size + 1`.

Verified TicTacToe default smoke (`support_size=10`, `action_space=range(9)`, `channels=16`, `observation_shape=(3, 3, 3)`) returned:

```text
initial_inference:   value (1, 21), reward (1, 21), policy_logits (1, 9), hidden_state (1, 16, 3, 3)
recurrent_inference: value (1, 21), reward (1, 21), policy_logits (1, 9), hidden_state (1, 16, 3, 3)
```

## Inference output contract

Both concrete networks return the same tuple order:

```python
value, reward, policy_logits, hidden_state = model.initial_inference(observation)
value, reward, policy_logits, hidden_state = model.recurrent_inference(hidden_state, action)
```

Meanings:

- `value`: categorical value logits, not a scalar. Decode with `support_to_scalar(value, config.support_size)`.
- `reward`: categorical reward logits. `initial_inference` uses a zero-reward center support vector for consistency.
- `policy_logits`: raw policy logits over action indexes. MCTS applies softmax only over the actions passed to `Node.expand`.
- `hidden_state`: normalized representation used by dynamics and MCTS recurrent steps.

Do not pass these logits directly to training loss assumptions unless the task is in `training-and-cli`; this sub-skill is about model/search debugging, not the trainer loss contract.

## MCTS root expansion and legal-action masking

`MCTS.run` performs these root steps when `override_root_with` is not supplied:

1. Creates `root = Node(0)`.
2. Converts the stacked observation to `torch.tensor(observation).float().unsqueeze(0)` on `next(model.parameters()).device`.
3. Calls `model.initial_inference(observation)`.
4. Decodes root predicted value and reward with `support_to_scalar`.
5. Asserts `legal_actions` is non-empty.
6. Asserts `set(legal_actions).issubset(set(config.action_space))`.
7. Calls `root.expand(legal_actions, to_play, reward, policy_logits, hidden_state)`.

`Node.expand` masks root policy by construction: it takes only the supplied `actions`, softmaxes `policy_logits[0][a]` for those action indexes, and creates children only for those actions. Later leaf expansion uses `config.action_space`, not the current game's legal actions.

Important action-index constraint: even though the subset assertion uses `config.action_space`, the implementation also indexes tensors by action integer (`policy_logits[0][a]` and FC one-hot scatter). Use contiguous integer actions such as `list(range(n))`, matching the config comments. Arbitrary action labels can pass a loose subset check yet still index the wrong policy column or fail at recurrent inference.

## Dirichlet exploration noise

When `add_exploration_noise=True`, MCTS calls:

```python
root.add_exploration_noise(config.root_dirichlet_alpha, config.root_exploration_fraction)
```

The method samples a Dirichlet vector with one entry per root child and mixes it into each child prior:

```text
new_prior = old_prior * (1 - exploration_fraction) + noise * exploration_fraction
```

Use exploration noise for self-play behavior; disable it for deterministic model/MCTS debugging unless the task is specifically about noisy priors.

## Search path logic

For each of `config.num_simulations` simulations:

1. Start at the root with `virtual_to_play = to_play` and `search_path = [root]`.
2. While the current node is expanded, choose the child with max UCB score, append it to the search path, and rotate `virtual_to_play` through `config.players`.
3. At the first unexpanded leaf, call `model.recurrent_inference(parent.hidden_state, torch.tensor([[action]]).to(parent.hidden_state.device))`.
4. Decode value and reward with `support_to_scalar`.
5. Expand the leaf with `config.action_space`.
6. Backpropagate the decoded value through the search path and update `MinMaxStats`.

`MCTS.run` returns `(root, extra_info)` where `extra_info` has:

```python
{
    "max_tree_depth": <int>,
    "root_predicted_value": <float or None when override_root_with is used>,
}
```

A tiny verified CartPole run expanded the root with two children and returned a depth/value info dictionary. Exact values are random-weight dependent; check shapes and child keys rather than hard-coding numeric values.

## UCB and MinMaxStats

`MinMaxStats` starts with `maximum = -inf`, `minimum = inf`.

- `update(value)` expands the observed min/max range.
- `normalize(value)` returns `(value - minimum) / (maximum - minimum)` only after both a real minimum and maximum exist; otherwise it returns the input value unchanged.

`MCTS.ucb_score` combines:

- prior score from the child prior, parent visit count, `pb_c_base`, and `pb_c_init`;
- normalized value score from `child.reward + discount * child.value()` in single-player mode;
- normalized value score from `child.reward + discount * -child.value()` in two-player mode.

## Two-player sign handling

MuZero General supports one or two players in this MCTS implementation:

- Single-player backpropagation adds the same decoded value through the path and updates `value = reward + discount * value`.
- Two-player backpropagation flips signs depending on whether `node.to_play == to_play`. The code stores `node.value_sum += value` for the same player and `-value` for the opponent, and alternates reward sign accordingly.
- More than two players raises `NotImplementedError("More than two player mode not implemented.")`.

For custom two-player games, verify that `config.players`, `Game.to_play()`, rewards, and legal actions are consistent before interpreting MCTS values.

## CPU/GPU and DataParallel basics

- Each network wraps major submodules in `torch.nn.DataParallel`, even on CPU.
- `MCTS.run` moves the observation to the model parameter device and recurrent action tensors to `parent.hidden_state.device`.
- Direct calls to `model.initial_inference` or `model.recurrent_inference` outside `MCTS.run` must put observation, hidden state, action tensor, and model on the same device.
- CPU is the safest default for shape/API smokes; use CUDA only when the task is specifically about GPU behavior.
- For Ray self-play/training device policy, route to `training-and-cli` because worker flags decide where models are moved.

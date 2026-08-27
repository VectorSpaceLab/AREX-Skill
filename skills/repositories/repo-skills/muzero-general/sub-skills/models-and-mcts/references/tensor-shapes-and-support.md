# Tensor Shapes and Support Transforms

## Purpose

Read this before debugging wrong observation rank, stacked-observation channel counts, FC/ResNet hidden-state shapes, recurrent action tensor shape, policy/action indexing, or value/reward support-size errors.

## Core shape rules

MuZero General expects game observations to be three-dimensional before stacking:

```text
observation_shape = (channels, height, width)
```

`SelfPlay.play_game` asserts both conditions before calling MCTS:

```text
len(numpy.array(observation).shape) == 3
numpy.array(observation).shape == config.observation_shape
```

If a one-dimensional environment vector is used, reshape it to `(1, 1, length)`. CartPole uses `(1, 1, 4)` and TicTacToe uses `(3, 3, 3)`.

## Stacked observations

`GameHistory.get_stacked_observations(index, num_stacked_observations, action_space_size)` returns the current observation plus `num_stacked_observations` past observation/action-plane pairs.

For base observation `(C, H, W)` and `N = num_stacked_observations`, the stacked output shape is:

```text
(C + N * (C + 1), H, W)
```

The extra `+1` channel per past step is an action plane filled with:

```text
action_history[past_observation_index + 1] / action_space_size
```

When the requested past index is before the start of the game history, MuZero General concatenates zero observation channels and a zero action plane.

Examples:

| Base shape | `stacked_observations` | Stacked shape | Notes |
| --- | ---: | --- | --- |
| CartPole `(1, 1, 4)` | `0` | `(1, 1, 4)` | Built-in CartPole default. |
| CartPole `(1, 1, 4)` | `2` | `(5, 1, 4)` | Current channel plus two `(observation + action)` pairs. |
| TicTacToe `(3, 3, 3)` | `0` | `(3, 3, 3)` | Built-in TicTacToe default. |
| TicTacToe `(3, 3, 3)` | `1` | `(7, 3, 3)` | Current 3 channels plus past 3 observation channels plus 1 action plane. |

Use `model_mcts_smoke.py --stacked-observations N` to verify whether a custom network/game pair accepts the stacked tensor shape.

## Model input shapes

The model APIs expect a batch dimension:

```python
observation_tensor = torch.tensor(stacked_observation).float().unsqueeze(0)
value, reward, policy_logits, hidden_state = model.initial_inference(observation_tensor)
```

| Network | Input shape to `initial_inference` | Hidden-state shape | Recurrent action shape |
| --- | --- | --- | --- |
| Fully connected | `(batch, C + N*(C+1), H, W)` then flattened internally | `(batch, config.encoding_size)` | `(batch, 1)` integer action indexes |
| ResNet with `downsample=False` | `(batch, C + N*(C+1), H, W)` | `(batch, config.channels, H, W)` | `(batch, 1)` integer action indexes |
| ResNet with `downsample="CNN"` or `"resnet"` | `(batch, C + N*(C+1), H, W)` | spatial size determined by downsample path; head sizes use `ceil(H/16)`, `ceil(W/16)` | `(batch, 1)` integer action indexes |

The recurrent call must use the hidden state returned by the same model family:

```python
action = torch.tensor([[legal_actions[0]]], device=hidden_state.device)
value, reward, policy_logits, next_hidden_state = model.recurrent_inference(hidden_state, action)
```

Common recurrent mistakes:

- Passing `action` shaped `(batch,)` instead of `(batch, 1)`.
- Passing a Python int directly instead of a tensor.
- Passing an action tensor on CPU while the hidden state/model is on CUDA.
- Passing a hidden state from FC into ResNet dynamics, or from a checkpoint/config with different `channels`, `encoding_size`, `downsample`, or `observation_shape`.

## Verified inference shape smokes

With default built-in configs and `support_size=10`, `full_support_size = 21`.

| Case | Network | Input observation | `initial_inference` output shapes | `recurrent_inference` output shapes |
| --- | --- | --- | --- | --- |
| CartPole | fully connected | `(1, 1, 1, 4)` | value `(1, 21)`, reward `(1, 21)`, policy `(1, 2)`, hidden `(1, 8)` | value `(1, 21)`, reward `(1, 21)`, policy `(1, 2)`, hidden `(1, 8)` |
| TicTacToe | ResNet | `(1, 3, 3, 3)` | value `(1, 21)`, reward `(1, 21)`, policy `(1, 9)`, hidden `(1, 16, 3, 3)` | value `(1, 21)`, reward `(1, 21)`, policy `(1, 9)`, hidden `(1, 16, 3, 3)` |

Run the bundled checker to reproduce the bundled source snapshot's shapes:

```bash
python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case both --num-simulations 1 --json
```

## Policy logits and action indexes

`policy_logits` width is `len(config.action_space)`. `Node.expand` indexes `policy_logits[0][a]` for every action `a` passed in. FC dynamics also scatters into a one-hot vector at the integer action index.

Practical rules:

- Keep `config.action_space` as `list(range(num_actions))`.
- Keep `legal_actions()` non-empty at every non-terminal search point.
- Keep every legal action inside `config.action_space`.
- Do not use arbitrary action IDs such as `[10, 20, 30]` unless the model code is changed; those IDs are used as tensor indexes.

## Support scalar transforms

MuZero General stores value and reward predictions as categorical logits over:

```text
[-support_size, ..., 0, ..., +support_size]
```

The vector width is:

```text
full_support_size = 2 * support_size + 1
```

For `support_size=10`, value and reward logits have width `21`.

### `support_to_scalar(logits, support_size)`

Input:

```text
logits shape: (batch, 2 * support_size + 1)
```

Behavior:

1. Applies `torch.softmax(logits, dim=1)`.
2. Computes the expected support value.
3. Inverts the MuZero square-root scaling.
4. Returns a scalar tensor shaped `(batch, 1)`.

Use this to interpret `value` and `reward` outputs from model inference or MCTS root prediction.

### `scalar_to_support(x, support_size)`

Input:

```text
x shape: (batch, target_columns)
```

Behavior:

1. Applies MuZero square-root scaling.
2. Clamps scaled values to `[-support_size, support_size]`.
3. Splits each scalar between floor and next support bin.
4. Returns shape `(batch, target_columns, 2 * support_size + 1)`.

Verified transform check: encoding scalars shaped `(3, 1)` with `support_size=10` returns `(3, 1, 21)`; decoding model value logits returns `(1, 1)`.

## Choosing `support_size`

The built-in configs use `support_size=10` and comments state value/reward are scaled and encoded on `[-support_size, support_size]`. Too small a support saturates large rewards/returns after scaling; too large a support increases output size and can make debugging harder.

For custom games:

- Estimate the largest absolute discounted return and immediate reward scale.
- Keep reward scaling consistent with game wrappers; TicTacToe multiplies terminal reward by `20`, so support choices matter.
- If decoded values are clipped or all mass lands on edge bins, increase `support_size` or adjust reward scaling.
- Keep checkpoint compatibility in mind; changing `support_size` changes value/reward head widths and prevents direct weight loading.

## Shape-debug workflow

1. Confirm the game config fields in sibling `games-and-configs`: `observation_shape`, `action_space`, `players`, and `stacked_observations`.
2. Run:

   ```bash
   python sub-skills/models-and-mcts/scripts/model_mcts_smoke.py --case custom --game-module <game_module> --network config --num-simulations 1 --json
   # For custom code in a staged copy, add: --repo-root <workdir>/muzero-general-source
   ```

3. If model inference fails before MCTS, compare `base_observation_shape`, `stacked_observation_shape`, and `initial_shapes` against the tables above.
4. If recurrent inference fails, inspect `hidden_state` and action tensor shape/device.
5. If MCTS fails, inspect legal actions and action index assumptions before debugging UCB or backpropagation.

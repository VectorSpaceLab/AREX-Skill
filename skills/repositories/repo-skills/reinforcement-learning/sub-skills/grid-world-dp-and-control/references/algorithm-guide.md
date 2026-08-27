# GridWorld Algorithm and API Guide

This guide distills the repository's GridWorld workflows into self-contained operating knowledge. The provenance workflow labels are `1-policy_iteration.py`, `2-value_iteration.py`, `3-sarsa.py`, `4-q_learning.py`, `5-deep_sarsa.py`, and `6-reinforce.py`; they are not runtime dependencies for this skill.

## 1. Shared 5x5 worlds

### DP world: `PolicyEnv`-style MDP

Use this model for policy iteration and value iteration.

- Grid size: `height = width = 5`.
- State convention: `[row, col]`.
- Terminal positive cell: `[2, 2]` with reward `+1.0` when entered.
- Negative reward cells: `[1, 2]` and `[2, 1]` with reward `-1.0` when entered.
- Transition probability: deterministic (`1.0`).
- Actions for DP: `0=up`, `1=down`, `2=left`, `3=right`.
- DP action deltas are applied to `[row, col]`:

| action | name | delta on `[row, col]` |
| --- | --- | --- |
| `0` | up | `[-1, 0]` |
| `1` | down | `[+1, 0]` |
| `2` | left | `[0, -1]` |
| `3` | right | `[0, +1]` |

The DP values and policies are table-indexed as `table[row][col]`. When drawing, plotting, or converting to screen coordinates, most graphics APIs expect `(x, y) = (col, row)`. Always swap: `draw_x = state[1]`, `draw_y = state[0]`.

### Static tabular control world: `Env`-style MDP

Use this model for tabular SARSA and tabular Q-learning.

- Grid size: `5x5`.
- State convention: `[col, row]`.
- Start: `[0, 0]`.
- Obstacles: `[1, 2]` and `[2, 1]`.
- Goal: `[2, 2]`.
- Rewards: `+100` and done on the goal; `-100` and done on an obstacle; `0` otherwise.
- Actions: `0=up`, `1=down`, `2=left`, `3=right`.
- Q-table keys in the original-style workflow are stringified coordinate lists such as `"[1, 0]"`.

Action deltas for `[col, row]`:

| action | name | delta on `[col, row]` |
| --- | --- | --- |
| `0` | up | `[0, -1]` |
| `1` | down | `[0, +1]` |
| `2` | left | `[-1, 0]` |
| `3` | right | `[+1, 0]` |

### Dynamic neural-control world: `DynamicEnv`-style MDP

Use this model for Deep SARSA and REINFORCE.

- State convention for positions: `[col, row]`.
- Observation vector size: `15`.
- Three moving obstacles each contribute four features: `dx`, `dy`, marker `-1`, and horizontal direction.
- Goal contributes three features: `goal_dx`, `goal_dy`, marker `+1`.
- Goal: `[4, 4]`, reward `+1.0`, terminal.
- Obstacle hits cost `-1.0` but do not terminate.
- Optional step penalty subtracts a small value each step; REINFORCE-style runs use `0.1` to encourage shorter paths.
- Rendering can be disabled with a `render_mode=None` pattern; do this for smoke checks and headless machines.
- Dynamic actions differ from the static tabular order:

| action | name in dynamic world | delta on `[col, row]` |
| --- | --- | --- |
| `0` | up | `[0, -1]` |
| `1` | down | `[0, +1]` |
| `2` | right | `[+1, 0]` |
| `3` | left | `[-1, 0]` |
| `4` | no-op by environment behavior | `[0, 0]` |

The distilled neural agents expose five action logits/values (`0..4`) while the dynamic environment only changes position for `0..3`. Treat action `4` as a source-compatible no-op. If you remove it, also change the model output dimension, sampling, and smoke expectations.

## 2. Policy iteration

Policy iteration alternates policy evaluation and policy improvement for the DP world.

### Tables and constants

- `V[row][col]`: scalar value table initialized to `0.0`.
- `pi[row][col][action]`: action probabilities initialized uniformly to `[0.25, 0.25, 0.25, 0.25]` for non-terminal states.
- Terminal policy at `[2, 2]`: empty list `[]`.
- Discount: `gamma = 0.9`.

### Policy evaluation

For each non-terminal state `s`, with deterministic next state `s' = T(s, a)`:

```text
V_new(s) = sum_a pi(a | s) * [ R(s, a) + gamma * V_old(T(s, a)) ]
```

In the original-style educational workflow, each synchronous evaluation sweep rounds values to two decimals. Preserve this rounding if you need output comparable to screenshots or overlays; avoid rounding inside a research-grade implementation unless you intentionally want the same didactic behavior.

### Policy improvement

For each non-terminal state:

```text
q(s, a) = R(s, a) + gamma * V(T(s, a))
A* = argmax_a q(s, a)
pi_new(a | s) = 1 / len(A*) if a in A* else 0
```

Ties are represented as equal probabilities across all best actions. This is useful for visual arrows because multiple arrows can be correct.

### Adaptation checklist

- Keep DP states as `[row, col]` until the moment of drawing.
- Use a new policy row/cell object per state if you reimplement the table; avoid accidental aliasing from list multiplication.
- Stop rollout at the goal before calling a policy picker that may not define an action for `[2, 2]`.
- A single evaluation or improvement sweep is a smoke/API check, not a convergence proof.

## 3. Value iteration

Value iteration applies the Bellman optimality equation directly.

### Update equation

For each non-terminal state:

```text
V_new(s) = max_a [ R(s, a) + gamma * V_old(T(s, a)) ]
```

The terminal state `[2, 2]` remains `0.0` as an absorbing target in the value table. As with policy iteration, the didactic workflow rounds each updated value to two decimals.

### Greedy policy extraction

After one or more value-iteration sweeps, the greedy action set is:

```text
A*(s) = { a : R(s, a) + gamma * V(T(s, a)) equals the state maximum }
```

For a visual policy, assign equal probability to every action in the greedy set. For control code that needs a single action, pick one action from the set deterministically for reproducibility or randomly to preserve tie diversity.

### Adaptation checklist

- `get_action([2, 2])` should return an empty action set.
- Use equal-probability arrows when several actions tie.
- If arrows look transposed, inspect `[row, col]` versus drawing `(col, row)` first; do not tune rewards to fix a plotting bug.

## 4. Tabular SARSA

SARSA is an on-policy temporal-difference control method. It learns from the transition tuple `<s, a, r, s', a'>`, where `a'` is sampled from the current behavior policy.

### Update equation

```text
Q(s, a) <- Q(s, a) + alpha * [ r + gamma * Q(s', a') - Q(s, a) ]
```

Distilled constants from the educational workflow:

- Learning rate: `alpha = 0.01`.
- Discount: `gamma = 0.9`.
- Exploration: epsilon-greedy with `epsilon = 0.1`.
- Q-table default: four zeros per unseen state.

### Action selection

Epsilon-greedy action selection:

1. With probability `epsilon`, sample a random action from `[0, 1, 2, 3]`.
2. Otherwise choose an action with the maximum Q-value.
3. If several actions tie, choose randomly among the tied actions.

### Adaptation checklist

- State keys are based on `[col, row]`, not `[row, col]`.
- SARSA must choose `next_action` before learning because the update is on-policy.
- A one-step update with a synthetic `next_action` is enough to smoke-test the API.
- Rendering every step is pedagogical; remove or guard rendering for tests.

## 5. Tabular Q-learning

Q-learning is off-policy TD control. It learns from `<s, a, r, s'>` and bootstraps from the greedy value of the next state, regardless of what action the behavior policy will actually take.

### Update equation

```text
Q(s, a) <- Q(s, a) + alpha * [ r + gamma * max_b Q(s', b) - Q(s, a) ]
```

Distilled constants match tabular SARSA: `alpha = 0.01`, `gamma = 0.9`, `epsilon = 0.1`, and four Q-values per state.

### SARSA versus Q-learning in this GridWorld

| Concern | SARSA | Q-learning |
| --- | --- | --- |
| Policy type | On-policy | Off-policy |
| Target action | Actual sampled `a'` | Greedy `argmax_b Q(s', b)` |
| Transition tuple | `<s,a,r,s',a'>` | `<s,a,r,s'>` |
| Risk in obstacle world | Learns the value of exploratory behavior | Learns greedy optimum under the Q-table |

## 6. Deep SARSA

Deep SARSA replaces the Q-table with a small neural network `Q_theta(s)`.

### Network shape

- Input: 15-dimensional dynamic-state vector.
- Hidden layers: two fully connected ReLU layers of width 30 in the distilled source workflow.
- Output: five Q-values, one per source-compatible action logit/value (`0..4`).

### One-step target

For transition `<s, a, r, s', a'>`:

```text
target = r                          if done
target = r + gamma * Q_theta(s')[a'] otherwise
loss = MSE(Q_theta(s)[a], target)
```

The target must be computed without gradient tracking. If the target is left connected to the same network graph, optimization can chase a moving target in the same backward pass and become unstable.

### Distilled constants

- Discount: `gamma = 0.99`.
- Learning rate: `1e-3` with Adam.
- Epsilon schedule: starts at `1.0`, multiplies by `0.9999`, floor `0.01`.
- Training length in the provenance workflow: `1000` episodes; do not use that as a smoke test.

### Adaptation checklist

- Use a headless dynamic environment for checks: create it with a `render_mode=None` behavior.
- Convert states to `float32` tensors.
- Keep `action_size=5` if preserving source-compatible behavior.
- For a smoke check, perform one optimizer step and assert finite loss plus epsilon decay.

## 7. REINFORCE

REINFORCE is a Monte Carlo policy-gradient method. It collects a full episode, computes returns, and applies one policy update.

### Network shape

- Input: 15-dimensional dynamic-state vector.
- Hidden layers: two fully connected ReLU layers of width 24 in the distilled source workflow.
- Output: five logits over source-compatible actions.

### Policy and returns

Sample from:

```text
pi_theta(a | s) = softmax(logits_theta(s))[a]
```

Compute discounted return backwards:

```text
G_t = r_t + gamma * G_{t+1}
```

With `gamma = 0.99`. The workflow standardizes returns per episode:

```text
G_hat = (G - mean(G)) / (std(G) + 1e-8)
```

Then minimizes the negative weighted log-likelihood:

```text
loss = - sum_t log pi_theta(a_t | s_t) * G_hat_t
```

This is gradient ascent on expected return expressed as minimization.

### Adaptation checklist

- Keep an episode buffer of states, actions, and rewards.
- Train once at episode end, then clear buffers.
- A two-step synthetic trajectory is enough to verify return computation, loss shape, and buffer clearing.
- Do not expect a tiny smoke run to improve policy quality.

## 8. Rendering and headless operation

The educational workflows use Pygame rendering for visualization. That is useful for a local desktop demonstration but unsuitable as a default validation path.

Safe default for this skill:

```bash
python scripts/grid_world_smoke.py
```

Rendering guidance:

- DP viewers are button-driven; a main loop waits for user clicks and should not be used in CI.
- Static tabular control loops render every step; guard or remove rendering for smoke tests.
- Dynamic neural workflows should use a `render_mode=None` pattern for training probes and headless servers.
- If you need visual output, verify display availability separately and keep the non-rendering script as the correctness smoke.

## 9. Safe API-level smoke checks

The bundled smoke script covers these assertions without importing original files:

- DP row/column convention: `[row, col]` transitions and `(col, row)` draw conversion.
- Policy-iteration evaluation/improvement changes a value table and keeps terminal policy empty.
- Value iteration produces a greedy action set for a state next to the goal.
- Static tabular control uses `[col, row]` and action `3=right`.
- SARSA and Q-learning each update a Q-table entry on a synthetic transition.
- Dynamic headless environment returns a 15-dimensional state and uses action `2=right`, unlike static tabular action `2=left`.
- Deep SARSA performs one Torch optimizer step and decays epsilon when Torch is available.
- REINFORCE computes discounted returns, performs one policy-gradient step, and clears its trajectory buffer when Torch is available.

Use `--strict-torch` when Torch coverage is required rather than optional.

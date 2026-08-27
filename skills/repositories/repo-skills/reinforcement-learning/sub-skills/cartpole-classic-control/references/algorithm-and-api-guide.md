# CartPole algorithm and API guide

This guide summarizes the CartPole-v1 DQN, A2C, and PPO workflows as self-contained operating knowledge. Source workflow names are used only as provenance labels.

## Shared environment facts

- Environment: `CartPole-v1` from Gymnasium classic control.
- Observation vector: 4 floating-point values; use `np.float32` before feeding PyTorch models.
- Action space: 2 discrete actions; all action pickers return Python `int` values in `{0, 1}`.
- Episode score: the scripts report the raw CartPole reward accumulated per step, so the maximum is 500.
- Termination handling: Gymnasium returns `terminated` and `truncated`; the training loops use `done = terminated or truncated`.
- Shared CLI flags: `--render` requests a human Pygame window during training; `--test` loads a checkpoint and replays episodes using human rendering.

## Reward shaping used by all three algorithms

The training score remains the raw episode length, but the learning update receives a shaped reward:

```python
shaped_reward = 0.1 if not done or score == 500 else -1
```

Implications:

- Normal survival steps receive `+0.1`, not the raw Gym reward `+1`.
- A failure terminal step receives `-1`.
- A perfect 500-step episode does not receive the failure penalty because `score == 500` preserves the positive step reward.
- If you compare learning curves with another CartPole implementation, separate raw score reporting from shaped update rewards.

## Workflow comparison

| Workflow label | Update style | Main model objects | Checkpoint payload | Training horizon |
| --- | --- | --- | --- | --- |
| DQN (`1-dqn.py`) | Off-policy Q-learning with replay and target network | `QNetwork`, `DQNAgent` | raw `QNetwork.state_dict()` saved as `cartpole_dqn.pt` | up to 300 episodes |
| A2C (`2-a2c.py`) | One-step synchronous actor-critic / TD(0) | `Actor`, `Critic`, `A2CAgent` | `{"actor": actor.state_dict(), "critic": critic.state_dict()}` saved as `cartpole_a2c.pt` | up to 1000 episodes |
| PPO (`3-ppo.py`) | On-policy clipped actor-critic with GAE rollouts | `ActorCritic`, `compute_gae` | raw `ActorCritic.state_dict()` saved as `cartpole_ppo.pt` | up to 1500 update cycles |

## DQN details

### Model and action selection

`QNetwork(state_size=4, action_size=2)` is a ReLU MLP:

```text
Linear(4, 24) -> ReLU -> Linear(24, 24) -> ReLU -> Linear(24, 2)
```

Linear layers use Kaiming-uniform initialization and zero biases. `DQNAgent.get_action(state)` is epsilon-greedy over `QNetwork(state)`:

- while exploring, it samples a random action;
- otherwise it returns `argmax_a Q(s, a)`;
- test mode sets `epsilon = 0.0`, so DQN replay is greedy.

### Training update

Important default hyperparameters:

| Field | Value | Meaning |
| --- | ---: | --- |
| `discount_factor` | `0.99` | TD bootstrap discount |
| `learning_rate` | `1e-3` | Adam learning rate |
| `epsilon` / `epsilon_decay` / `epsilon_min` | `1.0` / `0.999` / `0.01` | exploration schedule |
| `batch_size` | `64` | replay minibatch size |
| `train_start` | `1000` | no SGD until memory reaches this size |
| replay memory | `deque(maxlen=2000)` | sliding transition buffer |

For a sampled transition `(s, a, r, s', done)`, the target is:

```text
y = r                                  if done
y = r + gamma * max_a' Q_target(s',a') if not done
```

The loss is MSE between `Q_online(s,a)` and `y`. The target network is a hard copy of the online network and is updated once per completed episode.

### DQN footguns

- A short run may print many episodes before learning starts because `train_start=1000` delays SGD.
- The replay buffer has only 2000 slots; old transitions are intentionally discarded.
- Loading an A2C checkpoint into DQN gives nested `actor`/`critic` keys instead of Q-network layer keys.

## A2C details

### Model and action selection

A2C uses separate actor and critic networks:

```text
Actor:  Linear(4, 24) -> ReLU -> Linear(24, 2 logits)
Critic: Linear(4, 24) -> ReLU -> Linear(24, 1 value)
```

`A2CAgent.get_action(state)` computes `softmax(actor(state))` and samples from the categorical distribution. Test mode keeps this stochastic policy; it does not switch to greedy action selection.

### One-step update

Important defaults:

| Field | Value | Meaning |
| --- | ---: | --- |
| `discount_factor` | `0.99` | TD bootstrap discount |
| `actor_lr` | `1e-3` | Adam learning rate for the policy |
| `critic_lr` | `5e-3` | Adam learning rate for the value baseline |

For one transition:

```text
target    = r                         if done
target    = r + gamma * V(next_state) if not done
advantage = target - V(state)
```

The actor minimizes `-log pi(action|state) * advantage.detach()`. The critic minimizes `(V(state) - target)^2`. The advantage is detached for the actor so the actor does not backpropagate through the critic baseline.

### A2C footguns

- The checkpoint is not a raw actor or critic `state_dict`; it is a dictionary containing both `actor` and `critic` keys.
- The critic learning rate is deliberately larger than the actor learning rate so the baseline can track the policy.
- Because replay is stochastic, two test episodes from the same checkpoint can differ.

## PPO details

### Model

`ActorCritic(state_size=4, action_size=2)` is a shared-trunk actor-critic:

```text
Linear(4, 64) -> Tanh -> Linear(64, 64) -> Tanh
  -> policy head: Linear(64, 2 logits)
  -> value head:  Linear(64, 1 value)
```

Initialization follows common PPO/CleanRL practice:

- orthogonal trunk with gain `sqrt(2)`;
- small policy-head gain `0.01`, keeping the initial action distribution near uniform;
- value-head gain `1.0`.

### Rollout and GAE constants

| Constant | Value | Meaning |
| --- | ---: | --- |
| `ROLLOUT_STEPS` | `1024` | single-env steps collected before each PPO update |
| `EPOCHS` | `4` | SGD sweeps over the rollout batch |
| `MINIBATCH_SIZE` | `64` | minibatch size for PPO optimization |
| `CLIP_COEF` | `0.2` | probability-ratio clipping range |
| `GAMMA` | `0.99` | reward discount |
| `GAE_LAMBDA` | `0.95` | GAE trace parameter |
| `LR` | `3e-4` | Adam learning rate |
| `VALUE_COEF` | `0.5` | value-loss weight |
| `ENTROPY_COEF` | `0.01` | entropy-bonus weight |
| gradient clipping | `0.5` | global norm clip |

`compute_gae(rewards, values, dones, last_value)` performs the backward recursion:

```text
delta_t = r_t + gamma * V(s_{t+1}) * (1 - done_t) - V(s_t)
A_t     = delta_t + gamma * lambda * (1 - done_t) * A_{t+1}
return_t = A_t + V(s_t)
```

After GAE, advantages are normalized per rollout batch.

### PPO update

During rollout, PPO stores observations, actions, old log-probabilities, shaped rewards, done flags, and values. During optimization it recomputes log-probabilities under the current policy, forms:

```text
ratio = exp(new_log_prob - old_log_prob)
unclipped = ratio * advantage
clipped = clamp(ratio, 1 - clip_coef, 1 + clip_coef) * advantage
policy_loss = -mean(min(unclipped, clipped))
```

The total loss is:

```text
policy_loss + VALUE_COEF * value_loss - ENTROPY_COEF * entropy
```

### PPO footguns

- PPO is on-policy; do not reuse arbitrary old DQN/A2C transitions as PPO training data.
- A rollout of 1024 steps can contain multiple CartPole episodes; `done` resets the GAE recursion for terminal transitions.
- The PPO test action picker samples from the categorical policy, so it remains stochastic.
- `cartpole_ppo.pt` is a raw `ActorCritic.state_dict()`, not the same shape or key set as the DQN raw state dict.

## Safe validation expectations

Use the bundled [../scripts/cartpole_smoke.py](../scripts/cartpole_smoke.py) when you need a quick check. It verifies these invariants without creating a Gymnasium environment:

- DQN Q-network output has shape `(2,)`, replay-driven SGD can update online weights, and the target-network copy matches after `update_target_model()`.
- A2C actor logits and critic value have the expected shapes, action probabilities are finite, and one synthetic TD update changes parameters.
- PPO actor-critic logits/value shapes are valid, GAE returns finite advantages/returns, and a tiny clipped-surrogate update changes parameters.
- Algorithm-specific checkpoint validators accept the correct in-memory payload format and reject representative DQN/A2C/PPO mismatches.
- Headless render diagnostics explain whether `--render`/`--test` is likely to fail before opening a Pygame window.

Passing the smoke script does **not** prove CartPole convergence, Gymnasium installation, display availability, or checkpoint quality.

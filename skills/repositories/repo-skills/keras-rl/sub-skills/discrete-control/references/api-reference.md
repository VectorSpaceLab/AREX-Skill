# Discrete-control API reference

This reference summarizes the keras-rl discrete-action surfaces needed to build DQN-family, SARSA, and CEM agents against an installed keras-rl package. Use these APIs with a legacy Keras 2.x-compatible backend.

## Agent selection map

| Need | Agent | Required memory | Compile call | Main output contract |
| --- | --- | --- | --- | --- |
| Value-based discrete control with replay | `rl.agents.dqn.DQNAgent` | `SequentialMemory` | `compile(optimizer, metrics=[])` | model has a single output of shape `(None, nb_actions)` |
| Double DQN | `DQNAgent(enable_double_dqn=True, ...)` | `SequentialMemory` | same as DQN | same as DQN |
| Dueling DQN | `DQNAgent(enable_dueling_network=True, dueling_type="avg|max|naive", ...)` | `SequentialMemory` | same as DQN | base model still ends in `nb_actions`; agent replaces the final head internally |
| On-policy SARSA | `rl.agents.sarsa.SARSAAgent` | none | `compile(optimizer, metrics=[])` | model predicts one Q value per action |
| Cross-Entropy Method | `rl.agents.cem.CEMAgent` | `EpisodeParameterMemory` | `compile()` | model predicts one score/probability per action |

## DQNAgent

Verified constructor and compile signatures:

```python
DQNAgent(model, policy=None, test_policy=None,
         enable_double_dqn=False,
         enable_dueling_network=False,
         dueling_type='avg',
         *args, **kwargs)
DQNAgent.compile(optimizer, metrics=[])
```

Important inherited constructor keyword arguments accepted through `*args, **kwargs`:

| Argument | Typical value | Notes |
| --- | --- | --- |
| `nb_actions` | `env.action_space.n` | Required. Must match the model's final output width exactly. |
| `memory` | `SequentialMemory(limit=..., window_length=...)` | Required for DQN-family agents. |
| `gamma` | `0.99` | Discount factor. |
| `batch_size` | `32` | Replay mini-batch size; warm up memory enough before training. |
| `nb_steps_warmup` | `10` for tiny CartPole-style examples; much higher for pixels | Training starts only after warmup. |
| `train_interval` | `1` for low-dimensional states; often `4` for Atari-style frames | Train every N environment steps. |
| `memory_interval` | `1` | Store every N steps. |
| `target_model_update` | integer hard period such as `10000`, or soft coefficient such as `1e-2` | `>= 1` means hard copy every N steps; `0 < value < 1` means soft update. |
| `delta_clip` | `np.inf` or `1.0` | Huber loss clip; Atari-style DQN commonly uses `1.0`. |
| `processor` | processor instance or `None` | Processor implementation details are routed to the core-extension-and-logging sub-skill. |

DQN-specific toggles:

| Toggle | Meaning | Gotcha |
| --- | --- | --- |
| `enable_double_dqn=True` | Use online network for action selection and target network for value estimation. | Default is `False` in the installed API. Set explicitly when wanted. |
| `enable_dueling_network=True` | Replace the final Q head with a dueling value/advantage head. | The supplied base model is validated before replacement and must still end in exactly `nb_actions` outputs. |
| `dueling_type='avg'` | Aggregate `V(s)` and `A(s,a)` by subtracting average advantage. | Allowed values: `avg`, `max`, `naive`; `avg` is the safest default. |

Model contract:

```python
# For low-dimensional observations and window_length=1:
Flatten(input_shape=(1,) + observation_shape)
Dense(nb_actions)
Activation('linear')
```

DQN validates that the model has a single output and that the output shape is `(None, nb_actions)`. Many hard-to-read DQN failures are output-width or legacy symbolic-output compatibility problems.

## SARSAAgent

Verified constructor and compile signatures:

```python
SARSAAgent(model, nb_actions, policy=None, test_policy=None,
           gamma=0.99, nb_steps_warmup=10,
           train_interval=1, delta_clip=inf,
           *args, **kwargs)
SARSAAgent.compile(optimizer, metrics=[])
```

Key points:

- SARSA is on-policy and does **not** take replay memory.
- Use the same Q-output contract as DQN: one value per action.
- The constructor is less defensive than DQN about output shape; bad model shapes usually surface later as Q-value assertions or training-shape errors.
- `policy` controls training action selection; `test_policy` defaults to greedy behavior when omitted.
- `nb_steps_warmup`, `train_interval`, and `delta_clip` have the same practical meaning as DQN, but updates are one-step SARSA updates rather than replay batches.

## CEMAgent

Verified constructor and compile signatures:

```python
CEMAgent(model, nb_actions, memory, batch_size=50,
         nb_steps_warmup=1000, train_interval=50,
         elite_frac=0.05, memory_interval=1,
         theta_init=None, noise_decay_const=0.0,
         noise_ampl=0.0, **kwargs)
CEMAgent.compile()
```

Key points:

- Use `EpisodeParameterMemory`, not `SequentialMemory`.
- `compile()` takes no optimizer and no metrics argument; it internally compiles the model with a simple placeholder optimizer/loss.
- `batch_size * elite_frac` is converted to an integer elite count. Keep it at least `1` for meaningful updates.
- CEM samples full model parameter vectors per episode, records total episode rewards, and updates parameter distribution from elite episodes.
- A final softmax activation is common in CartPole-style examples, but the implementation exponentiates model outputs before action sampling; the critical shape is still `nb_actions`.

## Memories

### SequentialMemory

```python
SequentialMemory(limit, window_length=..., ignore_episode_boundaries=False)
```

Use with DQN-family agents. It stores transitions in ring buffers and samples replay experiences.

| Field | Practical guidance |
| --- | --- |
| `limit` | Maximum number of stored transitions; keep comfortably above warmup + batch size. |
| `window_length` | Number of recent observations in a state; the model input must include this leading window axis. |
| `ignore_episode_boundaries` | Usually `False`; when false, memory zero-pads across episode boundaries instead of leaking previous-episode frames. |
| `append(..., training=True)` | During testing, recent state is maintained but replay storage is not increased. |

### EpisodeParameterMemory

```python
EpisodeParameterMemory(limit, window_length=...)
```

Use with `CEMAgent`. It stores sampled parameter vectors and total episode rewards. Do not use it for DQN replay batches.

## Common policies

| Policy | Signature | Use |
| --- | --- | --- |
| `EpsGreedyQPolicy` | `EpsGreedyQPolicy(eps=0.1)` | Simple epsilon-greedy exploration for DQN/SARSA. |
| `GreedyQPolicy` | `GreedyQPolicy()` | Deterministic best-action test policy. |
| `BoltzmannQPolicy` | `BoltzmannQPolicy(tau=1.0, clip=(-500.0, 500.0))` | Softmax exploration over Q values; common in CartPole-style examples. |
| `LinearAnnealedPolicy` | `LinearAnnealedPolicy(inner_policy, attr, value_max, value_min, value_test, nb_steps)` | Anneal a policy attribute such as `eps`; common for Atari-style DQN. |
| `MaxBoltzmannQPolicy` | `MaxBoltzmannQPolicy(eps=0.1, tau=1.0, clip=(-500.0, 500.0))` | Mix greedy and Boltzmann exploration. |
| `BoltzmannGumbelQPolicy` | `BoltzmannGumbelQPolicy(C=1.0)` | Training-only exploration; do not use as a test policy. |

## Compile-before-use checklist

- DQN/SARSA: pass a Keras optimizer instance, for example a legacy `Adam(lr=1e-3)`, and optional metrics such as `['mae']`.
- CEM: call `cem.compile()` with no arguments.
- Compile before calling `fit`, `test`, `metrics_names`, `load_weights` into DQN target-network workflows, or any smoke that expects `trainable_model`/`target_model` to exist.
- If an optimizer keyword such as `lr` or `learning_rate` fails, first confirm that the environment is actually a Keras 2.x-compatible stack for keras-rl.

# TD3 and replay-buffer API reference

This reference distills the behavior evidenced by `TD3/train_velodyne_td3.py`,
`TD3/replay_buffer.py`, and the matching actor loader in
`TD3/test_velodyne_td3.py`. It is intentionally self-contained: use bundled
smoke scripts for executable checks instead of importing those source modules.

## Data contract

| Item | Contract |
|---|---|
| State | 20 range-bin values followed by `[distance, heading, linear_action, angular_action]`; shape `(24,)` for one state |
| Stored action | Actor-space pair in `[-1, 1]^2`; shape `(2,)` |
| Environment action | `[ (stored_action[0] + 1) / 2, stored_action[1] ]`; linear velocity is nonnegative after conversion |
| Reward | Scalar, batched to `(batch, 1)` by the buffer |
| Done stored | `0` at the artificial 500-step time limit, otherwise `int(done)`; this controls bootstrap masking |
| Next state | Same 24-value layout as state |

The source environment constructs the observation as 20 Velodyne minima plus four
robot values. The training script uses `environment_dim=20`, `robot_dim=4`,
`action_dim=2`, and `max_action=1`. A shape-only test must retain these sizes,
even when it uses synthetic values.

## Actor

`Actor(state_dim, action_dim)` has these layers:

```text
Linear(state_dim, 800) -> ReLU
Linear(800, 600)         -> ReLU
Linear(600, action_dim)  -> Tanh
```

With the repository dimensions, parameters have output shapes `800 x 24`,
`600 x 800`, and `2 x 600` (plus biases), and a batch of eight states returns
`(8, 2)`. `tanh` bounds the normalized output but does not perform the
linear-velocity conversion used by the simulator adapter.

`get_action(state)` reshapes one state to `(1, -1)`, moves it to the module's
selected device, runs the actor, and returns a flattened CPU NumPy array. A
portable implementation should use `torch.inference_mode()` or `no_grad()` for
inference rather than relying on `.data`.

## Twin Critic

`Critic(state_dim, action_dim)` owns two independent branches:

```text
Q1: state Linear(state_dim, 800) -> ReLU
    state Linear(800, 600) + action Linear(action_dim, 600) -> ReLU
    Linear(600, 1)
Q2: same dimensions, independent parameters
```

`forward(state, action)` returns `(q1, q2)`, each shaped `(batch, 1)`. The
source's forward method calls the second-layer Linear modules and discards
those results, then uses matrix multiplies and the action projection bias to
form the combined activation. This is an implementation quirk, not a reason to
change the state/action dimensions. Preserve the state-dict layer names when
loading compatible checkpoints; if reimplementing, document any numerical
change and verify outputs/shapes separately.

## TD3 wrapper

`TD3(state_dim, action_dim, max_action)` creates:

- online `actor` and `critic`;
- `actor_target` and `critic_target`, initially copied from the online models;
- one Adam optimizer for each online network;
- a `SummaryWriter()` using its default log directory;
- `iter_count`, incremented once after each `train` call.

`save(filename, directory)` writes two actor/critic state dictionaries as
`<directory>/<filename>_actor.pth` and
`<directory>/<filename>_critic.pth`. It does not save target parameters,
optimizer state, replay data, counters, or a configuration manifest.
`load(...)` restores only online actor and critic state dictionaries.

When adapting loading for a different device, use an explicit
`torch.load(path, map_location=device)` and validate the resulting keys and
shapes. Older and newer PyTorch versions may differ in `weights_only` defaults;
state-dict-only files are the intended artifact, but a compatibility failure
must be surfaced rather than caught as a generic fresh-start condition.

## `train(...)`

The method signature is:

```text
train(replay_buffer, iterations, batch_size=100, discount=1,
      tau=0.005, policy_noise=0.2, noise_clip=0.5, policy_freq=2)
```

The caller's training constants override several signature defaults. For each
iteration it samples a batch, computes target actions and clipped target noise,
gets both target Q values, uses `min(Q1, Q2)`, and applies
`reward + (1 - done) * discount * target_Q` after detaching. It then minimizes
`MSE(current_Q1, target_Q) + MSE(current_Q2, target_Q)`.

On `it % policy_freq == 0`, including `it == 0`, the actor minimizes the
negative mean of critic Q1 evaluated at the actor's action. Both target networks
are then updated with `tau * online + (1 - tau) * target`. Because `it` is local
to one `train` call and the source calls training once per finished episode,
the apparent delay resets at every episode. TensorBoard receives `loss`,
`Av. Q`, and `Max. Q` once per `train` call, with `iter_count` as the x-axis.

## ReplayBuffer

`ReplayBuffer(buffer_size, random_seed=123)` stores experiences in a deque.
`add(s, a, r, t, s2)` appends until capacity and thereafter removes the oldest
entry before appending. `size()` returns the count. `sample_batch(n)` samples
without replacement; when fewer than `n` items exist, it returns all available
items instead of raising or padding. Arrays are returned in the order
`states, actions, rewards, dones, next_states`; rewards and dones are reshaped
to `(returned_count, 1)`. `clear()` empties both deque and count.

The source seeds Python's `random` module in the constructor. Reproducibility
therefore requires controlling NumPy/PyTorch seeds as well as this sampler if
those libraries generate states or actions.

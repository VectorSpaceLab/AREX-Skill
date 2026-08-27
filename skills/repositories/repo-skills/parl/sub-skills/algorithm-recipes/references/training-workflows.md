# Training Workflows

This reference gives safe, short-form recipes for adapting PARL examples. It intentionally avoids full long-running training scripts, downloads, environment installation, and challenge launchers.

## Preflight checklist

1. Pick the backend and set it before importing PARL:

   ```python
   import os
   os.environ.setdefault("PARL_BACKEND", "torch")  # or "paddle" / "fluid"
   import parl
   ```

2. Select the algorithm from `algorithm-catalog.md` and check the model method surface before instantiation.
3. Keep environment wrappers and replay/logging utilities in the `environment-utils` sub-skill; do not reimplement Gym compatibility, replay buffers, or schedulers blindly.
4. For distributed examples, separate the algorithm loop from xparl cluster lifecycle. Use the `xparl-distributed` sub-skill before starting or connecting workers.
5. Add a `--dry-run` or `--max-episodes 1` path when adapting any training command for inspection. A short run proves wiring only, not benchmark quality.

## QuickStart / PolicyGradient recipe

Best for: CartPole-like discrete action spaces and teaching the PARL `Model -> Algorithm -> Agent` pattern.

Model contract:

- `forward(obs)` returns an action-probability vector or batch of probabilities.
- Agent `sample(obs)` samples from probabilities for exploration.
- Agent `predict(obs)` takes the greedy action for evaluation.
- Agent `learn(obs_batch, action_batch, reward_to_go_batch)` delegates to `alg.learn`.

Safe skeleton:

```python
model = CartpoleLikeModel(obs_dim=obs_dim, act_dim=act_dim)
alg = parl.algorithms.PolicyGradient(model, lr=1e-3)
agent = CartpoleLikeAgent(alg)

for episode in range(max_episodes):
    observations, actions, rewards = collect_one_episode(env, agent.sample)
    returns = reward_to_go(rewards, gamma=1.0)
    agent.learn(observations, actions, returns)
    if episode % eval_every == 0:
        evaluate_without_training(agent, make_eval_env)
```

Adaptation notes:

- Keep reward-to-go separate from raw rewards; the QuickStart pattern updates rewards backward with `G_t = r_t + gamma * G_{t+1}`.
- Use an environment compatibility wrapper for Gym reset/step API differences.
- Save checkpoints only under a user-selected output directory; avoid hard-coded `./model.ckpt` in reusable code.

## DQN / DDQN recipe

Best for: discrete action spaces with replay, e.g. CartPole or Atari-like tasks.

Model contract:

- `forward(obs)` returns Q-values shaped `[batch_size, act_dim]`.
- `DQN.learn(obs, action, reward, next_obs, terminal)` expects action indices suitable for gathering the selected Q-value.
- `sync_target()` copies online weights into the target model.

Safe skeleton:

```python
alg = parl.algorithms.DQN(model, gamma=0.99, lr=1e-3)
agent = DQNAgent(alg)
replay = ReplayMemory(max_size)

while not stop_condition():
    action = epsilon_greedy(agent.predict(obs), epsilon)
    next_obs, reward, done, info = env.step(action)
    replay.append(obs, action, reward, next_obs, done)
    if len(replay) >= warmup_size:
        batch = replay.sample(batch_size)
        agent.learn(batch)
    if global_step % target_update_interval == 0:
        alg.sync_target()
```

DDQN keeps the same model and Agent shape but changes the target calculation inside the algorithm. Dueling DQN is a model architecture choice; ensure its final `forward` still returns Q-values.

## Continuous actor-critic recipe: DDPG, TD3, SAC, OAC

Best for: MuJoCo-style continuous control and continuous-action simulators.

Shared model contract:

- `policy(obs)` returns an action or stochastic policy parameters.
- `value(obs, action)` returns one or two Q-values depending on the algorithm.
- `get_actor_params()` and `get_critic_params()` return disjoint trainable parameter groups.
- `TD3` additionally requires `Q1(obs, action)`.

Safe skeleton:

```python
alg = parl.algorithms.TD3(
    model,
    gamma=0.99,
    tau=0.005,
    actor_lr=1e-4,
    critic_lr=1e-3,
)
agent = ContinuousAgent(alg, action_low, action_high)
replay = ReplayMemory(max_size)

for step in range(max_steps):
    action = agent.sample(obs)  # add bounded exploration noise in the Agent
    next_obs, reward, done, info = env.step(action)
    replay.append(obs, action, reward, next_obs, done)
    if len(replay) >= warmup_size:
        for _ in range(updates_per_step):
            agent.learn(replay.sample(batch_size))
    if done:
        obs = env.reset()
```

Algorithm-specific notes:

- `DDPG`: deterministic policy plus critic; simple but sensitive to exploration and Q bias.
- `TD3`: twin critics, delayed policy updates, and target smoothing; verify the model's `Q1` method.
- `SAC`: stochastic policy with entropy term; `policy(obs)` commonly returns mean and log standard deviation.
- `OAC`: SAC-like model surface plus optimistic exploration; only use when the exploration method is intentional.
- `CQL`: offline RL; do not call environment collection inside the primary update loop.

## PPO / A2C recipe

Best for: on-policy rollouts where collected data is discarded after update.

Model contract:

- `PPO`: `policy(obs)` and `value(obs)`.
- `A2C`: `policy(obs)`, `value(obs)`, and `policy_and_value(obs)`.

Safe skeleton:

```python
rollout = []
for _ in range(rollout_steps):
    action, logprob, value = agent.sample(obs)
    next_obs, reward, done, info = env.step(action)
    rollout.append((obs, action, reward, done, logprob, value))
    obs = next_obs if not done else env.reset()

batch = compute_returns_and_advantages(rollout, gamma=0.99, lam=0.95)
agent.learn(batch)
```

Use PPO when you need clipped policy updates, minibatches, or continuous/discrete action flexibility. Use A2C for a simpler synchronous actor-critic baseline. For slow environment simulation or many actors, add xparl only after the single-process loop is correct.

## IMPALA recipe

Best for: actor-learner setups with many remote actors and V-trace correction.

Model contract:

- `policy(obs)` returns action logits or probabilities.
- `value(obs)` returns state values.

Workflow:

1. Validate the single learner imports and model methods.
2. Validate one actor's environment wrapper and trajectory schema locally.
3. Only then introduce xparl actors, distributed files, and learner queues.
4. Use a bounded local cluster only with explicit permission because cluster commands create processes and bind ports.

## Multi-agent recipe: QMIX, MADDPG, COMA, MAPPO

Best for: environments with multiple agents, joint state, per-agent observations/actions, and centralized training.

Shape checklist:

- Keep `n_agents`, `n_actions`, observation shape, state shape, and action availability masks in one config object.
- Ensure episode batches include padding/filled masks when episode lengths differ.
- Use lists or tensors consistently: do not mix per-agent lists and stacked tensors without a conversion boundary.

Algorithm notes:

- `QMIX`: uses recurrent per-agent Q-network plus a mixer. Agent model needs `init_hidden` and `forward`; mixer needs `forward` and `n_agents`.
- `MADDPG`: one algorithm instance per agent index; policy/value methods consume the selected agent's observation/action and all agents' joint tensors for the critic.
- `COMA`: Torch source expects actor/critic params and actor recurrent hidden initialization. Centralized critic inputs must match action availability and agent id encoding.
- `MAPPO`: model owns actor/critic submodules and exposes `policy`, `value`, and action-dimension metadata.

Safe synthetic wiring check:

```python
assert batch["obs"].shape[:3] == (batch_size, episode_len, n_agents)
assert batch["actions"].shape[:2] == (batch_size, episode_len)
assert batch["available_actions"].shape[-2:] == (n_agents, n_actions)
```

## Offline and sequence workflows: CQL, IQL, DecisionTransformer

Offline RL differs from online RL: the learner updates from a fixed dataset and should not mutate the dataset by collecting fresh exploratory transitions.

- `CQL`: use D4RL-like transition batches. Confirm observations/actions are normalized consistently with the dataset.
- `IQL`: expects actor, critic, and value parameter groups plus `qvalue`; top-level export may vary, so inspect the current package before use.
- `DecisionTransformer`: train on trajectories containing states, actions, returns-to-go, and timesteps. Use `get_action` for inference-style rollout. Do not wrap it in a replay-buffer online control loop unless the task explicitly asks for a hybrid design.

## Evaluation skeleton

Evaluation should be deterministic where the algorithm supports it:

```python
def evaluate(agent, make_env, episodes=5):
    scores = []
    for _ in range(episodes):
        env = make_env()
        obs = env.reset()
        total = 0.0
        done = False
        while not done:
            action = agent.predict(obs)
            obs, reward, done, info = env.step(action)
            total += float(reward)
        scores.append(total)
    return sum(scores) / len(scores)
```

Do not render by default; rendering may require a display server or create windows. Do not save videos or checkpoints unless the output location is user-approved.

## Minimal adaptation rubric

A safe adapted recipe should state:

- Backend and algorithm class.
- Model methods and tensor shapes.
- Agent methods and NumPy/backend tensor conversion boundary.
- Environment wrapper and action scaling decisions.
- Replay/rollout/dataset schema.
- Training stop condition and evaluation interval.
- What the smoke run proves, and what it does not prove.

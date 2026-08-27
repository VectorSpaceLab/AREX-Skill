# CartPole CLI and checkpoints

This guide covers the DQN, A2C, and PPO CartPole-v1 training/test command surfaces, shared flags, and checkpoint formats. It is self-contained; source workflow names are provenance labels.

## Command pattern

When you are operating in a repository checkout that contains the CartPole training workflows, run commands from the CartPole workflow directory so checkpoints land next to the workflow being executed.

```bash
# DQN training, no window
uv run python 1-dqn.py

# A2C training, no window
uv run python 2-a2c.py

# PPO training, no window
uv run python 3-ppo.py
```

The scripts share the same two flags:

```bash
--render   # show a Pygame CartPole window during training
--test     # load the saved checkpoint and replay episodes with human rendering
```

Examples:

```bash
# Watch DQN training, slower and display-dependent
uv run python 1-dqn.py --render

# Replay a trained A2C checkpoint; loops until interrupted
uv run python 2-a2c.py --test

# Replay a trained PPO checkpoint; loops until interrupted
uv run python 3-ppo.py --test
```

## Render and test behavior

The shared environment helper constructs:

```python
gym.make("CartPole-v1", render_mode="human" if (args.render or args.test) else None)
```

Consequences:

- Plain training without flags is headless and is the safest default for remote/CI machines.
- `--render` opens a Pygame window during training and can slow down all three algorithms.
- `--test` also opens a Pygame window; it is not a headless evaluation mode.
- Test mode uses an infinite replay loop. Stop it with `Ctrl-C` or by closing the window if the display event loop is functioning.
- On a headless server, prefer the bundled smoke script for checkpoint-format validation instead of `--test`.

To check render readiness without opening a window:

```bash
python scripts/cartpole_smoke.py --require-render-ready
```

Run it without `--require-render-ready` when you only want a warning-level display diagnostic.

## Checkpoint names and payloads

Each workflow saves one file in its current working directory after training exits:

| Algorithm | File name | Saved payload | Test loader expectation |
| --- | --- | --- | --- |
| DQN | `cartpole_dqn.pt` | raw `QNetwork.state_dict()` | `agent.model.load_state_dict(torch.load(path))` |
| A2C | `cartpole_a2c.pt` | dictionary with `actor` and `critic` state dicts | load `ckpt["actor"]` into `agent.actor` and `ckpt["critic"]` into `agent.critic` |
| PPO | `cartpole_ppo.pt` | raw `ActorCritic.state_dict()` | `model.load_state_dict(torch.load(path))` |

The files are not interchangeable.

### Loader sketches

DQN:

```python
agent = DQNAgent(state_size=4, action_size=2)
agent.model.load_state_dict(torch.load("cartpole_dqn.pt"))
agent.epsilon = 0.0
```

A2C:

```python
agent = A2CAgent(state_size=4, action_size=2)
ckpt = torch.load("cartpole_a2c.pt")
agent.actor.load_state_dict(ckpt["actor"])
agent.critic.load_state_dict(ckpt["critic"])
```

PPO:

```python
model = ActorCritic(state_size=4, action_size=2)
model.load_state_dict(torch.load("cartpole_ppo.pt"))
```

## Checkpoint validation without training or rendering

The bundled smoke script can validate checkpoint structure against the expected CartPole model keys:

```bash
# Validate a DQN raw state_dict
python scripts/cartpole_smoke.py --algorithm dqn --checkpoint cartpole_dqn.pt

# Validate an A2C nested actor/critic checkpoint
python scripts/cartpole_smoke.py --algorithm a2c --checkpoint cartpole_a2c.pt

# Validate a PPO raw ActorCritic state_dict
python scripts/cartpole_smoke.py --algorithm ppo --checkpoint cartpole_ppo.pt
```

If the script is launched from a different directory, adjust only the checkpoint path; the smoke script itself remains under this sub-skill's `scripts/` directory.

## Common mismatch signatures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Missing key(s)` / `Unexpected key(s)` while loading DQN | An A2C or PPO checkpoint was passed to DQN, or the DQN model definition changed. | Use `cartpole_dqn.pt` with DQN's `QNetwork`; regenerate if model dimensions changed. |
| `KeyError: 'actor'` in A2C test mode | A raw DQN/PPO `state_dict` was loaded as an A2C checkpoint. | Use `cartpole_a2c.pt` or a dictionary containing both `actor` and `critic`. |
| A2C validator says `actor`/`critic` values are not state dicts | The file is not the expected nested A2C payload. | Re-save with `{"actor": actor.state_dict(), "critic": critic.state_dict()}`. |
| PPO load reports DQN layer keys such as `net.0.weight` | A DQN checkpoint was passed to PPO. | Use `cartpole_ppo.pt` with PPO's `ActorCritic`. |
| Size mismatch for linear layer weights | The checkpoint was produced by a different architecture, state size, or action size. | Recreate the matching `state_size=4`, `action_size=2` model or retrain. |

## Operational notes

- A script saves its checkpoint even if it stops early for solving; if interrupted before the final `torch.save`, the checkpoint may be absent or stale.
- DQN test mode is greedy because it sets `epsilon = 0.0`; A2C and PPO test modes remain stochastic because they sample from their categorical policies.
- The CartPole solved criterion used by the workflows is a recent 10-episode mean above 490, not the older Gym threshold of 475 over 100 episodes.
- Do not use the smoke script as a substitute for measuring reward; it intentionally avoids Gymnasium training and display creation.

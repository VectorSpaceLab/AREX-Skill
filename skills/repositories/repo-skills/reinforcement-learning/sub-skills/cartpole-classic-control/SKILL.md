---
name: cartpole-classic-control
description: "Operate DQN, A2C, and PPO CartPole-v1 training, testing,
  checkpoints, and smoke diagnostics for the reinforcement-learning repo."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CartPole Classic Control

Use this sub-skill when the task involves the repository's CartPole-v1 DQN, A2C, or PPO workflows: choosing the right algorithm script, explaining network/update behavior, running training or replay, diagnosing checkpoints, or doing a safe headless smoke check.

Do not use it for GridWorld dynamic programming or tabular control, standard Atari Breakout/Pong CNN workflows, hard-exploration Atari/RND/Go-Explore/robustification, or paper-level benchmark claims.

## Fast route

- **Need algorithm/API facts or update formulas?** Read [references/algorithm-and-api-guide.md](references/algorithm-and-api-guide.md).
- **Need commands, flags, checkpoint names, or loader formats?** Read [references/cli-and-checkpoints.md](references/cli-and-checkpoints.md).
- **Need to debug imports, rendering, reward shaping, convergence, Gymnasium API changes, or checkpoint mismatch?** Read [references/troubleshooting.md](references/troubleshooting.md).
- **Need a quick verification that does not train or open a display?** Run [scripts/cartpole_smoke.py](scripts/cartpole_smoke.py). It uses synthetic states and includes checkpoint-format and render-readiness diagnostics.

## Operating guardrails

- Treat full CartPole training as a real run, not a smoke test. DQN can run up to 300 episodes, A2C up to 1000, and PPO up to 1500 update cycles with 1024 environment steps per update.
- Avoid `--render` during training unless the user explicitly wants an interactive window; it slows learning and can fail on headless hosts.
- `--test` also requests Gymnasium `render_mode="human"`; use it only when a display is available and a compatible checkpoint is present.
- The bundled smoke script is intentionally standalone and does not require Gymnasium, Pygame, the training scripts, or a display. It proves tensor/API shape and update invariants, not training convergence.
- Checkpoints are algorithm-specific: DQN and PPO save raw model `state_dict`s; A2C saves a dictionary with separate `actor` and `critic` entries.

## Provenance labels

This sub-skill distills the CartPole workflows identified in the source material as `2-cartpole/1-dqn.py`, `2-cartpole/2-a2c.py`, `2-cartpole/3-ppo.py`, and the shared CartPole environment helper `2-cartpole/env.py`. Those names are provenance/workflow labels; the runtime guidance below is self-contained and does not require opening the original source files.

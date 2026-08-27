---
name: bandits-and-reinforcement-learning
description: "Routes numpy-ml bandit, policy, trainer, and optional Gym-based
  reinforcement-learning tasks with dependency guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Bandits and Reinforcement Learning

Use this sub-skill for `numpy-ml` multi-armed bandit and tabular reinforcement
learning workflows:

- Bernoulli, multinomial, Gaussian, contextual Bernoulli, and contextual linear
  bandits;
- epsilon-greedy, UCB1, Thompson sampling, and LinUCB policies;
- bandit training/comparison helpers;
- Gym-backed RL agents and trainers for Monte Carlo, TD, cross-entropy, and
  Dyna-style workflows.

## First Checks

1. Run the plotting-free smoke helper for base bandit functionality:

   ```bash
   python sub-skills/bandits-and-reinforcement-learning/scripts/bandit_rl_smoke.py
   ```

2. Read [`references/api-reference.md`](references/api-reference.md) before
   constructing bandits, policies, or RL agents.
3. Read [`references/workflows.md`](references/workflows.md) for a tiny bandit
   policy loop and an RL/Gym preparation checklist.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when
   `gym`, `matplotlib`, action-space assumptions, plotting, or runtime length
   block a task.

## Route by Task

| User asks for | Use this route |
| --- | --- |
| simulate a small bandit | bandit API and smoke script. |
| compare policies without plotting | workflow reference with `plot=False`. |
| train on an OpenAI Gym environment | RL setup checklist and troubleshooting. |
| debug missing `gym` or `matplotlib` warnings | troubleshooting reference. |
| neural-network policies or deep RL | this repo only provides educational tabular/linear-style components; route neural layers to `../neural-network-components/SKILL.md`. |

## Operating Notes

- Bandit APIs work in the base CPU environment.
- RL training on real environments requires the optional Gym dependency and may
  be sensitive to Gym/Gymnasium API version drift.
- `policy.act(bandit, context=None)` returns `(reward, arm_id)` and mutates the
  policy's estimates.
- Plotting helpers are optional and should not be part of a safe smoke unless
  the user explicitly asks for plots.

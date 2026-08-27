---
name: value-based-discrete-control
description: "Use the repository's Char01 DQN family for discrete Gym control:
  CartPole, MountainCar, replay buffers, reward shaping, target-network updates,
  and TensorBoard logging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Value-Based Discrete Control

Use this sub-skill for requests about the repository's Deep Q-Network examples in
classic discrete-action Gym environments. It is a routing and operating guide for
the Char01 DQN family, not a packaged training API.

## Use when

- The user asks to run, adapt, or explain the CartPole DQN workflow.
- The user asks why MountainCar DQN is hard, how to shape its reward, or how to
  tune its replay/update settings.
- The user asks about the DQN replay buffer layout, sampling behavior,
  epsilon-greedy action selection, target network copy cadence, or TensorBoard
  loss/episode logs.
- The user needs a bounded compatibility probe for Gym classic-control + torch +
  tensorboardX before adapting a DQN script.

## Route elsewhere

- Tabular Q-learning/Sarsa/GridWorld requests -> sibling `tabular-control`.
- REINFORCE, policy-gradient, actor-critic, A2C, or PPO requests -> sibling
  `on-policy-actor-critic`.
- DDPG, SAC, TD3, Pendulum, BipedalWalker, or continuous-action off-policy
  requests -> sibling `off-policy-continuous-control`.
- Plot-only curve aggregation requests -> root/shared plotting support.

## Runtime entry points

1. For a DQN-family decision or code adaptation, read
   `references/dqn-family-map.md` first.
2. For failures, surprising learning curves, headless runs, TensorBoard output,
   or Gym-version issues, read `references/troubleshooting.md`.
3. For a bounded environment/API check, run the bundled inspection helper rather
   than launching a long training loop:

   ```bash
   python sub-skills/value-based-discrete-control/scripts/dqn_discrete_probe.py --env CartPole-v0 --steps 3
   python sub-skills/value-based-discrete-control/scripts/dqn_discrete_probe.py --env MountainCar-v0 --steps 3 --reward-shaping mountaincar-position-bonus
   ```

   The helper performs no learning and never calls `render()`.

## Source-script policy

The repository's DQN scripts are training-scale references, not safe default
helpers. Treat them as distilled patterns:

- `DQN_CartPole-v0.py` and `DQN_MountainCar-v0.py`: list replay buffer,
  tensorboardX logging, target/act networks, long episode counts.
- `DQN.py`, `naiveDQN.py`, and `DQN_mountain_car_v1.py`: older numpy-ring-buffer
  variants with unconditional render/plot behavior; use for algorithm notes and
  reward-shaping clues only.

Do not run the original long loops by default. If a user explicitly asks to run
training, first make it bounded: disable rendering, choose a writable logdir,
reduce episodes/capacity for a smoke, and preserve old-Gym reset/step semantics
or add a compatibility wrapper.

## Fast operating checklist

- Identify env family: CartPole has dense-ish balance reward; MountainCar needs
  explicit discussion of sparse/step-penalty learning and shaping.
- Identify replay style: list replay (`capacity=8000`, `batch_size=256`) versus
  numpy ring replay (`MEMORY_CAPACITY=2000` or `20000`).
- Check learning gate: most variants do not update until replay memory is full.
- Check target sync cadence: target networks are hard-copied every 100 update or
  learn steps, depending on the variant.
- Keep runtime edits self-contained; do not depend on the original checkout.

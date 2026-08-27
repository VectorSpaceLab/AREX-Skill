---
name: atari-breakout-pong
description: "Guides standard Atari Breakout and Pong DQN/PPO workflows with
  preprocessing, devices, checkpoints, W&B logging, and safe synthetic smoke
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Atari Breakout/Pong DQN and PPO

Use this sub-skill when a task is about the repository's standard Atari
Breakout/Pong workflows: DQN, PPO, ALE/Gymnasium preprocessing, Nature CNN
models, DQN replay buffers, PPO vector rollouts, device choice, W&B logging,
checkpoints, `--test`, or benchmark interpretation.

Do **not** use this sub-skill for Montezuma's Revenge, Pitfall, PrivateEye,
RND, Go-Explore, restore-state search, or robustification curricula; route those
to the hard-Atari exploration owner instead. Do not use it for CartPole PPO/DQN
or GridWorld formulas.

## Start here

1. Read [preprocessing-and-devices](references/preprocessing-and-devices.md)
   when the user asks about `--env breakout|pong`, `--device auto|cpu|cuda|mps`,
   wrappers, frame stacking, ROM/display requirements, or per-life versus
   per-game returns.
2. Read [algorithm-and-run-guide](references/algorithm-and-run-guide.md) for the
   DQN and PPO workflow contracts, checkpoint names, command-shape examples,
   training constants, W&B behavior, and benchmark caveats.
3. Read [troubleshooting](references/troubleshooting.md) before diagnosing ROM
   install failures, W&B login/network issues, missing checkpoints, device
   errors, replay-buffer sampling errors, headless rendering, or unexpectedly
   different scores.
4. Run or inspect [scripts/atari_basic_smoke.py](scripts/atari_basic_smoke.py)
   for a safe synthetic check of the Nature CNNs, DQN replay stacking/masking,
   PPO GAE, and tiny gradient updates. The helper intentionally avoids ALE env
   construction, ROM downloads, W&B credentials, and long training.

## Runtime boundaries

- Source workflow labels: `3-atari/1-dqn.py` is the Atari DQN workflow label;
  `3-atari/2-ppo.py` is the Atari PPO workflow label; `3-atari/env.py` is the
  preprocessing/device helper label. Treat these labels as provenance only, not
  as files this sub-skill needs future agents to open.
- This sub-skill is self-contained for guidance and smoke verification. If a
  user explicitly asks to run an actual repository checkout, apply the CLI
  contract documented in the references to that checkout's Atari entrypoints.
- Full Breakout/Pong training is expensive: the documented training budget is
  10M agent steps, and real env reset requires Atari ROM availability. Prefer
  the bundled smoke helper when the task is only to validate model/replay/GAE
  logic or environment-independent usability.

## Quick synthetic check

From this sub-skill directory:

```bash
python scripts/atari_basic_smoke.py --help
python scripts/atari_basic_smoke.py --device cpu
```

Use `--device auto` only when you want the helper to choose CUDA, then MPS, then
CPU using the same priority as the Atari workflows.

---
name: parl
description: "Use PARL reinforcement-learning framework workflows, core
  Model/Algorithm/Agent APIs, built-in algorithms, xparl distributed execution,
  wrappers, Waymax-RL, and EvoKit safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PARL repo skill

Use this repo skill when a task involves **PARL**, PaddlePaddle/PARL, `parl`, `xparl`, PARL `Model` / `Algorithm` / `Agent` classes, PARL built-in RL algorithms, PARL environment utilities, optional Waymax-RL, or optional EvoKit.

PARL is a reinforcement-learning framework with three main Python abstractions:

- `Model`: the policy, value, actor, critic, or Q-network forward computation.
- `Algorithm`: update logic, losses, optimizers, target models, and prediction/sampling methods.
- `Agent`: environment-facing I/O, preprocessing, action selection, learning calls, and persistence.

## Start here

1. **Identify the task surface.** Pick the matching sub-skill from the route map below instead of reading every file.
2. **Choose a backend before importing PARL.** Set `PARL_BACKEND=torch`, `PARL_BACKEND=paddle`, or `PARL_BACKEND=fluid` before `import parl` when the backend matters. If unset, PARL prefers installed Paddle 2.x, then legacy Fluid, then Torch.
3. **Verify installation with a safe checker.** From this skill directory, run:

   ```bash
   python scripts/check_parl_install.py --backend torch --xparl-help
   ```

   Replace `torch` with `paddle` or `fluid` only after installing and intentionally selecting that backend.
4. **Keep optional workflows explicit.** Waymax-RL needs a GPU JAX/Waymax/data stack; EvoKit needs native C++ dependencies; TIPC and challenge launchers can mutate systems or run long jobs. Do not treat a base PARL import as proof those workflows are ready.
5. **Use provenance for staleness.** Read `references/repo-provenance.md` before refreshing this skill or comparing it with a different PARL checkout.

## Route map

| User request or signal | Read next | Why |
| --- | --- | --- |
| Build or debug `parl.Model`, `parl.Algorithm`, `parl.Agent`, backend aliases, save/restore, weight sync. | `sub-skills/core-framework/SKILL.md` | Core abstraction and backend-selection guidance. |
| Choose/adapt DQN, DDQN, DDPG, TD3, SAC, OAC, CQL, PPO, A2C, IMPALA, QMIX, MADDPG, COMA, MAPPO, DecisionTransformer, IQL, QuickStart, TIPC, or PARL examples. | `sub-skills/algorithm-recipes/SKILL.md` | Algorithm catalog, model-method contracts, safe training skeletons, and example safety classifications. |
| Start/connect/status/stop `xparl`, use `@parl.remote_class`, distribute files, debug worker ports/logs, or reason about xparl security. | `sub-skills/xparl-distributed/SKILL.md` | Distributed execution, CLI/API flags, trust boundaries, and operations. |
| Use Gym compatibility wrappers, continuous action mapping, vector envs, replay memory, schedulers, CSVLogger, summaries, Atari/MuJoCo/multi-agent wrappers. | `sub-skills/environment-utils/SKILL.md` | Support utilities that make PARL training loops robust. |
| Use Waymax autonomous-driving all-GPU RL, Hydra `ppo_config`, JAX CUDA, Waymo TFRecord data, or rl-games runner settings. | `sub-skills/waymax-rl/SKILL.md` | Optional specialized workflow with no CPU substitute and a static config validator. |
| Use EvoKit C++ evolution strategies, `ESAgent`, `SamplingInfo`, CMake/protobuf/glog/gflags, libtorch, or PaddleLite. | `sub-skills/evo-kit/SKILL.md` | Optional C++ ES toolkit with read-only prerequisite checking. |

## Install and verification notes

- Public install entry point: `pip install parl`; local-source users can install from a checkout, but must verify imports from outside the checkout.
- Core model/algorithm work needs a deep-learning backend. Install exactly the backend intended by the task and set `PARL_BACKEND` before import.
- xparl operations use PARL's remote subsystem and `xparl` console script. Help checks are non-mutating; `xparl start`, `connect`, and `stop` start or stop real processes.
- PARL documentation for this snapshot described Python 3.7–3.10 as tested for install, with Python 3.8+ preferable for distributed training. Prefer a backend-supported Python rather than the newest host Python.
- Read `references/backend-verification.md` for what this generated skill verified and which optional backends remain source-backed.

## Cross-cutting references and scripts

- `references/backend-verification.md` — verified Torch CPU/xparl/help facts, optional backend boundaries, and safe checker sequence.
- `references/troubleshooting.md` — cross-cutting install/import/backend/xparl/training/optional-workflow recovery notes.
- `references/repo-provenance.md` — source commit, version, evidence paths, and refresh criteria.
- `references/repo-routing-metadata.json` — structured router metadata consumed by managed repo-skill import tooling.
- `scripts/check_parl_install.py` — safe root diagnostic for PARL import, backend aliases, and optional xparl help.

## Verification boundary

This generated skill was verified against PARL `2.2.1` source evidence. Runtime inspection verified the Torch backend on CPU for core aliases and tiny weight operations, plus xparl help and selected environment utilities. Paddle 2.x, legacy Fluid, CUDA execution, Waymax-RL, EvoKit builds, TIPC scripts, and large challenge examples are covered by source evidence and explicit readiness checks, not by completed runtime execution in this skill production run.

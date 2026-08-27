---
name: algorithm-recipes
description: "Select and adapt PARL built-in reinforcement-learning algorithms
  and safe recipe skeletons."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PARL Algorithm Recipes

Use this sub-skill when a task asks which PARL algorithm to use, which `parl.Model` methods an algorithm expects, how to adapt a PARL example into a safe training/evaluation loop, or how to interpret PARL's TIPC and challenge examples without running unsafe launchers.

## Route first

- Need `parl.Model`, `parl.Agent`, backend selection, save/restore, or weight-sync basics? Read `../core-framework/SKILL.md` first.
- Need wrappers, replay buffers, schedulers, vector environments, logging, or Gym API compatibility? Read `../environment-utils/SKILL.md` with this sub-skill.
- Need `xparl start/connect`, remote actors, distributed file shipping, ports, or cluster security? Read `../xparl-distributed/SKILL.md` before adapting distributed examples.
- Need Waymax all-GPU autonomous-driving PPO or EvoKit C++ evolution-strategy workflows? Route to `../waymax-rl/SKILL.md` or `../evo-kit/SKILL.md`; this sub-skill only names them as optional specialized workflows.

## Choose the reference

1. Read `references/algorithm-catalog.md` to select an algorithm family and confirm required model methods.
2. Read `references/training-workflows.md` for safe training/evaluation skeletons and QuickStart-style adaptation patterns.
3. Read `references/troubleshooting.md` before debugging import errors, backend gaps, tensor shape mismatches, unsupported model methods, target sync bugs, or convergence expectations.
4. Read `references/tipc-reference.md` only to classify PARL TIPC configurations; do not run the original TIPC shell launchers unless a human explicitly accepts the side effects.
5. Read `references/challenge-examples.md` when the task involves PARL competition examples, curriculum learning, OpenSim/L2RPN, or large distributed challenge runs.

## Safe inspection helper

Run the bundled helper from this sub-skill directory or pass a source root explicitly:

```bash
python scripts/inspect_algorithm_catalog.py --backend torch
python scripts/inspect_algorithm_catalog.py --backend paddle --no-import --source-root <repo-or-package-root>
python scripts/inspect_algorithm_catalog.py --backend torch --algorithm SAC --json
```

The helper is read-only. It imports PARL when available, otherwise falls back to static source inspection and reports missing backends without installing packages or launching training.

## Operating rules

- Set `PARL_BACKEND=torch`, `PARL_BACKEND=paddle`, or `PARL_BACKEND=fluid` before importing `parl` when the target backend matters.
- Treat Torch algorithm signatures as runtime-verified for the major built-in classes covered by the production inspection. Paddle and Fluid entries are source-backed in this skill unless the current task separately verifies those runtimes.
- Prefer tiny smoke checks and synthetic shape checks over long RL training. Do not claim benchmark reproduction from a one-episode or help-only run.
- Do not copy PARL example launchers into a user workspace unless you have replaced network downloads, long training defaults, system package changes, xparl process control, and environment-specific paths with explicit, user-approved steps.

---
name: ai-optimizer
description: "Route AI-Optimizer reinforcement-learning collection tasks across
  model-based RL, easy-MARL, offline RL, safe command builders, and repository
  limitations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AI-Optimizer

Use this repo skill when a task names AI-Optimizer or asks for help with its reinforcement-learning algorithm collection: model-based RL, easy-MARL multi-agent RL, offline RL, algorithm selection, command construction, dataset/schema checks, dependency caveats, or safe static verification before running experiments.

AI-Optimizer is a research-code collection rather than one installable Python distribution. Treat each algorithm family as its own runtime surface with separate dependencies and simulator/data requirements.

## Route by task

| User request mentions | Read |
|---|---|
| Dreamer, ED2-Dreamer, PlaNet, MuZero, Sampled MuZero, MBPO, ED2-MBPO, BMPO, CaDM, world models, learned dynamics, planning, model-based baselines | [model-based-rl](sub-skills/model-based-rl/SKILL.md) |
| MARL, easy-MARL, IDQN, VDN, QMIX, CommNet, IDDPG, MADDPG, IPPO, MAPPO, MAGYM, MPE, scenario names, multi-agent training commands | [multi-agent-rl](sub-skills/multi-agent-rl/SKILL.md) |
| Offline RL, batch RL, D4RL, MDPDataset, d3rlpy-derived APIs, BCQ, BEAR, CQL, AWAC, REDQ, UWAC, ISPI, COMBO, MOPO, E2O, PEX, offline-to-online | [offline-rl](sub-skills/offline-rl/SKILL.md) |
| Unsure where a folder or algorithm belongs, or need a high-level map of checked-in and empty areas | [repository-map.md](references/repository-map.md) |
| Import/install/backend/data failures shared across algorithm families | [troubleshooting.md](references/troubleshooting.md) |
| Staleness, source commit, dirty state, or evidence-path audit | [repo-provenance.md](references/repo-provenance.md) |

## Safe default workflow

1. Identify the algorithm family and route to the matching sub-skill.
2. Use bundled command builders or validators before running original training code:
   - Model-based MuZero command builder: `sub-skills/model-based-rl/scripts/build_muzero_command.py`.
   - Easy-MARL command builder: `sub-skills/multi-agent-rl/scripts/build_easy_marl_command.py`.
   - Offline RL command builders and dataset validator: `sub-skills/offline-rl/scripts/`.
3. Run [scripts/check_ai_optimizer_static.py](scripts/check_ai_optimizer_static.py) when checking a generated skill tree or a target checkout layout without launching training.
4. Before executing any printed command, verify the target runtime environment for that algorithm family. Do not assume dependencies are shared across subdirectories.
5. Treat full RL training, simulator execution, CUDA allocation, dataset downloads, and background experiment launches as deliberate heavy actions that need task-specific approval and resources.

## Important constraints

- The inspected checkout contains checked-in code for `modelbased-rl`, `multiagent-rl/easy-marl`, and `offline-rl-algorithms`.
- Several submodule placeholders are empty in the inspected source snapshot: `cornerstone`, `self-supervised-rl`, `transfer-and-multi-task-reinforcement-learning`, and `multiagent-rl/core`. Do not claim their code is available from this skill.
- Many algorithm folders target old ML stacks: TensorFlow 1.x/2.1/2.2 GPU, Ray 0.6/0.7, old Gym, MuJoCo 1.50, dm_control, D4RL, Waymo, MAGYM, or MPE. Keep those prerequisites explicit.
- This skill preserves operating guidance and safe helpers. It does not verify benchmark scores or completed training runs.
- Runtime links in this skill point to bundled skill files. Source-path names in references are identifiers for target AI-Optimizer checkouts, not links to this production checkout.

## Minimal inspection checks

For a target AI-Optimizer checkout, prefer safe checks before training:

```bash
python scripts/check_ai_optimizer_static.py --source-root /path/to/AI-Optimizer
python sub-skills/multi-agent-rl/scripts/build_easy_marl_command.py --agent-name IDQN --env-name discrete_meeting
python sub-skills/model-based-rl/scripts/build_muzero_command.py --env CartPole-v1 --case classic_control --opr train --no-cuda --force
python sub-skills/offline-rl/scripts/build_offline_rl_command.py bcq --dataset halfcheetah-medium-v2 --seed 0 --omit-gpu
```

The printed commands are recipes for a target checkout. The helpers do not install dependencies, start environments, download datasets, run training, or write model outputs.

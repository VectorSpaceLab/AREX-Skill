---
name: roboverse
description: "Routes RoboVerse research and engineering tasks across simulation,
  task authoring, learning, benchmark integrations, and cross-simulator parity."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RoboVerse

Use this skill when a task involves RoboVerse, `roboverse-py`, `roboverse_pack`,
RoboVerse tasks/robots/scenes, MetaSim package discovery, robot learning
pipelines, LIBERO/ManiSkill/MJLab/robosuite/RobotWin/SimplerEnv integrations,
or simulator parity.

RoboVerse is the downstream content, learning, dataset, benchmark, and example
layer. MetaSim is the upstream owner of core scenario/config types, task
registry, simulator handlers/backends, and environment abstractions. Keep that
boundary explicit before editing code.

## Start here

1. Read [references/installation-and-boundaries.md](references/installation-and-boundaries.md)
   for package identity, install variants, and the MetaSim/RoboVerse ownership
   boundary. Run the smallest import check before backend work.
2. Route by intent:
   - [simulation-workflows](sub-skills/simulation-workflows/SKILL.md) for
     ScenarioCfg, robots, scenes, grounds, assets, cameras, queries,
     randomization, teleop, rendering, and basic execution.
   - [task-development](sub-skills/task-development/SKILL.md) for new/changed
     tasks, registration, observations, rewards, resets, callbacks, and tests.
   - [learning-pipelines](sub-skills/learning-pipelines/SKILL.md) for RL, IL,
     VLA, fusion, datasets, checkpoints, runners, and evaluation.
   - [benchmark-integrations](sub-skills/benchmark-integrations/SKILL.md) for
     benchmark metadata, data/demo conversion, replay, and external stacks.
   - [parity-and-tooling](sub-skills/parity-and-tooling/SKILL.md) for measured
     cross-simulator comparisons, registration audits, and diagnostic scripts.
3. Read [references/troubleshooting.md](references/troubleshooting.md) whenever
   imports, optional dependencies, assets, data/config validation, or backend
   behavior fails.
4. Check [references/repo-provenance.md](references/repo-provenance.md) before
   treating this skill as current for a changed checkout.

## Minimal checks

```bash
python -m pip install -e ".[mujoco]"
python -c "import roboverse_pack, metasim; print('RoboVerse imports OK')"
python -c "import torch; print(torch.cuda.is_available())"  # report, do not assume
```

Choose `dev` for focused tests and `examples` for tutorial helpers. Add
`learn`, `vla`, or a simulator-specific extra only for the selected workflow.
Do not claim every advertised simulator or external benchmark is verified from a
CPU import or from one MuJoCo run.

## Operational rules

- Validate and normalize at boundaries; fail clearly for unsupported task,
  robot, backend, data, or config values.
- Run end-to-end before claiming numerical parity. Report exact backends and
  measured deltas; closed-loop policy transfer is a separate claim.
- Prefer additive task-family extensions and existing config composition.
- Keep GPU, display, external-data, credential, real-robot, and long-training
  actions explicit and bounded. The skill does not provide deployment advice.

---
name: learning-and-baselines
description: "Use ManiSkill RL/IL baseline families, benchmark task sets,
  evaluation conventions, and data-generation helpers without launching long
  training runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Learning and Baselines

Use this sub-skill when the task is to understand, compare, or prepare ManiSkill reinforcement-learning and imitation-learning baselines.

## Route here for

- PPO, SAC, TD-MPC2, BC, ACT, Diffusion Policy, RFCL, and RLPD
- baseline-specific setup, dependency, logging, checkpoint, and evaluation questions
- standard benchmark task-set selection and fair comparison conventions
- benchmark data-generation helpers used to create or replay datasets
- common pitfalls around wandb, missing extras, backend mismatch, dataset mismatch, and long-running workflows

## Do not handle here

- `gym.make`, observation/control/render mode setup, wrapper semantics, or CPU/GPU simulation selection -> [environment-usage](../environment-usage/)
- trajectory download/replay/conversion, teleoperation, or motion-planning details -> [trajectories-and-datasets](../trajectories-and-datasets/)
- custom task or benchmark-task authoring -> [custom-environments](../custom-environments/)

## How to work

1. Identify the family: online RL, supervised imitation learning, online learning from demonstrations, or model-based RL.
2. Consult the bundled references before recommending commands or evaluation settings.
3. Keep baseline scripts and data-generation helpers reference-only unless the user explicitly asks to run them.
4. Match the evaluation protocol to the benchmark family: no partial resets, reconfigure on reset, and record standard metrics.
5. If the request crosses into trajectory replay, dataset conversion, or demo file-layout details, route that part away.

## Key rules

- Treat baseline training and benchmark sweeps as expensive by default.
- Do not assume wandb login, external clones, or dataset availability.
- Keep data-collection backend and training/evaluation backend aligned when fairness depends on it.
- Prefer exact command families and relevant flags rather than inventing a new launcher.
- Follow the current docs when old comments or older examples disagree; note the mismatch instead of guessing.

## Bundled references

- `references/baselines.md`
- `references/benchmark-tasks.md`
- `references/evaluation.md`
- `references/troubleshooting.md`
- `references/data-generation.md`

## Bundled script

- `scripts/baseline_surface_index.py` — prints a safe index of the baseline families, benchmark sets, evaluation contract, and data-generation helpers; never starts training.

Start with `references/baselines.md` for algorithm coverage and `references/evaluation.md` for the fair-evaluation contract.

---
name: tensorforce
description: "Guide Tensorforce reinforcement-learning package workflows,
  including agents, environments, Runner execution, configuration modules,
  persistence, export, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensorforce

Use this repo skill when a task involves the Tensorforce Python package: creating reinforcement-learning agents, defining Tensorforce environments, configuring networks/objectives/optimizers, running `Runner` training/evaluation, saving/loading/exporting agents, or diagnosing Tensorforce 0.6.x dependency and API issues.

Tensorforce is an older TensorFlow-based RL framework. Prefer bounded CPU smoke checks before long training, and treat optional simulator, GPU, TensorFlow Addons, and BOHB tuning integrations as opt-in capabilities that require their own dependencies and evidence.

## Start here

1. Read [repo provenance](references/repo-provenance.md) before judging staleness for a checkout or package version.
2. Read [installation and inspection](references/installation-and-inspection.md) before installing, importing, or repairing dependencies.
3. Run or adapt [scripts/check_tensorforce_env.py](scripts/check_tensorforce_env.py) to verify an installed Tensorforce runtime.
4. Route the user task to the narrowest sub-skill below.
5. Use [cross-cutting troubleshooting](references/troubleshooting.md) for dependency, TensorFlow, Gym, optional extra, and package-age failures.

## Route by task

| User task | Read |
|---|---|
| Create/load agents, choose algorithm aliases, specify states/actions, use action masks, write `act`/`observe` or `experience`/`update` loops | [agents-and-specifications](sub-skills/agents-and-specifications/SKILL.md) |
| Configure networks, layers, preprocessing, memories, policies, objectives, optimizers, parameters, JSON/dict module specs, and `config` fields | [modules-and-configuration](sub-skills/modules-and-configuration/SKILL.md) |
| Implement or wrap environments, use `Environment.create`, Gym/custom adapters, reward shaping, vectorized/multi-actor/remote interaction, optional simulator adapters | [environments-and-interaction](sub-skills/environments-and-interaction/SKILL.md) |
| Run bounded training/evaluation with `Runner`, translate historical `run.py` flags, configure callbacks/logging/parallelism, reason about optional BOHB tuning | [runner-and-cli-workflows](sub-skills/runner-and-cli-workflows/SKILL.md) |
| Save/load agents, checkpoints, summaries/tracking, recorder/pretraining, and TensorFlow SavedModel export | [persistence-export-and-recording](sub-skills/persistence-export-and-recording/SKILL.md) |

## Minimal import check

```bash
python - <<'PY'
import tensorforce
from tensorforce import Agent, Environment, Runner
print(tensorforce.__version__)
print(Agent.create, Environment.create, Runner)
PY
```

For a stronger smoke check from this skill directory:

```bash
python scripts/check_tensorforce_env.py --smoke-agent
```

## Operating constraints

- Do not assume historical repository-level scripts, examples, benchmark configs, or tests exist in the user's project. Use the bundled references and scripts in this skill.
- Do not claim CARLA, ALE, Retro, ViZDoom, OpenSim/PLE, TensorFlow Addons, BOHB tuning, or GPU execution is verified unless the user's runtime has the required extra and a bounded check passes.
- Keep training examples short by default. Long RL runs are task experiments, not installation checks.
- Tensorforce 0.6.x dependency pins are old. If modern pip resolution fails around TensorFlow/NumPy/Gym, use [installation and inspection](references/installation-and-inspection.md) and document the exact compatible environment chosen.

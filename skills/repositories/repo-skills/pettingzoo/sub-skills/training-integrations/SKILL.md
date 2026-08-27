---
name: training-integrations
description: "Adapt PettingZoo training tutorials for CleanRL, Tianshou, SB3,
  Ray/RLlib, AgileRL, and LangChain while keeping heavy execution gated."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PettingZoo Training Integrations

Use this sub-skill when a user asks to connect PettingZoo environments to downstream training or agent frameworks such as CleanRL, Tianshou, Stable-Baselines3, Ray/RLlib, AgileRL, or LangChain. Keep actual training, framework installation, GPU use, display rendering, credentialed services, and network activity opt-in.

## Read First

- Read [framework-recipes.md](references/framework-recipes.md) to choose the right framework recipe, environment family, dependency group, and safe adaptation path.
- Read [vectorization-and-action-masks.md](references/vectorization-and-action-masks.md) when converting between AEC and Parallel APIs, preserving action masks, or using SuperSuit/vector wrappers.
- Read [troubleshooting.md](references/troubleshooting.md) when imports, version constraints, masks, vectorization, rendering, or long-running training fail.
- Run [inspect_integration_requirements.py](scripts/inspect_integration_requirements.py) to print the known tutorial requirement groups and optionally check whether framework modules are importable locally without installing anything.

## Routing Boundaries

- For basic PettingZoo `AECEnv` and `ParallelEnv` loops, route to `../use-environments/SKILL.md`.
- For optional family extras, ROMs, rendering dependencies, and environment selection, route to `../environment-families/SKILL.md`.
- For conversion wrappers, `AgentSelector`, utility wrappers, and wrapper ordering, route to `../wrappers-and-utilities/SKILL.md`.
- For compliance tests or safe native-test selection, route to `../testing-and-validation/SKILL.md`.

## Default Safety Policy

Training tutorials are reference recipes, not default runtime scripts. Before running any training framework command, confirm the user wants the required environment mutation, dependency installation, compute budget, checkpoint writes, display rendering, network access, or credentials.

---
name: pettingzoo
description: "Use, select, author, validate, wrap, and integrate PettingZoo
  multi-agent reinforcement-learning environments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PettingZoo

Use this repo skill when a task involves PettingZoo, the multi-agent reinforcement-learning environment API built around AEC and Parallel environment interfaces. It helps future agents write correct environment loops, choose optional environment families, implement custom environments, compose wrappers/utilities, run compliance tests, and adapt framework tutorials safely.

## Start Here

- Read [references/installation-and-extras.md](references/installation-and-extras.md) before installing optional families or diagnosing missing dependencies.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports, render modes, action masks, ROMs, wrappers, tests, or framework adapters fail.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a source checkout.
- Run [scripts/check_pettingzoo_install.py](scripts/check_pettingzoo_install.py) to check the installed PettingZoo version, base import, optional family imports, and optional constructor probes without downloads or training.

## Route By Task

- Use [sub-skills/use-environments/SKILL.md](sub-skills/use-environments/SKILL.md) for AEC or Parallel rollout loops, `reset`/`step` lifecycle, action masks, `termination`/`truncation`, `step(None)`, rendering, seeding, and bounded smoke checks.
- Use [sub-skills/environment-families/SKILL.md](sub-skills/environment-families/SKILL.md) for Classic, Butterfly, Atari, SISL, deprecated Magent, optional extras, environment selection, ROMs, and family-specific dependency errors.
- Use [sub-skills/custom-environments/SKILL.md](sub-skills/custom-environments/SKILL.md) to implement or review a new AEC or Parallel environment, including factories, spaces, metadata, action masks, wrappers, and versioned exports.
- Use [sub-skills/wrappers-and-utilities/SKILL.md](sub-skills/wrappers-and-utilities/SKILL.md) for `aec_to_parallel`, `parallel_to_aec`, utility wrappers, `AgentSelector`, `average_total_reward`, `save_observation`, and wrapper ordering.
- Use [sub-skills/testing-and-validation/SKILL.md](sub-skills/testing-and-validation/SKILL.md) for `api_test`, `parallel_api_test`, seed tests, render tests, max-cycle checks, CI selection, native test safety, and failure interpretation.
- Use [sub-skills/training-integrations/SKILL.md](sub-skills/training-integrations/SKILL.md) for CleanRL, Tianshou, Stable-Baselines3, Ray/RLlib, AgileRL, LangChain, vectorization, framework dependencies, and heavy-run gating.

## Verified Package Facts

- Package/import name: `pettingzoo`.
- Version covered by this skill: `1.26.1`.
- Python range: `>=3.9,<3.15`.
- Base dependencies: `numpy>=1.21.0` and `gymnasium>=1.0.0`.
- Base install covers API classes, wrappers, conversion helpers, test utilities, and custom environment authoring support.
- Optional extras are required for most built-in environment families: `[classic]`, `[butterfly]`, `[atari]`, `[sisl]`, `[other]`, `[testing]`, and `[all]`.
- PettingZoo declares no console entry points; use Python imports and bundled scripts instead of expecting a `pettingzoo` CLI.

## Minimal Install Guidance

Base API and custom environment work:

```bash
pip install pettingzoo
python -c "import pettingzoo; print(pettingzoo.__version__)"
```

Install only the family you need:

```bash
pip install 'pettingzoo[classic]'
pip install 'pettingzoo[butterfly]'
pip install 'pettingzoo[atari]'
pip install 'pettingzoo[sisl]'
```

Avoid `pettingzoo[all]` unless you deliberately need broad local coverage across several environment families. It can add compiled and GUI-related dependencies, and it does not install Atari ROMs or training frameworks.

## Safe Workflow Defaults

- Prefer bounded, headless smoke checks before GUI rendering, long training, framework setup, or Atari ROM workflows.
- Use `reset(seed=...)`, step only live agents, sample action masks when present, and call `close()` in `finally` blocks.
- Treat built-in environment tutorials as evidence and recipes, not as default commands to run; many require optional extras, render access, large frameworks, or long training.
- Use PettingZoo compliance helpers for custom environments before adapting them to training frameworks.
- Keep optional-family dependencies separate from framework dependencies; PettingZoo extras do not install CleanRL, Tianshou, SB3, Ray/RLlib, AgileRL, or LangChain.

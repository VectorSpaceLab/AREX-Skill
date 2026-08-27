---
name: environment-families
description: "Choose PettingZoo environment families, install minimal extras,
  and diagnose optional dependency, ROM, and render failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PettingZoo Environment Families

Use this sub-skill when choosing between PettingZoo Classic, Butterfly, Atari, SISL, deprecated Magent, or third-party environments, or when diagnosing missing optional dependencies for those families.

## Routing

- Read [Family Catalog](references/family-catalog.md) to choose an environment family, identify canonical module imports, and understand family-specific quirks such as action masks, render modes, common parameters, and deprecated Magent handling.
- Read [Optional Dependencies](references/optional-dependencies.md) before installing extras; it maps base PettingZoo and each optional group to the capabilities it unlocks and explains why `[all]` is often unnecessary.
- Read [Troubleshooting](references/troubleshooting.md) when imports, constructors, Atari ROM loading, headless rendering, system build packages, or unsupported platforms fail.
- Run [check_env_import.py](scripts/check_env_import.py) for a safe import-only probe, or an explicit constructor/reset probe, of a target module such as `pettingzoo.classic.rps_v2`.

For AEC and Parallel rollout loops after a family is chosen, use `../use-environments/`. For RL framework training recipes, use `../training-integrations/`. For authoring custom environments, use `../custom-environments/`.

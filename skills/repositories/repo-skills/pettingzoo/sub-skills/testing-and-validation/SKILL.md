---
name: testing-and-validation
description: "Run and interpret PettingZoo compliance, seed, render, max-cycles,
  save-observation, and safe native validation checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Testing And Validation

Use this sub-skill when an agent needs to run or interpret PettingZoo validation: `api_test`, `parallel_api_test`, seed checks, render checks, `max_cycles` checks, save-observation checks, CI-safe test selection, or failures from compliance helpers.

## Read Or Run

- Read [compliance tests](references/compliance-tests.md) when choosing a PettingZoo helper, setting bounded cycles, building CI commands, or interpreting pass signals and common assertions.
- Read [native test selection](references/native-test-selection.md) when deciding whether a repo-native test or example is safe, optional-extra gated, GUI/ROM gated, or too heavy for default validation.
- Read [troubleshooting](references/troubleshooting.md) when a validation failure mentions space identity, live-agent keys, revived agents, action masks, seeding, render return types, `max_cycles`, or excessive runtime.
- Run [run_compliance_checks.py](scripts/run_compliance_checks.py) when you need a safe CLI around installed `pettingzoo.test` helpers for a module factory such as `my_pkg.my_env_v0:parallel_env`.

## Route Elsewhere

- For fixing a custom AEC or Parallel environment implementation after a test identifies the broken contract, use [../custom-environments/SKILL.md](../custom-environments/SKILL.md).
- For wrapper ordering, conversion wrappers, `AgentSelector`, `save_observation`, or utility-wrapper behavior, use [../wrappers-and-utilities/SKILL.md](../wrappers-and-utilities/SKILL.md).
- For basic rollout loops, action sampling, reset/step lifecycle, or headless smoke checks that are not compliance tests, use [../use-environments/SKILL.md](../use-environments/SKILL.md).
- For missing optional family dependencies, Atari ROM requirements, or display/rendering prerequisites, use [../environment-families/SKILL.md](../environment-families/SKILL.md).

## Default Stance

Start with bounded, headless API and seed checks. Keep `render`, `human` render mode, `max_cycles`, performance benchmarks, observation-image saving, optional-family tests, ROM-backed environments, and training examples opt-in unless the user explicitly asks for broader validation.

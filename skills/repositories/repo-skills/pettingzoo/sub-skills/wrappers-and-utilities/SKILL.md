---
name: wrappers-and-utilities
description: "Use PettingZoo conversion wrappers, utility wrappers,
  AgentSelector, reward/observation helpers, and wrapper troubleshooting
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Wrappers And Utilities

Use this sub-skill when an agent needs to convert between PettingZoo AEC and Parallel APIs, compose utility wrappers, diagnose wrapper errors, use `AgentSelector`, compute random-policy reward baselines, save image observations, or capture text rendering.

## Read Or Run

- Read [references/wrappers-and-conversions.md](references/wrappers-and-conversions.md) when you need `aec_to_parallel`, `parallel_to_aec`, `turn_based_aec_to_parallel`, wrapper ordering, AEC-vs-Parallel limitations, base wrappers, or multi-episode wrappers.
- Read [references/utilities.md](references/utilities.md) when you need `AgentSelector`, `average_total_reward`, `save_observation`, `CaptureStdoutWrapper`, `capture_stdout`, or `EnvLogger` guidance.
- Read [references/troubleshooting.md](references/troubleshooting.md) when conversion assertions, order-enforcing errors, illegal-action termination, out-of-bounds actions, render/reset problems, or observation-saving failures occur.
- Run [scripts/wrapper_conversion_smoke.py](scripts/wrapper_conversion_smoke.py) when you need a bounded, dependency-light check that `parallel_to_aec` and valid `aec_to_parallel` conversion semantics work in the installed PettingZoo package.

## Route Elsewhere

- For ordinary AEC or Parallel rollout loops, action-mask sampling in policies, rendering choices, and `step(None)` control flow, use [../use-environments/SKILL.md](../use-environments/SKILL.md).
- For implementing new environment internals, `raw_env()` factories, `_was_dead_step`, `_clear_rewards`, or custom `AgentSelector` turn logic, use [../custom-environments/SKILL.md](../custom-environments/SKILL.md).
- For compliance tests such as `api_test`, `parallel_api_test`, seed tests, render tests, or native wrapper test selection, use [../testing-and-validation/SKILL.md](../testing-and-validation/SKILL.md).

## Default Stance

Treat PettingZoo's utility wrappers as mostly AEC-oriented. If a user starts from a Parallel environment, convert to AEC when needed, apply AEC wrappers there, then convert back only when the environment satisfies the parallel-conversion assumptions.
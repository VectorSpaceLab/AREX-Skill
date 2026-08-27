---
name: custom-environments
description: "Create and review PettingZoo AEC and Parallel custom environments,
  including factories, spaces, masks, wrappers, and versioned exports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Custom Environments

Use this sub-skill when implementing or reviewing a new PettingZoo environment: AEC, Parallel, action-masked, versioned module exports, `raw_env()`/`env()` factories, or `AgentSelector` turn logic.

## Start Here

- Read [AEC authoring](references/aec-authoring.md) when the environment steps one agent at a time or needs direct `AECEnv` control.
- Read [Parallel authoring](references/parallel-authoring.md) when all live agents act in the same step or when exposing both `parallel_env()` and an AEC-compatible `env()`.
- Read [Action masking](references/action-masking.md) when observations or infos need valid-action masks or invalid-action policy.
- Read [Troubleshooting](references/troubleshooting.md) when compliance tests fail around space identity, live-agent keys, dead agents, masks, seeding, render metadata, or wrapper ordering.
- Run [custom_env_template.py](scripts/custom_env_template.py) for a bounded, dependency-light template that exposes `parallel_env()`, `raw_env()`, and wrapped `env()` factories.

## Routing

- For compliance commands such as `api_test`, `parallel_api_test`, seed tests, render tests, or CI guidance, use the sibling `testing-and-validation` sub-skill.
- For conversion wrappers, utility wrapper behavior, and wrapper composition details, use the sibling `wrappers-and-utilities` sub-skill.
- For selecting and installing built-in PettingZoo environment families, use the sibling `environment-families` sub-skill.
- For ordinary rollout loops against an existing environment, use the sibling `use-environments` sub-skill.

## Authoring Defaults

- Prefer Parallel authoring when agents truly act simultaneously; expose an AEC interface with `parallel_to_aec` when needed.
- Prefer direct AEC authoring when turns, delayed rewards, dead-agent stepping, or per-agent observations are easier to express one agent at a time.
- Keep `possible_agents`, spaces, and metadata stable after initialization; update `agents` only for the current episode lifecycle.
- Keep bundled examples and validation defaults bounded; large-cycle stress tests belong in explicit validation work, not default templates.

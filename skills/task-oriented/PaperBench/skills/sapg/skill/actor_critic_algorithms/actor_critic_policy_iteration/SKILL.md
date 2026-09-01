---
name: actor_critic_policy_iteration
description: Apply policy-iteration style actor updates and verify objective improvement under compatible gradients.
---

# Actor Critic Policy Iteration

Use this skill when reproducing or checking policy-gradient actor-critic mechanisms from Sutton, McAllester, Singh, and Mansour (1999) without relying on an original implementation repository.

## Inputs
- A finite discounted MDP or a tiny generated proxy task.
- Differentiable stochastic-policy parameters, preferably softmax-linear features.
- Numeric tolerances for gradient, orthogonality, and improvement checks.

## Outputs
- Deterministic JSON-compatible quantities suitable for recovery evidence.
- Explicit failures when assumptions such as differentiability or compatible features are not met.

## Workflow
1. Read the module contract and identify the paper mechanism being tested.
2. Use exact finite-MDP computations for deterministic checks whenever possible.
3. Keep source boundaries strict: use the paper, generated modules, and generated skills, not an original source repository.
4. Save command outputs and numeric metrics as auditable artifacts.
5. Treat reduced/proxy recovery as valid only when it exercises the theorem mechanism.

## Validation
Run `python ../../../../Paper2Skills/Paper2Skills-Agent/src/packages/paper2skills-agent/src/paper2skills/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests` or invoke the local tests with the Distiller validator.

## Limitations
This skill validates the theorem mechanism on finite MDPs. It is not a benchmark implementation for large-scale reinforcement-learning tasks.

# Troubleshooting

## Missing `gym`

**Symptom:** importing RL utilities emits a warning that Gym is missing, or RL
agent construction fails when it needs an environment.

**Recovery:** install the optional RL dependency only when real Gym environment
training is selected. Base bandit workflows do not need Gym.

## Gym API drift

This legacy package was written for older OpenAI Gym APIs. New Gymnasium-style
environments may return `(obs, info)` from `reset` and five values from `step`.
If a task uses modern environments, add an adapter or choose an older compatible
Gym environment before blaming the agent update logic.

## Missing `matplotlib` or `seaborn`

Bandit/RL plotting is optional. Use `plot=False` for safe smoke checks. Install
plotting dependencies only for explicit visualization tasks.

## Continuous versus discrete action errors

Some agents assume discrete action spaces. Inspect the environment stats before
choosing `CrossEntropyAgent`, Monte Carlo, TD, or Dyna variants. For continuous
observations, check whether tile coding is configured and whether the grid size
is reasonable.

## Training runs too long

Use tiny episode/trial counts for validation. Avoid rendering and plotting in
headless sessions. Long RL training is not a required verification step for this
repo skill.

## Unexpected policy outputs

`policy.act(...)` returns `(reward, arm_id)` and mutates policy state. If you
only need an arm without updating estimates, inspect the policy's internal
selection method carefully instead of using `act` as a pure function.

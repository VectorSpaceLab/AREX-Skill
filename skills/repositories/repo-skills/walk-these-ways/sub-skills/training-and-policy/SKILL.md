---
name: training-and-policy
description: "Operate the Walk These Ways PPO and PPO-CSE/RMA policy workflow:
  validate dimensions, understand history and rollout contracts, inspect
  checkpoints, and plan bounded evaluation without claiming simulator
  execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Policy

Use this sub-skill for the policy-learning branch of Walk These Ways: PPO and
PPO-CSE/RMA architecture, history construction, rollout storage, checkpoint
export, pretrained policy inspection, and bounded policy-evaluation planning.

## Operating route

1. Read [api-reference.md](references/api-reference.md) before changing an
   actor, critic, adaptation module, rollout buffer, or history wrapper.
2. Read [training-workflow.md](references/training-workflow.md) before
   considering `scripts/train.py`; it contains the exact configuration override
   checklist, logger-prefix gate, export cadence, resume caveats, and the
   expensive-run boundary.
3. Use [checkpoint-format.md](references/checkpoint-format.md) and run
   [`inspect_checkpoint_layout.py`](scripts/inspect_checkpoint_layout.py) against
   an explicit run directory before loading policy artifacts.
4. Read [policy-evaluation.md](references/policy-evaluation.md) for the
   pretrained playback tensor path, `parameters.pkl` trust boundary, command
   indices, gait vectors, and bounded evaluation procedure.
5. Use [`validate_training_config.py`](scripts/validate_training_config.py) for
   a source-independent dimension/config check before attempting any native
   workflow. It performs no imports from this repository and writes nothing.
6. Consult [troubleshooting.md](references/troubleshooting.md) when a backend,
   shape, checkpoint, logger, memory, or configuration-resume problem occurs.

## Operating contract

- The PPO-CSE/RMA policy used by `scripts/train.py` is dimensioned by
  `num_obs=70`, `num_privileged_obs=2`, `num_obs_history=2100`, and
  `num_actions=12` in the checked-in recipe. The 2100 history values are 30
  frames of 70 scalar observations.
- In PPO-CSE, the adaptation module maps a flattened observation history to a
  2-value latent/privileged representation. The student body receives the
  concatenation of the 2100-value history and the 2-value latent and returns 12
  actions. The critic uses the history and privileged representation during
  training.
- `HistoryWrapper` owns a zero-initialized rolling buffer. It returns a mapping
  with `obs`, `privileged_obs`, and `obs_history`; resets clear the history.
  Keep the wrapper and policy dimensions synchronized.
- Rollout storage is allocated as `[num_transitions_per_env, num_envs, ...]`
  and records observations, privileged observations, history, actions, values,
  log probabilities, Gaussian parameters, rewards, dones, and `env_bins`.
  Returns use GAE with the configured `gamma` and `lam`.
- Training is an Isaac Gym/CUDA workflow, not a CPU-only workflow. Isaac Gym
  Preview 4 is unavailable in the construction environment. Static source
  reading, safe dimension checks, and the CSE tensor-shape smoke are not
  simulator execution, training convergence, or playback verification.
- Full native training and playback are intentionally unverified here. Do not
  start a 100000-iteration run, launch the online logger, or claim a policy
  result from a CPU shape check.
- Do not use source-relative `../runs` discovery as a runtime dependency. Pass
  an explicit run/checkpoint path to safe inspection or adapt a caller-owned
  evaluation harness.

## Routing boundaries

- Environment fields, terrain, domain randomization, observation construction,
  and simulator prerequisites belong to
  [simulation-environment](../simulation-environment/SKILL.md).
- Actuator fitting, deployment-log samples, and actuator-network training
  belong to [actuator-network](../actuator-network/SKILL.md).
- Hardware deployment, LCM, RC commands, calibration, and motor safety belong
  to [robot-deployment](../robot-deployment/SKILL.md).

## Bundled files

- [api-reference.md](references/api-reference.md) — architecture, arguments,
  history, storage, and the verified dimension smoke.
- [training-workflow.md](references/training-workflow.md) — training recipe,
  overrides, memory/logger gates, export cadence, and resume behavior.
- [policy-evaluation.md](references/policy-evaluation.md) — explicit-path
  checkpoint loading, command/gait semantics, and bounded playback planning.
- [checkpoint-format.md](references/checkpoint-format.md) — required artifacts
  and body/adaptation/state-dict tensor contracts.
- [troubleshooting.md](references/troubleshooting.md) — actionable diagnosis
  for backend, shape, artifact, logger, memory, and config divergence errors.
- [validate_training_config.py](scripts/validate_training_config.py) — safe
  JSON/YAML-like and numeric dimension validator; invalid input exits non-zero.
- [inspect_checkpoint_layout.py](scripts/inspect_checkpoint_layout.py) — safe,
  read-only run/checkpoint layout checker with optional TorchScript metadata.

## Verification boundary

Evidence was read from `README.md`, `scripts/train.py`, `scripts/play.py`, the
PPO and PPO-CSE modules, both history wrappers, deployment policy loading, the
checked-in checkpoint filenames, and the integration evidence map. The
PPO-CSE shape smoke `ActorCritic(70, 2, 2100, 12)` was run with the inspected
Python dependencies; it produced latent `(2, 2)` and action `(2, 12)`. That is
a CPU model-shape check only, not
simulator execution. No Isaac Gym Preview 4 package is available. Therefore
this skill explicitly does not verify full training, simulator playback,
logger networking, or hardware deployment.

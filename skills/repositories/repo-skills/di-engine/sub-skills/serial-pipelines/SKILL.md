---
name: serial-pipelines
description: "Routes legacy DI-engine serial, offline, evaluation, and
  data-collection pipelines."
metadata:
  disco-role: operating
  disable-model-invocation: true
license: Apache 2.0
disable-model-invocation: true
---

# Serial pipelines

Use this sub-skill for the legacy pipeline family built around
`ding.entry.serial_pipeline` and its related helpers.
These workflows are still the quickest path for many CartPole, Pendulum, and
reward-model recipes.

## Owns

- `serial_pipeline`, `serial_pipeline_onpolicy`, and `serial_pipeline_offline`
- `eval`, `collect_demo_data`, `collect_episodic_demo_data`,
  `episode_to_transitions`, and `episode_to_transitions_filter`
- special serial modes such as SQIL, GAIL, DQFD, TREX, NGU, and reward-model
  flows
- direct training entry scripts that manually wire configs, env managers,
  policies, collectors, learners, and evaluators
- environment-specific demo scripts under `dizoo/classic_control/`, `bitflip/`,
  `frozen_lake/`, and `league_demo/` when they are using the legacy loop style

## Does not own

- Framework/middleware examples such as `ding/example/*.py`; those belong to
  `framework-runtime`
- CLI parsing and config compilation details; those belong to `cli-config`
- Env-wrapper debugging and shape mismatches; those belong to `env-integration`

## Read this first when the user asks

- how to train or evaluate with a legacy DI-engine config file
- how to collect expert demonstrations or convert episodic data to transitions
- how the special SQIL/GAIL/DQFD/TREX/NGU launch paths differ from plain
  off-policy or on-policy training
- how to turn a CartPole or Pendulum config into a runnable single-process loop
- why a serial entry script hangs, exits early, or never reaches the stop value

## Workflow

1. Use `references/workflows.md` to match the request to the right pipeline
   family.
2. Use `references/troubleshooting.md` when the user hits a runtime failure or
   an expert-data/checkpoint mismatch.
3. Use `scripts/run_serial.sh` from the repo root when you simply want a thin
   wrapper over `ding -m serial`.
4. If the request actually wants the task/middleware runtime, move to
   `framework-runtime` instead of expanding this one.

## Common decision points

- Use `serial_pipeline` for the standard off-policy training loop.
- Use `serial_pipeline_onpolicy` for PPO/A2C/PG-style recipes.
- Use `serial_pipeline_offline` when the policy learns only from offline data.
- Use `eval` when the user already has a checkpoint and only needs performance
  or replay output.
- Use the collect-demo helpers when imitation-learning or offline-RL data must
  be written out before training.

## Helpful bundle links

- `references/workflows.md` for the pipeline family map and example entry
  scripts.
- `references/troubleshooting.md` for checkpoint, expert-data, and stop-value
  failures.
- `scripts/run_serial.sh` at the repo root for a generic launch wrapper.

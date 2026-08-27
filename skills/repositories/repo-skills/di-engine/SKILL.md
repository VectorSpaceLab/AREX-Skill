---
name: di-engine
description: "Routes DI-engine users to the right workflow for CLI/config
  launches, serial and framework-based RL pipelines, and environment
  integration."
metadata:
  disco-role: operating
  disable-model-invocation: true
license: Apache 2.0
disable-model-invocation: true
---

# DI-engine

Use this skill for the public DI-engine reinforcement-learning engine.
It routes common user requests to focused sub-skills instead of forcing future
agents to rediscover the repo structure from scratch.

## Quick check

If you only need to verify that the package is installed, start with:

```bash
python -m pip check
python -c "import ding, dizoo; print(ding.__version__)"
```

For a faster bundled smoke check, run `scripts/check_install.py` from an
environment where DI-engine is installed.

## Main routes

### `cli-config`
Read this when the user asks about:
- `ding` or `ditask` CLI usage
- config files, `main_config`, `create_config`, or `system_config`
- `compile_config`, `read_config`, `save_config`, or registry queries
- launch flags for `serial`, `parallel`, `dist`, `eval`, or `ditask`
- the repo-provided shell wrappers for serial/parallel launches

### `serial-pipelines`
Read this when the user asks about:
- `ding.entry.serial_pipeline`, `serial_pipeline_onpolicy`, or `serial_pipeline_offline`
- `eval`, `collect_demo_data`, `collect_episodic_demo_data`, or episodic post-processing
- legacy `ding/entry/*` launchers and environment-specific entry scripts under
  `dizoo/`
- special modes such as SQIL, GAIL, DQFD, TREX, NGU, reward-model, or offline RL

### `framework-runtime`
Read this when the user asks about:
- `ding.framework.task`, `Parallel`, `Supervisor`, or `EventLoop`
- middleware-based recipes using `StepCollector`, `OffPolicyLearner`,
  `multistep_trainer`, `interaction_evaluator`, `CkptSaver`, or `data_pusher`
- the modern example scripts in `ding/example/`
- multi-process message routing, `task.wait_for`, `task.emit`, or auto-recovery

### `env-integration`
Read this when the user asks about:
- `DingEnvWrapper`, `BaseEnvManager`, `BaseEnvManagerV2`, or `EnvSupervisor`
- env wrapper selection, reset/step shape mismatches, or new environment onboarding
- DIZoo environment patterns in `dizoo/classic_control/`, `bitflip/`,
  `frozen_lake/`, or `league_demo/`
- custom environment adapters and the env-specific config/template pattern

## Useful bundled helpers

- `scripts/check_install.py` — quick import/version/config smoke for a prepared environment.
- `scripts/run_serial.sh` — thin wrapper for `ding -m serial` with a config path and seed.
- `scripts/run_parallel.sh` — thin wrapper for `ding -m parallel` with a config path and seed.

## Read first

- `references/package-surface.md` for the repo module map and public entry points.
- `references/troubleshooting.md` for cross-cutting install/import/runtime failures.

## Notes

- This skill covers the core DI-engine workflows that can be exercised from the
  installed package and bundled helpers without reopening the source checkout.
- Advanced external environment families that need separate optional packages
  are intentionally left out of the default routes.
- If a request mentions a specific example, config, or entry script, route to the
  sub-skill that owns that workflow rather than reading the source tree directly.

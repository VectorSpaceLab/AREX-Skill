---
name: config-hyperparams
description: "Read, write, and statically validate RL Zoo hyperparameter configs
  and CLI override grammar."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# config-hyperparams

Use this sub-skill when the task is about RL Zoo hyperparameter configuration, not about running a training job. It is the routing point for reading, editing, linting, or explaining YAML/Python config files and StoreDict-style CLI override strings.

## Use this for

- Inspecting or editing algorithm hyperparameter config files such as `a2c.yml`, `ppo.yml`, `sac.yml`, `td3.yml`, `tqc.yml`, `trpo.yml`, or a custom YAML file.
- Checking `default`, `atari`, and environment-specific entries before a training command uses `--conf-file`.
- Translating between YAML config files and Python config files/modules that expose a top-level `hyperparams` dictionary.
- Validating `normalize`, schedules, `policy_kwargs`, `env_kwargs`, `monitor_kwargs`, `env_wrapper`, `vec_env_wrapper`, `callback`, `frame_stack`, and `n_timesteps` shapes.
- Explaining `--hyperparams`, `--env-kwargs`, and `--eval-env-kwargs` `key:value` override grammar and its eval trust boundary.

## Do not use this for

- Launching, resuming, or benchmarking actual training/evaluation runs; hand off to the training-cli or evaluation-and-artifacts sub-skill.
- Designing Optuna search spaces or interpreting study artifacts; hand off to the tuning-optimization sub-skill.
- Implementing or debugging wrapper/callback class internals; hand off to the custom-components sub-skill.

## Runtime references

- [Configuration semantics](references/configuration.md) covers loader precedence, special keys, schedules, normalization, wrapper/callback shapes, and StoreDict override parsing.
- [Hyperparameter files](references/hyperparameter-files.md) covers algorithm file families, reusable YAML/Python patterns, and concrete examples.
- [Troubleshooting](references/troubleshooting.md) covers missing fallback entries, indentation and quoting issues, eval trust boundaries, env-id/package mismatches, and normalization/vector-wrapper interactions.
- [Static validator](scripts/validate_hyperparams_config.py) checks config shape without training, network access, or mutation. Python configs are statically inspected by default; execute/import them only with `--import-python` when the caller explicitly accepts that trust boundary.

## Suggested workflow

1. Identify whether the input is YAML, a Python file, or an importable Python module containing `hyperparams`.
2. Resolve the target `--env` and whether the runtime should choose an exact entry, `atari`, or `default` fallback.
3. Use the configuration and hyperparameter-file references to edit or explain values.
4. Run the bundled validator before composing a training command, especially after changing wrapper/callback lists or `policy_kwargs` strings.
5. If validation requires actual environment registration, class importability, or a real run, route to the appropriate sibling sub-skill instead of training from here.

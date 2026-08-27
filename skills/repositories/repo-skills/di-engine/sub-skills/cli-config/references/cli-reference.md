# CLI reference

This page summarizes the public CLI surface that DI-engine users actually touch.

## `ding`

`ding` is the main launcher for legacy pipelines and direct runtime actions.

### Common modes

| Mode | Use | Notes |
| --- | --- | --- |
| `serial` | single-process off-policy training | most classic CartPole/Pendulum training configs |
| `serial_onpolicy` | single-process on-policy training | PPO/A2C/PG-style recipes |
| `serial_offline` | offline training | offline-RL configs and dataset-backed flows |
| `serial_sqil`, `serial_gail`, `serial_dqfd`, `serial_trex`, `serial_ngu` | special legacy modes | the mode usually implies extra data or a special reward path |
| `parallel` | multi-process local launch | used with `Parallel`-style worker routing |
| `dist` | distributed coordinator/collector/learner launch | use only when the config carries a distributed system block |
| `eval` | evaluation only | loads a checkpoint and runs the evaluator |
| `serial_reward_model` | reward-model workflows | used by imitation or reward-learning recipes |

### Common flags

- `-c/--config`: experiment config path.
- `-s/--seed`: one or more seeds.
- `-e/--env` and `-p/--policy`: predefined CartPole/Pendulum lookup.
- `--load-path`: checkpoint path for evaluation or resume-style runs.
- `--replay-path`: replay/video output directory.
- `-P/--platform`: `local`, `slurm`, or `k8s` for distributed launch helpers.
- `-M/--module`: distributed submodule such as `config`, `coordinator`,
  `collector`, or `learner`.
- `--add`, `--delete`, `--restart`: cluster maintenance helpers for the
  distributed controller surface.
- `--query-registry`: print registry details for a named module family.

## `ditask`

`ditask` is the multi-process task router used by the framework-based recipes.

### Common flags

- `--package`: package root containing the task entry module.
- `--main`: dotted path to the callable entry function.
- `--parallel-workers`: number of workers.
- `--topology`: `alone`, `mesh`, or `star`.
- `--protocol`: `tcp` or `ipc`.
- `--ports`, `--attach-to`, `--address`, `--labels`, `--node-ids`: routing and
  placement controls.
- `--platform` and `--platform-spec`: cluster-aware placement and task mapping.
- `--mq-type`: message queue backend, usually `nng` or `redis`.

## Practical rules

- Use `ding --version` or `ding --help` when you only need to verify that the
  CLI is installed correctly.
- Use `ditask --help` when you need the argument surface without launching a
  workflow.
- Prefer `serial` for the simplest reproducible example and `parallel` only when
  the recipe explicitly uses multi-process routing.
- Keep distributed launch flags minimal until the config is already known to be
  valid.

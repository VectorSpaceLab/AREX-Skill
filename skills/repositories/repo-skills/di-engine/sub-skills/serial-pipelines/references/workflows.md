# Serial pipeline workflows

This page maps the legacy DI-engine pipeline helpers to the way they are used
in the repo's direct training and demo scripts.

## Core pipeline functions

| Function | Typical use | Main dependencies |
| --- | --- | --- |
| `serial_pipeline` | standard off-policy training loop | `BaseEnvManager`, `create_policy`, `create_buffer`, `create_serial_collector`, `create_serial_evaluator` |
| `serial_pipeline_onpolicy` | on-policy loop for PPO/A2C/PG-style recipes | `StepCollector`, `gae_estimator`, `multistep_trainer` or the on-policy learner path |
| `serial_pipeline_offline` | offline RL training | offline data loader/fetcher, evaluator, and learner only |
| `eval` | checkpoint-only evaluation | evaluator env, policy eval mode, checkpoint load |
| `collect_demo_data` | transition-level expert collection | collector env, collect mode, optional state dict |
| `collect_episodic_demo_data` | episodic expert collection | `EpisodeSerialCollector`, collect mode, optional state dict |
| `episode_to_transitions` | convert episodic demos to transitions | offline pickle input |
| `episode_to_transitions_filter` | filter and convert episodic demos | offline pickle input plus return threshold |

## Special serial modes

- `serial_sqil`: asks for an expert config and then runs the SQIL variant.
- `serial_gail`: asks for an expert config and then runs a GAIL-style loop.
- `serial_dqfd`: validates the DQFD expert config naming convention before it
  starts training.
- `serial_trex` / `serial_trex_onpolicy`: TREX variants for off-policy and
  on-policy loops.
- `serial_ngu`: NGU-style serial training.
- `serial_reward_model`: reward-model training and evaluation support.

## Representative entry-script patterns

The distilled legacy-loop pattern was derived from representative CartPole,
Pendulum, and league-demo entry scripts. Do not depend on those source paths at
runtime; use the pattern below instead.

## Flow shape

A normal legacy pipeline script usually:

1. imports a config pair from `dizoo/<family>/config`
2. compiles the config with `compile_config`
3. creates collector and evaluator env managers
4. seeds the runtime
5. builds a policy/model pair
6. wires learner/collector/evaluator/buffer objects
7. loops until `stop_value`, `max_train_iter`, or `max_env_step`

## Read when you need to know

- which helper to use for off-policy vs on-policy vs offline training
- how to adapt a demo script into a reusable recipe
- how the expert-data and checkpoint paths are expected to flow through the
  pipeline
- where the manual training loop differs from the framework-based examples

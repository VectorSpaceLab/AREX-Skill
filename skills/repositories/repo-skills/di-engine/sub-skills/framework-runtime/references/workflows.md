# Framework runtime workflows

This page shows how the modern framework examples are grouped and what they are
trying to demonstrate.

## Example families

| Example family | Typical purpose | Notable middleware |
| --- | --- | --- |
| `ding/example/dqn.py` and similar off-policy recipes | classic single-agent training with task-based middleware | `OffPolicyLearner`, `StepCollector`, `interaction_evaluator`, `data_pusher`, `eps_greedy_handler`, `CkptSaver` |
| `ding/example/ppo.py`, `ppo_lunarlander.py`, `mappo.py`, and similar | on-policy or multi-agent task-based training | `multistep_trainer`, `StepCollector`, `gae_estimator`, `interaction_evaluator`, `CkptSaver` |
| `ding/example/cql.py`, `bcq.py`, `edac.py`, `dqn_eval.py`, and similar | offline or evaluation-oriented flows | `trainer`, `offline_data_fetcher`, `offline_logger`, `interaction_evaluator` |
| `ding/example/collect_demo_data.py` | collect offline or episodic data with the task runtime | `StepCollector`, `offline_data_saver` |
| `ding/example/dqn_her.py`, `sqil.py`, `trex.py`, `qgpo.py` | special reward or imitation-learning workflows | `HERLearner`, `EpisodeCollector`, `termination_checker`, `wandb_offline_logger`, custom data processors |

## Runtime shape

A modern example usually:

1. compiles a config pair
2. creates task contexts and env managers
3. seeds the runtime
4. builds a model and policy
5. attaches middleware in a deliberate order
6. runs the task until the middleware stack decides to stop

## When to prefer this runtime

- The user wants composable middleware rather than a monolithic pipeline.
- The recipe needs event emission, wrappers, or task-level branching.
- The script is already written as a `main()` function under `ding/example/`.
- The task must be extended with custom collectors, evaluators, or loggers.

## When to switch away

- The user only needs a simple legacy config launch; use `serial-pipelines`.
- The failure is really about env shape or wrapper selection; use
  `env-integration`.
- The problem is CLI parsing or config loading before the runtime starts; use
  `cli-config`.

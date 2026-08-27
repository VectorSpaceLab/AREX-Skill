---
name: runner-and-cli-workflows
description: "Use Tensorforce Runner training/evaluation workflows,
  CLI-equivalent semantics, logging, parallel execution, and optional BOHB
  tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runner and CLI Workflows

Use this sub-skill when the task is to run bounded Tensorforce training or evaluation through `tensorforce.Runner`, translate the historical runner CLI flags into public API calls, configure local/remote parallel execution, collect callback/logging metrics, or reason about optional BOHB hyperparameter tuning.

## Route map

- Start with `references/runner-workflows.md` for the public `Runner` constructor/run signatures, safe train/evaluate recipes, callbacks, stopping criteria, and parallel modes.
- Use `references/cli-reference.md` when a user provides command-line style flags such as `--agent`, `--environment`, `--episodes`, `--num-parallel`, `--remote`, `--path`, or `--save-best-agent`; translate them to a self-contained Python wrapper instead of relying on a repository script.
- Use `references/tuning.md` only for optional BOHB/Hyperband tuning. Treat tuning dependencies and long optimization runs as optional, not part of the minimum Tensorforce runtime.
- Use `references/troubleshooting.md` for non-terminating runs, evaluation placement errors, parallel/socket mistakes, missing `max_episode_timesteps`, logging extras, or dependency-version issues surfaced while running workflows.
- Run `scripts/quickstart_cartpole_smoke.py --help` for a compact CartPole quickstart smoke, or `scripts/tensorforce_runner_smoke.py --help` for a CLI-like Runner smoke. Both scripts use the installed Tensorforce package and do not call any repository-level CLI script.

## Boundaries

- For agent aliases, state/action specifications, action masking, manual `act`/`observe`, `experience`, or `update` loops, use `agents-and-specifications`.
- For network, objective, optimizer, memory, policy, preprocessing, and JSON/dict module configuration details, use `modules-and-configuration`.
- For custom `Environment` subclasses, Gym/adapter setup, reward shaping, vectorized/multi-actor environment contracts, or simulator backends, use `environments-and-interaction`.
- For checkpoints, TensorBoard summaries, recorder/pretraining, `Agent.save`, `Agent.load`, exported SavedModels, or best-agent persistence details, use `persistence-export-and-recording` after this sub-skill has established the runner workflow.

## Minimum safe pattern

```python
from tensorforce import Runner

runner = Runner(
    agent='random',
    environment=dict(environment='custom_cartpole'),
    max_episode_timesteps=10
)
try:
    runner.run(num_episodes=3, use_tqdm=False)
    print(runner.episode_returns)
finally:
    runner.close()
```

Always pass at least one bounded stopping criterion (`num_episodes`, `num_timesteps`, or `num_updates`). Prefer `use_tqdm=False` for automation and CI logs.

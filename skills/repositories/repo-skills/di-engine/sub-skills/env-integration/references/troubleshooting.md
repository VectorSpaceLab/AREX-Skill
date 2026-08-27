# Environment troubleshooting

## Observation or action shape mismatch

- Check the env wrapper first.
- Verify that the wrapped env's observation space, action space, and reward
  shape match the policy/model expected by the recipe.
- Compare the collector and evaluator env configs if one side works and the
  other fails.

## Old Gym vs Gymnasium API confusion

- `DingEnvWrapper` supports both, but the env family must be consistent with the
  wrapper and config.
- If you see step/reset deprecation messages, treat them as compatibility
  warnings unless the actual runtime contract fails.

## Manager hangs, blocks, or times out

- Reduce the manager complexity first: use the simplest local manager that fits
  the request.
- Check `shared_memory`, `reset_timeout`, `step_timeout`, and `max_retry`.
- Use the bundled smoke script before trying a long training loop.

## Child restart or error recovery issues

- `EnvSupervisor` and subprocess-backed managers have explicit retry behavior.
- Confirm whether the workflow expects `reset`-style retries or a full renew.
- If a child process cannot restart, the problem is often in the env function or
  in a non-picklable callback passed to the manager.

## Missing optional env packages

- External env families such as Mujoco, PettingZoo, Atari, D4RL, SMAC, and
  similar are intentionally outside the default CPU-friendly scope for this
  skill.
- Use the representative included env families first; only add an external
  package when the user explicitly asks for that env family.

## When the failure is elsewhere

- If the env wrapper is fine but the policy still fails, route to
  `serial-pipelines` or `framework-runtime`.
- If the failure happens before the env is even created, route to `cli-config`.

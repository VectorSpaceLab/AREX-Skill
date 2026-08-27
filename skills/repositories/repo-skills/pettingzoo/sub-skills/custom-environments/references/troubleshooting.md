# Troubleshooting Custom Environments

Use this guide when a custom PettingZoo environment fails compliance tests, random rollouts, conversion, or downstream training integration.

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `observation_space(agent)` or `action_space(agent)` identity failures | The method constructs a new space object on every call | Add `@functools.lru_cache(maxsize=None)` for static spaces, or create stable dict-backed spaces in `__init__` and return those objects. |
| Warnings about deprecated `observation_spaces` or `action_spaces` | The environment relies on legacy attributes instead of methods | Implement `observation_space(agent)` and `action_space(agent)` explicitly. |
| `reset()` succeeds but `step()` raises missing-key errors | Reset did not initialize all required state dictionaries or internal variables | Initialize `agents`, rewards, terminations, truncations, infos, observations/state, counters, and selectors inside every reset. |
| Parallel compliance complains about returned dictionary keys | `self.agents` changed before building final return dictionaries, or live agents were omitted | Build observations, rewards, terminations, truncations, and infos for the transition first; then update `self.agents`. |
| AEC loop crashes after an agent terminates | The dead-agent branch is missing or accepts a non-`None` action | At the top of `step()`, call `_was_dead_step(action)` for selected terminated/truncated agents and return immediately. |
| Rewards appear twice or not at all in AEC | `_cumulative_rewards` is not reset for the acting agent, rewards are not cleared mid-cycle, or `_accumulate_rewards()` is called too early | Reset `_cumulative_rewards[agent] = 0` for the acting agent, use `_clear_rewards()` until the cycle outcome is known, then call `_accumulate_rewards()` after assigning rewards. |
| `AgentSelector` skips or repeats agents unexpectedly | Selector order differs from `self.agents`, or dead agents are removed without reinitializing when needed | Keep selector order aligned with live turn order and reinitialize when the turn order genuinely changes. |
| Space says `MultiDiscrete` but observations fail containment | Observation values, dtype, shape, or bounds do not match the declared space | Check emitted observations with `env.observation_space(agent).contains(obs)` during development. |
| Action mask has wrong shape | The mask length does not equal `Discrete(n).n` | Build masks from the action space size and assert `mask.shape == (env.action_space(agent).n,)`. |
| Action mask is all zeros for a live agent | Environment logic removed every valid action but did not terminate/truncate the agent | Add a no-op/stay action, relax mask rules, or mark the agent done before asking for another action. |
| Random rollout ignores masks | The loop samples from `action_space(agent)` without reading observation or info masks | Read `observation["action_mask"]` or `info["action_mask"]` and sample from nonzero indices. |
| `render()` warnings or render test failures | `metadata["render_modes"]` does not match `render_mode`, or `render()` returns the wrong type | Declare supported render modes and return strings for `ansi`, arrays for `rgb_array`, and display/print for `human`. |
| `render_mode="ansi"` does not capture text from an AEC `env()` | `CaptureStdoutWrapper` was not applied or raw render was not configured to print | For AEC `env()`, construct the raw env with human-style rendering and wrap it with `CaptureStdoutWrapper` when users request `ansi`. |
| Seed tests are nondeterministic | Reset uses Python/global NumPy random state or action spaces are seeded inconsistently | Initialize the Gymnasium RNG in `reset(seed=...)` and draw all stochastic environment state from that RNG. |
| Parallel-to-AEC conversion behaves incorrectly | The Parallel environment changes state for one agent before seeing every live agent's action, or metadata overstates parallelizability | Use direct AEC authoring for sequential-turn games, or ensure Parallel state updates occur only after the full action dictionary is received. |
| Wrapper stack raises order-enforcing errors | Wrappers are applied around the wrong API type or in the wrong order | Apply AEC utility wrappers around `raw_env()` after conversion; do not wrap a `ParallelEnv` directly with AEC-only wrappers. |
| `AssertOutOfBoundsWrapper` passes but illegal masked moves still occur | The action is inside `Discrete(n)` but invalid for the current state | Add mask-aware sampling, an invalid-action policy, or a mask-aware strict wrapper strategy. |

## Fast Isolation Steps

1. Run the bounded template script in both `parallel` and `aec` modes to confirm the local PettingZoo API behaves as expected.
2. Print the keys of all five Parallel return dictionaries before and after terminal transitions.
3. For AEC, print `agent_selection`, `terminations[agent]`, `truncations[agent]`, and the chosen action before each `step()`.
4. Check `space.contains(value)` for every emitted observation and action during a short rollout.
5. Lower compliance cycles during debugging, then increase cycles only after the structural failure is fixed.

# AEC Authoring

AEC environments step exactly one selected agent at a time. Use direct `AECEnv` authoring when turns matter, rewards are assigned after a cycle of individual actions, or dead-agent handling must be explicit.

## Public Factories

Expose two factories from the versioned environment module:

- `raw_env(...)`: returns the bare `AECEnv` implementation for tests and advanced users.
- `env(...)`: constructs `raw_env(...)` and applies user-facing wrappers. A common stack is `CaptureStdoutWrapper` for `render_mode="ansi"`, then `AssertOutOfBoundsWrapper`, then `OrderEnforcingWrapper`.

Keep the versioned module name stable, such as `my_game_v0.py`, and keep the environment metadata name aligned with that version, such as `{"name": "my_game_v0"}`. Put package exports in a small module that imports the versioned factories rather than duplicating environment logic.

## Required State

A direct AEC implementation should initialize stable attributes in `__init__`:

- `possible_agents`: every agent that may appear in any episode.
- `agent_name_mapping`: optional but useful for stable integer ids.
- `render_mode`: the requested render mode.
- Space definitions or cached `observation_space(agent)` and `action_space(agent)` methods.
- Metadata with at least `name`; include `render_modes` when `render()` supports them.

`reset(seed=None, options=None)` must rebuild the complete episode state:

- `agents`: live agents for the new episode.
- `rewards`, `_cumulative_rewards`, `terminations`, `truncations`, and `infos`: dictionaries keyed by all live agents.
- `agent_selection`: the first agent to act.
- Any observation, board, score, timer, or RNG state used by `observe()`, `step()`, `render()`, or `state()`.

If the environment uses randomness, initialize the PettingZoo/Gymnasium RNG in `reset(seed=...)` and use that RNG for stochastic state, not the process-global random state.

## AgentSelector Pattern

`AgentSelector(agent_order)` cycles through a live agent order and reports whether the current agent is first or last in the cycle.

Typical reset logic:

```python
self._agent_selector = AgentSelector(self.agents)
self.agent_selection = self._agent_selector.next()
```

Typical step logic:

1. If `terminations[self.agent_selection]` or `truncations[self.agent_selection]` is true, call `_was_dead_step(action)` and return. The only valid action for a dead agent is `None`.
2. Store `agent = self.agent_selection` and set `_cumulative_rewards[agent] = 0` because `last()` has just exposed the previous cumulative reward.
3. Apply the current action to internal state.
4. If `self._agent_selector.is_last()` is true, compute rewards and terminal/truncation flags for every live agent and update observations for the next cycle.
5. If the cycle is not complete, call `_clear_rewards()` so intermediate agents do not receive premature rewards.
6. Advance `self.agent_selection = self._agent_selector.next()`.
7. Call `_accumulate_rewards()` after setting `self.rewards`.
8. Render only when `render_mode` asks for it.

## Observations And Rewards

- `observe(agent)` must be safe to call any time after `reset()`, even if the observation is not the newest possible value during the middle of a turn cycle.
- `last(observe=True)` calls `observe(agent_selection)` and returns `(observation, cumulative_reward, termination, truncation, info)` for the selected agent.
- `rewards` holds the immediate reward assigned by the last `step()` update; `_cumulative_rewards` is what AEC users see through `last()`.
- Use `_clear_rewards()` while waiting for a multi-agent cycle to complete, then assign all rewards together when the cycle outcome is known.

## Dead-Step Handling

For AEC environments, a terminated or truncated agent remains in `agents` until it receives one final dead step. When the selected agent is dead:

- Accept only `None` as the action.
- Call `_was_dead_step(action)` immediately.
- Do not update game logic, rewards, or observations in that branch.

This pattern keeps `agent_iter()` loops compatible with the expected `None` action for dead agents and prevents skipped cleanup of `terminations`, `truncations`, rewards, cumulative rewards, and infos.

## Spaces And Metadata

- `observation_space(agent)` and `action_space(agent)` must return the same object or equal stable space for the same agent name across calls.
- Use `@functools.lru_cache(maxsize=None)` for static spaces, or return prebuilt spaces from dictionaries created in `__init__`.
- Remove caching only when spaces genuinely change; changing spaces is unusual and makes validation harder.
- Include `metadata["render_modes"]` for every supported render mode and make `render()` return the correct type for non-human modes.

## Review Checklist

- `raw_env()` returns the unwrapped implementation; `env()` applies user-facing wrappers.
- `reset()` initializes every required dictionary and internal variable used later.
- `observe()` works immediately after reset and for every live agent.
- `step()` has a dead-agent branch before normal action handling.
- Rewards are cleared or accumulated at the right point in the turn cycle.
- Termination and truncation dictionaries are updated for all affected live agents.
- Spaces are stable and match the structure and dtype of emitted observations/actions.
- Randomness is controlled by `reset(seed=...)`.

# Troubleshooting Validation Failures

Use the failure text from PettingZoo helpers as the primary clue. Most failures point to a specific API contract rather than a random rollout bug.

## Space Identity

**Failure signals**: `observation_space should return the exact same space object`, `action_space should return the exact same space object`.

**Cause**: `observation_space(agent)` or `action_space(agent)` constructs a new Gymnasium space each call. PettingZoo expects the same object identity so space seeding and downstream wrappers stay stable.

**Fix direction**: store spaces in dictionaries keyed by agent or decorate deterministic space methods with `functools.lru_cache(maxsize=None)`. Keep spaces stable after initialization.

## Live-Agent Dict Keys

**Failure signals**: warnings about live agents not given observation/reward/terminated/truncated/info, dead agents receiving values, or assertions comparing `env.agents` with a live-agent set.

**Cause**: Parallel `step(actions)` returned dictionaries whose keys do not match the currently live agents after termination/truncation, or `env.agents` was updated at the wrong time.

**Fix direction**: after each Parallel step, remove terminated/truncated agents from `env.agents`; return observation/reward/termination/truncation/info dictionaries for the live set expected by the API; include all live agents on reset.

## Dead-Agent Revival

**Failure signals**: `agent cannot be revived once dead`, `agents cannot resurect`, or finished agents appearing again in `agent_iter()`.

**Cause**: an agent name was reused after that agent terminated or truncated in the same episode.

**Fix direction**: do not re-add a finished agent to `env.agents`. If the game needs generated agents, use new unique names and keep `possible_agents` broad enough to include every possible name.

## Rewards, Terminations, Truncations, Infos

**Failure signals**: `rewards, terminations, truncations, infos and agents must have the same length`, `terminations must all be False after reset`, or `terminated from last() and terminations[agent] do not match`.

**Cause**: AEC bookkeeping dictionaries are not synchronized with `env.agents`, reset leaves terminal flags behind, or `last()` reports values inconsistent with internal dictionaries.

**Fix direction**: initialize all dictionaries on reset for current agents, clear cumulative rewards at the right turn boundary, and delete dead-agent entries only when the API expects them removed.

## Action Masks

**Failure signals**: `Incorrect action mask`, warnings about mask dtype/shape/all-zero values, invalid sampled actions despite a mask, or seed tests failing only after masked actions.

**Cause**: masks differ across seeded runs, are not one-dimensional boolean-like arrays, have all actions illegal, or are exposed inconsistently between observation and info.

**Fix direction**: expose masks either in the observation dict under `action_mask` or in `info["action_mask"]`; keep mask length equal to the discrete action count; use only `0/1` or boolean values; make mask generation deterministic under `reset(seed=...)`.

## Seed Mismatch

**Failure signals**: `Incorrect observation`, `Incorrect reward`, `Incorrect termination`, `Incorrect truncation`, `Incorrect info`, `Incorrect actions`, or `Incorrect action seeding`.

**Cause**: environment randomness does not use the seeded RNG, action or observation spaces are recreated, dictionary ordering changes nondeterministically, or external state leaks between resets.

**Fix direction**: use Gymnasium seeding in `reset(seed=...)`, seed spaces deterministically, avoid global random state unless it is explicitly seeded, and make reset fully reconstruct episode state.

## Render Return Types

**Failure signals**: missing `render_modes`, `rgb_array mode must return a valid image array`, `ansi` result is not a string, or `human` result is not `None`.

**Cause**: metadata does not list supported render modes or `render()` returns the wrong type for the active mode.

**Fix direction**: set `metadata["render_modes"]`; return `None` for `human`, `str` for `ansi`, and `numpy.ndarray` with shape `(height, width, 3)` and dtype `uint8` for `rgb_array`; implement `close()` whenever `render()` is overridden.

## Max-Cycles Off By One

**Failure signals**: `max_cycles_test` asserts that the Parallel step count or AEC per-agent counts differ from `max_cycles`.

**Cause**: cycle counters increment per agent instead of per full cycle, truncate one step too early or late, or AEC and Parallel factories apply different `max_cycles` semantics.

**Fix direction**: accept `max_cycles` in both `env()` and `parallel_env()` when the module advertises the option; increment cycle counters once per simultaneous Parallel step or once per full AEC agent cycle; set truncations consistently for all live agents at the limit.

## Runtime Too Large

**Failure signals**: validation hangs, CI times out, or performance benchmarks dominate the job.

**Cause**: default helper cycles are large for development, the environment has many agents, or a long-running tutorial/training path entered the validation matrix.

**Fix direction**: lower `--cycles` to `25` or `50` while fixing compliance; exclude performance benchmarks and training examples from default CI; run optional family, ROM, GUI, or large-cycle stress tests only as explicit jobs.

## Save-Observation Checks

**Failure signals**: `Observations must be Box`, `Observations must be 0 to 255`, `Observations must be 2D or 3D`, or unsupported channel count.

**Cause**: observations are not image-like arrays suitable for saving.

**Fix direction**: reserve save-observation tests for visual/image observations. Use Box observations with low `0`, high `255`, 2D grayscale or 3D one-/three-channel shape, and inspect outputs manually rather than treating the file write as a full semantic pass.

## Wrong API Flavor

**Failure signals**: `Env must be an instance of pettingzoo.AECEnv`, Parallel helper failures on AEC envs, or AEC helper failures on Parallel envs.

**Cause**: the selected factory does not match `--api` or the direct helper call.

**Fix direction**: use `env()` for AEC checks, `parallel_env()` for Parallel checks, or the appropriate conversion wrapper before validation when the environment is intentionally exposed through both APIs.

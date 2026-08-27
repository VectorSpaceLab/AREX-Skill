# Troubleshooting manager/config errors

Start with the smallest non-running inspection: load the task config with the
bundled `scripts/inspect_env_config.py` helper and confirm manager keys before
constructing the environment. Then match the failure to the sections below.

## Missing or mismatched term names

| Symptom | Likely cause | Fix |
|---|---|---|
| `Term '<name>' not found in active terms` from reward, termination, curriculum, metrics, event, or recorder lookup. | Code, curriculum stages, or debugging logic references a key that is not in the corresponding manager dictionary, or that key was skipped because its config was `None`. | Inspect the manager keys. Rename the reference or add the term under that exact key. Keep names stable because they appear in logs and cross-manager params. |
| `Group '<name>' not found in active groups` or observation group absent. | Observation group has an empty `terms` dict, all terms are `None`, or the group key differs from what training/actor code expects. | Add at least one active `ObservationTermCfg`; use `"actor"` for policy observations and `"critic"` for value observations when the runner expects those groups. |
| `KeyError` or `None` when reading a command by name. | Observation term such as `generated_commands` references `command_name` that is absent from `cfg.commands`, or commands are disabled and the null command manager is active. | Add the command term under the referenced name or change the observation params. |
| Curriculum cannot update a reward or termination term. | `reward_name` or `termination_name` in curriculum params does not match the manager dictionary key. | Align the curriculum stage target names with `cfg.rewards` or `cfg.terminations`. |

## Tensor shape mismatch

Scalar managers require one value per environment. Common bad shapes are
`[num_envs, 1]`, `[1, num_envs]`, or a scalar without batch dimension.

| Failure | Expected | Fix |
|---|---|---|
| `RewardManager term '<name>' returned shape ..., expected (N,)`. | Reward term returns `torch.Tensor` shape `[num_envs]`. | Use `.squeeze(-1)` only when the trailing dimension is known to be 1, or reduce over feature dimensions with `sum(..., dim=-1)`. |
| `TerminationManager term '<name>' returned shape ..., expected (N,)`. | Boolean tensor `[num_envs]`. | Ensure comparisons/reductions produce one boolean per environment. |
| `MetricsManager term '<name>' returned shape ..., expected (N,)`. | Metric tensor `[num_envs]`, including `per_substep=True` metrics. | Reduce features before returning; choose `reduce="mean"`, `"last"`, `"max"`, or `"sum"` for episode aggregation. |
| `Invalid action shape, expected: X, received: Y`. | Policy action tensor has shape `[num_envs, action_manager.total_action_dim]`. | Inspect action term dimensions. Do not change `cfg.actions` without updating policy output dimensions and any action clipping wrapper. |
| Observation concatenation error. | Each observation term in a concatenated group must agree on all dimensions except the concatenation dimension after delay/history processing. | Check `group_obs_dim`, `history_length`, `flatten_history_dim`, and `concatenate_dim`. Use `concatenate_terms=False` temporarily to isolate the bad term. |

## NaN and Inf handling

### Observation NaNs

Observation NaN policy is configured on `ObservationGroupCfg.nan_policy`:

- `disabled`: no check; fastest but NaNs pass through.
- `warn`: prints the group or `group/term`, sanitizes to zero.
- `sanitize`: silently converts NaN, +Inf, and -Inf to zero.
- `error`: raises `ValueError` with affected environment IDs.

If `nan_check_per_term=True`, the error/warning points at a specific term such
as `actor/base_lin_vel`. If false, only the final group output is checked.
NaN checks run after noise/clip/scale and before delay/history buffers, so a
sanitized value does not poison temporal buffers.

### Reward NaNs

Reward values are always sanitized by the reward manager after weighting and
optional dt scaling. This prevents policy crashes but can hide the source. If a
reward unexpectedly vanishes for some environments:

1. Temporarily inspect the raw reward function output before the manager sums it.
2. Add a termination term that detects invalid physics state if NaNs come from
   simulation divergence.
3. Use observation `nan_policy="error"` in development to catch the first bad
   observation instead of letting a policy consume it.

### Simulation NaNs

If NaNs are in `env.sim.data` rather than a single observation/reward function,
use a termination term that detects invalid state and consider enabling the
simulation NaN guard in `SimulationCfg` for debugging. NaN guard and simulation
configuration details live with the scene/simulation runtime guidance.

## CommandTerm update/reset signatures

A command term must implement:

```python
def _update_command(self, env_ids: torch.Tensor | None) -> None: ...
```

The old zero-argument form raises a `TypeError` mentioning `env_ids` at command
term construction. Handle the two call sites deliberately:

- `env_ids is None`: per-step update for all environments.
- `env_ids` is a tensor: reset-scoped update for just those environments.

If the update advances state, such as a motion-frame index, advance only the
selected environments. If the update only recomputes a value from current sim
state, it can safely ignore `env_ids`.

`CommandTerm.reset(env_ids)` expects concrete tensor IDs from the environment
reset path. Do not call a command term's `reset(None)` manually. Use
`env.reset()` or `env.reset(env_ids=...)` so mjlab supplies the right IDs and
also resets observation/action/reward/event state consistently.

## Auto-reset and manual reset

| Symptom | Cause | Fix |
|---|---|---|
| `Environments [...] must be reset via reset(env_ids=...) before calling step() again when auto_reset=False.` | A done environment returned a terminal observation and is pending manual reset. | Compute `done_ids = (terminated | truncated).nonzero().squeeze(-1)`, consume terminal observations as needed, then call `env.reset(env_ids=done_ids)` before another step. |
| RSL-RL training hangs or crashes with `auto_reset=False`. | Stock RSL-RL runners do not perform per-environment manual resets. | Keep `auto_reset=True` for stock mjlab training, or write a custom wrapper/loop that handles manual reset. |
| Terminal observations seem missing with `auto_reset=True`. | Done environments are reset inside `step()` and returned observations are post-reset initial observations. | Use `auto_reset=False` in a custom loop when terminal observations are required, or capture terminal transition data in `record_pre_reset`. |
| Command or interval timers changed on reset. | Reset-scoped command/event update was not handled correctly in a custom term. | Ensure command `_update_command(env_ids)` scopes state advances to `env_ids`. For events, rely on `env.reset(env_ids=...)`; interval timers are resampled for reset envs. |

## `SceneEntityCfg` regex and ID matching

| Symptom | Likely cause | Fix |
|---|---|---|
| `Not all regular expressions are matched!` | Patterns use full-string matching and did not match available element names. | Add `.*` for substring matching, correct names after scene namespacing, or inspect entity element names through the scene/simulation tooling. |
| `Multiple matches for '<name>'` | Two regex patterns in the same field match the same target string. | Make patterns mutually exclusive or split the logic into separate terms. |
| `Inconsistent ... names and indices` | Both names and IDs were provided but resolve to different elements/order. | Provide either names or IDs, or set both only after confirming exact resolved order. |
| Term reads joints/geoms in unexpected order. | Default `preserve_order=False` returns entity/native order. | Set `preserve_order=True` when policy/action vector order or metric order must follow the query pattern order. |
| Selecting all elements unexpectedly yields `slice(None)`. | `SceneEntityCfg` optimizes full ordered selections for fast slicing. | Treat `slice(None)` as a valid resolved ID set. Avoid code that assumes IDs are always lists. |

## Event mode requirements

Normal `ManagerBasedRlEnv` calls satisfy these requirements automatically. They
matter when writing custom event code or invoking `EventManager.apply()` in a
unit test or debugging snippet.

| Mode | Required fields/call args | Common error | Fix |
|---|---|---|---|
| `startup` | `mode="startup"`; no `env_ids` needed. | Startup side effect expected after resets. | Use `reset` mode for per-episode changes; startup runs once at initialization. |
| `reset` | Concrete `env_ids` and `global_env_step_count`. Optional `min_step_count_between_reset`. | Error that reset mode requires total environment steps or concrete env IDs. | Let `env.reset()` call it, or pass both arguments when testing the manager directly. |
| `interval` | `interval_range_s=(min,max)` and `dt` when applying. Do not pass `env_ids`. | Missing `interval_range_s`, missing `dt`, or error that interval mode does not require env indices. | Set `interval_range_s` on the config; call `apply("interval", dt=env.step_dt)`. The manager chooses env IDs from timers. |
| `step` | `dt` when applying. | Error that step mode requires the time-step. | Call through the environment step path or pass `dt` in tests. |

If a custom event writes MuJoCo model fields, ensure those fields are declared
with the event model-field helper and an appropriate recompute level. Otherwise
per-environment storage or derived constants may be stale.

## Observation delay/history pitfalls

- Delay is applied before history; history stacks delayed samples.
- Repeated calls to `observation_manager.compute(update_history=True)` outside
  the step/reset path will advance buffers. Use `env.get_observations()` or a
  non-updating compute call for inspection.
- During a partial reset, reset envs' buffers are backfilled with the post-reset
  frame while other env timelines are untouched.
- Group-level `history_length` overrides term-level history settings. If an
  actor group unexpectedly has all terms with the same history length, inspect
  the group config first.
- With flattened, concatenated history, ordering is term-major. A policy ported
  from a framework that uses time-major ordering needs reindexing.

## Recorder hook confusion

- `record_pre_reset(env_ids)` sees the previous observation and terminal action
  before auto-reset zeroes actions. Use this for terminal transitions.
- `record_post_reset(env_ids)` sees fresh initial observations after reset.
- `record_post_step()` sees fresh observations for all envs, but reset envs now
  hold initial observations and zeroed actions.
- Recorder terms must subclass `RecorderTerm`; function-based recorder configs
  raise a type error.

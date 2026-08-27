# Lifecycle and managers

Use this reference when a bug depends on *when* a manager term runs or which
manager owns a piece of state.

## Construction phases

An mjlab environment passes through four phases:

1. **Build scene and simulation.** The scene composes entities into a MuJoCo
   model; the simulation allocates batched world state. Scene/model details are
   owned by the scene/simulation sub-skill, but manager terms depend on the
   resulting entity names and element names.
2. **Initialize managers.** Manager dictionaries are prepared, class terms are
   instantiated, `SceneEntityCfg` parameters are resolved, observation
   delay/history buffers are allocated, domain-randomization model fields are
   expanded, action/observation spaces are configured, and startup events fire.
3. **Reset.** The environment resets selected worlds, runs reset-time
   curricula/events, clears manager state, resamples commands, computes fresh
   observations, and emits reset logging extras.
4. **Step.** Actions are processed, physics advances for `decimation`
   substeps, scalar managers compute rewards/terminations/metrics, step and
   interval events fire, optional auto-reset runs, commands and sensors update,
   and observations are assembled for the next policy query.

## Manager construction order

`ManagerBasedRlEnv.load_managers()` creates managers in this order:

1. `EventManager` from `cfg.events`.
2. Simulation model fields required by event/domain-randomization terms are
   expanded.
3. `CommandManager` from `cfg.commands`, or `NullCommandManager` if empty.
4. `ActionManager` from `cfg.actions`.
5. `ObservationManager` from `cfg.observations`.
6. `TerminationManager` from `cfg.terminations`.
7. `RewardManager` from `cfg.rewards`.
8. `CurriculumManager` from `cfg.curriculum`, or a null manager if empty.
9. `MetricsManager` from `cfg.metrics`, or a null manager if empty.
10. `RecorderManager` from `cfg.recorders`, or a null manager if empty.
11. Gym-style action/observation spaces are configured.
12. Startup events run if any event has `mode="startup"`.

Ordering matters. Event manager must exist before model fields are expanded.
Command manager must exist before observation manager because observation terms
may read `generated_commands`. Action manager determines the flat action space
before wrappers or trainers use it.

## Reset flow

`env.reset(env_ids=None)` resolves `env_ids` to all environments when omitted,
clears `env.extras["log"]`, and calls an internal reset path. For selected
environments, the reset path does the following:

1. `curriculum_manager.compute(env_ids)` adjusts difficulty/configuration for
   the resetting environments.
2. `sim.reset(env_ids)` and `scene.reset(env_ids)` restore simulation and scene
   state.
3. Reset-mode events fire with concrete `env_ids` and the global environment
   step count. This is where state randomization normally belongs.
4. Managers reset in this order: observations, actions, rewards, metrics,
   curriculum logging, commands, interval-event timers, and terminations.
5. `episode_length_buf[env_ids]` is set to zero and manual-reset-pending flags
   are cleared.
6. Scene data is written to the simulation, `sim.forward()` refreshes derived
   quantities, commands compute with `dt=0.0` scoped to `env_ids`, sensors run,
   and observations are computed with history/delay update scoped to the reset
   environments.
7. Recorder `record_post_reset(env_ids)` hooks fire after fresh reset
   observations exist.

Partial resets are scoped. Observation history and delay buffers for other
environments are not advanced, and stateful commands update only the reset IDs.

## Step flow

The environment step order is:

```text
action_manager.process_action(action)
for _ in range(cfg.decimation):
    action_manager.apply_action()
    scene.write_data_to_sim()
    sim.step()
    scene.update(dt=physics_dt)
    metrics_manager.compute_substep()

episode_length_buf += 1
common_step_counter += 1
termination_manager.compute()
reward_manager.compute(dt=step_dt)
metrics_manager.compute()
event_manager.apply(mode="step", dt=step_dt)
event_manager.apply(mode="interval", dt=step_dt)

if auto_reset and any done:
    recorder_manager.record_pre_reset(done_ids)
    reset selected environments
    scene.write_data_to_sim()

sim.forward()
command_manager.compute(step_dt, or per-env dt with 0 for freshly reset envs)
sim.sense()
observation_manager.compute(update_history=True)

if auto_reset and any done:
    recorder_manager.record_post_reset(done_ids)
elif any done:
    mark manual reset pending

recorder_manager.record_post_step()
return obs, reward, terminated, truncated, extras
```

Key timing consequences:

- Termination, reward, step-event, and interval-event terms see state after the
  decimation loop but before the single post-step `sim.forward()` refresh. Some
  derived MuJoCo quantities can lag integrated `qpos`/`qvel` by one physics
  substep. This is consistent across envs and steps.
- If a term writes state and immediately reads derived quantities that depend on
  that state, refresh them explicitly before the read or move the read to a
  later lifecycle point.
- Step and interval events fire before auto-reset, on terminal state. Resetting
  environments are reset afterward, so a perturbation event can affect
  non-reset envs while the reset env starts the next episode cleanly.
- Commands update after `sim.forward()` and before sensors/observations. During
  auto-reset, freshly reset environments get `dt=0` so command timers start
  full and match an explicit manual reset flow.
- `record_pre_reset` is the only built-in hook that sees terminal actions for
  environments that are about to auto-reset. By `record_post_step`, reset envs'
  actions are zeroed and observations are initial observations for the new
  episode.

## Horizon, timeout, and reset semantics

### Timing fields

- `physics_dt = cfg.sim.mujoco.timestep`.
- `step_dt = cfg.sim.mujoco.timestep * cfg.decimation`.
- `max_episode_length = ceil(cfg.episode_length_s / step_dt)`.
- Register a time-limit termination with `TerminationTermCfg(func=mdp.time_out,
  time_out=True)` so it contributes to the `truncated` output rather than a
  terminal failure.

### Finite vs infinite horizon

`cfg.is_finite_horizon` communicates whether a time limit is part of the task
definition:

- `False` (default): the time limit is an artificial cutoff. RSL-RL wrappers add
  timeout information so value functions can bootstrap beyond truncation.
- `True`: the time limit is a true terminal boundary; future value beyond it is
  not expected.

Do not use `is_finite_horizon` as a substitute for `TerminationTermCfg.time_out`.
The termination term still controls the `terminated`/`truncated` tensors.

### Auto-reset

`cfg.auto_reset=True` is the default. Done environments are reset inside
`step()`, and returned observations for those environments are post-reset
initial observations. This matches mjlab's stock RSL-RL training path.

`cfg.auto_reset=False` returns the true terminal observation and does not reset
done environments. The caller must:

1. Derive `done = terminated | truncated` after `step()`.
2. Slice terminal observations for replay/bootstrap logic.
3. Call `env.reset(env_ids=done_ids)` before the next `step()`.

Calling `step()` again while a done environment has not been reset raises a
runtime error. Stock RSL-RL `OnPolicyRunner` does not drive these manual resets,
so use `auto_reset=False` only in a custom loop or wrapper that explicitly calls
`reset(env_ids=...)`.

## Manager responsibilities and useful state

| Manager | Owns | Common inspection points |
|---|---|---|
| `ObservationManager` | Observation groups, processing pipeline, delay/history buffers, observation NaN policy. | `active_terms`, `group_obs_dim`, `group_obs_concatenate`, `get_term_cfg(group, term)`. |
| `ActionManager` | Flat policy action tensor and per-term slices. | `total_action_dim`, `action_term_dim`, `action`, `prev_action`, `get_term(name)`. |
| `RewardManager` | Weighted sum and per-term episode reward logs. | `active_terms`, `get_term_cfg(name)`, `Episode_Reward/<term>`. |
| `TerminationManager` | Done aggregation, terminated vs truncated split. | `terminated`, `time_outs`, `dones`, `get_term_cfg(name)`, `Episode_Termination/<term>`. |
| `EventManager` | Startup/reset/interval/step side effects and domain-randomization field expansion. | `active_terms`, `available_modes`, `domain_randomization_fields`, `get_term_cfg(name)`. |
| `CommandManager` | Goal command tensors, timers, debug visualization, command metrics. | `active_terms`, `get_command(name)`, `get_term(name)`, command metrics logged as `Metrics/<command>/<metric>`. |
| `CurriculumManager` | Reset-time difficulty or config mutations. | `active_terms`, returned state logged under `Curriculum/<term>`. |
| `MetricsManager` | Per-step diagnostic scalars with episode reductions. | `active_terms`, `MetricsTermCfg.reduce`, `Episode_Metrics/<term>`. |
| `RecorderManager` | User-defined rollout logging hooks. | `active_terms`, `get_term(name)`, hook timing around resets and steps. |

Use the bundled `inspect_env_config.py` helper to inspect registered task config
keys without constructing a full simulation environment.

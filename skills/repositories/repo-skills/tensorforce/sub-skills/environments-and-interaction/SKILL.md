---
name: environments-and-interaction
description: "Create and troubleshoot Tensorforce environments, custom
  Environment subclasses, adapters, reward shaping, and parallel interaction
  boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensorforce environments and interaction

Use this sub-skill when the task is about constructing, implementing, wrapping, or debugging Tensorforce environments. It covers `Environment.create(...)`, custom `Environment` subclasses, Gym/custom adapters, reward shaping, `max_episode_timesteps` and abort terminals, optional simulator adapters, vectorized/multi-actor environment contracts, and remote environment boundaries.

## Route quickly

- Need the public environment factory forms or custom subclass contract? Read `references/environment-api.md`.
- Need Gym, `custom_cartpole`, ALE, Retro, ViZDoom, OpenSim/PLE, or CARLA adapter guidance? Read `references/optional-environment-adapters.md`.
- Need vectorized, multi-actor, multiprocessing, or socket environment boundaries? Read `references/advanced-environments.md`.
- Need to diagnose shape/type/terminal/socket/Gym dependency failures? Read `references/troubleshooting.md`.
- Need a small runtime check of custom environment behavior, reward shaping, and time-limit aborts? Run `scripts/custom_environment_smoke.py --help`, then run it in the user's Tensorforce environment.

## Boundaries

This sub-skill owns environment-side behavior only. Route agent construction, `act`/`observe`, action masking policy behavior, and offline `experience`/`update` details to the agent interaction sub-skill. Route `Runner.run(...)`, CLI training/evaluation, and tuning workflows to the runner workflow sub-skill. Route installation-wide dependency setup and TensorFlow device configuration to the root Tensorforce skill.

Optional simulator adapters are documented as public surfaces but were not executed during skill construction. Do not claim CARLA, ALE, Retro, ViZDoom, OpenSim, or PLE execution is verified unless the user supplies those dependencies/assets and you run a bounded adapter-specific smoke.

## Safe workflow

1. Create environments through `Environment.create(...)` where possible, so Tensorforce can wrap max-timestep and reward-shaping behavior consistently.
2. For custom environments, implement the minimal subclass contract: `states()`, `actions()`, `reset()`, `execute(actions)`, optional natural `max_episode_timesteps()`, and `close()`.
3. Always decide who owns the episode length. If the environment has no natural episode limit, pass `max_episode_timesteps` to `Environment.create(...)` or `Runner(...)` so Tensorforce can emit `terminal=2` for time-limit aborts.
4. Treat optional adapters and remote/socket workflows as dependency- and process-boundary work. Prefer bounded local smoke first, then add external simulator/server checks only when explicitly available.

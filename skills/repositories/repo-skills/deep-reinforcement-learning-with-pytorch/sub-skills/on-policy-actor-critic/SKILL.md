---
name: on-policy-actor-critic
description: "Router for REINFORCE, baseline, actor-critic, A2C, and PPO workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# On-policy Actor-Critic

Use this sub-skill for the repo's on-policy classic-control workflows in Char02, Char03, Char04, and Char07.

## Route here when the task says
- "run REINFORCE on CartPole"
- "compare baseline vs no-baseline"
- "inspect actor-critic updates"
- "use the A2C multiprocessing helper"
- "inspect PPO clipping"
- "play back a saved policy"

## Keep this route focused on
- REINFORCE and policy-gradient baselines in Char02.
- Actor-critic variants in Char03.
- A2C with `SubprocVecEnv` in Char04.
- PPO on CartPole, MountainCar, and Pendulum in Char07.
- Playback of saved policy pickles from the on-policy family.

## Do not use this route for
- Tabular control or GridWorld toy examples — route to the tabular-control route.
- DQN or other value-based discrete control — route to the value-based-discrete-control route.
- Off-policy continuous-control families such as DDPG, SAC, or TD3 — route to the off-policy continuous-control route.
- Standalone plotting or results aggregation.

## Read first
- `references/workflows.md` for the algorithm comparison, checkpoint map, and the exact source-script roles.
- `references/troubleshooting.md` for `env.seed`, old Gym step signatures, multiprocessing, checkpoint loading, TensorBoard paths, and headless plotting failures.

## Bundled helpers
- `scripts/multiprocessing_env.py` for the reusable subprocess vector-env helper used by A2C.
- `scripts/playback_saved_policy.py` for bounded playback of saved policy pickles from the REINFORCE / actor-critic family.

## Fast choice guide
- No critic, episode returns only, `saved_log_probs`: REINFORCE.
- Policy plus value head, advantage from `G - V`: actor-critic or baseline.
- Multiple env processes and short rollouts: A2C.
- `clip_param`, ratio clipping, minibatches, repeated epochs: PPO.
- A saved `.pkl` policy object that should be evaluated rather than trained: playback helper.

## Compatibility notes
- The inspection environment verified Gym 0.23.1 with classic-control envs and 4-value `step(...)` tuples.
- The source scripts still use legacy `env.seed(...)` and legacy env IDs such as `CartPole-v0`, `MountainCar-v0`, and `Pendulum-v0`.
- Treat `Pendulum-v0` as a compatibility note; use `Pendulum-v1` in the inspected environment when you need a modern substitute.
- This route is CPU-first, even though CUDA is available in the inspection environment.

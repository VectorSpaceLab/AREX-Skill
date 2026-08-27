---
name: envs-and-vectorization
description: "Integrate Gymnasium and PettingZoo environments with Tianshou
  vector envs, workers, wrappers, space introspection, seeding, and optional
  environment backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tianshou Environments and Vectorization

Use this sub-skill when work mentions `DummyVectorEnv`, `SubprocVectorEnv`, `ShmemVectorEnv`, `RayVectorEnv`, `PettingZooEnv`, action masks, custom Gymnasium environments, vectorized rollouts, environment workers, wrappers, seeding, or optional engines such as EnvPool, MuJoCo, Atari, VizDoom, Box2D, or robotics.

## Route First

- For algorithm, policy, replay buffer, collector, or trainer construction, use `../procedural-training/SKILL.md` after the environment interface is valid.
- For high-level experiment `EnvFactoryRegistered` setup, use `../highlevel-experiments/SKILL.md`; this sub-skill only covers lower-level env factories and vector env behavior.
- For multi-agent algorithm choices beyond PettingZoo wrapping and masks, use `../offline-and-specialized-rl/SKILL.md` after confirming the environment observation/action contract.

## Fast Path

1. Build each environment through a zero-argument factory such as `lambda: gym.make("CartPole-v1")`; never pass already-created env instances into Tianshou vector env constructors.
2. Start with `DummyVectorEnv(env_fns)` for API validation, deterministic debugging, custom wrappers, and smoke checks.
3. Move to `SubprocVectorEnv(env_fns, context="spawn" or "fork")` or `ShmemVectorEnv(env_fns)` only after the factories are picklable/importable and observations are compatible with batching.
4. Use `RayVectorEnv(env_fns)` only when `ray` is installed and distributed execution is actually needed.
5. Call `reset()` before stepping, pass one action per selected env id, reset done env ids yourself after `terminated | truncated`, and always call `close()`.
6. For PettingZoo AEC envs, wrap with `PettingZooEnv`; expect observations shaped as dictionaries containing `obs`, `agent_id`, and usually `mask` for discrete legal actions.

## References

- `references/api-reference.md` lists constructors, vector env methods, worker behavior, wrappers, `PettingZooEnv`, and `SpaceInfo`.
- `references/workflows.md` gives custom env, vectorization, seeding, PettingZoo/action-mask, and optional-backend workflows.
- `references/troubleshooting.md` maps common install/import, optional dependency, validation, CLI/API misuse, and workflow failures to fixes.
- `scripts/check_vector_env.py` is a tiny CartPole smoke check that validates Tianshou vector env calls without training.

## Safe Smoke Check

Run the bundled helper from the generated skill tree after installing public Tianshou dependencies:

```bash
python skills/tianshou/sub-skills/envs-and-vectorization/scripts/check_vector_env.py --num-envs 2 --steps 4
```

Add `--subproc` only after the default dummy run passes; subprocess mode is intentionally conservative and uses a top-level factory to avoid common pickling pitfalls.

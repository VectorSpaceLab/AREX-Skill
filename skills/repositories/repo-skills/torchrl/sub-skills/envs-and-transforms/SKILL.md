---
name: envs-and-transforms
description: "Build, validate, transform, vectorize, and debug TorchRL
  environments and TensorDict transition layouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TorchRL envs-and-transforms

Load this sub-skill when the task involves TorchRL environments, transformed environments, vectorized environments, environment specs, optional simulator wrappers, or the TensorDict transition layout produced by `EnvBase.step` and consumed by `step_mdp`.

## Use this skill for

- Building CPU-safe native environments such as `PendulumEnv` and custom `EnvBase` subclasses.
- Wrapping Gym/Gymnasium and other simulator backends with TorchRL environment wrappers.
- Adding `TransformedEnv`, `Compose`, `ObservationNorm`, `StepCounter`, `ActionScaling`, image transforms, reward transforms, action transforms, and key transforms.
- Checking and debugging `observation_spec`, `action_spec`, `reward_spec`, `done_spec`, `input_spec`, and `output_spec` with `check_env_specs`.
- Moving a transition from root + `"next"` layout to the next-step root layout with `step_mdp`.
- Choosing `SerialEnv` versus `ParallelEnv`, debugging vectorized worker issues, and validating specs before multiprocessing.
- Reasoning about multi-agent environment grouping and nested per-agent specs.
- Routing optional simulator, rendering, and pixel dependencies without claiming they are verified in a base CPU environment.

## Route away

- Policy, actor, critic, distribution, recurrent module, or network construction: use `modules-and-policies`.
- Collectors, replay buffers, samplers, writers, or data-collection topology: use `collectors-and-replay`.
- PPO/SAC/DQN/objective wiring, value estimators, target updates, trainers, Hydra configs, or SOTA recipes: use `objectives-and-training`.
- VLA-specific action chunk training targets and service-backed robot/LLM workflows: use `llm-vla-and-services`. Generic `ActionChunkTransform` key semantics are summarized here only to route safely.

## Fast operating path

1. Pick the smallest environment surface: native `PendulumEnv` or a custom `EnvBase` for core TorchRL behavior; wrapper classes only when the simulator dependency is installed.
2. Inspect specs before writing policy or collector code. Validate with `check_env_specs(env, ...)` offline because it runs a short rollout and may reset seeding state.
3. Add transforms with explicit `in_keys`, `out_keys`, `in_keys_inv`, and `out_keys_inv`; verify transformed specs and use `clone()` before reusing a transform already attached to another env.
4. Run a tiny rollout, inspect root keys and `("next", ...)` keys, then use `step_mdp` with the env's `reward_keys`, `done_keys`, and `action_keys` when keys are nested or multi-agent.
5. Debug in one process with `SerialEnv`; move to `ParallelEnv` only after the same factory passes `check_env_specs`.
6. For optional Gym/Gymnasium, MuJoCo, DM Control, IsaacLab, VMAS, PettingZoo, OpenSpiel, Brax, Jumanji, rendering, or pixel stacks, follow the optional-backend checklist before treating failures as TorchRL bugs.

## References

- [Environment workflows](references/env-workflows.md): construction, specs, rollout, `step_mdp`, vectorization, multi-agent layouts.
- [Transform reference](references/transform-reference.md): `TransformedEnv`, `Compose`, key routing, normalization, action scaling, and action chunk routing.
- [Optional environment backends](references/optional-env-backends.md): Gym/Gymnasium and simulator extras, rendering, and backend-specific cautions.
- [Troubleshooting](references/troubleshooting.md): common failure signatures and fixes.

## Safe smoke helper

Run [scripts/smoke_env_rollout.py](scripts/smoke_env_rollout.py) in an environment where `torchrl`, `torch`, and `tensordict` import. From this sub-skill directory:

```bash
python scripts/smoke_env_rollout.py --steps 3 --check-specs
```

From another working directory, pass the actual local path of this sub-skill's `scripts/smoke_env_rollout.py` copy to Python.

Expected signal: concise success text showing the TorchRL version, rollout batch size, and `step_mdp` keys. The helper uses only native `PendulumEnv`, `TransformedEnv`, `StepCounter`, `check_env_specs`, and `step_mdp`; it does not require Gym, rendering, multiprocessing, or GPUs.

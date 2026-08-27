---
name: modules-and-policies
description: "Assemble TensorDict-native TorchRL modules, policies, recurrent
  actors, multi-agent models, and model-based policy wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TorchRL modules and policies

Use this sub-skill when a task is about building or debugging TorchRL neural modules and policy wrappers: `Actor`, `ProbabilisticActor`, `ValueOperator`, `QValueActor`, `SafeModule`, `SafeSequential`, `MLP`, `TanhNormal`, `MaskedCategorical`, recurrent `GRUModule`/`LSTMModule`, `set_recurrent_mode`, multi-agent model modules, value normalization, world-model components, Decision Transformer wrappers, MCTS scores, or planners.

## Route here for

- Deterministic or probabilistic actor assembly from TensorDict keys.
- Actor/critic key contracts, including nested observation/action keys.
- Distribution-parameter extraction, log-prob keys, bounded continuous actions, masked discrete actions, and composite action heads.
- Safe output projection with `TensorSpec` / `Composite` specs.
- Q-value policies and action masks.
- Recurrent hidden-state conventions, primers, `is_init`, and `pad` / `scan` / `triton` backend choices.
- Multi-agent model grouping with `MultiAgentMLP` / `MultiAgentConvNet` and centralized/shared-parameter choices.
- API-level routing for Dreamer, Decision Transformer, world models, MCTS scores, and CEM/MPPI planners.

## Route elsewhere

- Environment construction, environment specs, transforms, rollouts, and `step_mdp`: use `envs-and-transforms`.
- Loss modules, value estimators, replay/trainer loops, and algorithm training wiring: use `objectives-and-training`.
- Generic collectors and replay buffers: use `collectors-and-replay`.
- LLM/VLA wrappers that require model serving, tokenizers, datasets, or accelerator services: use `llm-vla-and-services`.
- Code-editing policy, tests, docs, CI markers, and contribution rules: use `development-and-testing`.

## Start here

1. Identify the TensorDict contract: input keys, output keys, batch shape, and whether keys are nested.
2. Identify the action/value spec, if any. For safe actors, the spec keys must match output keys.
3. Choose a wrapper:
   - `Actor` for deterministic `observation -> action` mappings.
   - `ProbabilisticActor` for modules that first write distribution parameters, then sample/write actions.
   - `ValueOperator` for state-value or state-action-value heads.
   - `QValueActor` for discrete greedy policies over `action_value` tensors.
   - `SafeModule` / `SafeSequential` when explicit spec projection or TensorDict sequencing is needed.
4. For recurrent policies, wire `is_init` and hidden keys before trying training-time sequence batches.
5. For multi-agent models, decide whether the agent dimension is grouped in the tensordict key layout or a tensor dimension, then keep that choice consistent through models and losses.

## References

- [Policy API reference](references/policy-api-reference.md)
- [Recurrent and multi-agent modules](references/recurrent-and-multiagent.md)
- [Model-based, planner, wrapper, and value-normalization workflows](references/model-workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled checks

Run these after installing TorchRL. From this sub-skill directory:

```bash
python scripts/smoke_actor.py
python scripts/smoke_recurrent_actor.py
```

From another working directory, pass the actual local paths of this sub-skill's bundled scripts to Python.

The smoke scripts are CPU-only, deterministic, and assert TensorDict output keys/shapes. They do not depend on repository checkouts, simulator extras, Triton, CUDA, or external services.

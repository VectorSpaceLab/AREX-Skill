---
name: torch-agent-training
description: "Route and compose public single-agent PyTorch agents, models,
  memories, resources, trainers, and experiment controls in skrl 2.1.0."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Torch agent training

Use this route for a **single-agent PyTorch** skrl 2.1.0 workflow: choose an
algorithm, build its model-role dictionary, allocate rollout/replay memory,
configure preprocessors/noises/schedulers, select a trainer, and make a safe
train/evaluate/resume plan. Start with the bounded component check in
[`scripts/torch_ppo_components.py`](scripts/torch_ppo_components.py), then use
the references for the exact role keys and construction details.

## Route quickly

1. Establish the observation, optional state, and action spaces through the
   environment route; this skill does not choose or implement Gymnasium
   wrappers. See [`../../references/framework-selection.md`](../../references/framework-selection.md)
   and [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
   in the root skill before committing to a backend or trainer.
2. Choose an algorithm and its required model roles in
   [`references/algorithm-and-component-selection.md`](references/algorithm-and-component-selection.md).
   Match the policy distribution to the action space and use a deterministic
   value/critic model where the table requires it.
3. Compose the models, `RandomMemory` (when required), configuration, and agent
   using [`references/workflow-and-api.md`](references/workflow-and-api.md).
   Keep `memory_size` and the agent's rollout/update settings consistent.
4. Use `SequentialTrainer` for the normal loop, `StepTrainer` when the caller
   owns each iteration, and `ParallelTrainer` only after checking its process,
   pickling, shared-memory, and hardware constraints.
5. Disable writes during a smoke/evaluation probe, load a checkpoint into an
   architecture-equivalent agent, and only then enable training or logging.
   Check workflow-specific failure modes in
   [`references/troubleshooting.md`](references/troubleshooting.md).

## Boundaries

- **Environment wrappers and space conversion:** route to the
  [`environment-integration`](../../sub-skills/environment-integration/SKILL.md)
  sibling.
- **IPPO/MAPPO, multi-agent trainers, and Runner/YAML:** route to
  [`../../sub-skills/multi-agent-and-runner/SKILL.md`](../../sub-skills/multi-agent-and-runner/SKILL.md).
- **JAX and Warp:** not covered here.
- Framework-wide backend selection and package-wide install/import diagnosis
  belong to the root route; this sub-skill owns Torch-specific composition.

## Completion checklist

Before handing a workflow to a researcher, verify: `torch` and `skrl` import;
all model dictionary keys are exact; each model's input/output role is
compatible with the space; the memory device and environment count agree; the
trainer config has finite, intentional `timesteps`; logging/checkpoint paths
are explicitly chosen; and resume/evaluation uses an architecture-compatible
agent. A CPU smoke establishes import and CPU behavior only—it does **not**
prove CUDA or another accelerator.

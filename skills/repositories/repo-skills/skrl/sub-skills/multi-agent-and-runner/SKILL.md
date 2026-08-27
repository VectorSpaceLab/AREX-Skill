---
name: multi-agent-and-runner
description: "Route skrl 2.1.0 IPPO/MAPPO multi-agent workflows, framework
  Runner configuration, model and memory dictionaries, trainer scopes, and
  distributed/checkpoint boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Multi-agent and Runner

Use this route when the request names **IPPO**, **MAPPO**, PettingZoo or
another multi-agent environment, per-agent model/memory dictionaries, a
centralized state/value function, Runner/YAML configuration, trainer scopes,
or multi-process/distributed execution. It owns the multi-agent contract and
declarative Runner machinery; it does not replace environment wrapping or the
single-agent framework guides.

## Route quickly

1. Establish a framework-wrapped multi-agent environment first. Confirm
   `possible_agents`, current `agents`, `observation_spaces`, `state_spaces`,
   `action_spaces`, `device`, and `num_envs`. For PettingZoo or Isaac Lab,
   start with [`../environment-integration/SKILL.md`](../environment-integration/SKILL.md).
2. Choose the learning semantics in
   [`references/multi-agent-workflows.md`](references/multi-agent-workflows.md):
   IPPO is decentralized training/execution with an independent value model;
   MAPPO is centralized training/decentralized execution through a state-based
   value model. Both expose the same per-agent constructor shape.
3. Build **nested dictionaries keyed by every `possible_agents` entry**:
   `models[agent_id]["policy"]`, `models[agent_id]["value"]`, and, for
   training, `memories[agent_id]`. A single-agent model dictionary is not a
   multi-agent dictionary. Validate role keys, spaces, and model initialization
   before constructing the algorithm.
4. For declarative setup, use
   [`references/runner-configuration.md`](references/runner-configuration.md).
   A Runner needs a wrapped environment and top-level `models`, `memory`,
   `agent`, and `trainer` configuration. Treat YAML as trusted input: Runner
   evaluates selected component strings and expression fields.
5. Select a trainer deliberately. A single IPPO/MAPPO object normally uses
   `SequentialTrainer`, `StepTrainer`, or direct loop ownership. `ParallelTrainer`
   is a Torch multiprocessing facility, not the same thing as a multi-agent
   environment. Scope validation and simultaneous-agent limitations are in the
   workflow reference.
6. Before resuming, check framework-specific checkpoint format, experiment
   directory, rank ownership of logging, and model-role compatibility. Use
   [`references/troubleshooting.md`](references/troubleshooting.md) for shape,
   key, migration, YAML, scope, and distributed failures.

## Framework boundaries

- **Torch:** IPPO and MAPPO are available; Torch additionally supports a
  policy/value shared model through `shared_model` and automatic mixed
  precision. `ParallelTrainer` is Torch-only.
- **JAX:** IPPO and MAPPO are available with separate policy/value models.
  Runner does not support shared policy/value models and removes the
  unsupported mixed-precision setting. Call `init_state_dict` for generated
  models before use.
- **Warp:** the Warp Runner and sequential trainer cover single-agent Warp
  agents. This release has no Warp IPPO/MAPPO mapping; do not route a Warp
  multi-agent request to this path as if it were supported. See
  [`../warp-agent-training/SKILL.md`](../warp-agent-training/SKILL.md) for the
  single-agent boundary.
- Framework-specific model construction belongs to
  [`../torch-agent-training/SKILL.md`](../torch-agent-training/SKILL.md),
  [`../jax-agent-training/SKILL.md`](../jax-agent-training/SKILL.md), or
  [`../warp-agent-training/SKILL.md`](../warp-agent-training/SKILL.md). Link
  there for mixin or device details rather than duplicating those guides.

## Completion checklist

A safe handoff has: a wrapper-derived, immutable `possible_agents` list; all
model and memory dictionaries covering it; policy/action and value/state space
compatibility; an explicit choice between IPPO and MAPPO; a finite trainer
`timestep` plan; validated scopes if multiple agents share a vectorized
environment; trusted Runner/YAML component names if used; explicit logging and
checkpoint paths; and a framework/distributed boundary statement. Do not run
full multi-agent training or an unreviewed user YAML merely to diagnose its
shape.

---
name: rl-agent-zoo
description: "Implement SMARTS Agent policies, AgentSpec packages, versioned zoo
  locators, social-agent bubbles, and optional Ray/RLlib integrations without
  assuming optional training dependencies are installed."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RL and agent zoo

Use this route when a user needs a SMARTS policy object, an installable agent
package, a registered locator, a social agent or bubble, or an RLlib/Ray
adapter. Keep core policy and registry work separate from the simulation
lifecycle route. Keep benchmark commands and full training runs reference-only.

## Capability and boundary

This route covers:

- `smarts.core.agent.Agent` policies and the `act(obs, **configs)` contract.
- `smarts.zoo.agent_spec.AgentSpec`, registry registration, dynamic module
  loading, and `make`/`make_agent`.
- Interface/action/observation alignment for an agent specification.
- `SocialAgentActor`, `BoidAgentActor`, `Bubble`, airlocks, and policy kwargs.
- The shape of an `RLlibHiWayEnv` configuration and Ray worker distribution.
- Safe, import-only validation of a locator with
  [the bundled checker](scripts/check_agent_locator.py).
- Packaging an inference policy for a zoo or benchmark consumer.

Do not use this route for Gym reset/step/close basics or general action and
observation catalogues; use `simulation-environments`. Use `cli-integrations`
for `scl zoo` and `scl benchmark` command details. Do not promise training,
checkpoint downloads, benchmark scores, or regression results.

## Fast decision path

1. Decide whether the deliverable is a core Python policy, an installed zoo
   package, a social/bubble actor, or an RLlib integration.
2. Implement and test the policy with a concrete `AgentInterface`. The policy
   must return an action accepted by that interface's action space.
3. Wrap the policy and interface in an `AgentSpec`; register a versioned name
   from an importable module. Run the locator checker before attempting a
   simulation.
4. If RLlib is requested, first probe `ray` and `ray.rllib`. They are optional,
   and are not installed in the prepared core environment. Do not import
   `RLlibHiWayEnv` as a core smoke test when Ray is absent.
5. For a benchmark deliverable, package inference code and its model/dependency
   contract, then route installation and benchmark invocation to
   `cli-integrations`.

## Runtime invariants

- A policy subclasses `Agent` and implements `act(self, obs, **configs)`.
  `Agent.from_function(callable)` is suitable for a tiny stateless policy.
- `AgentSpec(interface=..., agent_builder=..., agent_params=...)` describes
  both the simulator-facing interface and the policy constructor. The builder
  is a class or callable, not an already-built policy instance.
- `agent_params` are dispatched as no arguments for `None`, positional
  arguments for a list/tuple, keyword arguments for a dict, and one argument
  otherwise. `build_agent()` raises if the builder is absent or not callable.
- `AgentSpec` is cloudpickle-checked at construction. Keep builders, params,
  adapters, and model handles serializable when workers will be used.
- Locators use `module.importable:registered-name-vN` (or `-latest`), where the
  registered name includes the version suffix. A bare `registered-name-vN`
  works only after that name is already registered in the current process.
- A module locator causes SMARTS to import the module and expects that import
  to execute `register(...)`. Importability is therefore part of the package
  contract; installing a distribution alone is not proof of registration.
- `make(locator, **kwargs)` returns an `AgentSpec`; `make_agent(locator,
  **kwargs)` returns `(Agent, interface)` and applies kwargs to the registered
  factory. Use `make` when the interface/spec must be inspected first.
- Do not use the deprecated observation/action/reward/info adapters for new
  core code. They remain fields on the current `AgentSpec` for compatibility;
  RLlib's current adapter path may still exercise them, so keep any legacy use
  explicit and test it against the selected RLlib release.

## Checks before handing off

- Confirm `AgentInterface` and the policy's raw action agree. Check the
  environment's per-agent `action_space[agent_id].contains(action)` rather
  than relying on a model's declared shape.
- Confirm the policy's observation adapter output agrees with the declared
  model observation space, including dtype, bounds, keys, and array shape.
- Import the package module and run
  `scripts/check_agent_locator.py --locator module:agent-name-v0`.
  The checker only imports and inspects the registry; it never installs,
  constructs a model, trains, downloads a checkpoint, or starts a simulator.
- Build the `AgentSpec` and policy without a scenario first. Use a bounded
  simulation smoke only when a scenario is supplied and the lifecycle route
  owns that smoke.
- For Ray, validate worker configuration and serialization before attempting
  any long run. The optional framework status is `unverified` until the user
  supplies a compatible installed stack.

## Progressive references

- [AgentSpec and registry](references/agent-spec-and-registry.md) — exact
  interfaces, locator grammar, registration and construction patterns.
- [RL frameworks](references/rl-frameworks.md) — RLlibHiWayEnv, Ray workers,
  spaces, optional Torch/TensorFlow, and resume caveats.
- [Social agents and bubbles](references/social-agents-and-bubbles.md) — actor,
  boid, bubble, airlock, travel, and policy-kwargs rules.
- [Benchmark packaging](references/benchmark-packaging.md) — inference package
  layout, dependency/model contracts, and benchmark compatibility gates.
- [Troubleshooting](references/troubleshooting.md) — installation/import,
  optional dependencies, config/data, API/CLI mistakes, and workflow failures.

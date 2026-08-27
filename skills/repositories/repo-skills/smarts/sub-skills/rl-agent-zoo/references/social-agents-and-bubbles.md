# Social agents and bubbles

## Social-agent actor

A `SocialAgentActor` is a scenario actor descriptor for a policy from the zoo,
not an already-running policy. Its verified constructor is:

```text
SocialAgentActor(name, agent_locator, policy_kwargs={}, initial_speed=None)
```

`agent_locator` uses the same importable-module and versioned-name grammar as
an ego agent. `policy_kwargs` are passed as keyword overrides when the
registered `AgentSpec` is constructed; they are not constructor arguments for
the `SocialAgentActor` itself. `initial_speed` optionally sets the initial
speed.

A social actor may be used in a scenario's traffic/social-agent configuration.
The policy must use an interface compatible with the captured vehicle and
return an action accepted by that interface. Register and validate the locator
before building the scenario. Do not assume a package's wheel or source
layout makes the module importable from worker processes.

A `BoidAgentActor` has the same base fields plus an id and optional
`BubbleLimits` capacity. A boid controls multiple vehicles; a regular social
agent controls an individual captured vehicle. Use the boid form when the
policy is intentionally multi-vehicle, and set capacity conservatively.

## Bubble semantics

The scenario `Bubble` descriptor is constructed as:

```text
Bubble(zone, actor, margin=2, limit=None, exclusion_prefixes=(), id=..., 
       follow_actor_id=None, follow_offset=None, keep_alive=False,
       follow_vehicle_id=None, active_condition=TRUE, airlock_condition=TRUE)
```

A bubble has a hijack zone and a surrounding airlock. A vehicle must pass
through the airlock and satisfy its condition before the bubble can capture it.
The bubble manager then assigns the social policy while the vehicle is in the
capture zone and relinquishes control after it exits the airlock. This means a
policy transition is spatial and stateful; it is not equivalent to adding a
second ego agent.

Important constructor invariants:

- `margin` must be non-negative.
- A traveling bubble may set **one** of `follow_actor_id` or
  `follow_vehicle_id`, never both.
- A traveling bubble must provide `follow_offset`.
- `keep_alive=True` is restricted to boid actors in the current implementation.
- The zone must resolve to a valid polygon when it is not a map zone.
- Broadphase active conditions cannot depend on current actor state.
- `limit` controls simultaneous captures; a boid's capacity and the bubble
  limit are both considered.

A fixed bubble uses a zone and no follow id. A traveling bubble follows one
actor or vehicle and repositions the zone using the configured offset. Use
`exclusion_prefixes` to prevent selected social actors from being captured.
Set an explicit `id` when a scenario or diagnostic needs stable references.

## Minimal construction pattern

The imports and scenario generation belong to the scenario route, but the
policy-facing shape is:

```python
from smarts.sstudio.sstypes import Bubble, PositionalZone, SocialAgentActor

bubble = Bubble(
    zone=PositionalZone(pos=(0, 0), size=(20, 40)),
    actor=SocialAgentActor(
        name="traffic-policy",
        agent_locator="my_policy_package:traffic-agent-v0",
        policy_kwargs={"speed": 10},
    ),
    margin=2,
)
```

For a traveling bubble, add exactly one of `follow_actor_id` or
`follow_vehicle_id`, plus `follow_offset=(x, y)`. For a multi-vehicle policy,
replace the actor with `BoidAgentActor` and review `capacity`/`BubbleLimits`.
Keep the zone and scenario assets in the user's scenario package; do not copy
large maps or generated build output into a policy package.

## Social versus ego configuration

Ego policies are normally supplied in the environment's `agent_specs` mapping.
Social policies are referenced by actor locator in scenario data and are
instantiated when the bubble/traffic manager captures a vehicle. Both use
`AgentSpec`, but their lifecycle differs:

- Ego: caller creates/owns the environment mapping and usually calls
  `make_agent` or `AgentSpec.build_agent`.
- Social: scenario data stores the locator and `policy_kwargs`; the simulator
  resolves it during actor capture.

When debugging a social agent, first validate the locator independently, then
validate the actor's interface/action contract, then inspect bubble geometry,
airlock, exclusions, and capacity. A successful import alone does not prove
that any vehicle will enter the bubble.

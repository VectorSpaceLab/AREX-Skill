---
name: simulation-environments
description: "Create and operate SMARTS HiWayEnvV1 and parallel Gymnasium
  environments, configure agent interfaces and policies, and diagnose action,
  observation, lifecycle, and deterministic-seeding issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SMARTS simulation environments

Use this route for the core CPU simulation loop: a pre-built SMARTS scenario,
`AgentInterface`/`AgentType`, an `Agent` policy, Gymnasium return values,
controller actions, deterministic scenario iteration, and bounded parallel
execution. The bundled scripts intentionally do not build scenarios, install
packages, launch visualization, or start external traffic services.

## Operating contract

- Run the commands from any directory in the Python environment that has
  SMARTS installed. Verify the install first with
  [`inspect_interfaces.py`](scripts/inspect_interfaces.py).
- Supply an already generated scenario directory to
  [`smoke_env.py`](scripts/smoke_env.py); `--scenario` is mandatory for a
  smoke run, the default configured agent id is `ego`, and the helper uses a
  Laner interface with a run bounded to eight steps. `--self-test` exercises
  parser and active-agent lifecycle logic without importing SMARTS or needing
  a scenario.
- A scenario must contain the generated map/traffic artifacts expected by the
  installed SMARTS version. Ask the `scenario-studio` route to define or build
  one; do not invent a source-checkout-relative path here.
- Use `headless=True` for core checks. Camera/image setup belongs to the
  `sensors-visualization` route. Ray/RLlib, registry packaging, and long
  training belong to `rl-agent-zoo`; public `scl` commands belong to
  `cli-integrations`.

## Fast start

```python
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.env.gymnasium.hiway_env_v1 import HiWayEnvV1

AGENT = "ego"
interface = AgentInterface.from_type(
    AgentType.LanerWithSpeed, max_episode_steps=200
)
env = HiWayEnvV1(
    scenarios=["built-scenario"],
    agent_interfaces={AGENT: interface},
    headless=True,
    seed=42,
)
try:
    observations, infos = env.reset(seed=42)
    while observations:
        actions = {
            agent_id: env.action_space[agent_id].sample()
            for agent_id in observations
        }
        observations, rewards, terminateds, truncateds, infos = env.step(actions)
        if terminateds.get("__all__", False) or truncateds.get("__all__", False):
            break
finally:
    env.close()
```

The default `HiWayEnvV1` formatting is multi-agent: only currently active
agent ids appear in the observation, reward, and policy-action dictionaries.
An empty observation dictionary is a valid intermediate window; keep stepping
with `{}` until `__all__` is true or the caller's own bound is reached. Never
send actions for an id that is not active in the current observation window.

## Choose an interface deliberately

- Start with `AgentInterface.from_type(AgentType.Laner)` for a four-valued
  lane policy, `LanerWithSpeed` for `(target_speed, lane_delta)`, `Standard`
  for waypoint/neighborhood observations with actuator-dynamic control, or
  `StandardWithAbsoluteSteering` for continuous throttle/brake/steering.
- Construct `AgentInterface(...)` when exact sensor parameters or done
  criteria matter. `True` sensor flags resolve to their default dataclass;
  use `Waypoints`, `NeighborhoodVehicles`, `RGB`, `OGM`, and related dataclasses
  for non-default dimensions or ranges.
- `AgentInterface.action` chooses both the expected action shape and the
  controller/chassis path. Match the policy output to `env.action_space[id]`,
  not to a guessed Python type. See
  [`action-observation-reward.md`](references/action-observation-reward.md).
- A policy can subclass `Agent` and implement `act(self, obs, **configs)`, or
  use `Agent.from_function(callable)`. Keep model loading outside `act` when
  possible and make policy output deterministic when reproducibility matters.

## Lifecycle and checks

1. Import `smarts.env.gymnasium` (or `smarts.env`) before using the registered
   Gymnasium id `hiway-v1`; direct `HiWayEnvV1(...)` avoids registration.
2. Inspect `env.observation_space` and `env.action_space` immediately after
   construction. In formatted modes they are Gymnasium `Dict` spaces keyed by
   configured agent id. `space.contains(candidate)` is the quickest mismatch
   test.
3. Call `reset(seed=integer)` once at the start of a reproducible run. A
   subsequent `reset(seed=None)` does not re-seed an existing RNG. SMARTS
   scenario iteration advances on each reset; use `ScenarioOrder.sequential`
   when order, rather than shuffled order, is part of the experiment.
4. Call `step(actions)` only before episode completion, then call `reset()` for
   the next episode. Always call `close()`, including when a policy raises.
   `with HiWayEnvV1(...) as env:` is supported.

## Return-shape essentials

`reset()` returns exactly `(observations, infos)`. In default per-agent mode,
`step()` returns exactly
`(observations, rewards, terminateds, truncateds, infos)`, where all five
values are dictionaries and `terminateds["__all__"]` marks completion of all
configured agents. SMARTS currently mirrors the done dictionary into both
`terminateds` and `truncateds`; treat the two positions separately in caller
code for Gymnasium compatibility. `environment_return_mode="environment"`
changes the middle status to `(float_reward, bool_terminated, bool_truncated,
info)` while observations remain a dictionary. See the full contract in the
bundled references before adapting a third-party vectorizer.

## Parallel route in this skill

`ParallelEnv` takes picklable `env_constructors`, requires all child
observation and action spaces to compare equal, and returns batches as
sequences: `reset()` yields `(observations_batch, infos_batch)` and `step()`
yields five batched sequences. It uses worker processes, seeds worker `i` as
`seed + i`, and can auto-reset completed workers. Close it explicitly; use
small `num_env` values that do not exceed available CPUs.

## References and safe helpers

- [`api-reference.md`](references/api-reference.md) — verified signatures,
  enums, classes, and import surface.
- [`workflows.md`](references/workflows.md) — single/multi-agent, deterministic,
  and parallel recipes.
- [`action-observation-reward.md`](references/action-observation-reward.md) —
  action mappings, formatted spaces, observation fields, rewards, and done
  semantics.
- [`configuration.md`](references/configuration.md) — environment/interface,
  scenario-order, vehicle, controller, and optional-image settings.
- [`troubleshooting.md`](references/troubleshooting.md) — installation,
  optional dependencies, data/configuration, API misuse, and workflow failures.
- [`scripts/inspect_interfaces.py`](scripts/inspect_interfaces.py) — import and
  signature/enum/space inspection without a scenario.
- [`scripts/smoke_env.py`](scripts/smoke_env.py) — explicit-scenario, headless,
  bounded reset/step/close smoke check.

The installed-package verification target for this route is SMARTS 2.0.1 on
Python 3.11 with CPU core dependencies. Rendering, RLlib/Ray, SUMO, ROS,
Waymo, Argoverse, and Visdom are optional integrations and are not implied by
the core smoke check.

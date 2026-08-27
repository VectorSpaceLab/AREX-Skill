# Environment workflows

These recipes assume the scenario directory has already been generated and is
readable by the installed SMARTS package. Scenario definition/build is owned by
the `scenario-studio` route. Use `headless=True` unless an explicit rendering
check is being performed.

## 1. Inspect before running

From any current working directory:

```bash
python skills/disco/smarts/sub-skills/simulation-environments/scripts/inspect_interfaces.py
```

If the skill has been copied elsewhere, invoke the script by its installed
path, or run:

```bash
python -m pip show smarts
python -c 'import smarts, smarts.env.gymnasium; print(smarts.__name__)'
```

The inspection script does not need a scenario and reports the live signatures,
enum members, and representative formatted spaces. Do not infer action shapes
from an old policy or a different SMARTS release.

## 2. Multi-agent HiWayEnvV1 loop

```python
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.env.configs.hiway_env_configs import ScenarioOrder
from smarts.env.gymnasium.hiway_env_v1 import HiWayEnvV1

agent_ids = ["ego-0", "ego-1"]
interfaces = {
    agent_id: AgentInterface.from_type(
        AgentType.Laner, max_episode_steps=100
    )
    for agent_id in agent_ids
}

env = HiWayEnvV1(
    scenarios=["built-scenario"],
    agent_interfaces=interfaces,
    scenarios_order=ScenarioOrder.sequential,
    headless=True,
    seed=7,
)
try:
    observations, infos = env.reset(seed=7)
    for step_index in range(100):
        # The active set, not the configured set, determines this action map.
        actions = {
            agent_id: env.action_space[agent_id].sample()
            for agent_id in observations
        }
        observations, rewards, terminateds, truncateds, infos = env.step(actions)
        if terminateds.get("__all__", False):
            break
finally:
    env.close()
```

A policy should be indexed as `policy.act(observations[agent_id])`. When an
agent has terminated, stop calling its policy and omit its id. If the active
set is empty but `__all__` is false, submit `{}` and continue: another agent
may be scheduled to enter later in the same scenario.

## 3. A real `Agent` policy

```python
from smarts.core.agent import Agent
from smarts.core.agent_interface import AgentInterface, AgentType

class KeepLane(Agent):
    def act(self, obs, **configs):
        return 0  # formatted Lane space: keep_lane

interface = AgentInterface.from_type(AgentType.Laner)
policy = KeepLane()
```

For `LanerWithSpeed`, return `(float(target_speed_mps), int(lane_delta))`.
For a custom policy, inspect its action space during construction and assert
`space.contains(policy.act(observation))` in a debug path. Keep observations
and action formatting consistent: a policy written for unformatted
`Observation` named tuples must not silently receive a formatted nested dict.

`AgentSpec`, locators, registry registration, social agents, and RL adapters
are intentionally not expanded here. Use the `rl-agent-zoo` route when a
policy must be packaged, dynamically loaded, or trained.

## 4. Single-agent Gymnasium wrapper

SMARTS remains multi-agent internally. Wrap exactly one configured agent when a
consumer requires scalar Gymnasium values:

```python
import gymnasium as gym
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.env.gymnasium.wrappers.single_agent import SingleAgent

base = gym.make(
    "smarts.env:hiway-v1",
    scenarios=["built-scenario"],
    agent_interfaces={"ego": AgentInterface.from_type(AgentType.Laner)},
    headless=True,
)
env = SingleAgent(base)
try:
    obs, info = env.reset(seed=11)
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
finally:
    env.close()
```

`SingleAgent` asserts that there is exactly one configured id. Its reset
returns that agent's `(observation, info)` and its step returns that agent's
`(observation, float reward, bool terminated, bool truncated, info)`. Do not
wrap a multi-agent environment containing two or more ids.

## 5. Deterministic scenario iteration

Set the same integer at construction and the first reset. For a deterministic
policy, repeated runs use the same SMARTS simulation trajectory. Use
`ScenarioOrder.sequential` to make the supplied scenario/variation order
observable; the default is `ScenarioOrder.scrambled`. Each reset advances the
scenario iterator, including traffic/map combinations discovered from a
scenario's generated traffic data. A later reset with `seed=None` is not a
request to restart the random stream.

A practical reproducibility record should include:

- SMARTS distribution version and Python version;
- integer seed and `fixed_timestep_sec`;
- scenario list and order mode;
- agent ids, interface preset/overrides, and policy version;
- action/observation formatting options;
- scenario log and bounded step count.

## 6. Parallel worker environments

`ParallelEnv` is process-based, not a thread wrapper. Define constructors at
module scope or use a picklable `functools.partial`:

```python
from functools import partial
import gymnasium as gym
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.env.gymnasium.wrappers.parallel_env import ParallelEnv

interfaces = {"ego": AgentInterface.from_type(AgentType.Laner)}

def make_env(seed, scenario):
    return gym.make(
        "smarts.env:hiway-v1",
        scenarios=[scenario], agent_interfaces=interfaces,
        headless=True, seed=seed,
    )

workers = ParallelEnv(
    [partial(make_env, scenario="built-scenario") for _ in range(2)],
    auto_reset=True,
    seed=100,
)
try:
    batch_obs, batch_info = workers.reset()
    batch_actions = [
        {agent_id: workers.action_space[agent_id].sample() for agent_id in obs}
        for obs in batch_obs
    ]
    batch_obs, batch_rewards, batch_terms, batch_truncs, batch_infos = workers.step(
        batch_actions
    )
finally:
    workers.close()
```

All child spaces must compare equal. With `auto_reset=True`, a worker resets
itself after its `__all__` termination and the returned terminal `info` retains
its final observation under the agent info entry. With `auto_reset=False`, do
not keep stepping a finished worker as though it were a new episode; reset all
workers explicitly according to the caller's synchronization policy. Worker
seed `100 + i` is observable through `workers.seed()`.

## 7. Empty active-agent windows

A scheduled multi-agent scenario can have configured agents whose missions
start or finish at different times. The sequence can be:

```text
reset -> {"early": obs}
step  -> {}
step  -> {"late": obs}
```

The empty dictionary is not proof of episode completion. Check
`terminateds.get("__all__", False)` and `truncateds.get("__all__", False)`.
The difficult synthetic test for this route should assert that a policy is not
called during the empty window, `{}` is accepted by `step`, and a later active
agent is still serviced.

## 8. Close and failure-safe operation

Use `try/finally` around every environment and worker pool. A failed policy or
space assertion must still call `close()`. Do not use process termination as a
normal reset strategy; reserve `ParallelEnv.close(terminate=True)` for a worker
that cannot respond during cleanup. Rendering windows, Envision connections,
and external traffic services are separate lifecycle concerns and are not
started by these recipes.

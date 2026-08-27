# Agent, AgentSpec, and registry

## Policy contract

A SMARTS policy is an instance of `smarts.core.agent.Agent`. Its required
method is:

```python
def act(self, obs, **configs):
    ...
```

`obs` is the adapted observation selected by the `AgentInterface`; the return
value is a raw SMARTS action for that interface. The base class also provides
`Agent.from_function(callable)` for a small stateless policy. The callable
receives one observation and must return an action. A policy can load a model
in `__init__`, but that model and its constructor arguments must be usable in
the target process and serializable if workers will construct it.

Do not infer an action from the class name. `AgentType.Laner`, for example,
uses a discrete lane action, while `AgentType.LanerWithSpeed` uses a speed/lane
pair. Inspect the actual interface and environment space.

## AgentSpec fields and verified signatures

The current installed SMARTS package exposes these call shapes:

```text
AgentSpec(interface=None, agent_builder=None, agent_params=None,
          observation_adapter=<identity>, action_adapter=<identity>,
          reward_adapter=<identity>, info_adapter=<identity>)
AgentSpec.build_agent(self) -> Agent
register(locator: str, entry_point, **kwargs)
make(locator: str, **kwargs) -> AgentSpec
make_agent(locator: str, **kwargs) -> (Agent, AgentInterface)
```

`AgentSpec` is a dataclass and cloudpickle-checks itself during construction.
The important fields are:

| Field | Runtime meaning |
|---|---|
| `interface` | Required for an environment-facing agent; selects sensors and action type. It may be `None` for a reusable spec that will be completed later. |
| `agent_builder` | Callable/class used by `build_agent`; pass the class or factory, not an instance. |
| `agent_params` | `None`, positional list/tuple, keyword dict, or one value forwarded to the builder. |
| `observation_adapter` | Legacy compatibility adapter; the current core interface is preferred for observation shaping. |
| `action_adapter` | Legacy compatibility adapter; if retained for an RL integration, it must produce the simulator action expected after model output. |
| `reward_adapter` | Legacy reward shaping hook. |
| `info_adapter` | Legacy info shaping hook. |

A dict of params is filtered to the builder's named parameters when the builder
does not accept `**kwargs`; unexpected keys are therefore not a reliable way
to detect a typo. Prefer a small explicit builder and validate its inputs.

Minimal pattern:

```python
from smarts.core.agent import Agent
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.zoo.agent_spec import AgentSpec
from smarts.zoo.registry import register

class KeepLane(Agent):
    def act(self, obs, **configs):
        return "keep_lane"  # correct only for a lane action interface

def entry_point(max_episode_steps=500, **kwargs):
    return AgentSpec(
        interface=AgentInterface.from_type(
            AgentType.Laner, max_episode_steps=max_episode_steps
        ),
        agent_builder=KeepLane,
    )

register("keep-lane-example-v0", entry_point)
```

The action comment is intentional: replace it with the action appropriate to
the selected interface. Before a run, inspect `env.action_space[agent_id]` and
call `contains` on a representative action.

## Locator grammar and import behavior

The registry validates names against the grammar equivalent to:

```text
^(optional-prefix/)?name-(v<integer>|latest)$
```

The public form should be:

```text
importable.python.module:registered-name-vN
```

The module part may be omitted only when the name is already in the process's
registry. The colon separates the module and registered key. The version is
not metadata separate from the key: `register("policy-v0", ...)` and
`make("module:policy-v0")` must match exactly. `policy` or `policy-v1` will
not find `policy-v0`.

`make` splits the locator at the colon. With a module component it imports
that module first, so module import side effects must register the key. It then
looks up the key in a process-global registry and calls the entry point. A
missing module produces an import error with PYTHONPATH guidance; an imported
module with no matching registration produces `NameError: Locator not
registered in lookup`.

Recommended validation order:

1. Use the target interpreter to `import your_package.module`.
2. Run the bundled locator checker with the exact locator.
3. Use `registry.make(locator, **kwargs)` and inspect `spec.interface`.
4. Use `registry.make_agent(locator, **kwargs)` only after the constructor and
   model path are safe to instantiate.

The checker reports import failure separately from missing name/version. It
never calls the entry point, so a successful registry lookup does not prove
that a model can load or that a policy action is valid.

## Package and registry layout

An installable inference package normally has a package module that imports
its policy, defines an entry point, creates an `AgentSpec`, and calls
`register("your-agent-v0", entry_point)`. Its distribution metadata should
pin the policy's own runtime dependencies. Do not add SMARTS as a package
requirement when following the benchmark template; SMARTS is the host runtime.
The host must still be installed separately.

Keep the locator stable for a compatible interface and model contract. Register
a new `-vN` when observation/action semantics or required model files change;
do not silently overwrite an incompatible registration. Registry registration
warns when a key is overwritten in the same process.

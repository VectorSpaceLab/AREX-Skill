# Tool and prompt customization workflows

Keep extension work separate from provider/executor setup. Start with the
minimal `@tool` route; use a package or subclass only when it solves a real
composition problem. The complete `ROSA` constructor and model/tool-calling
requirements belong to [agent-core](../../agent-core/SKILL.md).

## 1. Add one deterministic tool

Define an explicit, typed, documented LangChain tool. The return value should
be JSON-like and deterministic where practical:

```python
from typing import Optional
from langchain.agents import tool

@tool
def bounded_distance(x1: float, y1: float, x2: float, y2: float,
                      blacklist: Optional[list[str]] = None) -> dict:
    """Return a planned 2-D distance; never moves a robot."""
    # Validate bounds and units in a real adaptation.
    dx, dy = x2 - x1, y2 - y1
    return {"distance": (dx * dx + dy * dy) ** 0.5,
            "units": "caller-defined", "blacklist_seen": blacklist or []}
```

Then hand the tool object to `ROSA(..., tools=[bounded_distance])`. Do not pass
the undecorated Python function. Keep action authorization out of a
calculation helper: a tool that publishes, calls a service, launches a node,
or stops a node needs an explicit allowlist, validated target, bounded payload,
confirmation policy, and sequential execution plan. Route live ROS details to
the relevant sibling skill.

Before constructing an agent, inspect the object without middleware:

```python
assert bounded_distance.name == "bounded_distance"
assert hasattr(bounded_distance, "func")
print(bounded_distance.args_schema)
print(bounded_distance.invoke({"x1": 0, "y1": 0, "x2": 3, "y2": 4}))
```

The bundled `scripts/custom_tool_template.py` provides a safe, executable
version of this inspection recipe.

## 2. Add a package of tools

Put several decorated tools in an importable Python module/package and pass
that module in `tool_packages=[my_tool_package]`. ROSA scans public attributes
using `dir()`, so:

- decorate every intended function with `@tool`;
- give every tool a useful docstring and typed parameters;
- keep helper functions private (`_helper`) or in a private import module so
  they are not accidentally scanned;
- expose no unrelated object that happens to have both `name` and `func`;
- inspect names and schemas before agent construction;
- avoid relying on package import side effects, live ROS initialization, or
  network calls merely to enumerate tools.

`ROSA` adds the built-in calculation/log/system tools and selected ROS-family
tools first, then custom individual tools and packages. There is no duplicate
name resolution or overwrite guarantee, so choose unique names and fail a
preflight check on collisions. A plain function in a package is silently
ignored by the scanner because it lacks tool metadata.

The direct `ROSATools` route is useful for inspection or application-owned
composition:

```python
from rosa.tools import ROSATools
collection = ROSATools(ros_version=1, blacklist=["/unsafe_target"])
collection.add_tools([bounded_distance])
collection.add_packages([my_tool_package])
for item in collection.get_tools():
    print(item.name, item.args_schema)
```

This still imports the selected ROS family. If middleware imports are not
available, inspect base modules or use the safe template instead of claiming
that the full collection initialized.

## 3. Configure blacklist-aware tools

Use `ROSA(..., blacklist=[...])` for a stable default blacklist. ROSA's
`ROSATools` wraps only tools whose underlying code visibly has a `blacklist`
variable. The wrapper inserts the default when absent and prepends it to a
caller-supplied list. It does not deduplicate and does not automatically apply
the list to every custom tool.

The intended pattern is a tool that accepts and actually honors the value:

```python
@tool
def list_safe_targets(blacklist: Optional[list[str]] = None) -> list[str]:
    """List known targets except configured blacklist entries."""
    candidates = ["sensor_a", "sensor_b"]  # bounded fixture, not live ROS
    blocked = set(blacklist or [])
    return [name for name in candidates if name not in blocked]
```

Test both direct invocation and the LangChain dictionary invocation shape.
Remember that injection mutates a dictionary argument in place and may mutate
the supplied tool object's `.func`. Do not use a mutable injected list as
per-request state. A blacklist is a filter/guardrail, not a substitute for
checking a target's type, namespace, authorization, or side effects.

The `add_packages(..., blacklist=...)` parameter is misleading in v1.0.10:
the scan helper does not consume it. Put the effective list on the original
`ROSA`/`ROSATools` construction, and verify the resulting function signature
and a representative call. Never claim that a blacklist hides a tool itself
unless the application separately filters tool names.

## 4. Compose robot-specific prompts and guardrails

Create a fresh `RobotSystemPrompts` and fill only the fields that are useful:

```python
from rosa.prompts import RobotSystemPrompts

robot_prompts = RobotSystemPrompts(
    embodiment_and_persona="You are the inspection assistant for Rover A.",
    critical_instructions=(
        "Before any action, discover the current graph and verify the target."
    ),
    constraints_and_guardrails=(
        "Never launch arbitrary commands; never move without explicit approval."
    ),
    about_your_environment="Coordinates are metres in the rover/base frame.",
    mission_and_objectives="Prefer bounded observation and explain uncertainty.",
)
message = robot_prompts.as_message()
assert message[0] == "system"
agent = ROSA(ros_version=1, llm=llm, prompts=robot_prompts)
```

Prompt content is an instruction to the model, not an authorization mechanism.
Keep secrets, API keys, raw environment dumps, untrusted log text, and
user-controlled prompt fragments out of these fields. Put physical limits,
units, frames, required confirmations, discovery-first sequencing, and
failure behavior in explicit guardrails. A tool must enforce its own safety
bounds; a prompt cannot make an unsafe tool safe.

In v1.0.10, `_get_prompts` appends a custom message to the module-level
`system_prompts` list. Avoid modifying that list directly. If multiple agents
with different prompts share a process, isolate construction or use an
application-owned subclass/patch that copies the defaults before appending,
then regression-test that one instance's prompt is absent from the next.

## 5. Design an action tool safely

For a live robot adaptation, use this order:

1. **Discover** available nodes/topics/services in the selected ROS family;
   never accept a guessed entity name.
2. **Inspect** type, namespace, limits, and current state. For services,
   obtain the service type before constructing a request.
3. **Plan** with deterministic geometry tools, preserving frame and unit
   metadata. Return a dry-run plan before mutation.
4. **Authorize** the exact target, operation, bounds, and confirmation policy.
5. **Execute one call at a time**, with a timeout and an observable result.
6. **Verify** post-state and report errors without retrying a potentially
   destructive action blindly.

Allowlist operations and targets; reject arbitrary shell strings, unbounded
coordinates, unrestricted file paths, secrets, and command fragments. Keep
ROS 2 service/request quoting out of generic custom tools unless the route has
validated it. The custom tool template intentionally stops at a pure result;
it never launches, publishes, calls, kills, or writes.

## 6. Optional protected-method/subclass route

Use composition first. When an application must change construction policy,
ROSA v1.0.10 exposes protected hooks that the constructor calls:
`_get_tools`, `_get_prompts`, `_get_agent`, and `_get_executor`. A subclass can
copy defaults, enforce a tool allowlist, or supply an application-owned prompt
assembly, but it must preserve the public constructor's `ros_version`, model,
tool, package, prompt, blacklist, streaming, iteration, and history semantics.

A subclass should:

- call `super()` or reproduce only the narrowly required contract;
- keep selected ROS-family initialization explicit;
- maintain tool schemas and unique names;
- avoid arbitrary executor changes that bypass sequential/safety controls;
- add tests for prompt isolation, blacklist behavior, errors, and tool ordering;
- document the version coupling, since protected hooks are an adaptation seam,
  not a stable independent plugin ABI.

Do not override provider lifecycle or invent a parallel executor here; route
that work to `agent-core`.

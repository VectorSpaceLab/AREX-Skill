---
name: tool-customization
description: "Extend ROSA with safe LangChain tools, tool packages,
  blacklist-aware filtering, robot-specific prompts, deterministic utilities,
  and bounded robot adaptations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ROSA tool customization

Use this route when a task adds an `@tool`, passes `tools` or
`tool_packages`, needs a ROS-tool blacklist, defines a robot persona or
guardrails, uses ROSA's math/log/system utilities, or considers a safe
subclass/adaptation. This is an extension and inspection route, not an
executor or provider lifecycle route.

## Route and boundaries

1. Read [api-reference.md](references/api-reference.md) for the exact
   `ROSATools`, blacklist-injection, prompt, and constructor handoff contracts.
2. Use [tool-catalog.md](references/tool-catalog.md) before choosing an
   existing deterministic tool; record units and undefined/error cases.
3. Follow [workflows.md](references/workflows.md) for individual tools,
   packages, prompts, and bounded action-tool design.
4. Diagnose failures with [troubleshooting.md](references/troubleshooting.md).
5. For model configuration, invocation, streaming, history, and executor
   behavior, route to [agent-core](../agent-core/SKILL.md).
6. For live ROS 1 or ROS 2 tools, discovery, middleware, and action safety,
   route to [ros1-operations](../ros1-operations/SKILL.md) or
   [ros2-operations](../ros2-operations/SKILL.md). Do not reproduce their
   exhaustive API catalogs here.

The public extension point is a LangChain tool object: a decorated function
with tool metadata (`name`, `func`, and a generated argument schema). A plain
function is not enough for ROSA's package scanner. Keep custom tools
self-contained, deterministic where possible, bounded, and explicit about
side effects. A plan/calculation tool should be separate from a tool that can
move or mutate a robot. Never put arbitrary shell execution, credential
handling, network access, or live robot launches in this route's bundled
helper.

## ROS-version boundary

`ROSA` always builds `ROSATools` for the selected `ros_version`, so a normal
agent construction also imports the selected ROS-family module. The tools
package first adds the base calculation, log, and system modules and then
imports only `rosa.tools.ros1` for ROS 1 or only `rosa.tools.ros2` for ROS 2;
it does not intentionally import both families. Consequently, base
`rosa.tools.calculation`, `rosa.tools.log`, and `rosa.tools.system` can be
imported and inspected without middleware, while `ROSATools(1)` or
`ROSATools(2)` can still fail if the selected ROS Python/runtime dependency is
absent. Treat middleware availability as a separate prerequisite; do not
paper over it by selecting the other ROS version.

## Quick selection

| Need | Use | Important check |
|---|---|---|
| One pure helper | `@tool` plus `ROSA(..., tools=[...])` | Typed signature and docstring produce a useful schema |
| Several helpers | A module/package plus `tool_packages=[...]` | Public attributes must be decorated tools |
| Hide selected ROS results | `blacklist=[...]` | Only blacklist-aware tools consume the injected list |
| Robot persona/constraints | A fresh `RobotSystemPrompts` | Keep secrets and untrusted instructions out |
| Existing math/log/debug behavior | Built-in catalog | Validate domain, size, global-state, and wait limits |
| Deep construction override | Protected ROSA methods/subclass | Preserve constructor and executor safety; see `workflows.md` |

The safe template at [scripts/custom_tool_template.py](scripts/custom_tool_template.py)
prints its schema and a deterministic result by default. It imports no ROS,
LLM, network, credential, or filesystem functionality.

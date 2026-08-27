---
name: ros2-operations
description: "Route ROS 2 CLI-backed graph inspection, bounded
  topic/service/parameter actions, doctor checks, and log inspection through
  ROSA."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ROS 2 operations

Use this route when the task concerns ROS 2 (including Humble, Iron, or Jazzy),
`ros2 node`, `ros2 topic`, `ros2 service`, `ros2 param`, `ros2 doctor`, DDS or
domain discovery, or ROS 2 command and daemon errors.

This sub-skill describes ROSA's ROS 2 tools, not a general-purpose shell
interface. Read the focused contracts before choosing a tool:

- [API reference](references/api-reference.md) — arguments, command shapes,
  filtering, return values, and failure values.
- [Workflows](references/workflows.md) — source the intended distro, discover
  before acting, and keep operations bounded and sequential.
- [Troubleshooting](references/troubleshooting.md) — dependency, discovery,
  quoting, timeout, parser, and log failures.

## Route boundaries

- For constructing or invoking `ROSA(ros_version=2, ...)`, model/tool-calling
  setup, or general agent behavior, use the parent [agent-core](../agent-core/SKILL.md).
- For ROS 1/Noetic APIs such as `rosnode` or `rostopic`, use the sibling
  [ros1-operations](../ros1-operations/SKILL.md). Do not translate a ROS 1
  command into this route by guesswork.
- For blacklists, deterministic math, custom LangChain tools, or robot-specific
  prompts, use [tool-customization](../tool-customization/SKILL.md).
- For shared installation and runtime prerequisites, start at the parent
  [ROSA route](../../SKILL.md).

## Operating rules

1. Establish which ROS 2 distro and shell environment are intended. ROSA does
   not source a distro for the caller.
2. Use `ros2_doctor()` and the relevant list tool to observe the current graph;
   never invent node, topic, service, or parameter names.
3. List before `info`/`echo`/`call`, get a parameter before setting it, and
   inspect a service type before calling it. Run tool calls one at a time and
   wait for each result.
4. Keep topic echo bounded (`count` 1–10) and treat service calls and parameter
   writes as potentially state-changing operations requiring an explicit,
   validated target and request.
5. Treat every value interpolated into a ROS 2 command as untrusted input. The
   helper checks only the first command categories, then invokes
   `subprocess.check_output(..., shell=True)`. It must not be used for arbitrary
   command execution: the shallow category check does not block shell syntax
   after an accepted prefix. Validate names, options, type tokens, and request
   YAML; reject shell metacharacters and never suggest an arbitrary launcher.
6. Distinguish mocked wrapper tests from live middleware observations. The
   construction host has neither `rclpy` nor the `ros2` executable, so this
   route does not claim live ROS 2 verification.

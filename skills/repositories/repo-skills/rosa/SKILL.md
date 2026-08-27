---
name: rosa
description: "Route ROSA LangChain agent construction, ROS 1 and ROS 2
  operations, custom tool integration, and safe troubleshooting for jpl-rosa."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ROSA repository skill

Use this skill when a task names ROSA, `jpl-rosa`, `from rosa import ROSA`,
LangChain tool-calling agents for ROS, `ros_version`, ROSA tools, or the ROSA
TurtleSim-style agent pattern. It is a self-contained operating guide for the
public package; it does not require the original repository checkout.

## Route the request

- **Construct, configure, invoke, stream, or debug the agent:** read
  [agent-core](sub-skills/agent-core/SKILL.md).
- **ROS 1 / Noetic graph, topics, nodes, services, parameters, packages, logs,
  launch, or kill:** read [ros1-operations](sub-skills/ros1-operations/SKILL.md).
- **ROS 2 / Humble, Iron, or Jazzy CLI-backed graph, topics, services,
  parameters, doctor, or logs:** read
  [ros2-operations](sub-skills/ros2-operations/SKILL.md).
- **Custom LangChain tools or packages, blacklists, robot prompts, math,
  logging, or safe adaptation:** read
  [tool-customization](sub-skills/tool-customization/SKILL.md).

Start with the route matching the user's primary action, then follow its
cross-links instead of loading every reference. Read
[runtime prerequisites](references/runtime-prerequisites.md) and
[troubleshooting](references/troubleshooting.md) when environment boundaries
or failures are involved. The spaces in the first link are intentional
Markdown-label syntax; the target remains inside this skill tree.

## Package boundary and minimal check

The public distribution is `jpl-rosa` and the import package is `rosa`.
Install it in Python `>=3.9,<4`:

```bash
python -m pip install jpl-rosa
python -c "from rosa import ROSA, RobotSystemPrompts, ChatModel; print('rosa import ok')"
```

The base package includes LangChain OpenAI integration. Install only the
provider extra needed by the selected workflow, for example
`jpl-rosa[anthropic]` or `jpl-rosa[ollama]`. Package installation does **not**
install ROS 1/ROS 2 middleware, a ROS master/daemon, a DDS graph, an LLM
service, credentials, Docker, or a display server. Use the safe
[environment checker](scripts/check_environment.py) before constructing a live
agent; it never contacts a model or ROS system unless an explicit ROS check is
requested.

## Safe operating rules

1. Select `ros_version=1` or `2` from the user's actual middleware; never mix
   the ROS 1 and ROS 2 tool catalogs.
2. For action requests, discover current nodes and topics first, then inspect
   the exact service/topic/parameter/package before acting.
3. Execute one tool call at a time. Do not batch movement, drawing, service,
   launch, kill, or parameter operations.
4. Treat service calls, parameter writes, launches, and node kills as mutations;
   state the target and expected effect before execution.
5. Use the package's calculation tools for angles, distances, coordinates, and
   geometry rather than doing robotics arithmetic manually.
6. Keep API keys and private robot details out of prompts, logs, source files,
   and generated reports.

## Provenance and limits

Read [repo-provenance.md](references/repo-provenance.md) before deciding whether
this skill matches a changed ROSA checkout. Read the shared troubleshooting
reference for install/import, provider, middleware, input-validation, and demo
limitations. ROSA's Docker/X11 TurtleSim demo is intentionally documented as a
bounded optional integration; this skill does not launch it automatically.

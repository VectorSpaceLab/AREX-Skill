---
name: ros1-operations
description: "Inspect ROS 1 Noetic-or-newer graphs and perform bounded ROSA
  node, topic, service, parameter, package, log, launch, and node actions with
  discovery-first safety."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ROS 1 Operations

Use this sub-skill when the task concerns ROS 1/Noetic-or-newer, the ROS master,
`rosnode`, `rostopic`, `rosservice`, `rosparam`, ROS package or launch files,
ROS logs, or ROS 1 middleware errors. It describes ROSA's package-level tools;
it is not a shell-command recipe and must not be treated as a substitute for a
sourced ROS installation.

## Scope and prerequisites

- ROSA must be constructed for ROS 1 (for example, the parent agent's
  `ROSA(ros_version=1, ...)` path). See [agent-core](../agent-core/SKILL.md)
  for constructor, provider, executor, and runtime setup.
- A compatible ROS 1 Python environment must provide the imported ROS modules
  (`rosgraph`, `rospy`, `rosnode`, `rosparam`, `rospkg`, `rosservice`,
  `rostopic`, and `rosmsg`) and a reachable ROS master for live graph work.
  Without those prerequisites, report the middleware/import failure; do not
  infer that the graph is empty.
- Start with discovery. Never invent a node, topic, service, package, launch
  file, parameter, or log path. Use the returned names in later calls.
- Execute exactly one ROSA tool call at a time and wait for its result before
  selecting the next call. Do not parallelize inspection or actions.
- Treat `rosservice_call`, `rosparam_set`, `roslaunch`, and `rosnode_kill` as
  potentially mutating. Explain the target and expected side effect and obtain
  confirmation before an action when the user has not already given clear
  authorization. `roslaunch` and `rosnode_kill` are especially high risk.

## Operating procedure

1. Classify the request as graph inspection, bounded observation, read-only
   metadata lookup, or mutation.
2. For an action request, first call `rosnode_list` and `rostopic_list` with
   their defaults unless a specific, already-known non-root namespace is the
   task. For a service action, also call `rosservice_list`. These calls establish
   current availability; they do not prove a ROS master exists if they return an
   error.
3. Select only names present in the latest result. Before `rostopic_echo`,
   `rosservice_call`, `rosparam_set`, `roslaunch`, or `rosnode_kill`, inspect
   the selected entity or package with the corresponding info/list tool. For
   services, inspect service metadata and the service type before constructing
   arguments. For a launch, enumerate package launch files first.
4. Apply narrow pattern, namespace, and blacklist filters when an unfiltered
   list is too large. Use `rosgraph_get` for connected publisher-topic-
   subscriber relationships, never as a general node/topic list API.
5. Bound observations: keep topic echo counts in the documented 1--100 range,
   use a finite timeout, and avoid returning large message payloads. For logs,
   discover directories/files before reading a bounded recent slice.
6. After a mutation, report the exact tool result. Re-list or re-inspect when
   the result needs confirmation; do not claim a launch, kill, parameter write,
   or service effect from intent alone.

## API and failure details

- Read [api-reference.md](references/api-reference.md) for exact tool inputs,
  defaults, filtering semantics, and response shapes.
- Read [workflows.md](references/workflows.md) for entity discovery, graph,
  service, parameter, package, launch, log, and sequential-action workflows.
- Read [troubleshooting.md](references/troubleshooting.md) for missing modules
  or master, empty graphs, namespace/regex behavior, bounded output limits,
  service arguments, launch risks, blacklist effects, and kill confirmation.

## Boundaries and related skills

- This skill covers ROS 1 APIs in `rosa.tools.ros1` plus the shared ROSA
  `read_log` behavior needed to consume discovered logs. It does not cover ROS
  2 CLI-backed APIs; route ROS 2 requests to
  [ros2-operations](../ros2-operations/SKILL.md).
- It does not cover generic ROSA construction, model/provider setup, executor
  lifecycle, or package installation; route those to
  [agent-core](../agent-core/SKILL.md).
- It does not teach custom tool registration, prompt customization, or general
  blacklist injection; route those to
  [tool-customization](../tool-customization/SKILL.md).
- The parent router and shared prerequisites are in
  [rosa](../../SKILL.md). No source checkout, demo script, Docker/X11 setup, or
  live ROS script is a runtime dependency of this sub-skill.

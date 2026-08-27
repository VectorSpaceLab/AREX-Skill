---
name: agents-and-societies
description: "Build CAMEL ChatAgent workflows, BaseMessage setup, role-playing
  societies, Workforce orchestration, Task objects, and safe agent-loop
  debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Agents and Societies

Use this sub-skill when the user needs to assemble CAMEL-AI agents or multi-agent workflows: `ChatAgent` setup, system messages, tool-enabled agents at a routing level, `RolePlaying` societies, `Workforce` orchestration, `Task` objects, response terminators, callbacks, memory hooks, and loop debugging.

## Start Here

1. Read [references/api-reference.md](references/api-reference.md) to choose the right CAMEL classes and constructor options.
2. Read [references/workflows.md](references/workflows.md) for practical recipes: single agent, role-playing society, workforce, pipeline mode, and CI dry-run validation.
3. Run [scripts/inspect_agent_basics.py](scripts/inspect_agent_basics.py) to inspect installed CAMEL imports, signatures, message constructors, and dry-run object setup without model credentials.
4. Read [references/troubleshooting.md](references/troubleshooting.md) before debugging loops, missing API keys, termination, timeouts, callbacks, memory state, or task failures.

## Route By Task

- **Single conversational agent**: use `ChatAgent` with a string or `BaseMessage` system message, optional memory/window/token controls, and optional response terminators.
- **Message construction**: use `BaseMessage.make_system_message`, `make_assistant_message`, and `make_user_message` for explicit roles, metadata, and multimodal attachments.
- **Tool-enabled agent design**: attach `tools`, `external_tools`, timeouts, and masking at `ChatAgent` construction, then defer schema/toolkit details to `../tools-runtimes-and-services/`.
- **Two-role society**: use `RolePlaying` when an AI user and AI assistant should alternate turns, optionally with task specification, task planning, a critic, or pre-built `ChatAgent` instances.
- **Team orchestration**: use `Workforce` when tasks need decomposition, assignment to workers, failure recovery, streaming callbacks, shared memory, or pipeline-mode dependencies.
- **Task state and decomposition**: use `Task` for structured objectives, subtasks, dependencies, result propagation, and Workforce entry points.

## Boundaries And Cross-Links

- For provider credentials, `ModelFactory`, `BaseModelBackend`, model enums, and backend-specific configuration, use `../models-and-configuration/`.
- For `FunctionTool`, `MCPToolkit`, schema synthesis, sandboxed execution, and external services, use `../tools-runtimes-and-services/`.
- For `ChatHistoryMemory`, retrieval-backed memory, vector stores, and embedding internals, use `../memory-rag-and-data/`.
- For benchmark/data-generation recipes, use the sibling benchmark or datagen sub-skill if present; this sub-skill only covers agent workflow routing.

## Safety Defaults

- Prefer credential-free dry runs first: instantiate messages, tasks, agents with explicit local/dummy model planning, and inspect signatures before calling `.step()`.
- Always bound loops with `max_iteration`, `response_terminators`, role-play turn limits, or `task_timeout_seconds` before running in CI.
- Keep tool execution bounded with `tool_execution_timeout`, `mask_tool_output`, and targeted tools; route tool schema failures to the tools sub-skill.
- Treat `share_memory=True`, custom memory, and callbacks as workflow state surfaces that require explicit reset and logging plans.

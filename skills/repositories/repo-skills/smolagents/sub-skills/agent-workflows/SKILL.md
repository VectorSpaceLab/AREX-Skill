---
name: agent-workflows
description: "Build, configure, run, stream, serialize, load, and debug
  smolagents CodeAgent, ToolCallingAgent, MultiStepAgent, managed-agent, memory,
  planning, final-answer-check, and prompt-template workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Agent Workflows

Use this sub-skill when the task is to create or debug a smolagents agent workflow: choosing `CodeAgent` vs `ToolCallingAgent`, configuring `MultiStepAgent.run()`, composing managed agents, enabling planning, inspecting memory, validating final answers, streaming steps, or saving/loading agents.

## Route First

- Use `CodeAgent` when the model should write Python actions and you want stateful code execution through the Python executor.
- Use `ToolCallingAgent` when the model natively emits tool calls and you want JSON-like tool invocation, including parallel tool calls controlled by `max_tool_threads`.
- Use managed agents when a manager should delegate a subtask to a specialized `CodeAgent` or `ToolCallingAgent`; every managed agent must have `name` and `description`.
- Use `run(..., return_full_result=True)` or initialize with `return_full_result=True` when the caller needs output, token usage, timing, state, and serialized memory steps.
- Use memory, callbacks, and planning recipes in `references/planning-and-memory.md` for run inspection, `reset=False`, planning customization, or step-level intervention.

## Boundaries

- For custom tools, MCP tools, Hub tools, or tool authoring, route to `tools-and-integrations`.
- For model classes, provider credentials, inference parameters, and local model backends, route to `model-providers`.
- For `executor_type`, remote executor setup, import authorization, and sandbox/security trade-offs, route to `execution-and-safety`.
- For `smolagent`, `webagent`, Gradio UI, or wrapper entry points, route to `cli-and-ui`.

## Core References

- Start with `references/api-reference.md` for constructor parameters, run options, return values, and serialization APIs.
- Use `references/workflows.md` for concrete workflow recipes: single agents, managed agents, streaming, final-answer checks, and save/load.
- Use `references/planning-and-memory.md` for `planning_interval`, prompt template customization, callbacks, memory inspection, replay, and resume.
- Use `references/troubleshooting.md` for final-answer, parsing, imports, max-steps, prompt template, managed-agent, serialization, and memory issues.

## Bundled Script

- `scripts/inspect_agent_run.py` runs a deterministic no-network `CodeAgent` smoke workflow with a fake model, optional streaming, full-result output, and memory summaries. Run `python scripts/inspect_agent_run.py --help` for options.

---
name: agents-workflows
description: "Guides SuperAGI agent creation, workflow selection, prompt
  parsing, task queues, scheduling, and Celery execution loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SuperAGI Agents and Workflows

Use this sub-skill when the task is about how SuperAGI agents are prompted,
selected, queued, scheduled, executed, paused, resumed, or advanced through
workflow steps.

## Read First

- [references/workflows.md](references/workflows.md) for workflow types, seed
  names, and execution flow.
- [references/prompt-and-output-parsing.md](references/prompt-and-output-parsing.md)
  for prompt builders, parser signatures, and output-shape expectations.
- [references/execution-loop.md](references/execution-loop.md) for the agent,
  job, and Celery loop from config to execution step.
- [references/troubleshooting.md](references/troubleshooting.md) for parser,
  tool-selection, queue, permission, and scheduling failures.
- [scripts/validate_agent_payload.py](scripts/validate_agent_payload.py) for a
  safe structural check of agent/run payloads.

## Core Concepts

- **Goal-based workflow:** a single-step prompt loop that keeps selecting the
  next tool until completion.
- **Dynamic task workflow:** a task-analysis and task-prioritization loop that
  revisits the task queue.
- **Fixed task workflow:** a task queue that follows a fixed schedule of
  initialization and queue steps.
- **Tool workflow steps:** tool steps, wait steps, task-queue steps, and
  permission-gated steps are all represented in the workflow models.
- **Execution loop:** `superagi.worker` and `superagi.jobs.agent_executor`
  coordinate scheduled agents, waiting workflows, resource summaries, and
  webhook callbacks.

## Typical Questions This Sub-skill Answers

- Which workflow name should I assign to an agent template?
- Why did the agent choose the wrong tool or produce invalid JSON?
- Why is a task queue empty, repeated, or not advancing?
- How do permission checkpoints and wait steps change execution?
- Which Celery task or workflow seed owns a given behavior?

## Safe Workflow

1. Route by workflow family: agent templates and workflow names belong here,
   not in API or toolkit sub-skills.
2. Read prompt and parser references before changing or validating outputs.
3. If the user provides a payload, use the validator script for a structural
   check before thinking about execution.
4. For real execution, remember that workflow code depends on Redis, a database,
   and in many cases an LLM provider. Only run live execution when authorized.

## Boundary Notes

- HTTP route and model schema questions belong to `api-service`.
- Tool implementation and toolkit registration belong to `toolkits-integrations`.
- Provider, resource, and vector-store setup that a workflow merely consumes
  belongs to `models-resources-vector`.

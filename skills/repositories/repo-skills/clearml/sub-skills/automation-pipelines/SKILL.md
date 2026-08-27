---
name: automation-pipelines
description: "Build and debug ClearML automation workflows with
  PipelineController, PipelineDecorator, HPO, schedulers, triggers, and
  clearml-param-search."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearML Automation Pipelines

Use this sub-skill when an agent needs to create or troubleshoot ClearML automation workflows: pipeline DAGs, decorated function pipelines, hyperparameter search, recurring schedules, event triggers, and automation controller/service tasks.

## Read First

- [API reference](references/api-reference.md) lists the verified automation classes, important signatures, search-space classes, scheduler/trigger calls, and decision notes.
- [Workflow recipes](references/workflows.md) shows function pipelines, task pipelines, local debugging, HPO, scheduler, and trigger patterns.
- [HPO CLI reference](references/hpo-cli-reference.md) explains `clearml-param-search` flags and JSON payloads, plus offline validation with [hpo_search_space_check.py](scripts/hpo_search_space_check.py).
- [Troubleshooting](references/troubleshooting.md) covers parent references, parameter overrides, queues/agents, caching, objective metric matching, JSON errors, and recurring time validation.
- [Pipeline skeleton generator](scripts/pipeline_skeleton.py) writes minimal `PipelineDecorator` or `PipelineController` starter files without contacting a ClearML server.

## Route Boundaries

- Use this sub-skill for `PipelineController`, `PipelineDecorator`, `HyperParameterOptimizer`, `TaskScheduler`, `TriggerScheduler`, and the `clearml-param-search` CLI.
- For logging inside step code with `Task.init`, `Logger.report_scalar`, text, images, tables, or artifacts, route to `../experiment-tracking/SKILL.md`.
- For `Dataset`, `StorageManager`, dataset lineage, or object storage assets passed through pipelines, route to `../data-storage/SKILL.md`.
- For direct `clearml-task` packaging, enqueueing, or command-line task launches outside HPO/pipeline orchestration, route to `../remote-execution-cli/SKILL.md`.
- For HTTP routers, `Task.get_http_router()`, web services, or endpoint deployment, route to `../routers-services/SKILL.md`.

## Automation Decision Path

1. Choose `PipelineDecorator` when the user has ordinary Python functions and wants pipeline steps created from function calls.
2. Choose `PipelineController.add_function_step()` when the user wants explicit DAG nodes from Python functions, named return artifacts, parameter references, callbacks, retries, or queue overrides.
3. Choose `PipelineController.add_step()` when the user already has ClearML Tasks to clone and connect into a DAG.
4. Choose `HyperParameterOptimizer` or `clearml-param-search` when the user has a base task/script and wants to clone it across parameter ranges using an objective scalar.
5. Choose `TaskScheduler` for recurring cron-like launches and `TriggerScheduler` for model, dataset, or task events.

## Safety And Execution Notes

- Draft pipeline/HPO/scheduler code without running it unless the user explicitly has a configured ClearML server, credentials, queues, and safe execution target.
- Prefer local debugging paths first: `PipelineDecorator.debug_pipeline()`, `PipelineDecorator.run_locally()`, `PipelineController.start_locally()`, or HPO `--local` where appropriate.
- Treat remote queue names as deployment choices: pipeline controller defaults to a `services` queue, while step execution and HPO jobs usually need worker queues.
- Keep pipeline step imports inside the step function when they are required remotely; ClearML can infer per-step packages from imports used in function steps.

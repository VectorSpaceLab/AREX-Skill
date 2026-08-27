---
name: graph-build
description: "Routes MiroFish document upload, ontology generation, Zep graph
  construction, project graph inspection, task polling, reset, and graph
  deletion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# graph-build

Use this sub-skill when a task asks to create the first MiroFish project graph from seed documents, generate or debug the ontology, poll graph build progress, inspect graph data, reset a project graph, or delete a graph-backed project.

## Route first

- For installation, API keys, ports, or Docker/local service startup, begin at the root MiroFish setup reference.
- For simulation creation, profile generation, or `simulation_config.json`, route to the sibling `simulation-setup` sub-skill after the project status is `graph_completed` and a `graph_id` exists.
- For running/monitoring OASIS simulations, route to `simulation-run`.
- For reports and report-agent chat, route to `reporting`.

## Read or run the bundled material

- Read [references/workflows.md](references/workflows.md) for the document-upload → ontology → graph-build → graph-inspection flow and the reset/delete decision points.
- Read [references/api-reference.md](references/api-reference.md) when constructing `/api/graph` calls or interpreting task/project responses.
- Read [references/data-formats.md](references/data-formats.md) for accepted document types, ontology JSON shape, project/task/graph fields, and graph payload conventions.
- Read [references/troubleshooting.md](references/troubleshooting.md) for upload, ontology, LLM JSON, Zep Cloud, build-task, and graph lifecycle failures.
- Run [scripts/validate_ontology_payload.py](scripts/validate_ontology_payload.py) when validating ontology JSON from a file or stdin. Use `python scripts/validate_ontology_payload.py --help` to inspect options, or `python scripts/validate_ontology_payload.py --self-test` to check the validator without a live LLM or Zep account.

## Minimal operating path

1. Confirm the backend is running and configured with `LLM_API_KEY` and `ZEP_API_KEY`.
2. Submit seed files and a natural-language simulation requirement to ontology generation.
3. Persist the returned project state and ontology; keep the `project_id`.
4. Start graph build for that project; capture the returned `task_id` and provisional or final `graph_id`.
5. Poll the task endpoint until it is `completed` or `failed`.
6. Only continue to simulation setup after the project status is `graph_completed` and the graph data endpoint can return nodes/edges.

## Guardrails

- Supported seed files are PDF, Markdown, and text; reject unsupported extensions before upload.
- Treat ontology field names as public graph schema. Keep entity names PascalCase, relation names UPPER_SNAKE_CASE, and attribute names snake_case without reserved names.
- Do not issue reset/delete while the graph has active build, simulation, memory-updater, or report consumers; use the lifecycle guidance in troubleshooting.
- Do not turn a Zep authentication/permission/transport error into an empty graph. Empty lists are valid data only after a successful read.

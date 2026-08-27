---
name: project-datamodel
description: "Load, validate, persist, inspect, export, and package Kiln .kiln
  project data models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Project datamodel

Use this sub-skill when the task is about Kiln project files and core data-model objects: `Project`, `Task`, `TaskRun`, `TaskOutput`, `Prompt`, `DatasetSplit`, `Skill`, data guides, JSON schemas, input transforms, and safe CLI export of `.kiln` projects.

Do not use this sub-skill to invoke model providers or run a saved task. Route provider/task execution, tools, MCP runtime, and adapter selection to `task-execution-providers-tools`. Route evals, fine-tunes, prompt optimization, and synthetic-data generation workflows to `evals-optimization-finetuning`. Route documents, extraction, vector stores, and RAG to `rag-documents-data`.

## Load these references

1. Read [data-model-and-files.md](references/data-model-and-files.md) for the Python datamodel APIs, parent-child file layout, `load_from_file` / `save_to_file` / `delete`, readonly behavior, task-run leaf filtering, prompts, skills, dataset splits, and data guides.
2. Read [schema-and-input-transforms.md](references/schema-and-input-transforms.md) before creating tasks or task runs with structured JSON input/output, or when diagnosing schema and Jinja input-transform validation errors.
3. Read [cli-package-project.md](references/cli-package-project.md) for `kiln_ai projects list`, `kiln_ai tasks list`, and `kiln_ai package_project` workflows.
4. Read [troubleshooting.md](references/troubleshooting.md) when imports, file loading, schema validation, task-run enumeration, or packaging fail.

## Safe helper

Use [inspect_kiln_project.py](scripts/inspect_kiln_project.py) for read-only inspection of a project file and optional task:

```bash
python scripts/inspect_kiln_project.py --project-file /path/to/project.kiln
python scripts/inspect_kiln_project.py --project-file /path/to/project.kiln --task-id TASK_ID
```

The helper prints project/task metadata and counts without writing files or invoking providers.

## Operating rules

- Prefer `kiln_ai.datamodel` APIs over direct JSON edits; they preserve model types, validation, parent relationships, and on-disk folder conventions.
- When creating child records, pass `parent=` or an explicit stable `path`; then call `save_to_file()`.
- For bulk inspection, use `readonly=True`; for mutation, reload with `readonly=False` or use `mutable_copy()`.
- Remember `Task.runs()` returns leaf runs only by default. Pass `include_intermediate_runs=True` when a full multiturn run chain or exact on-disk inventory is required.
- Treat `delete()` as destructive: for a model file it removes the containing model directory, not just the `.kiln` file.

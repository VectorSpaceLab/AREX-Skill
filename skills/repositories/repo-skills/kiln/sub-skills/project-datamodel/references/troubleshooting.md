# Project datamodel troubleshooting

This guide covers failures while importing Kiln datamodel modules, loading `.kiln` files, mutating/saving/deleting records, validating schemas/input transforms, enumerating task runs, or packaging projects. It does not cover live provider invocation; route those failures to `task-execution-providers-tools`.

Evidence notes: distilled from core datamodel and CLI source/tests plus installed-package inspection for Kiln 1.0.4.

## Import and dependency issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: kiln_ai` | The `kiln-ai` package is not installed in the active Python environment. | Install or activate an environment with `kiln-ai`; for checkout development, use the repo's documented development install. |
| Import errors around `mcp` while importing tools or package-project dependencies | Current Kiln imports are lock-compatible with `mcp` 1.10.1; newer unconstrained `mcp` releases may break imports. | Use the lock-compatible `mcp[cli]==1.10.1` dependency set when preparing inspection/runtime environments. |
| Server-related imports fail with Starlette internals such as `collapse_excgroups` | Unconstrained installs can select a Starlette version incompatible with current server code; Starlette 1.6.0 was incompatible in inspection, while 0.52.1 worked. | Use the lock-compatible server dependency set rather than unconstrained latest FastAPI/Starlette packages. |
| LanceDB/RAG vector-store imports fail because `pandas` is missing | The LanceDB vector-store stack can import pandas transitively. | Install pandas when inspecting or running LanceDB-backed RAG code. Route RAG workflow details to `rag-documents-data`. |
| Provider, cloud, Ollama, Copilot, or fine-tune flows fail for credentials/service reasons | Those flows are optional and require external services, keys, quotas, model downloads, or local daemons. | Do not treat them as datamodel failures. Route runtime provider execution to `task-execution-providers-tools` or fine-tune/Copilot workflow questions to the owning sub-skill. |

## Loading `.kiln` files

| Error | Meaning | Action |
|---|---|---|
| `FileNotFoundError` | The path does not exist. | Check whether the user passed a project directory instead of `project.kiln`; for directories, append `project.kiln`. |
| `Invalid JSON` or JSON parse exception | The `.kiln` file is not valid JSON. | Do not partially load it. Inspect the file, recover from version control if possible, or repair JSON syntax before using datamodel APIs. |
| `Cannot load from file because the schema version is higher than the current version` | File was written by a newer Kiln schema version. | Upgrade Kiln before loading or avoid rewriting the file with an older install. |
| `Cannot load from file because the model type is incorrect` | The loader class does not match `model_type`; for example, loading a project as a task. | Use `Project.load_from_file(project.kiln)`, `Task.load_from_file(task.kiln)`, etc. Check that relationship paths point to the expected parent type. |
| `validation error for Task` while iterating task runs from a project path | `TaskRun.iterate_children_paths_of_parent_path()` expects a task file path, not a project file path. | Load the project, select a task, then enumerate runs from `task.path`. |

Use the bundled script for quick read-only checks:

```bash
python scripts/inspect_kiln_project.py --project-file /path/to/project.kiln
python scripts/inspect_kiln_project.py --project-file /path/to/project.kiln --task-id TASK_ID
```

## Parent-child path problems

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot save to file because 'path' is not set` | A root model lacks `path`, or a child lacks both `path` and a saved parent with a path. | Save the parent first or pass an explicit `path`. |
| Child saved under an unexpected folder name | Child path is built from relationship name plus ID and sanitized first 32 chars of `name`; an existing `path` is preserved. | Inspect `child.path` after save. To move a record, explicitly create a new model/path rather than expecting name changes to move files. |
| Folder name has invalid filename characters removed or replaced | Kiln sanitizes names for portable filenames. | Keep user-facing meaning in model fields; do not rely on folder names as the source of truth. Use model IDs. |
| Nested payload key is rejected because it matches an on-disk folder name | For relationships whose Python name differs from filesystem name, nested validation requires the Python relationship key. | Use the relationship method/key exposed by the model, not the folder name. For task runs, public `runs()` wraps a private `_runs` relationship that still stores files under `runs/`. |

## Readonly mutation errors

`load_from_file(readonly=True)` and relationship calls such as `task.runs(readonly=True)` return readonly objects. Assignment raises `ReadOnlyMutationError`.

Fix patterns:

```python
# Option 1: reload mutable.
task = Task.load_from_file(task.path, readonly=False)
task.description = "Updated"
task.save_to_file()

# Option 2: copy a readonly object.
mutable = readonly_task.mutable_copy()
mutable.description = "Updated"
mutable.save_to_file()
```

Use readonly for inspection and bulk scans. Use mutable objects only for intentional writes.

## `delete()` removed more than expected

`delete()` removes the containing directory for a model file. This is correct for child models because each child lives in its own folder. It also means deleting a `Project` whose path is `project.kiln` removes the whole project directory.

Before deleting:

```python
print(model.path)
print(model.path.parent if model.path and model.path.is_file() else model.path)
```

If you only need to remove a field or one sidecar file, do not call `delete()`.

## Task runs look missing

`Task.runs()` returns leaf runs only by default. In multiturn chains, intermediate runs are hidden when their IDs appear as another run's `parent_task_run_id`.

```python
leaf_runs = task.runs(readonly=True)
all_runs = task.runs(readonly=True, include_intermediate_runs=True)
```

Use `include_intermediate_runs=True` when comparing against files on disk, debugging trace lineage, or copying the full `runs/` tree.

## Schema validation failures

| Error | Cause | Fix |
|---|---|---|
| `JSON schema must be a dict` | Schema string decoded to a non-dict JSON value. | Use a JSON object for the schema. |
| `JSON schema must be an object with properties` | `output_json_schema` requires object schema. | Use `type: "object"` with `properties`; arrays are only accepted for `input_json_schema`. |
| `Input is not a valid JSON object` | Task has an input schema but the run input string is not valid JSON. | Store `json.dumps(value)` in `TaskRun.input`. For array input schemas, the JSON value may be an array. |
| `Output is not a valid JSON object` | Task has an output schema but output is not a JSON object string. | Store `json.dumps(object_value)` in `TaskOutput.output`. |
| `The error from the schema check was: ...` | JSON parsed but failed JSON Schema validation. | Check required fields, types, enums, numeric bounds, and `additionalProperties`. |

Do not bypass validation by writing JSON files directly unless the task is a careful recovery of already-corrupt files. Prefer constructing `TaskRun(parent=task, ...)` and letting pydantic raise before any save.

## Input-transform failures

| Error | Cause | Fix |
|---|---|---|
| `Invalid Jinja2 template` | Template syntax does not compile. | Construct `JinjaInputTransform(template=...)` early and fix the line reported. |
| Discriminated-union validation error for `InputTransform` | Missing or unknown `type`. | Use `{"type": "jinja", "template": "..."}` for current transforms. |
| Runtime render failure on missing variable | The template environment uses strict undefined variables. | Reference fields under `input`, and use Jinja defaults for optional fields. |
| Rendered prompt shows raw JSON string fields unexpectedly | String inputs are parsed as JSON when possible; invalid JSON stays a raw string. | Pass dict/list values to rendering when possible, or ensure string input is valid JSON when schema-backed. |

## Packaging failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `No project path provided` | `kiln_ai package_project` requires a path argument. | Pass a `project.kiln` file or directory containing it. |
| `Project has no tasks` | The project loaded but has no task children. | Create/save tasks first or select the correct project. |
| `No tasks specified` | Neither `--task`/`--tasks`, `--task all`, nor `--all-tasks` was supplied. | List tasks, then pass IDs or `--all-tasks`. |
| `Task ID(s) not found` | Requested task ID is absent from the project. | Run `kiln_ai tasks list <project>` and copy exact IDs. |
| `Task ... has no default run config set` | Deployment export needs a default `TaskRunConfig`. | Set a default run config in the project before packaging. |
| `Default run config ... not found` | `default_run_config_id` points to a deleted/missing run config. | Create a new run config and update `default_run_config_id`. |
| Dynamic prompt warning | The selected prompt generator builds prompts from current data and may not be stable. | Prefer a static prompt for deployment, or accept the CLI prompt if a built snapshot is acceptable. |
| MCP warning | Exported task references local/remote MCP tools that require deployment-machine setup. | Confirm the MCP server and credentials will exist where the package runs. |
| RAG tool error | `package_project` does not support RAG deployment packages. | Route to `rag-documents-data`; do not claim the zip is sufficient for RAG. |
| Skill export error | A skill tool references a missing skill or a skill without a saved path/sidecar. | Verify `project.skills()`, `skill.kiln`, `SKILL.md`, `references/`, and `assets/`. |

## Routing reminders

- If the user asks to run a task, configure a provider, inspect model capabilities, debug LiteLLM, use MCP tools, or call `adapter_for_task`, route to `task-execution-providers-tools`.
- If the user asks about eval configs, evaluator runs, synthetic data, data generation jobs, repair, prompt optimization, or fine-tuning, route to `evals-optimization-finetuning`.
- If the user asks about documents, extraction, chunking, embeddings, vector stores, rerankers, or RAG indexes/tools, route to `rag-documents-data`.
- If the user asks about REST endpoints, server app startup, desktop studio APIs, Git sync, web UI, or OpenAPI TypeScript schema checks, route to `server-desktop-web-api`.

# CLI listing and project packaging

Kiln's installed core CLI exposes three in-scope datamodel commands:

```text
kiln_ai projects list
kiln_ai tasks list <project-file-or-project-id>
kiln_ai package_project <project-file-or-project-dir> [--task TASK_IDS | --all-tasks] [--output ZIP]
```

Evidence notes: this reference is distilled from `libs/core/kiln_ai/cli/cli.py`, `cli/commands/projects.py`, `tasks.py`, `package_project.py`, CLI tests, and installed CLI inspection for version 1.0.4.

## `kiln_ai projects list`

Use this when the user wants to see projects registered in Kiln's user configuration.

```bash
kiln_ai projects list
```

Behavior:

- Reads the configured project file paths.
- Loads each path with `Project.load_from_file()`.
- Prints ID, name, and path for loadable projects.
- Shows failed rows for configured projects that cannot load.
- Exits successfully when no projects are configured.

If a project is not in the user's configuration, use its `project.kiln` path directly with Python or with `kiln_ai tasks list` / `kiln_ai package_project`.

## `kiln_ai tasks list`

Use this to inspect task IDs before export or scripting.

```bash
kiln_ai tasks list /path/to/project.kiln
kiln_ai tasks list PROJECT_ID_FROM_PROJECTS_LIST
```

Behavior:

- Accepts either a project file path or a configured project ID. If you have a project directory, pass its `project.kiln` file.
- Loads the project through the datamodel.
- Lists each task's ID, name, description, and file path.
- Uses `project.tasks(readonly=True)` so listing does not mutate files.

Common failure modes:

- `Project not found`: pass a valid project file path or a configured project ID.
- `Error loading project`: the file is missing, invalid JSON, wrong `model_type`, or a newer schema version than this Kiln install supports.

## `kiln_ai package_project`

Use this to export a minimal project zip for running one or more saved tasks elsewhere. It packages files; it does not invoke the model provider.

```bash
# Export one task.
kiln_ai package_project /path/to/project.kiln -t TASK_ID -o exported_kiln_project.zip

# Export several tasks.
kiln_ai package_project /path/to/project.kiln --tasks TASK_ID_1,TASK_ID_2 --output deploy.zip

# Export all tasks in the project.
kiln_ai package_project /path/to/project-directory --all-tasks -o all_tasks.zip

# The tasks argument also accepts the literal string "all".
kiln_ai package_project /path/to/project.kiln --task all -o all_tasks.zip
```

Options:

| Option | Meaning |
|---|---|
| `project_path` | Path to `project.kiln` or to a directory containing it. Required for packaging. |
| `-t`, `--task`, `--tasks` | Comma-separated task IDs, or `all`. |
| `--all-tasks` | Export every task in the project. |
| `-o`, `--output` | Output zip path. Defaults to `exported_kiln_project.zip`. |

## What packaging validates

`package_project` performs validation before writing the final zip:

1. Load the project file or directory.
2. Resolve requested task IDs; if none are supplied, print available tasks and exit with an error.
3. Add required subtasks referenced by `kiln_task` tools.
4. Validate that every task exists.
5. Validate that every task has a `default_run_config_id` and the referenced `TaskRunConfig` exists.
6. Validate tool references in those run configs.
7. Build static prompts for each task's selected prompt ID.
8. Create a temporary export directory.
9. Copy `project.kiln`, selected `task.kiln` files, default `task_run_config.kiln` files, built prompt files, required external tool servers, and required project skills.
10. Update exported run configs to point at the exported prompt via `id::<prompt_id>`.
11. Validate that exported prompts still rebuild to the expected prompt text.
12. Create the zip and remove the temporary directory.

The package preserves original task folder names and run-config folder names inside the export.

## What the deployment package contains

For a simple task, expect a zip structure like:

```text
project.kiln
tasks/
  <task_id> - <Task name>/
    task.kiln
    run_configs/
      <config_id> - <Run Config name>/task_run_config.kiln
    prompts/
      <prompt_id> - Exported Prompt/prompt.kiln
```

Additional files may be included when required:

- `external_tool_servers/` for `kiln_task`, local MCP, or remote MCP tool servers referenced by exported tasks.
- `skills/` with `skill.kiln`, `SKILL.md`, `references/`, and `assets/` for project skills referenced as tools.
- Extra task folders for subtasks required by `kiln_task` tools.

The deployment package does not routinely include task-run datasets, eval runs, fine-tune state, or document/RAG indexes. Those belong to separate evaluation, training, or RAG workflows.

## Tool handling during packaging

| Tool type in run config | Packaging behavior |
|---|---|
| Built-in Kiln tool | Allowed; no extra server export. |
| Kiln task tool | Adds the referenced subtask and exports its required server/config. |
| Project skill tool | Exports the referenced project skill directory. |
| Remote MCP tool | Allowed after warning that remote credentials/configuration may be needed on the deployment machine. |
| Local MCP tool | Prompts for confirmation because the local MCP server must be installed on the deployment machine. |
| RAG tool | Fails: the project package tool does not currently support RAG deployment packages. Route RAG deployment work to `rag-documents-data`. |
| Unknown tool prefix | Fails rather than silently exporting an incomplete package. |

Packaging can succeed without provider credentials because it only builds files. Running the exported task later may still need provider keys, local services, MCP servers, Ollama models, cloud services, or Copilot access depending on the saved run config and tools.

## Dynamic prompts

If a task's default run config uses a dynamic prompt generator such as few-shot, multi-shot, repairs, or chain-of-thought variants, the CLI warns and asks whether to continue. If accepted, it builds and saves a concrete prompt in the export. For more deterministic deployments, create or select a static prompt-backed default run config before packaging.

In non-interactive automation, prefer validating prompts with library helpers that raise exceptions instead of calling `typer.confirm()` or exiting the process.

## Calling packaging from Python

Use the CLI for ordinary operator work. If you need to call the packager from Python in a controlled script, call the command function with concrete `Path` values:

```python
from pathlib import Path
from kiln_ai.cli.commands.package_project import package_project

package_project(
    project_path=Path("/path/to/project.kiln"),
    tasks="TASK_ID_1,TASK_ID_2",
    all_tasks=False,
    output=Path("deploy.zip"),
)
```

Be aware that the CLI variant may prompt for dynamic prompts and MCP tools or raise `typer.Exit` on validation failure. Server or library code should prefer non-interactive helper functions from the same module when it must raise `ValueError` instead of exiting.

## Export checklist

Before running `package_project`:

- Load the project and list tasks to confirm task IDs.
- Check each exported task has a saved default run config.
- Confirm the default run config uses a prompt that can be built without provider calls.
- Check whether tools reference RAG, MCP, skills, or subtasks.
- For skill tools, verify the referenced `Skill` exists and has its `SKILL.md` sidecar.
- Decide whether local/remote MCP dependencies are acceptable for the deployment target.
- If RAG is required, do not use this package path as the complete deployment story; route to RAG guidance.

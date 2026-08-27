# Kiln data model and files

Use Kiln's Python datamodel APIs for project-file work whenever possible. The models enforce JSON schema, model type, parent relationships, file names, and sidecar resource rules that direct JSON editing can accidentally break.

Evidence notes: this reference is distilled from `libs/core/README.md`, `libs/core/kiln_ai/datamodel/basemodel.py`, `project.py`, `task.py`, `task_run.py`, `task_output.py`, `prompt.py`, `dataset_split.py`, `skill.py`, `data_guide.py`, and related datamodel tests.

## Mental model

A Kiln project is a directory rooted by `project.kiln`. Most child objects are JSON files with `.kiln` extensions under relationship folders. Child folder names begin with the model's 12-digit-ish ID and may include a sanitized name prefix for readable diffs.

Typical in-scope layout:

```text
project.kiln
skills/
  <skill_id> - <skill-name>/
    skill.kiln
    SKILL.md
    references/
    assets/
tasks/
  <task_id> - <Task name>/
    task.kiln
    runs/
      <run_id>/task_run.kiln
    prompts/
      <prompt_id> - <Prompt name>/prompt.kiln
    dataset_splits/
      <split_id> - <DatasetSplit name>/dataset_split.kiln
    run_configs/
      <config_id> - <TaskRunConfig name>/task_run_config.kiln
    data_guides/
      <guide_id>/data_guide.kiln
```

Also present in broader Kiln projects but routed elsewhere: `documents/`, extractor/chunker/embedding/vector/RAG/reranker config folders, `evals/`, `finetunes/`, `prompt_optimization_jobs/`, and `specs/`.

Key relationships:

- `Project` parents `tasks` and `skills` plus document/RAG/tool-server config objects.
- `Task` parents `runs`, `prompts`, `dataset_splits`, `run_configs`, `data_guides`, and eval/fine-tune/spec objects.
- `TaskRun` lineage for multiturn flows is flat under `runs/`; parent-child run chains use `parent_task_run_id`, not nested run folders.
- `Skill` stores metadata in `skill.kiln`; the actual instructions are a sibling `SKILL.md` plus optional `references/` and `assets/` folders.

## Loading and inspecting

```python
from pathlib import Path
from kiln_ai.datamodel import Project, Task

project = Project.load_from_file(Path("/path/to/project.kiln"))
print(project.id, project.name, project.description)

# Children are loaded from disk through generated relationship methods.
tasks = project.tasks(readonly=True)
for task in tasks:
    print(task.id, task.name, task.path)

# Fast ID lookup for a child model.
task = Task.from_id_and_parent_path("TASK_ID", project.path)
if task is None:
    raise ValueError("Task not found")
```

Use `readonly=True` for large inspections. Readonly models are cached and protected from assignment. If you need to mutate a readonly object, reload it without readonly or call `mutable_copy()`:

```python
readonly_task = Task.load_from_file("/path/to/task.kiln", readonly=True)
mutable_task = readonly_task.mutable_copy()
mutable_task.description = "Updated description"
mutable_task.save_to_file()
```

Assignments to readonly fields raise `ReadOnlyMutationError`. The `parent` and `path` fields are safe internal exceptions so lazy loading still works.

## Creating and saving project objects

Create parent objects first, save them, then create children with `parent=`.

```python
import json
from pathlib import Path
from kiln_ai.datamodel import Project, Task, TaskRun, TaskOutput
from kiln_ai.datamodel.task_output import DataSource, DataSourceType

project_dir = Path("/path/to/new_project")
project = Project(name="Support Bot", path=project_dir / "project.kiln")
project.save_to_file()

task = Task(
    name="Classify Ticket",
    description="Classify support tickets by category.",
    instruction="Return one category and a concise reason.",
    input_json_schema=json.dumps({
        "type": "object",
        "properties": {"ticket": {"type": "string"}},
        "required": ["ticket"],
    }),
    output_json_schema=json.dumps({
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["category", "reason"],
    }),
    parent=project,
)
task.save_to_file()

run = TaskRun(
    parent=task,
    input=json.dumps({"ticket": "Cannot reset my password"}),
    input_source=DataSource(
        type=DataSourceType.human,
        properties={"created_by": "analyst"},
    ),
    output=TaskOutput(
        output=json.dumps({"category": "account", "reason": "Password reset issue"}),
        source=DataSource(
            type=DataSourceType.human,
            properties={"created_by": "analyst"},
        ),
    ),
)
run.save_to_file()
```

`save_to_file()` builds a path from the parent relationship if `path` is unset. If a model was loaded from an existing file or has `path` set, saving keeps that exact path even if `name` changes; this prevents renames from leaving orphaned folders.

## Deleting

`delete()` is intentionally directory-oriented:

- For a child file such as `tasks/<id> - Name/runs/<run_id>/task_run.kiln`, it removes that run's containing folder.
- For `project.kiln`, it removes the project directory containing the file.
- For a directory path, it removes the directory itself.

Only call `delete()` after confirming the target model's `path` and that deleting the containing directory is intended.

## Task runs and leaf filtering

`Task.runs()` is optimized for dataset/eval iteration and returns leaf runs only by default. In a multiturn chain, any run whose ID appears as another run's `parent_task_run_id` is treated as an intermediate run and hidden from the default view.

```python
leaf_runs = task.runs(readonly=True)
all_runs = task.runs(readonly=True, include_intermediate_runs=True)
print(len(leaf_runs), len(all_runs))
```

Use default leaf filtering for most dataset iteration. Use `include_intermediate_runs=True` for diagnostics, export validation, lineage inspection, or exact on-disk counts.

## Task outputs, data sources, ratings, and tags

`TaskRun.input` and `TaskOutput.output` are strings. They are JSON strings only when the parent task has corresponding schemas. `TaskOutputRating` supports five-star, pass/fail, pass/fail-critical, and custom rating types. Tags must be non-empty strings without spaces.

```python
from kiln_ai.datamodel import TaskOutputRating, TaskOutputRatingType

run.output.rating = TaskOutputRating(
    value=5.0,
    type=TaskOutputRatingType.five_star,
)
run.tags = ["gold", "password_reset"]
run.save_to_file()
```

When strict mode is enabled, new task runs require `input_source` and new outputs require `source`. Loading older files from disk is allowed even if those fields are missing.

## Prompts

Prompts are task children. The `Prompt` body is stored in `prompt.kiln` and can include optional chain-of-thought instructions.

```python
from kiln_ai.datamodel import Prompt

prompt = Prompt(
    parent=task,
    name="Production Prompt",
    description="Pinned prompt for deployment.",
    prompt="Classify the ticket and explain briefly.",
)
prompt.save_to_file()
```

`TaskRunConfig` objects can refer to prompts through prompt IDs. Detailed provider/run-config behavior belongs in `task-execution-providers-tools`; this sub-skill only covers persistence and export implications.

## Dataset splits

`DatasetSplit` stores split definitions and run IDs, not duplicated run payloads. `DatasetSplit.from_task()` builds a split from the task's current leaf runs and an optional filter.

```python
from kiln_ai.datamodel import DatasetSplit
from kiln_ai.datamodel.dataset_split import Train80Test20SplitDefinition

split = DatasetSplit.from_task(
    name="train-test",
    task=task,
    splits=Train80Test20SplitDefinition,
    filter_id="all",
)
split.save_to_file()
print(split.split_contents)
print(split.missing_count())
```

`missing_count()` reports referenced run IDs that no longer exist in the task's current leaf-run view. If a split should include intermediate multiturn runs, build that ID list explicitly instead of relying on the default `from_task()` helper.

## Skills stored in projects

Project skills are persisted as a `Skill` model plus a `SKILL.md` sidecar. Use `save_skill_md()` so frontmatter stays synchronized and the resource directories exist.

```python
from kiln_ai.datamodel import Skill

skill = Skill(
    parent=project,
    name="triage-policy",
    description="Apply the support triage policy.",
)
skill.save_to_file()
skill.save_skill_md("# Triage policy\n\nUse the current support taxonomy.")
print(skill.body())
```

`read_reference()` and `read_asset()` reject path traversal, folders, missing files, and unreadable binary files.

## Data guides

`DataGuide` is a task child containing a markdown guide for realistic task inputs. It is input-data guidance, not output behavior and not model invocation.

```python
from kiln_ai.datamodel.data_guide import DataGuide

guide = DataGuide(
    parent=task,
    source="manual",
    guide="# Semantics\n\nTickets mention one customer issue at a time.",
)
guide.save_to_file()
current = task.current_data_guide(readonly=True)
```

By design, current code treats at most one guide as canonical; `current_data_guide()` returns the first saved guide or `None`.

## Flat dataset export pattern

For analytics, load through the datamodel and then flatten as needed:

```python
rows = []
for run in task.runs(readonly=True):
    rows.append({
        "run_id": run.id,
        "input": run.input,
        "output": run.output.output,
        "rating": run.output.rating.value if run.output.rating else None,
        "tags": list(run.tags),
    })
```

If the task uses JSON schemas, parse `run.input` and `run.output.output` with `json.loads()` after loading. Keep invalid historical files visible rather than silently dropping them; use the troubleshooting reference to diagnose validation failures before rewriting files.

# Workflow Configuration

Use this reference to build txtai workflows in Python or YAML. Workflows are streaming, batch-oriented callables: `workflow(elements)` returns a generator and does not execute until consumed.

## Python API

```python
from txtai.workflow import Task, Workflow

workflow = Workflow([
    Task(lambda rows: [row.strip() for row in rows]),
    Task(lambda rows: [row.upper() for row in rows]),
], batch=100)

results = list(workflow(["  one  ", "two"]))
```

Constructor facts:

- `Workflow(tasks, batch=100, workers=None, name=None, stream=None)`.
- `tasks` is an ordered list of task instances.
- `batch` controls how many elements each task action receives at a time.
- `workers` defaults to the maximum number of actions in any task; override when multi-action tasks need controlled concurrency.
- `stream` is an optional stream processor applied before batching.
- `schedule(cron, elements, iterations=None)` repeats a workflow on a cron schedule and consumes/discards outputs internally.

## Task API

`Task(action=None, select=None, unpack=True, column=None, merge="hstack", initialize=None, finalize=None, concurrency=None, onetomany=True, **kwargs)` controls how data is selected, prepared, executed, and packed.

Key parameters:

| Parameter | Meaning | Common use |
| --- | --- | --- |
| `action` | Callable or list of callables | Pass a pipeline instance, Python function, or list of parallel actions |
| `select` | Regex filter | Only process elements matching a pattern, often file extensions |
| `unpack` | Whether `(id, data, tags)` tuples are unpacked to `data` | Set `False` for indexing sinks or whole-tuple processing |
| `column` | Tuple column index or per-action map | Feed only one column to a downstream action |
| `merge` | `hstack`, `vstack`, `concat`, or `None` | Combine multi-action outputs |
| `initialize` / `finalize` | Callable hooks | Open/close resources or flush buffered indexing |
| `concurrency` | `thread`, `process`, or unset | Multi-action I/O, CPU, or GPU concurrency |
| `onetomany` | Expand list outputs into multiple rows | Disable for transforms that must preserve row shape |

Action callables receive a batch/list of inputs. If a callable returns a generator, txtai consumes it into a list inside the task.

## Task Subclasses

| Task class | YAML `task` | Purpose | Dependency/caveat |
| --- | --- | --- | --- |
| `Task` | omitted or empty | Generic action wrapper | Pure Python; safest for smoke tests |
| `FileTask` | `file` | Accept existing local file paths and `file://` URLs | Skips non-existing files and non-matching `select` regexes |
| `RetrieveTask` | `retrieve` | Retrieve URL/local content into a local directory | Uses URL retrieval and can be network-dependent |
| `ServiceTask` | `service` | Call HTTP service endpoints and parse JSON/XML | Needs `txtai[workflow]`; network-dependent |
| `ConsoleTask` | `console` | Print inputs/outputs while passing data through | Useful for schedule/debug demos |
| `ImageTask` | `image` | Open image files as PIL images | Needs Pillow from `workflow` or `pipeline-image` extra |
| `TemplateTask` | `template` | Format text/templates from strings, dicts, or tuples | Strict formatting raises on unused/missing variables |
| `RagTask` / `ExtractorTask` | `rag`-style template task via class import | Prepare `{query, question}` dicts | Route RAG prompt design to agents/LLM sub-skill |
| `WorkflowTask` | `workflow` or named workflow action | Call another workflow inside a workflow | Consumes nested workflow output into a list |
| `StreamTask` | `stream` when used as workflow stream | Expands/generates elements before regular tasks | Set `batch: true` when action expects the whole iterable |
| `ExportTask` | `export` | Export records to file formats | Needs export dependencies such as pandas/openpyxl for Excel |
| `StorageTask` / `UrlTask` | `storage` / `url` | Storage/URL input helpers | Optional storage/network behavior; validate dependencies and side effects |

## Generator Consumption

Always consume workflow output:

```python
# Small data
rows = list(workflow(elements))

# Large data
for row in workflow(elements):
    handle(row)

# Discard output but force execution
for _ in workflow(elements):
    pass
```

A common bug is constructing `workflow(elements)` and never iterating it. In that case `initialize`, task actions, indexing finalizers, and `finalize` hooks do not run.

## Batching and Streaming

- Lists, tuples, arrays, and tensors are chunked by slicing: `elements[x:x + batch]`.
- Generators and other dynamic iterables are accumulated until `batch` elements are available; the final partial batch is still processed.
- Use smaller `batch` values for memory-heavy model pipelines and larger values for cheap pure-Python transforms.
- `stream` processors run before batching. YAML stream config is a task-like object under the workflow, not inside `tasks`.

YAML stream example:

```yaml
workflow:
  expand:
    stream:
      action: mypackage.streamers.expand
      batch: true
    tasks:
      - action: nop
```

## YAML Application Workflows

Create an application from a YAML string, dict, or file path:

```python
from txtai import Application

app = Application(config, loaddata=False)
rows = list(app.workflow("clean", ["  One  "]))
```

Minimal YAML with callable path actions:

```yaml
workflow:
  clean:
    tasks:
      - mypackage.transforms.strip_text
      - mypackage.transforms.upper_text
```

Pipeline-backed YAML:

```yaml
segmentation:
  sentences: true

workflow:
  segment:
    tasks:
      - action: segmentation
```

Workflow with args:

```yaml
translation:

workflow:
  translate-fr:
    tasks:
      - action: translation
        args: [fr]
```

`args` can be a list of positional arguments or a dict of keyword arguments. For a multi-action task, `args` is indexed per action.

## YAML Action Resolution

When `Application` builds workflows, each `action` is resolved in this order:

1. `index` or `upsert`: buffer workflow data and finalize into the configured embeddings index; `unpack` is forced to `False`.
2. `search`: run application batch search over incoming query elements.
3. `transform`: run embeddings vector transform; one-to-many is disabled.
4. A configured pipeline name, such as `summary`, `translation`, `textractor`, `segmentation`, `labels`, `caption`, or `llm`.
5. A configured workflow name, enabling workflow chaining.
6. A fully qualified callable/class path resolved through txtai's resolver.

Shorthand tasks are allowed:

```yaml
workflow:
  run:
    tasks:
      - segmentation
      - index
```

This is equivalent to task entries with `action: segmentation` and `action: index`.

## YAML Task Keys

```yaml
workflow:
  name:
    batch: 50
    workers: 2
    tasks:
      - task: file
        action: textractor
        select: "\\.pdf$"
      - action: summary
      - action: translation
        args: [fr]
```

Useful task keys:

- `task`: task type, for example `file`, `retrieve`, `service`, `console`, `image`, `template`, `workflow`, or a custom task class path.
- `action`: callable action name/path or list of action names/paths.
- `args`: positional list or keyword dict prepended to each action call after workflow data.
- `select`: regex filter applied to candidate elements.
- `unpack`, `column`, `merge`, `concurrency`, `onetomany`: same semantics as Python `Task` parameters.
- `initialize`, `finalize`: callable names/paths resolved like actions.
- Task-specific keys such as `template`, `rules`, `strict`, `directory`, `flatten`, `url`, `method`, `params`, `batch`, and `extract` are passed to the task subclass `register` method.

## Index/Search Actions In Workflows

YAML workflows can use special embeddings actions when the application has an `embeddings` section:

```yaml
writable: true
embeddings:
  path: sentence-transformers/paraphrase-MiniLM-L3-v2
  content: true

segmentation:
  sentences: true

workflow:
  index:
    tasks:
      - action: segmentation
      - action: index
  search:
    tasks:
      - search
```

Route detailed embeddings configuration, row formats, SQL, storage, save/load, and search tuning to [embeddings-search](../../embeddings-search/SKILL.md).

## Schedules

Python schedule:

```python
workflow.schedule("0/5 * * * *", elements, iterations=1)
```

YAML schedule:

```yaml
workflow:
  poll:
    schedule:
      cron: "0/5 * * * *"
      elements: ["input"]
      iterations: 1
    tasks:
      - task: console
```

Notes:

- Scheduling requires `croniter`, installed by `txtai[workflow]`.
- Cron can use five fields for minute-level schedules or six fields when seconds are included.
- YAML schedules are started during `Application` creation and run in a thread pool. Keep the process alive with `app.wait()` when appropriate.
- Exceptions in scheduled runs are logged and the scheduler continues until `iterations` is exhausted or the process exits.

## Safe Validation Pattern

For no-download validation, use pure Python callables or the bundled smoke script instead of default ML pipelines:

```bash
python skills/txtai/sub-skills/pipelines-and-workflows/scripts/workflow_smoke.py --mode all
```

Then separately validate any model-backed pipeline with explicit model/cache assumptions and focused optional extras.

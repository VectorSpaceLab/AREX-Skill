---
name: pipelines-and-workflows
description: "Compose deterministic txtai pipelines and workflows for
  extraction, transformation, batching, streaming, YAML task configuration, and
  schedules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipelines and Workflows

Use this sub-skill when the task is to choose txtai pipelines, wire them into deterministic `Workflow` task chains, convert between Python and YAML workflow definitions, debug lazy workflow execution, or validate pipeline/workflow configuration without deploying a service.

Route elsewhere when the user is asking for:

- Embeddings indexing, SQL search, hybrid search, graph search, or index storage: [embeddings-search](../embeddings-search/SKILL.md).
- RAG prompt design, LLM backend selection, agent tools, or multi-agent reasoning: [agents-and-llm-orchestration](../agents-and-llm-orchestration/SKILL.md).
- FastAPI/API serving, OpenAI-compatible endpoints, MCP, auth, Docker, or service deployment: [api-and-deployment](../api-and-deployment/SKILL.md).

## Fast Start

```python
from txtai.workflow import Task, Workflow

workflow = Workflow([
    Task(lambda rows: [row.strip() for row in rows]),
    Task(lambda rows: [row.upper() for row in rows]),
], batch=2)

results = list(workflow([" first ", "second", " third "]))
```

Important behavior:

- `Workflow(tasks, batch=100, workers=None, name=None, stream=None)` returns a lazy generator from `workflow(elements)`; nothing runs until the generator is iterated or wrapped in `list(...)`.
- `Task(action)` receives a batch/list of elements and should return one output per input unless deliberately performing one-to-many expansion.
- Pipelines are callable and can be passed directly to `Task(...)`; pure Python callables are safer for smoke tests because default ML pipelines often download models.
- Workflow inputs can be strings, dicts, tuples, generators, NumPy arrays, tensors, or `(id, data, tags)` tuples depending on downstream tasks.

## Pick The Right Surface

- Use Python workflows for local scripts, unit tests, dynamic callables, task graphs that need Python objects, or careful generator consumption.
- Use YAML workflows when building a `txtai.Application` configuration with named pipelines and reusable named workflows.
- Use schedules only for long-running processes that poll dynamic inputs; scheduling needs the `workflow` extra and valid cron syntax.
- Use bundled script `scripts/workflow_smoke.py` when you need a no-download, deterministic check of Python workflow execution and YAML template shape.

## Core Python Pattern

```python
from txtai.workflow import Task, Workflow

normalize = Task(lambda rows: [row.lower() for row in rows])
annotate = Task(lambda rows: [{"text": row, "length": len(row)} for row in rows])
workflow = Workflow([normalize, annotate], batch=100)

for row in workflow(["A Text", "Another Text"]):
    print(row)
```

For file processing, use `FileTask(action, select=r"\.pdf$")` to accept existing local files matching a regex. For image paths, use `ImageTask(...)` when Pillow is installed. For URL/local retrieval, use `RetrieveTask(...)`, but treat remote URLs as network-dependent and avoid them in offline validation.

## YAML Workflow Pattern

YAML pipelines are top-level sections named by lower-case pipeline class names. Workflows live under `workflow` and contain named workflows with `tasks`.

```yaml
summary:
translation:

workflow:
  summarize-translate:
    tasks:
      - action: summary
      - action: translation
        args: [fr]
```

`Application(config).workflow("summarize-translate", elements)` returns a generator, just like direct Python workflows. YAML `action` resolution is:

- A configured pipeline name, such as `summary`, `translation`, `textractor`, `segmentation`, `labels`, or `llm`.
- Special embeddings actions `index`, `upsert`, `search`, or `transform` when the application has an embeddings configuration.
- Another configured workflow name, when chaining workflows.
- A fully qualified callable path, such as `mypackage.module.function`.

## References

- `references/pipeline-catalog.md`: pipeline families, common classes, extras, and input/output caveats.
- `references/workflow-configuration.md`: `Workflow`, `Task`, task subclasses, YAML keys, batching, streaming, schedule configuration, and action resolution.
- `references/troubleshooting.md`: generator consumption, missing extras, offline/model-download behavior, selector regexes, YAML callable resolution, schedules, and heavy pipeline families.
- `scripts/workflow_smoke.py`: deterministic no-download smoke helper with Python workflow checks and optional YAML template output.

## Validation Checklist

- Confirm whether the workflow should be pure Python, YAML `Application`, scheduled, or API-served; route API serving to [api-and-deployment](../api-and-deployment/SKILL.md).
- If using pipelines, install only the focused extra family needed for that pipeline class; avoid broad `all` unless the user explicitly wants the full environment.
- Consume workflow output with `list(...)`, a `for` loop, or an indexing/search sink; otherwise no work happens.
- Keep no-download smoke tests separate from ML pipeline tests; default `Summary`, `Translation`, `Transcription`, `Caption`, `LLM`, and similar classes can trigger model downloads.
- For YAML, define pipeline sections before referencing them as `action`, and use fully qualified Python paths for custom callables.
- For schedules, require `txtai[workflow]`, a cron expression, `schedule.elements`, and a running process that calls `app.wait()` or otherwise stays alive.

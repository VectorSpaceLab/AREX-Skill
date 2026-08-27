# Custom Graphs and Pipelines

Read this when a Cognee workflow needs domain-specific graph extraction or custom pipeline tasks.

## Custom `DataPoint` models

Public import path:

```python
from cognee.infrastructure.engine import DataPoint, Dedup, Embeddable, LLMContext
```

A custom model is a Pydantic model that subclasses `DataPoint`:

```python
from typing import Annotated
from cognee.infrastructure.engine import DataPoint, Dedup, Embeddable

class ScientificPaper(DataPoint):
    title: Annotated[str, Dedup()]
    findings: Annotated[list[str], Embeddable()]
```

Important behavior:
- `DataPoint` creates a UUID by default.
- If the class metadata has `identity_fields`, the id is deterministic through `id_for(...)`.
- `Dedup()` and `Embeddable()` annotations can auto-populate metadata when the class does not override `metadata` directly.
- `ontology_uri` and `ontology_valid` preserve ontology grounding when a node is matched to an ontology.

## Custom graph extraction

Use custom graph models in `cognify` or `remember` kwargs when the extraction should follow a domain schema:

```python
await cognee.cognify(
    datasets="papers",
    graph_model=ScientificPaper,
    custom_prompt="Extract title, authors, methods, findings, and citations.",
)
```

Route chunking, LLM provider, and embedding-provider setup to [configuration-backends](../../configuration-backends/SKILL.md).

## Ontology-guided extraction

Cognee supports ontology resolver configuration around RDF/OWL-style grounding.
Use this when entity labels must map to a controlled vocabulary.

Common settings:
- `ONTOLOGY_RESOLVER=rdflib`
- `MATCHING_STRATEGY=fuzzy`
- `ONTOLOGY_FILE_PATH=/path/to/ontology.owl`

Keep ontology paths project-specific in the user's own code. Do not hard-code a path from a generated skill.

## Custom pipelines

Public helper:

```python
from cognee.modules.pipelines.tasks.task import Task, task
await cognee.run_custom_pipeline(
    tasks=[Task(my_async_task)],
    data="input",
    dataset="research",
    pipeline_name="custom_pipeline",
)
```

`run_custom_pipeline(...)` accepts:
- `tasks`: a list of `Task` objects or task specs.
- `data`: forwarded to the first task.
- `dataset`: dataset name or UUID.
- `use_pipeline_cache`, `incremental_loading`, `data_cache`.
- `run_in_background` for detached execution.
- `skip_connection_test` for deterministic non-LLM pipelines.

The `@task` decorator returns a `TaskSpec`; calling a `TaskSpec` binds kwargs for later pipeline execution and does not run the function immediately.

## `memify`

`memify(...)` enriches an existing graph and can accept extraction/enrichment task lists:

```python
await cognee.memify(dataset="research", node_name=["important_entity"])
```

Use it when the graph already exists and the user wants enrichment, feedback weighting, or an additional memory pass rather than a fresh add/cognify pipeline.

## Validation pattern

Before running a full extraction:

1. Import the custom model.
2. Construct a tiny instance.
3. Inspect `model_fields` and `metadata`.
4. Confirm any identity fields produce a stable `id_for(...)` value.
5. Only then run `remember`, `cognify`, or a custom pipeline with provider credentials.

Use [scripts/inspect_custom_model.py](../scripts/inspect_custom_model.py) for the first three checks.

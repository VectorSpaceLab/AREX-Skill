# Pipeline and Node Workflows

Use these workflows to design, refactor, and inspect Kedro graphs using only public Kedro package imports. They assume Kedro 1.4.0 and the public `kedro.pipeline` API.

## Design a New Pipeline

1. Write plain Python functions first. Avoid catalog access, runner calls, global state, or configuration loading inside node functions.
2. Decide dataset edge names before writing nodes. Use clear names such as `raw_customers`, `clean_customers`, and `features`.
3. Use `params:name` for single parameters. Use `parameters` only when the node function genuinely needs the whole parameters dictionary.
4. Build nodes with explicit names and tags so slicing and CLI commands are stable.
5. Build a `Pipeline` or `pipeline(...)` object and inspect it with `describe()`, `inputs()`, `outputs()`, and `datasets()`.
6. Confirm there are no duplicate output names, duplicate node names, unexpected free inputs, or circular dependencies.

Template:

```python
from kedro.pipeline import Pipeline, node


def clean(raw_table):
    return raw_table.dropna()


def make_features(clean_table, options):
    return clean_table.assign(scale=options["scale"])


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(clean, "raw_table", "clean_table", name="clean_table", tags="prep"),
            node(
                make_features,
                inputs=["clean_table", "params:feature_options"],
                outputs="feature_table",
                name="make_features",
                tags=["features", "model-input"],
            ),
        ],
        tags="feature_engineering",
    )
```

Before handing the graph to execution, check:

```python
pipe = create_pipeline()
print(pipe.describe())
assert pipe.inputs() == {"raw_table", "params:feature_options"}
assert pipe.outputs() == {"feature_table"}
```

Route catalog entries for `raw_table`, `feature_table`, and parameters to `../data-catalog-and-config/SKILL.md`; route running the pipeline to `../runners-and-execution/SKILL.md`.

## Build a Reusable Namespaced Pipeline

Use `pipeline(...)`, not `kedro.pipeline.modular_pipeline`, to reuse a graph with renamed inputs, outputs, and parameters.

Example feature-engineering template:

```python
from kedro.pipeline import Pipeline, node, pipeline


def normalize(raw, options):
    return [value * options["multiplier"] for value in raw]


def summarize(features):
    return {"features": features, "stats": {"rows": len(features)}}


def base_feature_pipeline() -> Pipeline:
    return pipeline(
        [
            node(normalize, ["raw", "params:options"], "features", name="normalize", tags="features"),
            node(
                summarize,
                "features",
                {"features": "feature_table", "stats": "feature_stats"},
                name="summarize",
                tags="reporting",
            ),
        ]
    )


def create_pipeline(**kwargs) -> Pipeline:
    base = base_feature_pipeline()
    train = pipeline(
        base,
        inputs={"raw": "train_raw"},
        outputs={"feature_table": "train_features", "feature_stats": "train_feature_stats"},
        parameters={"options": "train_feature_options"},
        namespace="train_features",
    )
    score = pipeline(
        base,
        inputs={"raw": "score_raw"},
        outputs={"feature_table": "score_features", "feature_stats": "score_feature_stats"},
        parameters={"options": "score_feature_options"},
        namespace="score_features",
    )
    return train + score
```

Expected effects:

- Node names become `train_features.normalize`, `train_features.summarize`, `score_features.normalize`, and `score_features.summarize`.
- Internal datasets such as `features` become namespaced, for example `train_features.features`.
- Exposed inputs and outputs keep the mapped names, for example `train_raw` and `train_features`.
- Parameter references become `params:train_feature_options` and `params:score_feature_options`.
- The combined graph avoids duplicate node names and duplicate output datasets.

Common validation checks:

```python
pipe = create_pipeline()
assert "train_raw" in pipe.inputs()
assert "score_raw" in pipe.inputs()
assert "train_features" in pipe.outputs()
assert "score_features" in pipe.outputs()
assert all(node.name for node in pipe.nodes)
```

## Use Namespaces for Grouping Only

If a deployment or visualization task needs namespaced node names but unchanged dataset names, set `prefix_datasets_with_namespace=False`:

```python
grouped = pipeline(
    base_feature_pipeline(),
    namespace="feature_group",
    prefix_datasets_with_namespace=False,
)
```

This keeps dataset names such as `raw`, `features`, and `feature_table` unchanged while node names receive the namespace. Use this carefully: it does not isolate datasets for graph reuse, so combining two copies can still create duplicate outputs.

For deployment grouping, prefer pipeline-level namespaces and inspect `GroupedNodes`:

```python
for group in pipe.group_nodes_by(group_by="namespace"):
    print(group.name, group.type, group.nodes, group.dependencies)
```

Use `group_by=None` if every node should become its own group.

## Structure Modular Pipeline Code

Inside a Kedro project, a modular pipeline should normally have a package with:

```text
pipelines/<pipeline_name>/__init__.py
pipelines/<pipeline_name>/nodes.py
pipelines/<pipeline_name>/pipeline.py
```

`pipeline.py` should expose `create_pipeline(**kwargs) -> Pipeline`. Keep node functions in `nodes.py` and import them into `pipeline.py`.

Example `__init__.py`:

```python
from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
```

Example `pipeline.py`:

```python
from kedro.pipeline import Pipeline, node
from .nodes import clean, make_features


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        node(clean, "raw", "clean", name="clean"),
        node(make_features, ["clean", "params:features"], "features", name="make_features"),
    ])
```

Project CLI scaffolding (`kedro pipeline create`, template selection, and delete behavior) belongs in `../project-cli-and-sessions/SKILL.md`; this sub-skill owns the graph API and `create_pipeline()` contract.

## Register Pipelines at API Level

A project registry returns a mapping of names to `Pipeline` objects. A default pipeline is conventionally registered under `"__default__"`.

Manual registry pattern:

```python
from kedro.pipeline import pipeline
from .pipelines import features, reporting


def register_pipelines():
    feature_pipe = features.create_pipeline()
    reporting_pipe = reporting.create_pipeline()
    return {
        "features": feature_pipe,
        "reporting": reporting_pipe,
        "__default__": feature_pipe + reporting_pipe,
    }
```

Autodiscovery pattern after project configuration:

```python
from kedro.framework.project import find_pipelines


def register_pipelines():
    pipelines = find_pipelines()
    pipelines["__default__"] = sum(pipelines.values())
    return pipelines
```

Selective discovery:

```python
pipelines = find_pipelines(pipelines_to_find=["features", "reporting"])
```

Use `find_pipelines(raise_errors=True)` when broken or missing `create_pipeline()` functions should fail fast instead of producing warnings and skipping modules.

## Slice and Inspect a Graph Programmatically

Use slicing methods for graph reasoning even when a future run will use CLI flags.

```python
pipe = create_pipeline()

# Direct or transitive subsets.
downstream = pipe.from_nodes("make_features")
upstream = pipe.to_outputs("model_input_table")
tagged = pipe.only_nodes_with_tags("features", "reporting")
namespace_subset = pipe.only_nodes_with_namespaces(["train_features"])

# Intersect several conditions at once.
focused = pipe.filter(
    tags=["features"],
    from_inputs=["train_raw"],
    to_outputs=["train_features"],
)
```

Remember:

- `only_nodes_with_tags("a", "b")` is OR semantics.
- `filter(tags=["a"], to_outputs=["x"])` intersects conditions.
- `from_nodes` includes selected nodes and downstream dependencies.
- `to_nodes` includes selected nodes and upstream requirements.
- `from_inputs` and `to_outputs` traverse through transcoded dataset compatibility.
- Exact node selection by namespaced node usually needs the full name, such as `train_features.normalize`; Kedro may suggest namespaced matches when a bare name is ambiguous.

For `kedro run` flag construction, validate semantics here and then route command details to `../runners-and-execution/SKILL.md`.

## Inspect Preview and LLM Context Surfaces

Use preview payloads for lightweight graph-facing summaries:

```python
from kedro.pipeline import node
from kedro.pipeline.preview_contract import MermaidPreview


def preview_flow():
    return MermaidPreview(content="graph LR\nraw-->features")

preview_node = node(
    lambda raw: raw,
    inputs="raw",
    outputs="features",
    name="identity_features",
    preview_fn=preview_flow,
)

payload = preview_node.preview()
if payload is not None:
    payload_dict = payload.to_dict()
```

Keep previews deterministic and JSON-safe. `preview_fn` does not receive runtime node inputs automatically; use closures only for static context.

Use `llm_context_node(...)` when the graph should construct an `LLMContext` dataset from declared LLM, prompt, and tool datasets:

```python
from kedro.pipeline import Pipeline, llm_context_node, node, tool


def build_lookup(docs, max_matches):
    return {"docs": docs, "max_matches": max_matches}


def answer(context):
    return f"prompts={list(context.prompts)} tools={list(context.tools)}"

pipe = Pipeline([
    llm_context_node(
        outputs="response_context",
        llm="llm",
        prompts=["system_prompt", "user_prompt"],
        tools=[tool(build_lookup, "docs", "params:max_matches")],
        name="response_context_node",
    ),
    node(answer, "response_context", "response", name="answer"),
])
```

This graph declares data dependencies only. Route LLM client construction, prompt datasets, credentials, and actual serving to sibling sub-skills.

## Pre-Execution Graph Review Checklist

Before running or handing off a graph:

- `pipe.describe()` shows expected node order, free inputs, and outputs.
- `pipe.inputs()` contains only catalog-provided datasets and expected `params:*` entries.
- `pipe.outputs()` contains expected final outputs and not accidental intermediates.
- Reused pipelines use `pipeline(...)` with `inputs`, `outputs`, `parameters`, and `namespace` mappings.
- No parameter remapping is placed under `inputs`.
- No two nodes output the same dataset or transcode-compatible base name.
- No node has an output that is also its input.
- Namespaced node selection uses full names where necessary.
- Registry functions return actual `Pipeline` objects, not lists of nodes or `None`.

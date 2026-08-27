# Pipeline and Node API Reference

This reference covers Kedro 1.4.0 graph-authoring APIs exposed from the public `kedro.pipeline` package. The current reusable pipeline helper is `kedro.pipeline.pipeline`; do not use the stale `kedro.pipeline.modular_pipeline` import path.

## Imports and Signatures

Use these imports for public graph APIs:

```python
from kedro.pipeline import GroupedNodes, Node, Pipeline, node, pipeline
```

Current core signatures:

```python
node(func, inputs, outputs, *, name=None, tags=None, confirms=None, namespace=None, preview_fn=None) -> Node
Node(func, inputs, outputs, *, name=None, tags=None, confirms=None, namespace=None, preview_fn=None)
Pipeline(nodes, *, inputs=None, outputs=None, parameters=None, tags=None, namespace=None, prefix_datasets_with_namespace=True)
pipeline(nodes, *, inputs=None, outputs=None, parameters=None, tags=None, namespace=None, prefix_datasets_with_namespace=True) -> Pipeline
```

`pipeline(...)` is a convenience wrapper around `Pipeline(...)` with the same reusable-pipeline remapping behavior.

## Node Construction

A Kedro `Node` wraps one Python callable plus named graph edges.

- `func` must be callable.
- `inputs` may be `None`, a dataset name string, a list of dataset names, or a dict mapping function argument names to dataset names.
- `outputs` may be `None`, a dataset name string, a list of dataset names, or a dict mapping returned dictionary keys to dataset names.
- At least one of `inputs` or `outputs` must be present.
- Node names and tags may contain only letters, digits, hyphens, underscores, and full stops.
- Dataset names containing `.` are allowed but trigger a warning unless they align with the node namespace or are `params:*`; prefer underscores for non-namespace dataset names.
- A node cannot use the same dataset as an input and output, even with transcoding variants stripped to the same base name.
- A node cannot declare duplicate output dataset names.

Example with positional, keyword, and dictionary outputs:

```python
from kedro.pipeline import node


def split_and_score(data, model_options):
    train, test = data[:-1], data[-1:]
    return {"train": train, "test": test, "score": len(data) + model_options["offset"]}

split_node = node(
    split_and_score,
    inputs={"data": "raw_features", "model_options": "params:model_options"},
    outputs={"train": "train_features", "test": "test_features", "score": "model_score"},
    name="split_and_score",
    tags=["features", "scoring"],
)
```

When running a node directly, pass a dictionary keyed by the declared Kedro input dataset names. The return value is a dictionary keyed by declared output dataset names:

```python
result = split_node.run({"raw_features": [1, 2, 3], "params:model_options": {"offset": 10}})
assert set(result) == {"train_features", "test_features", "model_score"}
```

`Node.__call__(**kwargs)` delegates to `Node.run(inputs=kwargs)`.

## Pipeline Construction

A `Pipeline` contains `Node` objects or nested `Pipeline` objects. Nested pipelines are expanded into one graph. Kedro resolves execution order from dataset dependencies, not from the order in which nodes appear in code.

Useful construction patterns:

```python
from kedro.pipeline import Pipeline, node, pipeline


def clean(raw):
    return raw.strip()


def featurize(cleaned, options):
    return f"{cleaned}:{options['version']}"

base = pipeline(
    [
        node(clean, "raw", "cleaned", name="clean", tags="prep"),
        node(featurize, ["cleaned", "params:feature_options"], "features", name="featurize", tags="features"),
    ]
)

training_features = pipeline(
    base,
    inputs={"raw": "training_raw"},
    outputs={"features": "training_features"},
    parameters={"feature_options": "training_feature_options"},
    namespace="train",
)
```

In the reusable example:

- `inputs={"raw": "training_raw"}` exposes `training_raw` without prefixing it as `train.training_raw`.
- `outputs={"features": "training_features"}` exposes that final output without namespace prefixing.
- `parameters={"feature_options": "training_feature_options"}` maps `params:feature_options` to `params:training_feature_options`.
- Internal datasets such as `cleaned` become `train.cleaned` by default.
- Node names become `train.clean` and `train.featurize`.

## Pipeline Operators and Metadata

Pipeline operators return new `Pipeline` objects:

- `pipeline_a + pipeline_b` and `pipeline_a | pipeline_b` combine nodes.
- `pipeline_a - pipeline_b` removes nodes present in the second pipeline.
- `pipeline_a & pipeline_b` intersects nodes.
- `sum(pipelines.values())` is a common registry pattern for combining many pipelines into `__default__`; empty collections should start from `pipeline([])` or rely on Python `sum()` handling of `0` only when values are pipelines.

Inspection methods:

- `pipeline.nodes` returns all nodes in topological order.
- `pipeline.grouped_nodes` returns topologically ready groups of nodes.
- `pipeline.node_dependencies` maps each node to parent nodes.
- `pipeline.inputs()` returns free inputs that must be provided by the runtime catalog.
- `pipeline.outputs()` returns final outputs, excluding intermediate datasets consumed by downstream nodes.
- `pipeline.datasets()` returns all node inputs and outputs.
- `pipeline.describe(names_only=True)` returns a human-readable execution-order summary.
- `pipeline.to_json()` returns JSON containing `kedro_version` plus each node's name, inputs, outputs, and tags.

## Filtering and Slicing API

Use these methods to inspect or create graph subsets before handing execution to a runner:

- `only_nodes(*node_names)` selects exact node names.
- `from_nodes(*node_names)` selects named nodes and everything downstream.
- `to_nodes(*node_names)` selects named nodes and everything upstream required to produce their inputs.
- `only_nodes_with_inputs(*inputs)` selects nodes directly consuming the datasets.
- `from_inputs(*inputs)` selects nodes directly or transitively downstream from datasets.
- `only_nodes_with_outputs(*outputs)` selects nodes directly producing the datasets.
- `to_outputs(*outputs)` selects nodes directly or transitively upstream of datasets.
- `only_nodes_with_tags(*tags)` selects nodes containing any supplied tag.
- `only_nodes_with_namespaces([namespace, ...])` selects nodes whose namespace equals or starts with the supplied namespace.
- `filter(tags=None, from_nodes=None, to_nodes=None, node_names=None, from_inputs=None, to_outputs=None, node_namespaces=None)` intersects all supplied slice conditions.

`filter(...)` applies each condition to the original pipeline and intersects the results. This avoids order-dependent surprises from chaining several slice methods manually.

## Namespaces and GroupedNodes

Pipeline-level `namespace` prefixes node names and, by default, internal datasets and single-parameter names. Explicit `inputs`, `outputs`, and `parameters` mappings are connection points and are not prefixed after mapping.

Set `prefix_datasets_with_namespace=False` when the namespace is only a grouping label and dataset names must stay unchanged.

Node-level `namespace` prefixes the node name and is useful for visual grouping. It does not apply the same dataset/parameter mapping semantics as pipeline-level namespaces.

`group_nodes_by(group_by="namespace")` returns a list of `GroupedNodes` objects:

```python
GroupedNodes(name="features", type="namespace", nodes=["features.clean"], dependencies=[])
```

Supported grouping modes are:

- `"namespace"`: group by top-level namespace; un-namespaced nodes become single-node groups of type `"nodes"`.
- `None` or `"none"`: return one `GroupedNodes` per node.

Unsupported grouping strategies raise `ValueError: Unsupported group_by strategy: ...`.

## Transcoded Dataset Names

Kedro supports transcoded dataset names such as `features@pandas` and `features@spark`. Pipeline dependency and slicing logic strips the transcoding suffix when checking compatibility, so asking for `features` may match multiple transcoded branches.

Avoid mixing a bare dataset name and transcoded variants in the same pipeline, such as `features` and `features@pandas`; Kedro raises an error that the dataset is used with transcoding but referenced without the separator. Duplicate transcoded outputs with the same base name, such as two nodes outputting `features@pandas` and `features@spark`, are also invalid because output base names must be unique.

## Preview Payload API

`node(..., preview_fn=...)` is experimental. The preview function must be callable, takes no node inputs automatically, and must return one of these public preview payloads:

```python
from kedro.pipeline.preview_contract import CustomPreview, ImagePreview, MermaidPreview, TextPreview
```

Preview payload rules:

- `TextPreview(content=str, meta=None)` for text or code blocks.
- `MermaidPreview(content=str, meta=None)` for Mermaid diagrams.
- `ImagePreview(content=str, meta=None)` for URLs or data URIs.
- `CustomPreview(renderer_key=str, content=dict, meta=None)` for JSON-safe custom renderers.
- `meta` and custom content must be JSON-serializable with string dictionary keys.
- `node.preview()` returns `None` if no preview function exists, otherwise validates the returned payload type.
- Kedro emits an experimental warning the first time a `preview_fn` node is created in a session.

## LLM Context Nodes

Kedro 1.4.0 exposes experimental LLM context helpers from `kedro.pipeline` and `kedro.pipeline.llm_context`:

```python
from kedro.pipeline import LLMContext, LLMContextNode, llm_context_node, tool
```

Signatures:

```python
tool(func, *inputs)
llm_context_node(*, outputs, llm, prompts, tools=None, name=None, tags=None, confirms=None, namespace=None, preview_fn=None) -> Node
LLMContextNode(*, outputs, llm, prompts, tools=None, name=None, tags=None, confirms=None, namespace=None, preview_fn=None)
```

Use an LLM context node only to construct an `LLMContext` dataset from declared Kedro inputs. It does not invoke the LLM. All `llm`, prompt, and tool input datasets are normal Kedro inputs and must be supplied by the catalog at execution time. Route actual model clients, credentials, prompt datasets, and server integration concerns to the relevant sibling sub-skills.

## Registry-Facing APIs

Pipeline modules should expose a top-level `create_pipeline(**kwargs) -> Pipeline` function. Project registries usually expose `register_pipelines() -> dict[str, Pipeline]` and may use `find_pipelines()` after project configuration.

`find_pipelines()` discovers modules under a project's `pipelines` package, calls `create_pipeline()`, and accepts only objects that are instances of `Pipeline`. It can skip broken modules with warnings or fail fast with `raise_errors=True`. Use registry APIs to list and combine pipelines, but route project bootstrapping and CLI command details to `../project-cli-and-sessions/SKILL.md`.

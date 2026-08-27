# Pipeline and Node Troubleshooting

Use this reference when a Kedro graph fails during construction, inspection, discovery, or a tiny smoke run. It focuses on `node()`, `Node`, `Pipeline`, and `pipeline()` failures; route catalog configuration to `../data-catalog-and-config/SKILL.md` and execution/runners to `../runners-and-execution/SKILL.md`.

## Import and Version Confusion

### `ModuleNotFoundError: No module named 'kedro'`

Kedro is not installed in the active Python environment. Install the public `kedro` distribution in the environment used by the agent or project.

Validation probes:

```bash
python -c "import kedro; print(kedro.__version__)"
kedro --version
```

### `ModuleNotFoundError: No module named 'kedro.pipeline.modular_pipeline'`

The old `kedro.pipeline.modular_pipeline` import path is not available in Kedro 1.4.0. Replace it with:

```python
from kedro.pipeline import pipeline
```

Then call `pipeline(base_pipeline, inputs=..., outputs=..., parameters=..., namespace=...)`.

### Import errors for `DataCatalog`, `SequentialRunner`, or package dependencies

Some graph-only imports can work while runtime execution imports fail if the environment is incomplete. For graph authoring, first validate:

```python
from kedro.pipeline import Node, Pipeline, node, pipeline
```

For bundled smoke execution or in-memory runner checks, the environment must also import:

```python
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner
```

If those fail, fix the Kedro installation before treating the graph code as broken. Optional server, notebook, or dataset packages are not required for this sub-skill unless the user task explicitly touches them.

## Invalid Node Definitions

### `Invalid Node definition: first argument must be a function`

`node()` received a non-callable first argument. Pass a function, bound method, callable class instance, or another callable object.

### `Invalid Node definition: 'inputs' type must be one of [String, List, Dict, None]`

`inputs` must be `None`, a string, a list of strings, or a dict mapping function parameter names to dataset names. Tuples, sets, integers, and nested objects are invalid.

### `Invalid Node definition: 'outputs' type must be one of [String, List, Dict, None]`

`outputs` must be `None`, a string, a list of strings, or a dict mapping returned dictionary keys to dataset names.

### `Invalid Node definition: it must have some 'inputs' or 'outputs'`

A node cannot have both `inputs=None` and `outputs=None`. If the callable has side effects and returns nothing, at least model its required inputs. Prefer avoiding side-effect-only nodes unless the project design already relies on them.

### `Inputs of '<func>' function expected ... but got ...`

Kedro validates the declared node inputs against the callable signature. Fix by aligning declaration style to the function:

```python
# Positional arguments.
node(func, ["left", "right"], "out")

# Keyword arguments with dataset aliases.
node(func, {"left_arg": "left_dataset", "right_arg": "right_dataset"}, "out")

# Single argument.
node(func, "one_dataset", "out")
```

For `functools.partial`, use `functools.update_wrapper()` if readable logs matter.

### Duplicate node output error

Signals:

- `Failed to create node ... due to duplicate output(s) {'A'}`
- `Output(s) ['D', 'E'] are returned by more than one nodes. Node outputs must be unique.`

Fix within one node by making output names unique. Fix across a pipeline by renaming one node's output, exposing it through `outputs=...`, or adding a namespace/remapping when reusing a pipeline.

### `A node cannot have the same inputs and outputs even if they are transcoded`

A node cannot read and write the same base dataset in one step. Use a new output name such as `cleaned_data`, then let a catalog or later pipeline stage decide persistence. Transcoded forms such as `data@pandas` and `data@spark` still share base name `data` for this validation.

### Invalid node name or tag

Node names and tags can contain letters, digits, hyphens, underscores, and full stops. Spaces and commas are invalid. Prefer simple names such as `split_data`, `train_model`, or `evaluate-model`.

## Pipeline Graph Errors

### `Pipeline nodes must have unique names`

Two nodes have the same `name`, or a reused pipeline was added without a namespace. Fix by naming each node uniquely or wrapping reused pipelines:

```python
from kedro.pipeline import pipeline

combined = pipeline(base, namespace="train") + pipeline(base, namespace="score")
```

### Duplicate outputs after combining reusable pipelines

If two pipeline copies emit the same output dataset, namespace internal datasets and explicitly remap exposed outputs:

```python
train = pipeline(base, inputs={"raw": "train_raw"}, outputs={"features": "train_features"}, namespace="train")
score = pipeline(base, inputs={"raw": "score_raw"}, outputs={"features": "score_features"}, namespace="score")
combined = train + score
```

### `Circular dependencies exist among...`

A chain of nodes feeds back into an earlier input. Print `Pipeline.describe()` on smaller pieces or inspect `node.inputs` and `node.outputs` to find the cycle. Rename one intermediate dataset or split the graph into separate stages so dependencies flow in one direction.

### `Pipeline input(s) {...} not found in the DataCatalog`

The graph is asking for free inputs not present in the runtime catalog. Use this sub-skill to confirm `pipe.inputs()`, then route to `../data-catalog-and-config/SKILL.md` for adding datasets/parameters or to `../runners-and-execution/SKILL.md` for runtime selection.

### Empty filter result

`Pipeline.filter(...)` raises `Pipeline contains no nodes after applying all provided filters` when the intersection of conditions is empty. Inspect each condition separately:

```python
pipe.only_nodes_with_tags("features").describe()
pipe.from_inputs("raw").describe()
pipe.to_outputs("model_input_table").describe()
```

Then combine only conditions that overlap.

### Unknown node, dataset, namespace, or grouping strategy

Common signals:

- `Pipeline does not contain nodes named [...]`
- `Did you mean: ['namespace.node_name']?`
- `Pipeline does not contain datasets named [...]`
- `Pipeline does not contain nodes with the following namespaces: [...]`
- `Unsupported group_by strategy: unknown`

Fix by inspecting available values:

```python
[node.name for node in pipe.nodes]
pipe.datasets()
[node.namespace for node in pipe.nodes]
pipe.group_nodes_by(group_by="namespace")
```

Use full namespaced node names for exact node selection.

## Reusable Pipeline Mapping Errors

### `Parameters should be specified in the 'parameters' argument`

Do not put `params:*` or `parameters` in reusable `inputs=...`. Put parameter remaps under `parameters=...`:

```python
# Wrong
pipeline(base, inputs={"params:alpha": "params:beta"})

# Right
pipeline(base, parameters={"alpha": "beta"})
```

Kedro accepts keys with or without the `params:` prefix in `parameters`; it normalizes single parameters to `params:name` internally. The special name `parameters` refers to the whole parameters dictionary and is not remapped to `params:parameters`.

### `Inputs must not be outputs from another node in the same pipeline`

Reusable `inputs=...` may expose only free inputs of the base pipeline. If you want to expose an intermediate result, map it under `outputs=...` instead.

### `All outputs must be generated by some node within the pipeline`

Reusable `outputs=...` must refer to a dataset produced by a node in the base pipeline. Free inputs cannot be exposed as outputs.

### `Failed to map datasets and/or parameters onto the nodes provided...`

The mapping refers to a dataset or parameter not present in the base pipeline. Check:

```python
base.datasets()
base.inputs()
base.outputs()
```

Then fix spelling or map the correct `params:*` name under `parameters=...`.

## Namespace Warnings

### Dotted dataset name warning

Kedro warns when dataset names contain `.` because dot notation is reserved for namespaces. If the dot is not a namespace, rename the dataset with underscores. If it is a namespace, ensure the dataset prefix aligns with the node namespace.

### `Namespace '...' is interrupted by nodes [...] and thus invalid`

A chain enters a namespace, leaves it, and then re-enters it. Keep related nodes in a continuous namespace path or split the graph so unrelated nodes do not interrupt the namespaced chain. Child namespaces and parallel branches are allowed; interrupted sequential paths are the problem.

### Unexpected namespaced catalog keys

Pipeline-level `namespace` prefixes internal datasets by default. If a free input unexpectedly became `namespace.raw`, expose it:

```python
pipeline(base, namespace="namespace", inputs={"raw"})
```

If every dataset name should remain unchanged and only node names should be grouped, use `prefix_datasets_with_namespace=False`.

## Transcoding Errors

### `The following datasets are used with transcoding, but were referenced without the separator...`

Do not mix `dataset` with `dataset@format` in the same pipeline. Use transcoded names consistently or rename the bare dataset.

### Duplicate transcoded outputs

Kedro treats output base names as unique. Two nodes outputting `features@pandas` and `features@spark` conflict because both strip to `features`. Use distinct base names if both are produced by separate nodes.

### Slicing with transcoded names returns more nodes than expected

Passing a base name such as `features` can match all compatible transcodes. Pass the full name such as `features@pandas` when the task needs a specific branch.

## Preview and LLM Context Errors

### `preview_fn must be a function, not 'str'`

Pass a callable preview function, not a precomputed payload or string.

### `preview_fn must return one of the valid preview types...`

Return one of `TextPreview`, `MermaidPreview`, `ImagePreview`, or `CustomPreview`. Do not return raw strings or dictionaries.

### `value is not JSON-serializable` in preview metadata or custom content

Preview payload `meta` and `CustomPreview.content` must contain JSON-safe scalars, lists, and dictionaries with string keys. Convert objects, paths, classes, and DataFrames to strings or small JSON-safe summaries.

### LLM context node does not call the LLM

`llm_context_node()` constructs an `LLMContext` object from Kedro inputs. A downstream node must consume that context to call an LLM or produce a response. Missing LLM, prompt, or tool datasets are catalog/runtime issues, not graph declaration issues.

## Registry and Discovery Problems

### `find_pipelines cannot be called before the project is configured`

`find_pipelines()` is a project API. Use it inside a configured Kedro project registry. For standalone graph code, call each `create_pipeline()` directly.

### Pipeline discovery skips a module

`find_pipelines()` requires each discovered pipeline module to expose `create_pipeline()` and for that function to return a `Pipeline` object. If development should fail fast, use `find_pipelines(raise_errors=True)` in the registry.

### Tags do not run a registered pipeline

Tags select nodes within the chosen pipeline. If a tagged pipeline is registered outside `__default__`, running by tag alone may not include it. The execution command must select the named pipeline as well. Route the exact `kedro run` command to `../runners-and-execution/SKILL.md`.

## Safe Debugging Checklist

Run these checks before changing catalog or runner code:

```python
print(pipe.describe())
print("inputs", sorted(pipe.inputs()))
print("outputs", sorted(pipe.outputs()))
print("datasets", sorted(pipe.datasets()))
print("nodes", [node.name for node in pipe.nodes])
print("tags", {node.name: sorted(node.tags) for node in pipe.nodes})
print("namespaces", {node.name: node.namespace for node in pipe.nodes})
```

If these are correct, move to catalog and execution troubleshooting in sibling sub-skills.

# Descriptor API Reference

## Descriptor Classes

Meshroom descriptors are imported with:

```python
from meshroom.core import desc
```

Key classes:

```text
BaseNode, Node, CommandLineNode, AVCommandLineNode,
InitNode, InputNode, OutputNode, BackdropNode,
File, StringParam, IntParam, FloatParam, BoolParam,
ChoiceParam, ColorParam, PushButtonParam,
ListAttribute, GroupAttribute, AnySet,
Size2d, Vec2d, Point2d, Line2d, Rectangle, Circle, ShapeList,
StaticNodeSize, DynamicNodeSize, Parallelization
```

## Basic Descriptor Pattern

```python
from meshroom.core import desc

class GenerateFile(desc.Node):
    category = "Custom"
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.IntParam(name="count", label="Count", description="", value=1),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt"),
    ]

    def process(self, node):
        with open(node.output.value, "w") as output:
            output.write(f"{node.input.value} x {node.count.value}\n")
```

## Common Attribute Concepts

- `name` is the API key used in Python and graph serialization.
- `label` and `description` feed the UI.
- `value` is the default for inputs or an expression/dynamic placeholder for outputs.
- `exposed=True` makes an attribute easier to configure in the Graph Editor and output/input workflows.
- `advanced=True` hides expert settings by default.
- `invalidate=False` excludes an input from downstream UID invalidation; use sparingly.
- `enabled` may be a bool or callable receiving the node instance.
- `keyable=True` enables per-view/key values for supported parameter types.
- `commandLineGroup` controls grouping/formatting for generated command-line values.

## Compound Attributes

`ListAttribute` contains homogeneous children declared with `elementDesc`; `GroupAttribute` contains named heterogeneous children declared with `items`; `AnySet` is a dynamic mixed container. Compound values serialize recursively and can contain linked children.

Example:

```python
inputs = [
    desc.ListAttribute(
        name="files",
        label="Files",
        description="Input files",
        elementDesc=desc.File(name="file", label="File", description="", value=""),
        exposed=True,
    ),
    desc.GroupAttribute(
        name="advanced",
        items=[
            desc.BoolParam(name="strict", label="Strict", description="", value=True),
            desc.IntParam(name="limit", label="Limit", description="", value=0),
        ],
        advanced=True,
    ),
]
```

## Node Processing

- `Node.process(self, node)` is for non-parallel Python work.
- `BaseNode.processChunk(self, chunk)` is called for parallelized work; use `chunk.node`, `chunk.range`, `chunk.logger`, and `chunk.logManager`.
- Override `preprocess(self, node)`/`postprocess(self, node)` for setup/aggregation; their status is tracked separately.
- `CommandLineNode.buildCommandLine(self, chunk)` expands descriptor expressions and `commandLineRange` for parallel chunks.
- `CommandLineNode` executes through the provider's runtime environment, so plugin `config.json` and process-env configuration can affect the final command.

## Input and Output Mixins

`InputNode.initialize(node, inputs, recursiveInputs)` receives CLI/UI input lists. Use `resetAttributes`, `setAttributes`, and `extendAttributes` from `IONode` so initialization follows descriptor conventions.

`OutputNode` exposes output configuration:

```python
class ExportResults(desc.Node, desc.OutputNode):
    outputAttributes = ["folder", "label", "enabled"]
    inputs = [
        desc.File(name="folder", label="Folder", description="", value=""),
        desc.StringParam(name="label", label="Label", description="", value="results"),
        desc.BoolParam(name="enabled", label="Enabled", description="", value=True),
    ]
```

- `getOutputAttributes(node)` returns only exposed attributes.
- `setOutputFolder(node, path)` sets all exposed `File` output-folder attributes.
- `setOutputAttribute(node, name, value)` rejects attributes not listed in `outputAttributes`.
- If `outputAttributes` is omitted, the backward-compatible `outputAttribute="output"` is used.

## Size and Resources

- `StaticNodeSize(n)` creates a fixed number of chunks.
- `DynamicNodeSize("inputName")` resolves size from an attribute.
- `Parallelization(staticNbBlocks=0, blockSize=0)` describes chunking.
- `cpu`, `ram`, and `gpu` are resource-level values or callables. A GPU level in a descriptor does not install a GPU backend; the external process/plugin must support it.

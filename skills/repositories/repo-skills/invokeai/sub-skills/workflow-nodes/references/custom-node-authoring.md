# Custom Node Authoring

InvokeAI custom nodes are Pydantic-based invocation classes registered by decorators. Future agents should write custom nodes against `invokeai.invocation_api`, not private `invokeai.app.*` modules, because that public module re-exports the supported authoring surface.

## Minimal Pattern

```python
from invokeai.invocation_api import (
    BaseInvocation,
    BaseInvocationOutput,
    ImageField,
    Input,
    InputField,
    InvocationContext,
    OutputField,
    UIComponent,
    invocation,
    invocation_output,
)

@invocation_output("example_passthrough_output")
class ExamplePassthroughOutput(BaseInvocationOutput):
    image: ImageField = OutputField(description="The output image")

@invocation(
    "example_passthrough",
    title="Example Passthrough",
    tags=["example"],
    category="custom",
    version="1.0.0",
)
class ExamplePassthroughInvocation(BaseInvocation):
    image: ImageField = InputField(description="Image to pass through", input=Input.Connection)
    note: str = InputField(default="", description="Optional note", ui_component=UIComponent.Textarea)

    def invoke(self, context: InvocationContext) -> ExamplePassthroughOutput:
        context.logger.info(f"Passing through {self.image.image_name}: {self.note}")
        return ExamplePassthroughOutput(image=self.image)
```

Checklist:

- Define an output class derived from `BaseInvocationOutput` and decorate it with `@invocation_output("unique_output_type")`.
- Define an invocation class derived from `BaseInvocation` and decorate it with `@invocation("unique_node_type", version="x.y.z")`.
- Annotate every input with `InputField(...)` and every output with `OutputField(...)`; decorator validation rejects missing field metadata.
- Implement `invoke(self, context: InvocationContext) -> YourOutputClass`; the return annotation must be a concrete `BaseInvocationOutput` subclass.
- Use unique non-whitespace type strings for both node and output types.
- Use valid semver for `version`; invalid versions raise `InvalidVersionError` during import.

## Public Imports

`invokeai.invocation_api` re-exports the custom-node authoring surface. It includes:

- Core decorators/classes: `BaseInvocation`, `BaseInvocationOutput`, `invocation`, `invocation_output`, `InvocationContext`, `Classification`, `Bottleneck`.
- Field helpers: `InputField`, `OutputField`, `Input`, `FieldKind`, `UIType`, `UIComponent`, `FieldDescriptions`.
- Mixins and common fields: `WithMetadata`, `WithBoard`, `WithWorkflow`, `ImageField`, `BoardField`, `ColorField`, `LatentsField`, `ConditioningField`, `FluxConditioningField`, `DenoiseMaskField`, `BoundingBoxField`, `MetadataField`.
- Common outputs: primitive outputs such as `StringOutput`, `IntegerOutput`, `FloatOutput`, `BooleanOutput`, `ImageOutput`, collection outputs, scheduler/model outputs, and metadata outputs.
- Model-related field classes and taxonomy values are public, but route detailed model loading/cache work to `../model-management/`.

Avoid importing private invocation internals in custom node packs unless there is no public equivalent. Private imports are more likely to break across InvokeAI releases.

## Decorator Semantics

`@invocation(...)` registers a node class and creates a literal `type` field. Important arguments:

- `invocation_type`: serialized node type and registry key; must be unique and contain no whitespace.
- `title`, `tags`, `category`: UI search/grouping metadata.
- `version`: semver string; omit only for quick local experiments because InvokeAI logs a warning and uses `1.0.0`.
- `use_cache`: default cache setting; set `False` for random/network/stateful nodes.
- `classification`: one of `stable`, `beta`, `prototype`, `deprecated`, `internal`, or `special` via `Classification`.
- `bottleneck`: `Bottleneck.GPU` or `Bottleneck.Network`, used as node metadata.

`@invocation_output(...)` registers a result model and creates a literal `type` field. Output models can also carry `output_meta`, which is node-output metadata and is not exposed as a graph output port.

The registry warns and replaces an existing node/output if a later import uses the same type. If the clobbered node is core InvokeAI, the warning says a core node is being overridden. Treat this as a serious conflict, not a feature.

## Fields and Connection Behavior

`InputField(...)` stores UI metadata plus execution metadata in JSON schema extras. Its `input` argument controls how graph execution handles required data:

- `Input.Direct`: value must be present directly on the node instance.
- `Input.Connection`: value is expected from an incoming edge.
- `Input.Any`: either direct value or incoming edge is allowed.

For `Input.Any` and `Input.Connection`, InvokeAI makes the Pydantic field optional at node-instantiation time so workflows can serialize nodes before upstream edges provide values. Before invoking, `BaseInvocation.invoke_internal()` restores defaults and checks missing required data:

- Required `Input.Connection` with no edge/value raises a required-connection error.
- Required `Input.Any` with no value or edge raises a missing-input error.

Use `Input.Connection` for tensors/images/models that must be produced by upstream nodes. Use `Input.Direct` for hidden execution attributes and values that must be serialized directly. Use `Input.Any` for normal UI-editable fields that may also be connected.

## Field Metadata and UI

Useful `InputField` metadata:

- `title`, `description`, numeric constraints (`gt`, `ge`, `lt`, `le`), string constraints, and `default` are passed through to Pydantic/schema.
- `ui_component=UIComponent.Textarea` renders text as a multi-line field; `UIComponent.Slider` requests a slider; `UIComponent.None_` suppresses specialized component selection.
- `ui_hidden=True` hides internal execution fields in the editor.
- `ui_order` controls field ordering.
- `ui_choice_labels` gives display labels for `Literal[...]` choices.
- `ui_type=UIType.Scheduler` and `ui_type=UIType.Any` are current public non-model hints. Internal `_Collection`, `_CollectionItem`, and `_IsIntermediate` values are reserved for InvokeAI's own iterate/collect/runtime nodes.

Deprecated `UIType` values start with `DEPRECATED_`. Some deprecated model UI hints are migrated to new model-filter metadata, while non-migratable deprecated values are ignored with warnings. For model fields, use `ui_model_base`, `ui_model_type`, `ui_model_variant`, `ui_model_format`, and `ui_model_provider_id` instead of deprecated model `UIType` values.

## Mixins and Reserved Fields

Reserved node attribute/input/output names are validated by decorators. Do not define fields named `id`, `type`, `workflow`, `bottleneck`, `is_intermediate`, `use_cache`, `metadata`, `board`, or `output_meta` yourself.

Use provided mixins instead:

- `WithMetadata` adds internal `metadata`; `context.images.save()` automatically applies it unless metadata is passed explicitly.
- `WithBoard` adds internal `board`; `context.images.save()` automatically applies it unless `board_id` is passed explicitly.
- `WithWorkflow` is deprecated; use `context.workflow` instead.

`BaseInvocation` already provides `id`, `is_intermediate`, and `use_cache`. `BaseInvocationOutput` already provides `output_meta`.

## Node Pack Loading

Custom nodes are loaded from configured node-pack directories. Each top-level node pack must be a directory containing `__init__.py`; hidden directories, underscored directories, files, and directories without `__init__.py` are skipped. The loader imports only packages visible from the pack's `__init__.py`, so import each invocation class there.

Example pack layout:

```text
my_pack/
  __init__.py
  image_nodes.py
  helpers.py
```

```python
# my_pack/__init__.py
from .image_nodes import ExamplePassthroughInvocation
```

When nodes are added or changed, restart the app so the node pack is imported again. If a pack partially imports and then fails, some classes may already be registered; fix the import error and restart cleanly.

## Authoring Guardrails

- Keep custom node imports light; node pack import happens at startup and decorator registration happens during import.
- Avoid side effects in module import other than class registration.
- Make node/output type names globally unique; prefix with a pack or organization identifier when distributing.
- For image/tensor data, store payloads through `InvocationContext` services and return small field references (`ImageField`, `LatentsField`, names), not large objects.
- For random or network-bound operations, set `use_cache=False` and consider `bottleneck=Bottleneck.Network`.
- For unstable nodes, mark `classification=Classification.Beta` or `Classification.Prototype`; avoid `Stable` until serialized workflows can be trusted across releases.

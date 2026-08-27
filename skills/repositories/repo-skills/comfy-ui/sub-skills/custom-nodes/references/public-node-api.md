# Public Node API

ComfyUI also exposes a public `comfy_api.latest` surface for typed node definitions and extension hooks. Use it when writing nodes that benefit from schema objects, typed input/output helpers, normalized execution returns, progress updates, or API-node metadata.

## Main Imports

Typical public API imports are:

```python
from comfy_api.latest import ComfyAPI, ComfyAPISync, ComfyExtension, IO, Input
```

Important exported groups:

- `IO.ComfyNode`: base class for schema-defined nodes.
- `IO.Schema`: node metadata, inputs, outputs, hidden values, flags, and API-node settings.
- `IO.NodeOutput`: normalized execution result that can hold positional results, UI output, expansion data, or a blocking message.
- `IO.Hidden`: enum values such as `unique_id`, `prompt`, `extra_pnginfo`, `dynprompt`, `auth_token_comfy_org`, `api_key_comfy_org`, and `comfy_usage_source`.
- `ComfyAPI` / `ComfyAPISync`: async and sync access to public runtime services such as progress updates.

## Schema-Defined Node Pattern

```python
from comfy_api.latest import IO

class ExampleTypedNode(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ExampleTypedNode",
            display_name="Example Typed Node",
            category="custom/example",
            description="Pass an image through with a strength widget.",
            inputs=[
                IO.Image.Input("image"),
                IO.Float.Input("strength", default=1.0, min=0.0, max=1.0, step=0.01, optional=True),
            ],
            outputs=[IO.Image.Output("image")],
            hidden=[IO.Hidden.unique_id, IO.Hidden.prompt],
        )

    @classmethod
    def execute(cls, image, strength=1.0):
        return IO.NodeOutput(image)
```

The public base class finalizes the schema into classic-compatible properties such as `INPUT_TYPES`, `RETURN_TYPES`, `RETURN_NAMES`, `OUTPUT_NODE`, and `FUNCTION`.

## Schema Fields to Know

- `node_id` is the stable workflow-facing id and should be globally unique.
- `display_name`, `category`, `description`, `search_aliases`, and `essentials_category` drive UI discoverability.
- `inputs` and `outputs` are lists of typed `IO.*.Input` and `IO.*.Output` declarations.
- `hidden` requests injected values; output nodes automatically receive prompt/metadata hidden values after finalization.
- `is_output_node`, `is_input_list`, `is_deprecated`, `is_experimental`, `is_dev_only`, `has_intermediate_output`, and `not_idempotent` map to classic execution/UI flags.
- `accept_all_inputs=True` forwards all prompt inputs to the node, including inputs not declared in schema. Use only for deliberate dynamic nodes.
- `enable_expand=True` is required before returning expansion data in `IO.NodeOutput(expand=...)`.

## Typed Inputs and Outputs

The public API includes typed helpers for common ComfyUI data:

- `IO.Image`, `IO.Mask`, `IO.Latent`, `IO.Audio`, and video/file utility types.
- Widget types such as `IO.String`, `IO.Int`, `IO.Float`, `IO.Boolean`, `IO.Combo`, and `IO.MultiCombo`.
- `IO.Custom("TYPE_NAME")` for custom domain-specific socket types.
- Input options include defaults, bounds, display mode, tooltips, optional inputs, lazy inputs, raw links, socket/widget behavior, and multiselect metadata.

Prefer typed helpers over raw strings when using this API because schema validation catches duplicate ids, invalid price badge dependencies, and output metadata mistakes earlier.

## Execution Return Rules

Public `execute` may be sync or async. Valid returns include:

- `IO.NodeOutput(value1, value2, ui=..., expand=..., block_execution=...)`.
- A tuple, which is normalized to a `NodeOutput`.
- A dict with supported keys such as `result`, `ui`, and `expand`.
- `None`, for no outputs.

If returning `expand`, set `enable_expand=True` in the schema. If returning multiple outputs, the number and order must match `outputs`.

## Progress API

Use the public API instead of older global hooks for progress reporting:

```python
from comfy_api.latest import ComfyAPI, ComfyAPISync

api = ComfyAPI()
api_sync = ComfyAPISync()

await api.execution.set_progress(value=0.5, max_value=1.0)
api_sync.execution.set_progress(value=0.5, max_value=1.0)
```

When called outside an executing node context, pass `node_id` explicitly. Preview images can be supplied as PIL images or compatible image tensors; keep previews small unless deliberately overriding size limits.

## Generated Stubs Caveat

The repository contains stub-generation machinery for public API sync wrappers. Treat it as maintainer infrastructure, not as the normal way to author a custom node. Node authors should import the public API and let the runtime-provided API surface handle sync/async wrappers.

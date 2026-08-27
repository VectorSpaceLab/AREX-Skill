# Prompt Format

## API Prompt vs UI Workflow

ComfyUI's server expects an API prompt object for `/prompt`: a mapping from node id strings to node objects. Each node object has at least:

```json
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 123,
      "model": ["4", 0]
    }
  }
}
```

The UI workflow export is different. It commonly contains top-level UI metadata such as `nodes`, `links`, `groups`, `config`, `version`, positions, widgets, colors, and reroute information. Do not POST that UI workflow directly as `prompt`. Export/save in API format or convert it so each executable node id maps to `{class_type, inputs}`.

## Node Object Rules

- Node ids are object keys. Treat them as strings even when they look numeric.
- `class_type` names the registered node class, such as `LoadImage`, `KSampler`, `SaveImage`, or a custom node mapping name.
- `inputs` is an object whose keys must match that node's required or optional input names.
- Constants/widgets are stored directly as JSON values: strings, numbers, booleans, arrays, objects, or null where the node accepts them.
- Links are two-item arrays: `[upstream_node_id, output_index]`.
- Output indexes are zero-based integers. A bad index can pass shape checks but fail when the upstream node output tuple is read.

## Link Syntax

A normal linked input looks like this:

```json
"image": ["12", 0]
```

This means: take output socket `0` from node id `12` and pass it to the input named `image`. The upstream node must exist. The validator flags missing upstream ids and malformed link arrays, but only a live node schema check can confirm that output socket `0` has the expected type.

A list with a non-integer second element is not a ComfyUI link. For example, `["12", "0"]` is suspicious because output indexes are integers, not strings.

## Minimal Structural Checklist

Before asking a server to run a prompt:

- Top-level JSON is an object, or a wrapper object containing a `prompt` object.
- Each prompt node value is an object.
- Each node has `class_type` as a non-empty string.
- Each node has `inputs` as an object, even if empty.
- Every `[node_id, output_index]` input points to an existing node id.
- The graph has at least one likely output node, or the caller intentionally uses partial execution targets.

## Wrapped Request Shape

Server clients usually send a wrapper like:

```json
{
  "prompt": { "1": { "class_type": "PreviewImage", "inputs": { "images": ["2", 0] } } },
  "client_id": "optional-client-id"
}
```

The graph itself is the value of `prompt`; `client_id`, `extra_data`, and queue options belong to transport/request handling, not inside individual graph nodes.

## Schema Boundary

Static prompt-shape validation catches JSON and graph reference errors. It does not prove that:

- a custom node is installed,
- a `class_type` exists in the running node registry,
- a widget value is in an allowed combo list,
- a linked output type matches a target input type,
- a checkpoint/model name exists,
- runtime resources are available.

For those checks, inspect the node definitions and run ComfyUI's server-side validation. Use `../../custom-nodes/SKILL.md` for node schemas and `../../models-config/SKILL.md` for model-name/path issues.

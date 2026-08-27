# Workflow Expansion Reference

This reference explains how Graph workspace state becomes a custom generation
request.

## Workflow sources

`WorkflowSource` distinguishes where a graph came from:

- local file/user collection,
- server/web-provided shared workflow,
- embedded document workflow.

`WorkflowCollection` can import a JSON file, save/overwrite workflows, remove
items, clear the list, and add a document-embedded graph. A graph may be held as
embedded state until the collection is connected and loaded.

## Parameter coercion

`CustomWorkspace` stores `workflow_params` per workflow ID. When a graph is
selected or updated, metadata from `workflow_parameters` is used to coerce stored
values back to expected types and defaults:

- number controls coerce to `int`/`float` with fallback to default.
- toggles coerce to booleans.
- text and prompt fields coerce to strings.
- choice values fall back to default if not in available choices.
- image/mask/style selectors preserve IDs/names where valid.

If a user's saved parameters appear to reset, inspect graph ID changes and
metadata type changes.

## Custom generation modes

`CustomGenerationMode`:

```text
regular, live, animation
```

- `regular`: one-shot Graph workspace generation.
- `live`: repeats generation/polling for live preview using `_live_poll_rate`.
- `animation`: produces animation jobs/frames rather than a single diffusion
  history item.

Custom outputs can include images and text output. Text output providers are
collected from client output messages; image outputs go through Graph/Krita
output handling.

## `WorkflowInput(kind=custom)`

The custom graph route ultimately creates a `WorkflowInput` with
`custom_workflow` containing:

- raw ComfyUI workflow graph dict,
- parameter map,
- evaluated positive/negative prompts when prompt/style placeholders are used,
- optional checkpoint/sampling model data for style placeholders.

Image, mask, canvas, and layer inputs are injected according to placeholders.
If the final payload is wrong, inspect both the static graph placeholders and
DocumentModel/document state.

## Output behavior

`handle_output` maps client output back into jobs/results. Depending on mode and
output type, a job may be treated as diffusion, animation, or live preview. If a
custom graph returns no images, check whether it uses `ETN_KritaOutput` or only
text/side outputs.

## Cross-skill dependencies

- Server resources: ETN nodes must be installed in ComfyUI for live execution.
  Static inspection can still parse a graph without server connectivity.
- Document/image state: image layer, mask layer, selection, canvas, and style
  placeholders depend on document and style APIs.
- Inference workflows: once custom graph metadata is correct, inspect the final
  `WorkflowInput(kind=custom)` structure.

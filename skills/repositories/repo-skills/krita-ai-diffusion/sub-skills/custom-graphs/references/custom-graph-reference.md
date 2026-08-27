# Custom Graph Reference

The Graph workspace lets users run ComfyUI workflows that contain Krita-specific
placeholder nodes. The plugin inspects those nodes to build UI controls and to
inject canvas, layer, prompt, style, mask, seed, and output behavior at runtime.

## Core parser APIs

- `CustomWorkflow`: stores graph ID, source, and `ComfyWorkflow` graph.
- `WorkflowCollection`: imports/saves/removes workflows, tracks file/web/document
  sources, loads remote workflows after connection, and exposes a Qt list model.
- `workflow_parameters(w: ComfyWorkflow)`: yields `CustomParam` objects from
  ETN placeholder nodes.
- `CustomParam`: parameter metadata with `kind`, `name`, `default`, `min`,
  `max`, `choices`, `display_name`, and `group`.
- `ParamKind`: `image_layer`, `mask_layer`, `number_int`, `number_float`,
  `toggle`, `text`, `prompt_positive`, `prompt_negative`, `choice`, `style`.
- `CustomWorkspace`: selected workflow, persisted per-workflow params, mode,
  live state, outputs, validation error, graph metadata, and custom generation.

## Placeholder node behavior

| Node class | Runtime meaning |
| --- | --- |
| `ETN_KritaCanvas` | Injects current canvas image, width, height, seed, and mask/alpha outputs. |
| `ETN_KritaOutput` | Marks image output that should return to Krita/history/layer application. |
| `ETN_Parameter` | Generates UI parameter controls from `type`, `name`, `default`, `min`, `max`, and connected choices. |
| `ETN_KritaImageLayer` | Lets the user choose a Krita image layer for workflow input. |
| `ETN_KritaMaskLayer` | Lets the user choose a Krita mask/selection layer for workflow input. |
| `ETN_KritaStyle` | Uses a selected style and can expose sampler preset defaults. |
| `ETN_KritaStyleAndPrompt` | Combines style and prompt behavior; only one is allowed per workflow. |
| `ETN_KritaSelection` | Uses selection context for inpaint-like workflows; `context` maps to `InpaintContext`. |

The underlying Comfy graph may also contain normal ComfyUI nodes. The plugin only
creates Krita UI/metadata for known ETN placeholders and parameter nodes.

## Parameter naming and order

`CustomParam.display_name` and `.group` split names on `/` and strip optional
numeric ordering prefixes such as `"2. Detail/4. CFG"`:

- group: `Detail`
- display name: `CFG`
- order: numeric prefixes sort before plain alphabetical names.

Use this to explain why controls are grouped or sorted differently from raw node
IDs.

## `ETN_Parameter` types

Recognized types:

- `number (integer)` -> `ParamKind.number_int`, with integer min/max/default.
- `number` -> `ParamKind.number_float`, with float min/max/default.
- `toggle` -> `ParamKind.toggle`.
- `text` -> `ParamKind.text`.
- `prompt (positive)` -> `ParamKind.prompt_positive`.
- `prompt (negative)` -> `ParamKind.prompt_negative`.
- `choice` -> `ParamKind.choice` if connected node definitions provide choices;
  otherwise falls back to text.
- `auto` -> ignored by parameter listing.
- Unknown non-auto types log a warning and are not turned into rich controls.

## Validation rule

The Graph workspace allows at most one `ETN_KritaStyleAndPrompt` node. Multiple
instances set a validation warning:

```text
Workflow contains multiple 'Krita Style & Prompt' nodes, but only one is allowed.
```

## Static inspection

Use the bundled script:

```bash
python sub-skills/custom-graphs/scripts/inspect_custom_workflow.py workflow.json
```

It reports format, node count, Krita placeholders, parameter ordering/grouping,
outputs, links, and warnings without executing the graph.

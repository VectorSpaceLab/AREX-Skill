# Blueprints and Templates

## What Blueprints Are

Blueprint JSON files are reusable workflow/template descriptions. They may include executable prompt-like content plus UI/template metadata, model placeholders, helper text, or deployment-specific assumptions. Treat them as source material for building a prompt, not automatically as a ready `/prompt` payload.

## Template-Safe Validation

A safe template review checks structure without requiring model downloads or a live GPU/backend:

- JSON parses successfully.
- The file either contains an API prompt object or clearly contains UI/template metadata requiring conversion.
- Prompt-like node objects have `class_type` and `inputs`.
- Links point to existing node ids within the prompt-like graph.
- Placeholder values are explicit and not mistaken for real model filenames.
- Model loader inputs are routed to model/path review rather than hardcoded blindly.
- Output nodes are present or template instructions explain how outputs are produced.

Use `../scripts/validate_prompt_graph.py --allow-ui-workflow --allow-templates file.json` to flag obvious prompt-shape problems while tolerating UI workflow exports and placeholder strings.

## Converting a Template to API Prompt

When an agent receives a UI workflow or blueprint and needs a runnable API prompt:

1. Identify executable nodes and their class mapping names.
2. Convert UI node ids to prompt object keys.
3. Move widget values into the appropriate `inputs` keys expected by each node class.
4. Convert UI link records into `[upstream_node_id, output_index]` input values.
5. Keep only runtime-relevant prompt data under the `prompt` object.
6. Validate structure, then validate against the running node registry.
7. Fill model names, filenames, dimensions, seeds, and prompt text intentionally.

Do not preserve UI-only fields such as node positions, colors, groups, or canvas settings inside API prompt nodes unless a custom node explicitly expects them as input values.

## Placeholder Policy

Templates often contain placeholders such as `<checkpoint>`, `${prompt}`, `MODEL_NAME`, or empty strings. These are useful during drafting but unsafe for direct execution. Before live submission:

- Replace checkpoint/loramodel/vae/controlnet names with values that exist in the configured model folders.
- Replace file inputs with files available to the server.
- Choose concrete dimensions/batch sizes/sampler parameters.
- Remove credentials from prompt JSON and route API-node secrets through the expected server/user configuration.

## Blueprint Review Output

When reviewing a blueprint, report:

- whether it is UI workflow, API prompt, wrapped prompt, or mixed/template format,
- number of prompt-like nodes found,
- missing or malformed `class_type`/`inputs`,
- unresolved links,
- likely output nodes,
- placeholder/model values requiring user action,
- whether live execution is safe, expensive, or backend/model-dependent.

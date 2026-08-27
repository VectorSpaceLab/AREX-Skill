# Flow JSON and Tweaks

Langflow flows are serialized JSON documents that describe a directed graph of component nodes and edges plus flow metadata. A valid exported flow normally has top-level metadata such as `id`, `name`, `description`, `endpoint_name`, `last_tested_version`, `tags`, and a `data` object. The graph itself lives in `data.nodes`, `data.edges`, and often `data.viewport`.

## Flow Shape

Common exported flow shape:

```json
{
  "id": "flow-uuid-or-string",
  "name": "Basic Prompting",
  "description": "...",
  "endpoint_name": "optional-alias",
  "last_tested_version": "1.x.y",
  "data": {
    "nodes": [],
    "edges": [],
    "viewport": {"x": 0, "y": 0, "zoom": 1}
  }
}
```

Some internal and test fixtures use a graph-only form with `nodes` and `edges` at the root. Langflow and `lfx` code paths often accept both `flow["data"]["nodes"]` and `flow["nodes"]`, but exported user-facing files should keep the top-level metadata plus `data.nodes` and `data.edges`.

## Nodes

A component node usually contains:

- `id`: unique component instance id such as `ChatInput-b6UCc`; this is the key used by edges and node-id tweaks.
- `type`: React/node rendering type, usually `genericNode` for component nodes and note-specific values for notes.
- `data.id`: component instance id, normally matching the root `id`.
- `data.type`: component class/type such as `ChatInput`, `ChatOutput`, `Agent`, `Prompt`, `LanguageModelComponent`, or a custom component type.
- `data.node.display_name`: human-readable component name.
- `data.node.template`: editable component fields. Most field entries are objects that include keys such as `name`, `display_name`, `type`, `value`, `required`, `show`, `advanced`, `password`, and `load_from_db`.
- `position`, `positionAbsolute`, `measured`, and selection/dragging fields: editor state used by the visual workspace.

Node ids must be unique. Edges reference the root node ids, not display names. If you copy nodes by hand, change every copied root `id`, `data.id`, edge `source`/`target`, and handle payload id that points to the copied node.

## Edges

An edge connects `source` to `target` node ids. The `data.sourceHandle` and `data.targetHandle` objects describe output and input ports:

- `sourceHandle.id`: source node id.
- `sourceHandle.name`: source output name such as `message`.
- `sourceHandle.output_types`: emitted data types such as `Message`, `Data`, `DataFrame`, or `LanguageModel`.
- `targetHandle.id`: target node id.
- `targetHandle.fieldName`: input field to populate on the target node.
- `targetHandle.inputTypes` or `targetHandle.type`: accepted target data type.

Use compatible types when connecting ports. Message-to-message/chat fields are common. JSON/Data ports should feed fields that expect structured data. Table/DataFrame and LanguageModel ports are specialized. If an edge points to a missing node or an incompatible field, static validation may pass JSON parsing but graph build or `lfx validate --level 3` can fail or warn.

## Notes and Layout

Starter projects often include note nodes that explain the flow. Notes can carry Markdown text under a node description field. Regression tests distinguish note nodes from component nodes for editor layout: note nodes may carry width/height on the root node, while non-note component nodes should generally not depend on root-level `width` and `height` for execution. Treat visual-only fields as editor metadata; do not use them as runtime control signals.

## Entry Points and Outputs

For chat-style flows, the standard shape is `ChatInput` → model/agent/workflow components → `ChatOutput`.

- The Playground chat interface expects a connected `ChatInput`, a model or agent-style middle path, and a `ChatOutput`.
- Text Input/Text Output flows can still move text-like values, but they are not the best target for the Playground chat UI.
- Webhook flows use a `Webhook` component as the run entry point and often connect it to `Parser` before the rest of the flow.
- API and `lfx run` execution can target flows that are not Playground-friendly, but the caller must provide appropriate `input_value`, `input_type`, `output_type`, `output_component`, and `session_id` values.

Run responses are nested. For API runs, useful text is usually under an output result such as `outputs[*].outputs[*].results.message.text` or a similar `message` field. Graph tests also show fallback behavior where result extraction joins chat messages, stringifies list-shaped messages, falls back to `results` when messages are absent, and reports `(no output)` when no output exists.

## Tweaks

Tweaks are one-run overrides. They modify component parameters at runtime without permanently changing the flow file.

Canonical API body pattern:

```json
{
  "input_value": "Text to input to the flow",
  "input_type": "chat",
  "output_type": "chat",
  "session_id": "optional-session-id",
  "tweaks": {
    "ChatInput-b6UCc": {
      "should_store_message": false
    }
  }
}
```

Rules for reliable tweaks:

- Prefer node ids as keys, e.g. `ChatInput-b6UCc`, because display names can repeat. Some runtime paths also accept component display names, but node ids are less ambiguous.
- Field names inside each tweak must match keys in the node's `data.node.template`, such as `input_value`, `system_prompt`, `model`, `api_key`, `temperature`, or `should_store_message`.
- A non-dict top-level tweak such as `{"temperature": 0.2}` can be applied across all nodes that have that field. Use this only when the field name is intentionally global; otherwise it can silently touch the wrong component or no component.
- For regular fields, a scalar value usually sets the field's `value`.
- For dict fields, pass a dict. A single-key dict shaped as `{"value": ...}` may be unwrapped by runtime processing.
- For file fields, scalar tweaks map to `file_path` rather than `value`.
- For `NestedDict` fields, JSON-like strings may be repaired/parsed by runtime utilities; prefer valid JSON objects to avoid surprises.
- Runtime code refuses to override code-execution fields such as literal `code` fields, fields typed as `code`, and known code/sandbox fields on code-execution components. Do not try to use tweaks to inject executable code.

## Tweak Debugging Checklist

When a tweak is ignored:

1. Confirm the outer `tweaks` value is an object, not a JSON string inside a string.
2. Confirm the component key matches a node `id` exactly, including suffix casing.
3. Confirm the field key exists in `data.node.template` for that node.
4. Confirm the field is not a protected code field.
5. Confirm the request is JSON with `Content-Type: application/json` when using the REST run endpoint.
6. If using embedded widgets or generated snippets, confirm JSON props are correctly stringified or property-bound for the framework.
7. For duplicate display names, use node ids rather than display names.
8. For credential fields, prefer global variables or request headers over embedding secrets in exported flow JSON.

## Secrets and Variables

Exports can include literal secrets if a user typed a real key directly into a component field and chose to save keys. Safer patterns:

- Use Langflow global variables for API keys and provider credentials.
- Keep exported JSON free of literal secrets.
- For API runs, pass request-scoped variables with headers named `X-LANGFLOW-GLOBAL-VAR-{VARIABLE_NAME}`.
- For offline `lfx run`, ensure load-from-db/global-variable field values are valid environment variable names when using the no-op database path. Valid names use letters, numbers, and underscores and do not start with a number.
- If `lfx validate` reports a missing credential, either provide the matching environment variable, connect the credential field from another component, or intentionally skip credential checks for a structure-only pass.

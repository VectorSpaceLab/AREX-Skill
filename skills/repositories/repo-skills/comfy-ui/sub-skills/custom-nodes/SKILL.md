---
name: custom-nodes
description: "Implement, inspect, test, and package ComfyUI custom nodes,
  including classic INPUT_TYPES nodes, public comfy_api nodes, hidden inputs,
  async/lazy behavior, output metadata, and API-node credentials."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# ComfyUI Custom Nodes

Use this sub-skill when the user wants to scaffold, diagnose, inspect, or package ComfyUI node definitions. It covers classic `NODE_CLASS_MAPPINGS` nodes, the public `comfy_api.latest` node API, API-provider nodes, and common execution metadata contracts.

## Route First

- Use `references/node-authoring.md` for classic custom nodes with `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, `CATEGORY`, `NODE_CLASS_MAPPINGS`, and `NODE_DISPLAY_NAME_MAPPINGS`.
- Use `references/public-node-api.md` for `comfy_api.latest.IO.ComfyNode`, `IO.Schema`, typed inputs/outputs, `IO.NodeOutput`, progress updates, node replacement, and public API caveats.
- Use `references/api-nodes.md` for provider-backed nodes that set `is_api_node=True`, use Comfy Org hidden credentials, call proxy endpoints, or need internet/API-key warnings.
- Use `references/troubleshooting.md` when validation fails, a node is missing from the UI, output tuple lengths mismatch, `ANY` causes type confusion, async/lazy validation fails, or API nodes are disabled.
- Use `../workflow-execution/SKILL.md` for prompt graph validation/execution behavior and `../server-api/SKILL.md` for HTTP/websocket transport, API-node server configuration, and credential routing.

## Fast Authoring Checklist

1. Create a Python package or module under ComfyUI's `custom_nodes` loading area with an importable `__init__.py` when using a package.
2. Export `NODE_CLASS_MAPPINGS = {"StableNodeId": NodeClass}`; add `NODE_DISPLAY_NAME_MAPPINGS` for friendly names.
3. Define `INPUT_TYPES` as a `@classmethod` returning `required`, optional `optional`, and optional `hidden` dictionaries.
4. Set `RETURN_TYPES` to a tuple of output type strings; `RETURN_NAMES`, `OUTPUT_IS_LIST`, and `OUTPUT_TOOLTIPS` must align by index when present.
5. Set `FUNCTION` to the exact method name and return a tuple with one item per `RETURN_TYPES`, or a dict with `result`/`ui`/`expand` only when using the supported execution form.
6. Add `CATEGORY`, `DESCRIPTION`, and flags such as `OUTPUT_NODE`, `EXPERIMENTAL`, `DEPRECATED`, or `DEV_ONLY` only when they match behavior.
7. Avoid `IO.ANY` / `"*"` unless the node genuinely accepts arbitrary types; prefer concrete types or multi-types like `FLOAT,INT`.
8. Use hidden inputs deliberately: `PROMPT`, `UNIQUE_ID`, `EXTRA_PNGINFO`, and `DYNPROMPT` are injected by execution and should not be user widgets.

## Bundled Helpers

- `scripts/scaffold_custom_node.py` writes a safe classic custom-node package with required image input, optional strength widget, optional hidden prompt metadata, class mappings, and a tuple-length self-check.
- `scripts/inspect_node_definitions.py` statically inspects one or more Python files for classic node mappings, missing attributes, input/return schema issues, `ANY` usage, hidden inputs, and probable return tuple mismatches.

Both scripts are standalone and safe by default. Run `python scripts/scaffold_custom_node.py --help` or `python scripts/inspect_node_definitions.py --help` from this sub-skill directory for options.

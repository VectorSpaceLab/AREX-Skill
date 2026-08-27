---
name: workflow-execution
description: "Build, validate, debug, and reason about ComfyUI API prompt JSON,
  graph execution, caching, async nodes, output metadata, blueprints, and
  inference failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Workflow Execution

Use this sub-skill when an agent needs to convert or check a ComfyUI API prompt, debug prompt graph errors, explain why nodes execute or are cached, validate workflow templates/blueprints, or reason about async/lazy execution behavior.

## When to Use

- Validate a prompt before sending it to ComfyUI's `/prompt` endpoint.
- Explain the difference between exported UI workflow JSON and API prompt JSON.
- Find missing node ids, malformed `[node_id, output_index]` links, absent `class_type`, or non-object `inputs` values.
- Diagnose execution failures involving validation, lazy inputs, async nodes, progress messages, output metadata, cache reuse, or expensive inference runs.
- Review a blueprint or reusable template for placeholder safety before filling model names or parameters.

For endpoint submission, queue/history/websocket handling, and live server transport, use `../server-api/SKILL.md`. For node schema/class implementation details, use `../custom-nodes/SKILL.md`. For model filenames, search paths, memory modes, and backend flags, use `../models-config/SKILL.md`.

## Fast Workflow

1. Decide whether the file is API prompt JSON or UI workflow JSON; convert/export to API format before POSTing.
2. Run `python scripts/validate_prompt_graph.py prompt.json` for structural checks that do not import ComfyUI or load models.
3. Check every node has string id, `class_type`, and `inputs`; every link is `["upstream_id", output_index]` or `[upstream_id, output_index]`.
4. Verify node-specific input names/types against the active node registry or docs; the bundled validator intentionally cannot know custom node schemas.
5. Confirm output nodes such as save/preview nodes are reachable from intended generation nodes.
6. If live execution fails, inspect ComfyUI validation errors first, then graph dependency/cycle errors, then async/runtime/model/backend errors.

## References

- `references/prompt-format.md` explains API prompt JSON shape, link syntax, and UI workflow differences.
- `references/execution-semantics.md` explains validation order, topological execution, lazy inputs, async behavior, output metadata, and cache modes.
- `references/blueprints-and-templates.md` explains blueprint/template handling and safe placeholder validation.
- `references/troubleshooting.md` maps common prompt/execution failures to fixes.
- `scripts/validate_prompt_graph.py` performs self-contained structural validation for prompts and template-like JSON.

## Grounding Notes

This guidance is distilled from ComfyUI's execution engine, graph scheduler, cache implementation, async/progress behavior, inference patterns, API examples, and blueprint/template formats. Full live execution can require optional model/backend capabilities; validate prompt shape separately from model availability and hardware-specific runtime behavior.

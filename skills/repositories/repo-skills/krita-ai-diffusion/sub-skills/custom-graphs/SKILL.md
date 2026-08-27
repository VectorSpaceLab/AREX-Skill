---
name: custom-graphs
description: "Guides Krita AI Diffusion Graph workspace custom ComfyUI
  workflows, ETN Krita placeholders, parameter metadata, outputs, live mode, and
  animation tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# custom-graphs

Use this sub-skill when the task is about importing, validating,
parameterizing, or running custom ComfyUI workflows through the Krita AI
Diffusion Graph workspace.

Trigger examples:

- A user has a ComfyUI `workflow.json` and wants to know which Krita UI controls
  will be generated.
- Debugging ETN placeholder nodes such as `ETN_KritaCanvas`,
  `ETN_KritaOutput`, `ETN_Parameter`, `ETN_KritaImageLayer`,
  `ETN_KritaMaskLayer`, `ETN_KritaStyle`, or `ETN_KritaStyleAndPrompt`.
- Explaining `workflow_parameters`, `CustomParam`, `ParamKind`, grouped order,
  custom workflow save/import/overwrite behavior, or document-embedded graphs.
- Diagnosing custom Graph validation warnings, live custom generation, or
  animation mode.

## Safe entry point

```bash
python sub-skills/custom-graphs/scripts/inspect_custom_workflow.py workflow.json
```

The helper parses a workflow JSON file statically and does not connect to
ComfyUI, load models, launch Krita, or run generation.

## References

- [references/custom-graph-reference.md](references/custom-graph-reference.md):
  placeholder node and parameter metadata contract.
- [references/workflow-expansion.md](references/workflow-expansion.md): how the
  Graph workspace turns placeholders/params into inputs, live output, and
  animation work.
- [references/troubleshooting.md](references/troubleshooting.md): custom graph
  validation and import/output failures.
- [scripts/inspect_custom_workflow.py](scripts/inspect_custom_workflow.py):
  static custom workflow inspector.

## Boundaries

- For the final `WorkflowInput(kind=custom)` payload and image request fields,
  route to `inference-workflows`.
- For server-side availability of ETN custom nodes and model resources, route to
  `server-resources`.
- For document/layer/mask/image semantics used by placeholders, route to
  `document-image-state`.

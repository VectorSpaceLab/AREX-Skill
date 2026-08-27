---
name: inference-workflows
description: "Guides Krita AI Diffusion WorkflowInput construction, prompt
  preparation, inpaint, refine, upscale, control-image, and ComfyUI workflow
  lowering tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# inference-workflows

Use this sub-skill when the task is about image-generation request payloads or
how Krita AI Diffusion lowers plugin state into local ComfyUI/cloud work.

Trigger examples:

- Building, inspecting, serializing, or deserializing `WorkflowInput`.
- Choosing among `WorkflowKind.generate`, `refine`, `inpaint`, `refine_region`,
  `upscale_simple`, `upscale_tiled`, `control_image`, and `custom`.
- Debugging prompt/style/LoRA/wildcard/layer-token preparation before a job is
  sent to a client.
- Explaining inpaint fill/mask/reference choices or selection/crop extents.
- Estimating `passes_count`, `cost`, or request image payload shape without
  running actual generation.
- Reviewing ComfyUI workflow lowering in `backend.workflow` or
  `backend.comfy_workflow`.

## Safe entry points

```bash
python sub-skills/inference-workflows/scripts/inspect_workflow_input.py --kind generate --round-trip
python sub-skills/inference-workflows/scripts/inspect_workflow_input.py --kind inpaint --round-trip
python sub-skills/inference-workflows/scripts/inspect_workflow_input.py --kind upscale-tiled --target 2048x1536 --round-trip
```

These commands construct tiny in-memory payloads and do not connect to ComfyUI,
launch Krita, download models, call cloud APIs, or generate images.

## References

- [references/api-reference.md](references/api-reference.md): dataclass/API
  contracts for `WorkflowInput` and related inputs.
- [references/workflow-recipes.md](references/workflow-recipes.md): request
  recipes for generate, refine, inpaint, upscale, control image, prompt/LoRA,
  and ComfyUI lowering.
- [references/troubleshooting.md](references/troubleshooting.md): workflow-kind,
  prompt, mask, model, and serialization failure recovery.
- [scripts/inspect_workflow_input.py](scripts/inspect_workflow_input.py): bundled
  offline request inspector.

## Boundaries

- For server URLs, model catalogs, custom nodes, cloud/local clients, or managed
  server errors, route to `server-resources`.
- For Qt workspace state that decides when `DocumentModel.generate()` enqueues a
  particular workflow kind, route to `ui-workspaces` as well.
- For custom ComfyUI Graph workspace metadata and ETN placeholders, route to
  `custom-graphs`.
- For `Image`, `Mask`, `Bounds`, layer tokens, prompt comments, style JSON, or
  PNG metadata, route to `document-image-state`.

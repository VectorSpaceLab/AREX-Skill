---
name: ui-workspaces
description: "Guides Krita AI Diffusion Qt model, workspace, settings, job
  queue, connection state, live preview, upscaling, animation, and UI routing
  tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# ui-workspaces

Use this sub-skill when the task is about plugin UI/model state rather than the
backend request dataclasses alone.

Trigger examples:

- Understanding `DocumentModel`, `Workspace`, `QueueMode`, `ProgressKind`,
  `ErrorKind`, `JobKind`, or `JobState`.
- Debugging why Generate, Live, Upscale, Animation, or Graph workspace enqueues a
  job or reports a validation/error state.
- Working with observable properties, settings persistence, connection state,
  or job queue behavior.
- Running headless Qt model tests or static enum inspection.
- Mapping UI controls to `WorkflowInput` fields.

## Safe entry points

```bash
python sub-skills/ui-workspaces/scripts/inspect_workspace_enums.py --static-only
QT_QPA_PLATFORM=offscreen python sub-skills/ui-workspaces/scripts/inspect_workspace_enums.py --import-live
```

Static mode is safest and performs no imports. Live import mode requires a
package/test environment where `ai_diffusion` imports successfully.

## References

- [references/workspace-model-reference.md](references/workspace-model-reference.md):
  workspace/model/job state and observable property map.
- [references/ui-routing-and-settings.md](references/ui-routing-and-settings.md):
  how UI settings route generation, server mode, apply behavior, persistence,
  and test setup.
- [references/troubleshooting.md](references/troubleshooting.md): Qt/headless,
  job queue, connection, and validation recovery.
- [scripts/inspect_workspace_enums.py](scripts/inspect_workspace_enums.py):
  static/live enum and model-property inspector.

## Boundaries

- For `WorkflowInput` payload internals after a workspace enqueues work, route
  to `inference-workflows`.
- For server mode/backend/URL and connection resources, route to
  `server-resources`.
- For custom Graph workspace node metadata, route to `custom-graphs`.
- For document, layer, image, mask, prompt, style, and persistence details,
  route to `document-image-state`.

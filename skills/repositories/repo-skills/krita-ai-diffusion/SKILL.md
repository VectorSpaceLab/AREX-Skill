---
name: krita-ai-diffusion
description: "Routes Krita AI Diffusion plugin tasks across inference workflows,
  ComfyUI and cloud resources, Qt workspaces, custom graphs, and Krita document
  image state."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# krita-ai-diffusion

Use this repo skill for Krita AI Diffusion, a Python plugin that adds diffusion
image generation, inpainting, live preview, upscaling, animation, custom
ComfyUI graph execution, and model/server management to Krita.

This skill is self-contained. Use the bundled references and scripts here; do
not send users to source-checkout docs, tests, examples, or scripts as runtime
instructions. Treat actual image generation, model downloads, managed ComfyUI
installation, and cloud API calls as side-effecting operations that require an
explicit user request.

## First safe checks

From any checkout or installed package environment, prefer safe read-only checks
before launching Krita, ComfyUI, cloud requests, downloads, or generation:

```bash
python scripts/check_krita_ai_diffusion_environment.py --static-only
python scripts/list_krita_ai_diffusion_resources.py --summary
```

If the package is importable and the user needs live API facts:

```bash
QT_QPA_PLATFORM=offscreen python scripts/check_krita_ai_diffusion_environment.py --strict
python scripts/list_krita_ai_diffusion_resources.py --parse-url localhost:8188
```

Known baseline for this generated skill:

- Plugin package version: `1.52.1`
- Resource catalog/server version: `1.52.0`
- Safe verification scope: CPU/package inspection, static graph inspection, and
  selected fast tests. GPU generation, managed server install/download, external
  ComfyUI runtime, and cloud service execution are optional/unselected.

Read [references/repo-provenance.md](references/repo-provenance.md) before
checking staleness or refreshing this skill. Read
[references/development-and-testing.md](references/development-and-testing.md)
for contributor commands and test-selection policy. Read
[references/troubleshooting.md](references/troubleshooting.md) for cross-cutting
install/import, Qt, server, model, and generation failure recovery.

## Route by user task

- **Build, inspect, serialize, or debug image generation requests and ComfyUI
  workflow lowering**: use
  [sub-skills/inference-workflows/SKILL.md](sub-skills/inference-workflows/SKILL.md).
  Covers `WorkflowInput`, `WorkflowKind.generate`, `inpaint`, `refine`,
  upscaling, control image workflows, prompt/style/LoRA preparation, inpaint
  mode detection, cost/pass estimates, and offline request inspection.

- **Connect to, configure, inventory, or troubleshoot ComfyUI/cloud/managed
  server resources**: use
  [sub-skills/server-resources/SKILL.md](sub-skills/server-resources/SKILL.md).
  Covers `ComfyClient`, `CloudClient`, `Server`, `resources.py`, required and
  optional custom nodes, model catalog/resource IDs, URL normalization, backend
  selection, install/download safety, and server error parsing.

- **Work with Qt/Krita model state, workspace routing, jobs, queue behavior, or
  UI settings**: use
  [sub-skills/ui-workspaces/SKILL.md](sub-skills/ui-workspaces/SKILL.md).
  Covers `DocumentModel`, `Workspace`, `QueueMode`, generation/live/upscale/
  custom/animation workspaces, `ConnectionState`, progress/error kinds,
  settings persistence, and headless Qt constraints.

- **Import, validate, parameterize, or run custom ComfyUI Graph workspace
  workflows**: use
  [sub-skills/custom-graphs/SKILL.md](sub-skills/custom-graphs/SKILL.md).
  Covers ETN Krita placeholder nodes, `workflow_parameters`, graph UI metadata,
  custom generation modes, live/animation graph behavior, and static custom
  workflow inspection.

- **Manipulate Krita documents, layers, regions, image/mask data, prompt text,
  styles, metadata, and persistence**: use
  [sub-skills/document-image-state/SKILL.md](sub-skills/document-image-state/SKILL.md).
  Covers `Image`, `ImageCollection`, `Mask`, `Bounds`, `Extent`, layer tokens,
  prompt comments/wildcards/LoRA extraction, style JSON, PNG metadata, document
  persistence, regions, and layer-state troubleshooting.

## Package and runtime notes

- The plugin is designed for Krita's embedded Python interpreter. Outside Krita,
  tests and safe inspection rely on Qt/PyQt and the repo's mock Krita module.
- The source package intentionally vendors `ai_diffusion.websockets` for plugin
  releases. If importing `ai_diffusion` from a source checkout fails with a
  missing websockets message, initialize or package the vendored websockets
  submodule before claiming the plugin is installed correctly.
- Avoid third-party runtime assumptions beyond Qt/PyQt and websockets unless a
  workflow explicitly covers server-side ComfyUI packages.
- `api.py`/`WorkflowInput` is the boundary for image generation requests:
  everything relevant to a generation job must be represented there before it
  is sent to local ComfyUI or cloud clients.

## Verification summary

This skill was verified with static frontmatter/link/path checks, bundled script
compilation and help checks, package import/API smoke checks, and selected fast
native tests that do not require generation backends. No import into DisCo's
managed repo-skill library was performed because the user requested `not import`.

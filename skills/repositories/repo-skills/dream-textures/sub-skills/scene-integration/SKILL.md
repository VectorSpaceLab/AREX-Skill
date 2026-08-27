---
name: scene-integration
description: "Routes Dream Textures Blender scene workflows: texture projection,
  Cycles render pass, Dream Textures render-engine nodes, and scene-derived
  ControlNet annotation maps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Scene Integration

Load this sub-skill when the user is working with Dream Textures and Blender scene data rather than an Image Editor-only generation. Stay router-like: choose the right scene path, load the linked reference, run the safe size helper when dimensions are part of the problem, and route install/model/backend-only issues to sibling skills.

## Route first

- **Project Dream Texture onto selected mesh faces**: use [references/texture-projection.md](references/texture-projection.md) for selected objects, Edit Mode, selected faces, projected UVs, viewport depth/color input, material creation, and optional bake. Use [references/troubleshooting.md](references/troubleshooting.md) for disabled buttons, `No objects selected`, `Enter edit mode`, `No faces selected.`, warped projection, viewport color surprises, or GPU offscreen failures.
- **Use the Cycles Dream Textures render pass**: use [references/render-pass-and-engine.md](references/render-pass-and-engine.md) for Cycles setup, pass inputs, compositor routing, animation behavior, color management, and final scaled render size. Run [scripts/validate_scene_generation_size.py](scripts/validate_scene_generation_size.py) before changing render resolution or percentage.
- **Build or diagnose the Dream Textures render engine node tree**: use [references/render-pass-and-engine.md](references/render-pass-and-engine.md) for render-engine setup, node executor behavior, and Stable Diffusion node tasks. Use [references/controlnet-annotations.md](references/controlnet-annotations.md) when the graph involves Depth, Normal, OpenPose, ADE20K, Viewport Color, or ControlNet nodes.
- **Use scene-derived ControlNet or annotation maps**: use [references/controlnet-annotations.md](references/controlnet-annotations.md) for ControlNet node contracts, collection versus scene sources, map prerequisites, model-map matching, and minimal Depth/OpenPose/ADE20K node recipes.
- **Triage scene workflow failures**: start with [references/troubleshooting.md](references/troubleshooting.md), then route to setup, generation, or backend only if the failure is outside scene integration.

## Prerequisites to confirm

Before giving workflow instructions, identify which scene surface the user is on:

1. **Texture projection** lives in the 3D Viewport sidebar under the Dream panel. It requires selected mesh object(s), Edit Mode, selected faces, a visible/current viewport, and either a depth-to-image model route or a depth ControlNet route.
2. **Cycles render pass** lives in Render Properties while the render engine is Cycles. It requires the Dream Textures render pass to be enabled. If pass input includes depth, the view-layer Z pass and a depth-capable model are required.
3. **Dream Textures render engine** uses render engine `DREAM_TEXTURES` and an assigned Dream Textures node tree. The default node tree feeds Render Properties resolution into a Stable Diffusion node and then to Group Output.
4. **Annotation/ControlNet maps** require matching scene data: camera and visible geometry for depth/normal/ADE20K, mapped or recognizable armature bones for OpenPose, ADE20K labels for segmentation, and a visible 3D Viewport for Viewport Color.
5. **Generation size** should be planned as multiples of 64. For the Cycles render pass, check the final scaled size after resolution percentage; for texture projection and render-engine nodes, check the planned generation width/height.

## Bundled references and safe script

- [references/texture-projection.md](references/texture-projection.md): Project Dream Texture operation, viewport input choices, depth model versus depth ControlNet route, projected UVs, material/bake behavior, and projection recipes.
- [references/render-pass-and-engine.md](references/render-pass-and-engine.md): Cycles render pass setup, pass inputs, size scaling, compositor socket, animation advice, Dream Textures render-engine overview, node categories, Stable Diffusion node behavior, and executor details.
- [references/controlnet-annotations.md](references/controlnet-annotations.md): Depth/Normal/OpenPose/ADE20K/Viewport Color maps, ControlNet node contract, map prerequisites, model-map matching, and minimal node-tree recipes.
- [references/troubleshooting.md](references/troubleshooting.md): symptom table and decision trees for projection, render pass, model mismatch, ControlNet mismatch, VRAM, compositor, and GPU offscreen issues.
- [scripts/validate_scene_generation_size.py](scripts/validate_scene_generation_size.py): Blender-free argparse helper. Example:

```bash
python scripts/validate_scene_generation_size.py \
  --workflow render-pass \
  --width 1000 --height 700 \
  --resolution-percentage 50 \
  --render-pass-input color-depth
```

Use `--json` when a parent agent needs a machine-readable summary.

## Fast checklists

### Texture projection checklist

1. Select the target mesh object(s) in the 3D Viewport.
2. Enter Edit Mode and select target faces; only selected faces receive material/UV updates.
3. Use Local View if unrelated visible objects should not contribute to the viewport depth map.
4. Choose **Depth** when prompt/model should control color; choose **Depth and Color** when existing viewport/material colors should matter.
5. Choose one conditioning route: depth-to-image model, or Use ControlNet with a depth ControlNet model.
6. Match planned size to viewport aspect where possible; validate multiples of 64 with `--workflow texture-projection`.
7. Enable Bake only when the target UV map is chosen and the user wants the result transferred from Projected UVs to an existing unwrap.

### Cycles render-pass checklist

1. Set render engine to Cycles.
2. Enable the Dream Textures render pass in Render Properties.
3. Pick pass input: `color`, `depth`, or `color-depth`.
4. If depth is involved, enable the view-layer Z pass and select a depth-capable model.
5. Run the size helper using raw Output Properties dimensions and resolution percentage; the add-on validates the scaled final size.
6. In the Compositor, enable Use Nodes and connect Render Layers **Dream Textures** to Composite **Image** if the generated pass should be the final output.
7. For animation, keep seed/prompt/noise stable unless per-frame variation is intended.

### Render-engine node-tree checklist

1. Set render engine to Dream Textures and assign or create a Dream Textures node tree.
2. Ensure a Group Output exists; node execution starts from linked Group Output inputs.
3. Feed Stable Diffusion Width/Height from Render Properties or explicit integer nodes, then validate with `--workflow render-engine`.
4. Use Depth-to-Image task only with a depth map and depth-capable model.
5. Use ControlNet nodes only with map-compatible models: depth with depth, normal with normal, OpenPose with OpenPose, ADE20K with segmentation/ADE20K.
6. Inspect blank maps by checking camera, render visibility, collection scope, ADE20K labels, armature/bone mapping, and GPU offscreen context.

## Boundaries and sibling routes

This sub-skill owns scene interaction, projection, render pass, render-engine node trees, and scene-derived annotation/ControlNet guidance. Route away instead of expanding scope:

- **Install, add-on import, dependency variants, model download/link/import, Hugging Face token, DreamStudio key, checkpoint config choices**: route to `setup-and-models`.
- **Image Editor prompt-to-image, image-to-image, inpaint/outpaint, upscaling, prompt history, file batch prompts, image-only ControlNet preprocessing**: route to `generation-workflows`.
- **Backend class implementation, Diffusers internals, scheduler/model enum tracebacks, generator subprocess import failures, custom community backend code**: route to `backend-and-api`.

## Troubleshooting route

Use the shortest path from symptom to reference:

- Projection disabled or failed before generation: [references/troubleshooting.md](references/troubleshooting.md#projection-specific-checks), then [references/texture-projection.md](references/texture-projection.md#target-selection-requirements).
- Render-pass dimension error: [references/troubleshooting.md](references/troubleshooting.md#dimension-multiples), then run [scripts/validate_scene_generation_size.py](scripts/validate_scene_generation_size.py).
- Missing depth/Z pass or unsupported model in the render-pass panel: [references/render-pass-and-engine.md](references/render-pass-and-engine.md#cycles-dream-textures-render-pass) and [references/troubleshooting.md](references/troubleshooting.md#model-and-controlnet-mismatches).
- Blank scene annotation map: [references/controlnet-annotations.md](references/controlnet-annotations.md#annotation-nodes) and [references/troubleshooting.md](references/troubleshooting.md#gpu-offscreen-and-headless-blender-issues).
- ControlNet gives distorted or weak results: [references/controlnet-annotations.md](references/controlnet-annotations.md#choosing-the-right-conditioning-map) and verify model-map matching before adjusting conditioning scale.
- VRAM or GPU offscreen failures: [references/troubleshooting.md](references/troubleshooting.md#vram-and-performance-recovery); for backend tracebacks after generation starts, route to `backend-and-api`.

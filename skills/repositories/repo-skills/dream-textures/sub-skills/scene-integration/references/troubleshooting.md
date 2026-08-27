# Scene Integration Troubleshooting

## Purpose

Use this for Dream Textures scene workflow failures: disabled projection, missing selected objects/faces, edit-mode requirements, render-pass dimension errors, missing camera/Z/depth data, VRAM pressure, wrong model type, ControlNet map/model mismatches, and GPU offscreen limitations.

## Quick triage table

| Symptom / error | Likely cause | What to do |
| --- | --- | --- |
| **Project Dream Texture** button disabled | Operator poll failed selection, backend validation, or generator-busy check. | Check selected mesh objects, Edit Mode, selected faces, model selection, and whether another generation is running. |
| `No objects selected` | No target mesh selected in the 3D Viewport. | Select at least one mesh object. If the UI offers fixes, switch to Object Mode or select mesh objects, then return to Edit Mode. |
| `Enter edit mode` | A target object is selected but not in Edit Mode. | Switch target mesh to Edit Mode and select faces. Projection intentionally targets selected faces only. |
| `No faces selected.` | Selected objects exist, but no face is selected in Edit Mode. | Use face select mode and select target faces; optionally Select All Faces for full-object projection. |
| Projection output warps across a large face | Projected UVs on a broad unbroken polygon do not have enough geometry to follow the surface. | Subdivide the mesh or select smaller/denser regions before projecting. |
| Projection ignores expected material colors | Input mode is Depth only, or viewport shading does not show the colors you expect. | Choose **Depth and Color**, switch viewport to material preview/rendered shading, and lower Noise Strength if preserving colors. |
| `Image dimensions must be multiples of 64` | Cycles render pass scaled output size is not divisible by 64. | Run `python scripts/validate_scene_generation_size.py --workflow render-pass --width W --height H --resolution-percentage P` and update render resolution or percentage. |
| Render-pass depth controls show `Z Pass Disabled` | Dream Textures pass input uses depth but the view layer Z pass is off. | Enable the Z pass in the View Layer/Render Properties panel before rendering. |
| Render-pass panel says `Unsupported model` / select depth model | Depth or Color+Depth pass selected with a non-depth model. | Select a depth model such as `stabilityai/stable-diffusion-2-depth`, or use Color input with an image-to-image capable model. |
| Blank or bad depth/normal/ADE20K/OpenPose maps | No camera, hidden objects, excluded collection, unlabeled ADE20K objects, unmapped armature bones, or offscreen render failure. | Set a scene camera, ensure render visibility, check collection scope, enable ADE20K/OpenPose mappings, and test a simpler visible scene. |
| ControlNet has little effect or distorts badly | Control map type and ControlNet model do not match, conditioning scale is inappropriate, or map is blank. | Match depth/normal/OpenPose/ADE20K map to a model trained for that map type; inspect/bake the map first; tune conditioning scale. |
| Blender/GPU error from offscreen rendering | Texture projection and annotation maps use `gpu.types.GPUOffScreen`, which needs an available GPU context and often a visible viewport. | Avoid headless/background runs for projection/viewport nodes; use a visible Blender session and simplify the scene. |
| Render pass or projection crashes/slowdowns with VRAM errors | Cycles plus Diffusers can exceed GPU VRAM. | Lower resolution, reduce steps/batch, enable backend memory optimizations, render Cycles on CPU to reserve GPU VRAM for Dream Textures, or use a smaller model. |
| Projection or render pass waits indefinitely after generation starts | Backend callback did not return, generator subprocess failed, or generation was cancelled/blocked. | Cancel/release the generator in the Dream panel, inspect Blender console/system console logs, then route backend-specific errors to `backend-and-api`. |

## Projection-specific checks

### Disabled button decision tree

1. Is there a selected object? If not, select mesh objects.
2. Is the active target in Edit Mode? If not, switch to Edit Mode.
3. Are faces selected? If not, select faces in face-select mode.
4. Is a backend/model selected and valid for the task?
   - Depth model route: use a depth-to-image model.
   - ControlNet route: enable Use ControlNet and choose a depth ControlNet model.
5. Is another Dream Textures generation running? Wait, cancel, or release the generator.

The source operator uses these validation gates before enabling `shade.dream_texture_project`, so a disabled button is usually intentional and recoverable.

### No selected objects / faces

Projection writes material indices and UVs only on selected faces. In multi-object edit workflows, every selected mesh can receive the material, but at least one selected face across the selected objects is required. Non-mesh selected objects are ignored for material assignment, but visible scene objects can still affect the rendered depth map unless Local View excludes them.

### UV and bake surprises

- **Projected UVs** is created or reused when Bake is off.
- Bake uses the active/destination UV layer, so the user must choose the intended target UVs before generating.
- Baked images are packed Blender image datablocks, not external files by default.
- If the baked texture appears on the wrong UV island, verify active UV maps per object and repeat projection with Bake settings corrected.

## Render-pass checks

### Dimension multiples

The render pass validates scaled dimensions after applying resolution percentage, not only the raw Output Properties dimensions. Example: `1024x768` at `50%` becomes `512x384`, both valid multiples of 64. `1000x700` at `50%` becomes `500x350`, invalid.

Use:

```bash
python scripts/validate_scene_generation_size.py --workflow render-pass --width 1000 --height 700 --resolution-percentage 50 --render-pass-input color-depth
```

Then apply one of the suggested scaled/raw sizes.

### No camera or no depth

Depth annotations use a scene camera by default; projection uses the active viewport matrices instead. For render-engine annotation maps or render-pass depth:

- Set a scene camera.
- Ensure the camera sees the target geometry.
- Enable Z pass for the Cycles render pass when pass input includes depth.
- Keep geometry render-visible and included in the selected collection, if collection scoping is used.

### Compositor not showing the generated pass

If render completes but the final output is still the regular Cycles render, the Dream Textures pass may exist but not be connected. In the Compositor: enable **Use Nodes**, then connect **Render Layers > Dream Textures** to **Composite > Image**. If the socket is missing, confirm the render pass was registered and enabled while using Cycles.

## Model and ControlNet mismatches

| Workflow | Correct model family | Common mismatch |
| --- | --- | --- |
| Projection Depth mode | Depth-to-image model | Base prompt-to-image model selected, causing validation/fix-it errors. |
| Projection Use ControlNet | Base image model plus depth ControlNet | No ControlNet model, non-depth ControlNet, or missing first ControlNet entry. |
| Render pass Color | Image-to-image capable model | Expecting depth geometry preservation from color-only input. |
| Render pass Depth / Color+Depth | Depth-to-image model | Non-depth model triggers unsupported model guidance. |
| Render-engine Depth ControlNet | Depth ControlNet model | Using normal/OpenPose/ADE20K model with depth map. |
| Render-engine Normal/OpenPose/ADE20K | Matching ControlNet model | Map type does not match selected model. |

Route model acquisition, checkpoint import, and token/network issues to `setup-and-models`. Route backend validation implementation details to `backend-and-api`.

## VRAM and performance recovery

Scene workflows are heavier than Image Editor generation because they combine Blender scene rendering, GPU offscreen map generation, and Diffusers inference.

Try these in order:

1. Validate and reduce dimensions, starting at `512x512` or `768x512`.
2. Reduce steps and avoid multiple iterations/batches during debugging.
3. For render pass workflows, render Cycles on CPU so GPU memory is available for Dream Textures.
4. Disable extra ControlNets or use a smaller model.
5. Enable backend memory optimizations such as attention slicing, VAE slicing/tiling, or lower precision if supported by the selected backend.
6. If the host cannot provide a GPU/viewport context, avoid projection and viewport-color annotation in background/headless sessions.

## GPU offscreen and headless Blender issues

Projection, depth maps, normals, OpenPose, ADE20K, and viewport color use Blender GPU offscreen APIs. They are not safe to treat as pure Python or headless CLI workflows. Common limitations:

- A visible 3D Viewport may be required, especially for viewport color capture and Project Dream Texture.
- Offscreen rendering can fail without a GPU context or with restricted remote-display/headless sessions.
- Viewport Color specifically searches for a `VIEW_3D` area and window region.
- Texture projection relies on current `context.region` and `context.space_data.region_3d` matrices.

If a user is running Blender in background mode, recommend a visible Blender session for these workflows or switch to non-viewport Image Editor workflows where possible.

## When to stop and route elsewhere

- Missing add-on install, missing `.python_dependencies`, dependency variant questions, model downloads, Hugging Face/DreamStudio credentials: route to `setup-and-models`.
- Prompt construction, image editing, outpainting, prompt history, AI upscaling, image-only ControlNet processors: route to `generation-workflows`.
- Tracebacks inside backend `generate`, scheduler/model validation internals, generator subprocess import failures, custom backends: route to `backend-and-api`.

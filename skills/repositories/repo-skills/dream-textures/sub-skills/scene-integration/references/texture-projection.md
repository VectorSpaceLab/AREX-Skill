# Texture Projection

## Purpose

Read this when a user asks about Project Dream Texture, selected faces, edit mode, projected UVs, viewport depth/color input, or baking a generated scene texture onto an existing UV layout.

## What Dream Textures projects

Texture projection starts from the current 3D Viewport view. Dream Textures renders scene depth from that view, optionally captures the viewport color, generates an image, then assigns a material whose image texture is mapped onto the selected faces from the view direction. The source workflow is documented as `Project Dream Texture`; the source operator is `shade.dream_texture_project`.

Important consequences:

- The projection view is the active 3D Viewport camera-like view, not necessarily the scene camera.
- The depth map aspect ratio follows the 3D Viewport window. Pick width/height that match that viewport shape, for example `768x512` for a landscape viewport or `512x512` for a square viewport.
- All visible viewport objects affect the depth map. To make only selected objects affect depth, use Blender Local View before generating.
- Large unbroken faces can warp because one projection must cover a broad surface. Subdivide the mesh or select smaller face regions when projection stretching is visible.

## Target selection requirements

Before pressing **Project Dream Texture**:

1. In the 3D Viewport, select at least one mesh object to receive the material.
2. Enter **Edit Mode** on the selected target object(s).
3. Select at least one face. Only selected faces receive the projected material and UV updates.
4. Optionally enter **Local View** if unrelated objects should not affect depth.
5. Keep the desired view angle and focal length. The add-on writes projected UVs from the viewport-to-face mapping at generation time.

The projection operator intentionally disables itself or emits fix-it guidance if any of these selection conditions fail. Typical error labels are `No objects selected`, `Enter edit mode`, and `No faces selected.`

## Inputs: Depth versus Depth and Color

The projection panel exposes scene input choices through the `dream_textures_project_framebuffer_arguments` setting:

| UI choice | Internal value | What is sent to generation | Best use |
| --- | --- | --- | --- |
| Depth | `depth` | A scene depth map rendered from the 3D Viewport. | Structure-faithful texture generation when the prompt should control color/style. |
| Depth and Color | `color` | Viewport color plus the depth map. The UI also exposes Noise Strength for this path. | Style transfer or preserving existing viewport colors/material cues. |

For Depth and Color, Dream Textures temporarily renders the viewport color with overlays hidden and uses the current viewport shading. Switch to material preview/rendered shading when the user expects EEVEE/Cycles material color to influence the generated result.

## Model requirements and ControlNet alternative

Projection has two conditioning modes:

- **Depth model mode**: Dream Textures sets the generation task to Depth-to-Image. Use a depth-capable model such as `stabilityai/stable-diffusion-2-depth`. This is the documented default requirement.
- **Use ControlNet mode**: Dream Textures switches the task back to Prompt-to-Image and supplies the viewport depth map as the first ControlNet image. Select a depth ControlNet model in the projection panel and set its conditioning scale. Use this when the base image model is not a depth-to-image model but a compatible depth ControlNet is installed.

Route missing downloads, checkpoint import, Hugging Face tokens, and backend dependency variants to `setup-and-models`. Stay in this sub-skill for choosing between depth-model projection and depth-ControlNet projection.

## What the operator writes

When generation starts successfully, Dream Textures performs these scene mutations:

1. Creates a new material with shader nodes: image texture connected to the Principled BSDF base color, plus a UV Map node.
2. Adds that material to each selected mesh object that has material slots/data.
3. Finds or creates a UV layer named **Projected UVs**.
4. For every selected face, maps each loop to normalized screen coordinates from the generation viewport and assigns the new material index.
5. Generates the depth map via GPU offscreen drawing and updates the image texture during step previews.
6. Names the final generated image from the prompt subject and seed.

If **Bake** is disabled, the material uses the **Projected UVs** layer. If **Bake** is enabled, Dream Textures uses the active target UV layer on each selected object's mesh as the destination and bakes the projected result into a packed Blender image named like the generated image plus `(Baked)`. Baking is useful when the user wants the result on an existing unwrap rather than a viewport-projected UV layer.

## Practical recipes

### Project a new texture onto selected faces

1. Select the mesh object(s).
2. Enter Edit Mode and select the target faces.
3. Optionally use Local View to exclude background scene objects from depth.
4. Open the 3D Viewport sidebar, Dream panel, projection section.
5. Choose a depth-capable model or enable ControlNet and choose a depth ControlNet.
6. Enter prompt, negative prompt, scheduler, seed, steps, and size as needed.
7. Use the bundled size helper if manually choosing size: `python scripts/validate_scene_generation_size.py --width 768 --height 512 --workflow texture-projection`.
8. Pick **Depth** or **Depth and Color**. Use Depth and Color only when existing viewport colors should guide the output.
9. Enable **Bake** only if the selected objects already have target UV maps or need one-texture-per-existing-UV output.
10. Press **Project Dream Texture** and watch the viewport or shader preview.

### Preserve existing material colors during projection

- Use **Depth and Color**.
- Switch viewport shading to the color source the user expects: material preview/rendered for material color, not solid mode unless solid color is intended.
- Lower Noise Strength when preserving existing color/composition matters; raise it when the prompt should dominate.
- Confirm the model supports the chosen conditioning route. Depth-to-Image mode needs a depth model; ControlNet mode needs a matching depth ControlNet.

### Bake projected result to existing UVs

1. Select each target object and ensure the desired destination UV map exists and is active.
2. In Edit Mode select the faces to project.
3. Enable **Bake** in the projection actions panel.
4. For each selected object, choose the target UVs if Blender exposes the UV search field.
5. Generate. Dream Textures creates the projection using view-space **Projected UVs**, then bakes from that projection into the active/destination UV coordinates and packs the result image.

## Validation signals

A future agent should be able to answer projection questions using these concrete signals:

- Disabled Project Dream Texture button with object/edit/face selection errors means selection preconditions failed before generation.
- Warped projection on a large polygon usually means too few faces/UV samples; subdivide or target smaller selected faces.
- Output stretches because viewport aspect and image size differ; make the generation dimensions resemble the viewport window aspect.
- Colors ignored because **Depth** was selected or the viewport was in a shading mode that did not show the expected material/rendered colors.
- Projection works but render pass does not: switch to [render-pass-and-engine.md](render-pass-and-engine.md); the two workflows use different UI surfaces and scene inputs.

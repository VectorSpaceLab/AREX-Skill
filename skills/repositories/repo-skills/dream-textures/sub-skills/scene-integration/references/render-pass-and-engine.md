# Render Pass and Dream Textures Render Engine

## Purpose

Read this for Cycles Dream Textures render pass questions, compositor routing, render dimensions, animation behavior, or the separate Dream Textures render engine and node tree.

## Cycles Dream Textures render pass

Dream Textures monkey-patches Cycles to register an additional render pass named **Dream Textures**. When enabled in Render Properties, Cycles renders the scene first, then Dream Textures runs Stable Diffusion on one of the selected pass inputs and writes the generated pixels into the Dream Textures pass.

### Setup checklist

1. In Render Properties, set render engine to **Cycles**.
2. Enable the **Dream Textures** render pass panel checkbox.
3. Choose backend/model and prompt options in the Dream Textures render properties panel.
4. Choose **Pass Inputs**:
   - **Color** (`color`): uses the Cycles Combined pass as an Image-to-Image input.
   - **Depth** (`depth`): uses the Cycles Depth/Z pass as a Depth-to-Image input with no color.
   - **Color and Depth** (`color_depth`): uses both Combined color and Depth/Z as a Depth-to-Image input.
5. If using Depth or Color and Depth, enable the view layer **Z** pass and select a depth-capable model such as `stabilityai/stable-diffusion-2-depth`.
6. In the Compositor, enable **Use Nodes** and connect the **Dream Textures** output socket on the Render Layers node to the **Image** socket of the Composite node if the generated image should become the final render result.

### Dimensions and scaling

The render pass uses the final scaled render size:

```text
size_x = render.resolution_x * render.resolution_percentage / 100
size_y = render.resolution_y * render.resolution_percentage / 100
```

Both scaled dimensions must be multiples of 64. If not, Dream Textures reports an error like:

```text
Image dimensions must be multiples of 64 ... closest is 768x512
```

Use the bundled helper before rendering:

```bash
python scripts/validate_scene_generation_size.py --workflow render-pass --width 1000 --height 700 --resolution-percentage 50 --render-pass-input color-depth
```

The helper validates the scaled size, suggests nearest multiples of 64, and summarizes whether the chosen pass input needs a depth model or Z pass.

### Prompt controls that matter most

- **Noise Strength**: important for Color and Color+Depth inputs. Lower values preserve composition/colors; higher values let Stable Diffusion change the scene more. When using Depth-only input, color preservation is not relevant.
- **Seed**: a fixed seed is better for coherent style transfer across animation frames. Random seed can be useful for experimentation but may flicker across frames.
- **Model**: Color input can use image-to-image capable models; Depth/Color+Depth requires a depth model.
- **Resolution**: start around `512x512` or similarly modest multiples of 64, then increase only if VRAM allows.

### Animation behavior

The render pass runs each time the scene is rendered, including animations. Most render-pass Dream Textures properties can be keyframed like normal Blender properties; the add-on evaluates the scene properties for each frame. For stable animation style transfer, prefer a fixed seed, stable prompt, modest noise strength, and the depth or color+depth input if geometry consistency matters.

### Color management behavior

The render pass source code converts the Cycles Combined pass with color management into sRGB before generation. After generation, it writes pixels back with an inverse color-management transform so Blender's final display transform remains sensible. This matters when diagnosing color mismatches: distinguish color-management mismatch from prompt/noise/model effects.

## Dream Textures render engine and node tree

Dream Textures also provides a custom render engine with id **DREAM_TEXTURES** and label **Dream Textures**. Unlike the Cycles render pass, this engine executes a Dream Textures node tree to produce the render result directly.

### When to use the render engine instead of the Cycles pass

Use the Cycles render pass when the user wants Cycles to render a scene, then run Stable Diffusion as a post-process pass. Use the Dream Textures render engine when the user wants a node-based image-generation graph that can combine render properties, scene annotation maps, ControlNet conditioning, image files, utility image operations, and Stable Diffusion nodes.

### Engine setup overview

1. Set render engine to **Dream Textures**.
2. In Render Properties, select a backend for the render engine.
3. Create or assign a Dream Textures node tree. The **New Node Tree** operator creates a default tree with:
   - **Render Properties** node feeding **Resolution X** and **Resolution Y** into a **Stable Diffusion** node.
   - **Stable Diffusion** node output connected to the group **Image** output.
4. Use node categories for Pipeline, Input, Utility, Annotations, and Group nodes.
5. Render. The engine executes the node tree from the group output, updates progress per node, writes image arrays into the Combined render pass, and writes scalar/string group outputs into render stamp metadata.

### Core node categories

| Category | Nodes | Operating use |
| --- | --- | --- |
| Pipeline | Stable Diffusion, ControlNet | Generate images and package ControlNet conditioning. |
| Input | Integer, String, Collection, Image, Image File, Render Properties | Feed prompts, dimensions, image data, collections, frame number, and output paths. Image File is registered only for Blender 3.5+. |
| Annotations | Depth Map, Normal Map, OpenPose Map, ADE20K Segmentation Map, Viewport Color | Render scene-derived maps for ControlNet or direct image workflows. |
| Utilities | Math, Random Value, Random Seed, Seed, Clamp, Frame Path, Crop Image, Resize Image, Join Images, Color Correct, Separate/Combine Color, Switch, Compare, Replace String | Build dynamic prompts/paths, crop/resize/join maps, color-correct outputs, and branch node graphs. Resize Image is registered only for Blender 3.5+. |
| Group | Group Output | Required terminal node; the engine starts execution from the group output. |

### Stable Diffusion node behavior

The **Stable Diffusion** node exposes tasks:

- Prompt to Image
- Image to Image
- Depth to Image
- Inpaint

Inputs include Depth Map, Source Image, Noise Strength, Prompt, Negative Prompt, Width, Height, Steps, Seed, CFG Scale, and ControlNets. Sockets are enabled/disabled by task:

- Source Image: image-to-image, depth-to-image, inpaint.
- Noise Strength: image-to-image and depth-to-image; defaults to `1.0` for depth-to-image.
- Depth Map: depth-to-image.
- ControlNets: all tasks except depth-to-image.

The node builds a `GenerationArguments` object, maps a linked ControlNet node or list of nodes to API ControlNet objects, executes the selected backend, and waits for the callback result before returning the generated image.

### Node executor behavior to remember

- The executor evaluates from the group output backward through linked inputs.
- Unlinked sockets supply their default values.
- Multiple links to one input become a list of upstream outputs, which is how multiple ControlNets can be passed.
- The switch node evaluates lazily: only the selected branch is evaluated.
- The executor has a per-run cache for nodes, but source code currently initializes an empty cache per execution context. Treat outputs as per-render results, not persistent scene cache.

## Common render-pass versus render-engine confusions

- **Cycles render pass** requires Cycles and compositor socket routing. It uses `dream_textures_render_properties_*` scene settings.
- **Dream Textures render engine** uses render engine `DREAM_TEXTURES`, an assigned `dream_textures_render_engine.node_tree`, and node categories registered by the add-on.
- **Texture projection** lives in the 3D Viewport sidebar and writes materials/UVs. It is neither the Cycles render pass nor the custom render engine.
- **Image Editor generation** is not scene-integrated unless the source image or ControlNet image was derived from the scene. Route general Image Editor generation to `generation-workflows`.

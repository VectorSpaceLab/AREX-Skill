# Editing, outpainting, and AI upscaling

This reference covers source-image editing, inpainting, seamless repair, outpainting, and Stable Diffusion x4 upscaling. It assumes the required model is installed. Route model acquisition and dependency setup to `../setup-and-models/`.

## Source image modify workflows

Enable `Source Image`, choose `File` or `Open Image`, and set `Action` to `Modify` for image-to-image or depth-conditioned editing.

| `Image Type` | Source interpretation | API task | Model requirement |
| --- | --- | --- | --- |
| `Color` | RGB/color image controls style and composition. | `ImageToImage(image, strength, fit)` | prompt-to-image model |
| `Color and Generated Depth` | RGB image plus generated depth from MiDaS/DPT. | `DepthToImage(depth=None, image=init_image, strength=strength)` | depth model |
| `Color and Depth Map` | RGB image plus secondary grayscale depth map. | `DepthToImage(depth=grayscale(init_depth), image=init_image, strength=strength)` | depth model |
| `Depth` | Source image is grayscale depth; color ignored. | `DepthToImage(depth=grayscale(init_image), image=None, strength=strength)` | depth model |

Important controls:

- `Noise Strength` (`strength`): how much latent noise is mixed into the source. Low values preserve more composition/color; high values change more. Values below 1 may run only a fraction of requested sampler steps.
- `Fit to width/height` (`fit`): if enabled, resize the source to the generation size. If disabled, use source-native dimensions.
- `Seamless Axes`: `Auto-detect` can inspect the source image and then set circular padding axes before generation.

## Inpainting

Inpainting fills erased or masked regions. It requires an inpainting model such as `stabilityai/stable-diffusion-2-inpainting` or an equivalent inpaint checkpoint.

Alpha-mask workflow:

1. Open the image in an Image Editor.
2. Use the `Mark Inpaint Area` brush to erase/mark the part to fill. The workflow uses alpha transparency as the mask.
3. Enter a prompt describing the desired fill.
4. Enable `Source Image`, choose `Open Image` or `File`, set `Action` to `Inpaint`.
5. Set `Mask Source` to `Alpha Channel`.
6. Generate with an inpainting model.

Prompt-mask workflow:

1. Set `Mask Source` to `Prompt`.
2. Fill `Mask Prompt` with the object/area to segment.
3. Adjust `Confidence Threshold` (`text_mask_confidence`, default `0.5`). Higher values usually produce smaller, stricter masks.
4. Generate with an inpainting model.

Prompt masks use CLIPSeg (`CIDAS/clipseg-rd64-refined`) through `transformers`. Missing dependencies, blocked downloads, or uncached model weights can fail before diffusion starts. Use alpha masks for offline deterministic workflows.

The `Replace` (`inpaint_replace`) slider is visible in the UI, but the distilled generator path consumes `strength`, mask source, mask prompt, and confidence. Diagnose failures with those fields first.

## Seamless texture repair by inpainting

To repair visible borders on an existing texture:

1. Erase/mark edge seams with the inpaint brush.
2. Use a material prompt such as `mossy stone texture`.
3. Set `Seamless Axes` to `Both` (`xy`) for a fully tiling texture, or to a concrete single axis when only one direction should tile.
4. Enable `Source Image`, choose the source, set `Action` to `Inpaint`, and use `Alpha Channel` mask source.
5. Generate with an inpainting model.

`Auto-detect` checks source-image edge continuity when dimensions are at least 8x8. Explicit axes are safer when the output must tile exactly.

## Outpainting model and coordinate rules

Outpainting extends a source image by building an RGBA canvas, cropping a transparent tile, and delegating to the inpaint workflow. It requires an inpainting model and uses the generation `Size` fields as the tile size.

`outpaint_origin = (x, y)` is the tile's top-left corner relative to the original image top-left `(0, 0)`. The source image occupies `[0, source_width) x [0, source_height)`. The tile occupies `[x, x + tile_width) x [y, y + tile_height)`.

Hard bounds from `generator_process/actions/outpaint.py`:

- `-tile_width <= x <= source_width`
- `-tile_height <= y <= source_height`

Equality at an extreme is technically valid but creates no overlap on that axis. The UI warns `Outpaint has no overlap, so the result will not blend` when `x <= -tile_width`, `y <= -tile_height`, `x >= source_width`, or `y >= source_height`.

Overlap with the original source is:

```text
overlap_width  = max(0, min(source_width,  x + tile_width)  - max(0, x))
overlap_height = max(0, min(source_height, y + tile_height) - max(0, y))
```

Use positive overlap whenever style continuity matters. For 512-sized tiles, 32-128 px is a practical starting range. Too little overlap blends poorly; too much overlap leaves little new area.

## Outpaint origin recipes

Use the bundled planner before entering coordinates in Blender:

```bash
python scripts/plan_outpaint_origin.py --source-size 512x960 --tile-size 512x512 --overlap 64 --region bottom-right
```

For the repository's documented 512x960 source, 512x512 tile, 64 px overlap, bottom-right side recipe:

```text
x = source_width - overlap = 512 - 64 = 448
y = source_height - tile_height = 960 - 512 = 448
origin = (448, 448)
```

This extends the right edge while aligning the tile to the bottom of the taller source. To grow a canvas both downward and rightward, do sequential passes or use the helper's `--strategy outside` and inspect warnings/actual overlap.

Default `edge` strategy used by the helper:

| Region | Origin intent |
| --- | --- |
| `right` | Extend the right edge: `x = source_width - overlap`, vertically centered if the source is taller than the tile. |
| `left` | Extend the left edge: `x = -tile_width + overlap`, vertically centered. |
| `top` | Extend above: `y = -tile_height + overlap`, horizontally centered. |
| `bottom` | Extend below: `y = source_height - overlap`, horizontally centered. |
| `top-right` | Extend the right side while aligning to top when possible. |
| `bottom-right` | Extend the right side while aligning to bottom when possible. |
| `top-left` | Extend the left side while aligning to top when possible. |
| `bottom-left` | Extend the left side while aligning to bottom when possible. |
| `center` | Validate a centered tile over the source; useful for overlap inspection, not extension. |

The helper reports bounds validity, actual overlap, new canvas size, and no-overlap warnings.

## AI upscaling panel

Dream Textures' `AI Upscaling` panel uses the Stable Diffusion x4 upscaler and opens the result as `Source Image Name (Upscaled)`. The output is always 4x the source dimensions.

Source selection order from `operators/upscale.py`:

1. In a material node tree, if a selected `ShaderNodeTexImage` has an image, upscale that image.
2. Else, if the active area is an Image Editor, upscale the active image.
3. Else, use another open Image Editor image if one is available.
4. If no image is found, the operator reports `No open image in the Image Editor space, or selected Image Texture node.`

Fields:

| Field | Source/default | Meaning |
| --- | --- | --- |
| `Backend` and `Model` | selected `DreamPrompt` backend/model | Use an upscaler model such as `stabilityai/stable-diffusion-x4-upscaler`. |
| prompt subject | custom prompt field | Text subtly guides details during upscaling. |
| `Tile Size` | default `128`, min `64`, max `512`, step `64` | Input tile size. A 128 tile becomes a 512 model tile after 4x scaling. |
| `Blend` | default `32`, min `0`, max `512`, step `8` | Overlap/blend between tiles to reduce seams; internal tiler clamps excessive blend to usable per-axis limits. |
| `Seamless Axes` | `auto`, `off`, `x`, `y`, `xy` | Wraps tiles and/or uses circular model padding for tiling textures. |
| Advanced fields | seed, steps, CFG, scheduler, preview, optimizations | Reused from `DreamPrompt`; operator then replaces task with `Upscale(image, tile_size, blend)`. |

The upscaler splits the source image into tiles, upscales each tile independently, and stitches them back into a final canvas. Preview shows the combined upscaled image as tiles complete unless step preview is `None`. If invoked from a selected Image Texture node, successful upscaling replaces that node's image with the upscaled result.

VRAM guidance:

- Start with tile size `128` and blend `32`.
- Reduce tile size, keep batch size 1, lower preview work, or enable memory optimizations when memory is tight.
- Increase blend moderately or set correct seamless axes when seams appear.
- The UI warns when tile size is above 128 because VRAM rises quickly.

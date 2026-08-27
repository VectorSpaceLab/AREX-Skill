# Demo inputs, options, preprocessing, and outputs

This reference captures the Streamlit and Gradio UI behavior from the repo
evidence. It is for explaining or adapting demo/serving behavior. For the exact
Diffusers pipeline API, scheduler semantics, ControlNets, camera pose table, and
batch generation commands, route to [`../../generation/SKILL.md`](../../generation/SKILL.md).

## UI option matrix

| Option | Streamlit demo behavior | Gradio demo behavior | Deployment notes |
| --- | --- | --- | --- |
| Input image | File uploader accepts `png`, `jpg`, and `webp`. Example buttons can replace the uploaded image. | `gr.Image` receives a PIL RGBA image. Example thumbnails can populate the input. | The model expects a square image; demos expand or recenter inputs before calling the pipeline. Recommended input resolution is at least 320 x 320. |
| Example images | Source examples are listed, sorted, and displayed in four columns with a use button. | Source examples are passed to `gr.Examples` and shown below the uploader. | The evidence examples are `extinguisher.png`, `ghost-eating-burger.png`, `mushroom.png`, and `tianw2.png`. The generated launcher does not bundle them; supply an input explicitly. |
| Remove input background | Checkbox: `Remove Input Background`, default off. | Advanced checkbox group includes `Background Removal`, default on. | Uses `rembg` to estimate alpha and SAM to refine the mask. Requires `rembg`, `segment_anything`, and a local SAM checkpoint. |
| Rescale/recenter input | Not exposed as a separate control; the app resizes oversized inputs and expands to a square. | Advanced checkbox group includes `Rescale`, default off. | Rescale recenters the object using the alpha mask and places it in a square canvas at roughly 75% of the side length. |
| Inference steps | Slider from 15 to 100, default 75. | Slider from 15 to 100, default 75, step 1. | README guidance says general objects often work around 28 steps; delicate details such as faces may need 75 or more. |
| Guidance scale | Slider from 1.0 to 10.0, default 4.0. | Slider from 1 to 10, default 4, step 1. | This is classifier-free guidance. Use generation sub-skill references for tuning rationale. |
| Seed | Text input default `42`; converted to int before inference. | Numeric input default `42`. | Both demos seed PyTorch and pass a generator/manual seed for reproducibility. Invalid text seed in Streamlit fails at conversion time. |
| Remove output background | Checkbox: `Remove Output Background`, default off. | Advanced output postprocessing checkbox group includes `Background Removal`, default off. | Applies background removal separately to the six generated views and may add significant compute/model overhead. |
| Run/queue | Submit button; a global lock serializes generation and progress messages update in the UI. | Generate button; preprocessing runs first, then generation runs through Gradio queue. | Queue waits may indicate first model load, download/cache stalls, or single-GPU serialization. |
| Output display | Shows the generated 640 x 960 grid and optionally a background-removed grid. | Shows processed input plus six separate output tiles. | The six-view ordering is row-major over a 2-column x 3-row grid. Camera/view semantics belong in the generation sub-skill. |

## Streamlit preprocessing and output behavior

1. The selected image is opened with PIL. If the largest side is above 1280
   pixels, it is resized down while preserving aspect ratio.
2. If input background removal is enabled:
   - `rembg.remove` produces an alpha mask.
   - SAM refines the mask using the initial mask-derived bounding box.
   - The original RGB content is pasted into a transparent RGBA image using the
     refined mask.
3. The image is expanded to a square canvas with a gray/transparent background.
4. The pipeline is called with the UI-selected steps, guidance scale, and seed.
5. The raw result is a single 640 x 960 multi-view grid.
6. If output background removal is enabled, the grid is cropped into six 320 x
   320 tiles, each tile is processed with `rembg` plus SAM, masked pixels are
   replaced with white, and the tiles are concatenated back into a 640 x 960
   grid.

Streamlit progress states are roughly: queue wait, input preparation, diffusion
step progress, post-processing, and idle. A global lock prevents overlapping
pipeline calls from the same app process.

## Gradio preprocessing and output behavior

1. The input image is thumbnailed to at most 1024 x 1024.
2. If `Background Removal` is selected:
   - The input is converted to RGBA.
   - `rembg.remove(..., alpha_matting=True)` estimates alpha.
   - The nonzero alpha bounding box is passed to SAM.
   - SAM returns an RGBA foreground cutout.
3. If `Rescale` is selected:
   - The alpha channel is thresholded and bounded.
   - The object is centered into a square transparent canvas so the object
     occupies about 75% of the side length.
   - Transparent pixels are composited over white and resized to the selected
     output resolution.
4. If `Rescale` is not selected, the image is expanded to a square gray canvas.
5. Gradio keeps both a high-resolution processed image for generation and a 320 x
   320 processed preview for display.
6. The generated grid is split into six row-major views. If output background
   removal is selected, each view is run through the same background-removal
   preprocessing path before being returned to the UI.

The bundled launcher intentionally implements only the core upload/steps/guidance/seed
surface and six-view gallery. Add SAM/rembg options only when the deployment has
explicitly approved their dependencies, checkpoint, and downloads.

## Example input behavior

The source demos do not require example files for inference; they are convenience
fixtures for the UI. The source evidence includes four example image names:

- `extinguisher.png`
- `ghost-eating-burger.png`
- `mushroom.png`
- `tianw2.png`

When adapting a demo, decide whether examples are needed. If they are, bundle
new example assets with that deployment or make the example directory a
configuration option. Do not assume a repository checkout-relative examples
folder exists in production.

## Background-removal decision guide

Use background removal when the user needs object-centric inputs or white/alpha
cleanups in demo outputs. Avoid it when:

- network access is unavailable and the SAM/rembg models are not already staged;
- deployment must start quickly and deterministically in CI;
- the input already has a clean square object crop;
- the request is only to demonstrate the core multiview pipeline.

If background removal is required, confirm all of the following before launch:
`rembg` import works, ONNX runtime dependencies are present, `segment_anything`
imports, the SAM ViT-H checkpoint is present, and CUDA/VRAM can cover both SAM
and the diffusion pipeline.

# Image generation workflows

This reference covers Dream Textures generation from Blender's Image Editor or Shader Editor `Dream` sidebar tab. It assumes the add-on, backend dependencies, and model entries already exist. Route install, dependency, Hugging Face token, DreamStudio key, and model acquisition questions to `../setup-and-models/`.

## Open the Dream panel

1. Open an `Image Editor` or `Shader Editor` area in Blender.
2. Show the sidebar with `N` or `View > Sidebar`.
3. Select the `Dream` tab and expand `Dream Texture`.
4. Choose `Backend` and `Model` before tuning prompt, size, source image, ControlNet, and advanced fields.
5. Press `Generate`.

The `Generate` operator builds `GenerationArguments` from `DreamPrompt`, asks the selected backend to validate them, and then sends the task to the generator process. A disabled button usually means backend validation failed, the generator actor cannot run, or the selected model does not match the emitted task.

## Dream panel fields to API arguments

| DreamPrompt field | UI meaning | API destination | Operating notes |
| --- | --- | --- | --- |
| `backend` | Backend selector | selected `Backend` | Local Diffusers, DreamStudio, or any registered backend. Backend internals route to `../backend-and-api/`. |
| `model` | Model selector | `GenerationArguments.model` | Must match the task type: prompt/image, depth, inpaint/outpaint, or upscale. |
| `prompt_structure` plus `prompt_structure_token_*` | Prompt preset and tokens | `Prompt.positive` | Presets render a prompt string; `file_batch` uses non-empty lines from a Blender text datablock. |
| `use_negative_prompt`, `negative_prompt` | Negative prompt panel | `Prompt.negative` | Disabled sends `None`; enabled repeats the string for each generated image. File batch sends blank negative strings. |
| `use_size`, `width`, `height` | Manual dimensions | `GenerationArguments.size` | UI dimensions start at 64 and step by 64. Keep dimensions multiples of 64 for normal generation. |
| `seamless_axes` | Seamless/tilable axes | `GenerationArguments.seamless_axes` | Values are `auto`, `off`, `x`, `y`, `xy`; `auto` is resolved from source/history when possible. |
| `random_seed`, `seed` | Seed controls | `GenerationArguments.seed` | Random sends `None`; numeric strings clamp to `0..2^32-1`; non-numeric strings are hashed in-process. |
| `iterations` | Number of outputs | `GenerationArguments.iterations` | File batch overrides the loop with the number of non-empty file lines. |
| `steps` | Sampler steps | `GenerationArguments.steps` | More steps cost time/VRAM; low `strength` image workflows use only part of the schedule. |
| `cfg_scale` | Classifier-free guidance | `GenerationArguments.guidance_scale` | Higher values force prompt adherence and can create artifacts. |
| `scheduler` | Sampler scheduler | `GenerationArguments.scheduler` | Use display strings from the backend, not Python enum names, in prompt JSON. |
| `step_preview_mode` | Progress preview mode | `GenerationArguments.step_preview_mode` | `Accurate` decodes every step and is much slower; `Fast` samples latents. |
| `control_nets` | Enabled ControlNet entries | `GenerationArguments.control_nets` | Each enabled entry adds model id, processed control image, and conditioning scale. |

## Prompt-to-image

When `use_init_img` is disabled, Dream Textures emits `PromptToImage()`.

Use this for new images/textures from prompt only. Choose a prompt-to-image Stable Diffusion model such as the current Stable Diffusion 2.x prompt model recommended by setup guidance. For prompt-only seamless generation, `seamless_axes=auto` behaves like off because there is no source image to inspect; set `x`, `y`, or `xy` explicitly for tiling textures.

Typical starting values:

- Size `512x512`, or one axis near 512, in multiples of 64.
- Steps `25`; use around `20` for previews and `50` for final refinement.
- CFG scale `7.5` as a neutral starting point.
- Scheduler `DPM Solver Multistep` when available.
- Step Preview `Fast` or `None` for speed; avoid `Accurate` while debugging memory.

## Source image modify and depth modes

Enable `Source Image`, choose `File` or `Open Image`, then set `Action` to `Modify` for image-to-image or depth-conditioned generation.

Source lookup:

- `file`: uses the scene `Init Image` datablock/file slot.
- `open_editor`: uses the active Image Editor image when invoked from an Image Editor, otherwise the first open Image Editor image found on the screen.

`Modify` then uses `Image Type`:

| Image Type | Extra fields | API task emitted | Required model type |
| --- | --- | --- | --- |
| `Color` | `strength`, `fit` | `ImageToImage(image, strength, fit)` | prompt-to-image model |
| `Color and Generated Depth` | `strength`; source RGB image | `DepthToImage(depth=None, image=init_image, strength=strength)` | depth model; depth estimator may need cached dependencies |
| `Color and Depth Map` | `strength`; secondary `init_depth` image | `DepthToImage(depth=grayscale(init_depth), image=init_image, strength=strength)` | depth model |
| `Depth` | `strength`; source interpreted as grayscale depth | `DepthToImage(depth=grayscale(init_image), image=None, strength=strength)` | depth model |

`Noise Strength` controls deviation from the source. Lower values preserve style/composition more strongly; higher values diverge. `Fit to width/height` resizes the source to the requested size before generation; when disabled, image-to-image follows the source dimensions.

`Color Correct` is present in the UI. The distilled public task dataclasses consume image arrays, not a stable `color_correct` argument, so treat color-space problems as source-image diagnostics.

## Negative prompts

Enable `Use Negative Prompt` to send `Prompt.negative`. If disabled, the backend receives `None` and should not apply negative classifier-free text.

Use negative prompts to suppress unwanted details: `text`, `watermark`, `building`, `hands`, `border`, `low quality`, `blurry`, or `seams`. For material textures, keep negatives short and concrete.

In file-batch mode, the negative prompt UI is hidden. Dream Textures builds a list of positive prompts from non-empty file lines and sends a matching list of blank negative strings, so per-line negatives are not supported by the built-in file-batch workflow.

## Size, seeds, scheduler, and iterations

- **Size:** The docs and UI expect width/height multiples of 64. ControlNet preprocessing rounds internally to multiples of 8, but do not rely on that for the Dream panel.
- **VRAM:** If generation fails with CUDA/VRAM errors, lower width/height, steps, iterations, preview accuracy, backend batch size, or upscale tile size. Release the generator to clear cached models when switching heavy workflows.
- **Numeric seeds:** Turn off `Random Seed` and enter a number for repeatability. Values clamp to `0..2^32-1`.
- **Text seeds:** Non-numeric strings are hashed by the active Python process. Do not assume the same text seed is stable across sessions; use history's stored numeric seed for exact recall.
- **Random seed:** A random run writes the actual result seed back to prompt/history. Recall or export history before trying to reproduce.
- **Scheduler:** Prompt JSON should use display strings such as `DPM Solver Multistep`, `Euler Discrete`, or `UniPC Multistep`.
- **Iterations:** Non-file-batch iterations create multiple results. In a node editor, results are placed in a square-ish grid of new image texture nodes.

Common local scheduler display strings include `DDIM`, `DDPM`, `DEIS Multistep`, `DPM Solver Multistep`, `DPM Solver Multistep Karras`, `DPM Solver Singlestep`, `DPM Solver Singlestep Karras`, `Euler Discrete`, `Euler Discrete Karras`, `Euler Ancestral Discrete`, `Heun Discrete`, `Heun Discrete Karras`, `KDPM2 Discrete`, `KDPM2 Ancestral Discrete`, `LMS Discrete`, `LMS Discrete Karras`, `PNDM`, and `UniPC Multistep`.

## Seamless axes during generation

`seamless_axes` values:

- `auto` / `Auto-detect`: detect from a source image, ControlNet image, upscaling input, or recalled history where supported.
- `off` / `Off`: no circular padding.
- `x` / `X`: horizontal tiling.
- `y` / `Y`: vertical tiling.
- `xy` / `Both`: horizontal and vertical tiling.

Prompt-to-image converts `auto` to off at model padding time. Image-to-image and inpaint detect axes from the source image when it is at least 8x8. ControlNet can combine detected axes from the init image and the control image. When exact tiling is required, set `x`, `y`, or `xy` explicitly.

## ControlNet from images

Use the `ControlNet` panel to add conditioning images. ControlNet does not replace the base model; it adds one or more conditioning branches to prompt-to-image, image-to-image, and inpaint paths.

| ControlNet field | Meaning |
| --- | --- |
| `control_net` | Installed ControlNet model id selected from `Add ControlNet`. |
| `control_image` | Blender image datablock used as the control source. |
| `processor_id` | Optional preprocessor. `none` uses the image as-is. |
| `conditioning_scale` | Control strength; default `1.0`. |
| `enabled` | Disabled entries are ignored when building `GenerationArguments`. |

Supported processor ids include `none`, `depth_leres`, `depth_leres++`, `depth_midas`, `depth_zoe`, `canny`, `mlsd`, `softedge_hed`, `softedge_hedsafe`, `softedge_pidinet`, `softedge_pidsafe`, `lineart_anime`, `lineart_coarse`, `lineart_realistic`, `normal_bae`, `openpose`, `openpose_face`, `openpose_faceonly`, `openpose_full`, `openpose_hand`, `scribble_hed`, `scribble_pidinet`, and `shuffle`.

The bake button runs the selected processor once, creates a processed image datablock named from the source and processor label, switches the entry back to `none`, and opens the processed image in an unpinned Image Editor. Use bake when repeated generation should not redo preprocessing or when you need to inspect the control image.

Current source evidence applies ControlNet to prompt-to-image, image-to-image, and inpaint paths. Do not rely on ControlNet entries for the outpaint task path.

## Result and history side effects

Successful generation creates Blender image datablocks named from a trimmed prompt and seed. Each generated image receives a `dream_textures_hash` custom property derived from the image pixels. Prompt history stores a copy of the prompt state with `iterations=1`, `random_seed=False`, concrete `seed`, image `hash`, and final `width`/`height`. File-batch history stores each line as a recalled `custom` subject.

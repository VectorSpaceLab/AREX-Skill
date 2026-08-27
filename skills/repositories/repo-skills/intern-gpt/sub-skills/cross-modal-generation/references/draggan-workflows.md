# StyleGAN and DragGAN Workflows

## Purpose

Read this when a task asks how InternGPT's DragGAN tab works, how to create a StyleGAN image, how start/end points are stored, why point counts must match, or what outputs to expect from `New Image`, `Clear Points`, and `Drag It`.

## Components

- `StyleGAN` is the loaded foundation model for the DragGAN tab. It wraps a StyleGAN2 generator, tracks the target device and energy-saving mode, and exposes an image size of 1024 for the default FFHQ checkpoint family.
- The app uses the DragGAN optimization function directly with the `StyleGAN` state. The prompt-decorated `DragGAN` wrapper exists in the model layer, but the interactive Gradio tab relies on controller callbacks rather than a free-form LangChain tool.
- The default checkpoint key in the model wrapper is `stylegan2-ffhq-config-f.pt`, with a 1024px image-size entry. Other checkpoint keys are commented out in the wrapper and should not be assumed available.

## App callback sequence

1. Open the DragGAN tab or click `New Image`.
2. The app calls the new-image callback. It requires `StyleGAN` to be loaded; otherwise the chat state receives `Please load StyleGAN!`.
3. On the first image in a session, the controller seeds generation with 2048. It samples a random latent vector, prepares StyleGAN latent/noise inputs, runs one generation pass, and stores the generated image and state.
4. Click the image to create paired points. The first click of each pair is a start point; the next click is its end point. The manual describes blue points as starts and red points as ends.
5. Click `Drag It` after each start point has a matching end point. The max-iterations slider controls the number of DragGAN optimization iterations. The progress slider is updated as frames are yielded.
6. Use `Clear Points` to remove all queued start/end pairs and restore the latest generated or edited image without deleting the StyleGAN latent state.

## Stored state

The controller stores DragGAN data under the per-user `StyleGAN` state:

| Field | Meaning | Notes |
| --- | --- | --- |
| `state.latent` | Current StyleGAN latent tensor. | Kept on CPU between calls when possible; moved to the target device during editing. |
| `state.noise` | StyleGAN noise tensors. | Each tensor is moved to the target device during editing and may be kept on CPU between callbacks. |
| `state.F` | Intermediate feature tensor used by DragGAN. | Updated after each DragGAN iteration. |
| `state.sample` | Latest raw generated tensor. | Used to restore the image when points are cleared. |
| `state.history` | Per-iteration image frames without overlaid points. | Written to a video when the requested max iteration count is reached. |
| `points.start` | List of start points as `[row, column]`-style coordinates after click conversion. | Count must equal `points.end` before dragging. |
| `points.end` | List of target/end points. | The next click after a start point becomes an end point. |
| `image_path` | Current generated image path in the app output area. | DragGAN output filenames are derived from this path. |
| `image_size` | Default 1024 for the active StyleGAN wrapper. | Controls click marker size. |
| `click_size` | Marker radius; 15 for 1024px images and 6 for 256px images. | Used only for preview overlays. |

## Drag It behavior

Before running, the controller checks:

- `StyleGAN` is loaded;
- a `New Image` state exists;
- an image path exists;
- at least one start point was clicked;
- start and end point counts match; and
- StyleGAN latent/noise/F state exists.

If all checks pass, it converts `max_iters` to an integer, moves latent/noise/F and the model to the target device as needed, then iterates the DragGAN optimizer. During each iteration it:

1. receives an updated sample, latent, feature tensor, and handle/start points;
2. updates `state.F`, `state.latent`, `state.sample`, and the current start-point positions;
3. appends the raw frame to `state.history`;
4. overlays start/end markers for the preview image; and
5. yields the preview and current progress step.

When the final iteration is reached, the controller saves two artifacts:

- an MP4 video of the editing process with a `DragGAN` suffix; and
- a PNG image of the processed final frame with a `DragGAN` suffix.

The final edited image is also injected into the app memory as a provided image so follow-up visual tools can operate on it.

## Minimal operating recipes

### DragGAN-only interactive editing

Use this sub-skill for the point-editing sequence, but route exact launch flags and service setup to the app-deployment sub-skill. The minimum conceptual load is the `StyleGAN` foundation model plus the `DragGAN` tab. Once the service is running:

1. Click `New Image`.
2. Add start/end point pairs: blue start, red end.
3. Set max iterations, commonly 25 in the app UI.
4. Click `Drag It` and wait for progress to reach the requested iteration count.
5. Use the returned image for further visual dialogue or the returned video to review the deformation process.

### Correcting point mistakes

- If a start point has no matching end point, add the missing end click before dragging.
- If the wrong point was clicked, use `Clear Points` and recreate the point pairs.
- If no image is visible or state was cleared, click `New Image` again before selecting points.

## Runtime prerequisites

DragGAN is not a lightweight CPU feature. Expect CUDA-capable PyTorch, the StyleGAN checkpoint, compatible custom operations from the DragGAN/StyleGAN implementation, and enough VRAM for 1024px StyleGAN2 editing. Energy-saving mode can reduce idle memory by moving the generator off GPU between calls, but it does not remove the need for GPU memory during generation and optimization.

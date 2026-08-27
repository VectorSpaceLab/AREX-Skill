# ControlNet Annotator Reference

This reference distills the ControlNet 1.0 annotation stack into runtime-safe guidance. It is self-contained: future agents should not need to open the original source checkout to answer preprocessing questions.

## Shared Preprocessing Semantics

ControlNet annotator UI functions first convert the uploaded image with `HWC3`, then call `resize_image`.

| Step | Behavior | Practical consequence |
| --- | --- | --- |
| `HWC3(x)` | Requires `uint8`; accepts 2D grayscale or 3D arrays with 1, 3, or 4 channels; returns 3 channels. | Convert floats, bools, PIL modes, and tensor formats before calling detector-style code. |
| Grayscale input | A 2D array or a 1-channel array is repeated into R, G, and B channels. | Grayscale sketches become neutral RGB images, not label maps. |
| RGBA input | RGB is alpha-composited over a white background using `rgb * alpha + 255 * (1 - alpha)`. | Transparent scribbles may become pale or white; check alpha and polarity before blaming ControlNet. |
| `resize_image(input_image, resolution)` | Scales the short side to `resolution`, then rounds both dimensions to nearest multiples of 64. | A request for 512 means short side near 512 and dimensions divisible by 64, not necessarily 512×512. |
| Interpolation | Uses Lanczos when upscaling and area interpolation when downscaling. | Thin edges can change subtly after resizing; tune thresholds after resizing, not before. |

Resolution sliders in the annotator UI use multiples of 64 and generally range from 256 to 1024. MLSD and MiDaS default to 384 in the UI; Canny, OpenPose, and Uniformer default to 512.

## Detector Selection

| Need | Best first detector | Why | Avoid when |
| --- | --- | --- | --- |
| Fast safe edge map without model weights | Canny | Uses OpenCV only; call signature is explicit thresholds. | Soft semantic boundaries or stylized recoloring need HED-like edges. |
| Soft object/detail boundaries | HED | Produces smoother learned boundaries suited to ControlNet HED models. | Detector checkpoint, CUDA, or HED dependencies are unavailable. |
| Straight room/building lines | MLSD | Extracts line segments and returns a sparse white-line map. | Curved contours, people, or organic shapes dominate the image. |
| Monocular depth conditioning | MiDaS depth | Produces a normalized uint8 depth map for depth ControlNet. | You need precise metric depth; MiDaS depth is relative. |
| Geometry-preserving surface orientation | MiDaS normal | Derives a normal map from MiDaS depth and a background threshold. | RGB/BGR interpretation cannot be controlled or background threshold is unknown. |
| Human body pose | OpenPose | Produces colored skeleton/pose canvas and optional hand keypoints. | Hand pose is not wanted; ControlNet 1.0 production-ready model expected hand detection off. |
| ADE20K-style semantic layout | Uniformer segmentation | Produces a color segmentation map using ADE palette conventions. | The task needs instance masks, custom class ids, or training labels instead of visualization colors. |

For text-to-image generation using a prepared map, switch to [gradio-inference-apps](../../gradio-inference-apps/SKILL.md). For missing model files or model directory layout, switch to [model-and-weight-utilities](../../model-and-weight-utilities/SKILL.md). For dataset-scale paired annotations, switch to [training-and-datasets](../../training-and-datasets/SKILL.md).

## Wrapper Signatures And Outputs

| UI function | Detector wrapper call | UI parameters | Output shape/channel expectation | Checkpoint/dependency behavior |
| --- | --- | --- | --- | --- |
| `canny(img, res, l, h)` | `CannyDetector().__call__(img, low_threshold, high_threshold)` | `low_threshold`, `high_threshold`, `resolution` | 2D uint8 edge map from OpenCV Canny. | Requires OpenCV; no detector checkpoint. |
| `hed(img, res)` | `HEDdetector().__call__(input_image)` | `resolution` | 2D uint8 soft edge map. | Constructs a CUDA Torch model and expects `ControlNetHED.pth`; missing file may trigger a download in source code. |
| `mlsd(img, res, thr_v, thr_d)` | `MLSDdetector().__call__(input_image, thr_v, thr_d)` | `value_threshold`, `distance_threshold`, `resolution` | 2D uint8 line map; white lines on black background. | Constructs a CUDA Torch model and expects `mlsd_large_512_fp32.pth`; missing file may trigger a download in source code. |
| `midas(img, res, a)` | `MidasDetector().__call__(input_image, a=np.pi * 2.0, bg_th=0.1)` | `alpha`, `resolution` | Returns `(depth_image, normal_image)` as uint8 arrays; depth is 2D, normal is 3-channel. | Constructs MiDaS DPT hybrid on CUDA and expects `dpt_hybrid-midas-501f0c75.pt`; missing file may trigger a download. |
| `openpose(img, res, has_hand)` | `OpenposeDetector().__call__(oriImg, hand=False)` | `detect hand`, `resolution` | Returns `[pose_canvas]` from UI function; wrapper returns `(canvas, metadata)`. | Expects `body_pose_model.pth` and `hand_pose_model.pth`; missing hand file triggers body and hand downloads in source code. |
| `uniformer(img, res)` | `UniformerDetector().__call__(img)` | `resolution` | 3-channel ADE-palette segmentation visualization. | Expects `upernet_global_small.pth` plus Uniformer/mmseg dependencies; missing file may trigger a download. |

The original Gradio annotator lazily instantiates detector globals on first use. That keeps the UI import light but means a single button click can load CUDA models, require optional Python packages, or attempt checkpoint downloads in the source implementation. A safe helper or batch script should not instantiate checkpoint-dependent detectors unless the user explicitly confirms weights, dependencies, and hardware are available.

## Channel And Color Gotchas

- Canny, HED, and MLSD produce single-channel edge or line maps. Some downstream visualization code may display them as grayscale, while some generation code may expand them to three channels.
- The annotation docs warn about black-edge/white-background versus white-edge/black-background. Canny and MLSD wrappers naturally produce white foreground strokes on black background. User scribbles may arrive inverted or alpha-composited over white.
- The HED wrapper explicitly notes it is an RGB-input model, chosen to fit Gradio's RGB protocol rather than BGR conventions.
- OpenPose internally flips the input with `oriImg[:, :, ::-1]` before body and hand estimation, then draws a colored pose canvas. If colors look swapped, verify whether an upstream loader produced RGB or BGR.
- MiDaS normal maps are derived from Sobel gradients of relative depth and encoded as `(normal * 127.5 + 127.5)`. The docs specifically warn to be careful about RGB/BGR in normal maps.
- Uniformer segmentation returns color visualizations using an ADE palette. Do not treat the colors as stable numeric training class ids unless the generating code and palette are controlled.

## Checkpoint Expectations

ControlNet 1.0 places detector weights under an annotator checkpoint directory in the source implementation. Public runtime skill instructions should describe expected filenames rather than assuming the original checkout exists.

| Detector | Expected checkpoint filename(s) |
| --- | --- |
| HED | `ControlNetHED.pth` |
| MLSD | `mlsd_large_512_fp32.pth` |
| MiDaS | `dpt_hybrid-midas-501f0c75.pt` for the default DPT-hybrid path |
| OpenPose | `body_pose_model.pth`, `hand_pose_model.pth` |
| Uniformer | `upernet_global_small.pth` |

When these files are absent, do not silently attempt model execution from a generated skill. Ask the user whether network access, checkpoints, compatible CUDA/Torch, and optional packages are available, or choose a Canny-only path.

## Safe Batch Preprocessing Recipes

### Canny-only safe path

Use this when the user asks for batch annotation but has no learned detector checkpoints.

1. Load each image as `uint8` RGB or convert it to an HWC array.
2. Apply ControlNet-style `HWC3` conversion, especially for grayscale or RGBA scribbles.
3. Resize with short-side scaling and 64-multiple rounding.
4. Run Canny with task-specific low/high thresholds.
5. Save the edge map and record the thresholds and final output dimensions.

### Checkpoint-dependent detector path

Use this only after confirming local detector weights and dependencies.

1. Confirm which ControlNet model family the user will condition: edge, line, pose, depth, normal, or segmentation.
2. Confirm expected detector checkpoint filenames and optional packages are present.
3. Normalize and resize inputs the same way the Gradio annotator does.
4. Instantiate one detector once per process, not once per image.
5. Preserve output channel conventions and document polarity or palette choices.
6. If any detector attempts network download or fails CUDA initialization, stop and ask for environment/model access rather than substituting another detector silently.

### Static UI inspection path

Use the bundled `scripts/inspect_annotator_inputs.py --repo-root <checkout>` only for local development or verification. It parses `gradio_annotator.py` with AST and lists function signatures without importing Gradio, launching a server, instantiating detectors, downloading weights, or running generation.

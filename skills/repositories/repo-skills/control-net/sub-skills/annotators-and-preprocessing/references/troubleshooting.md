# Annotator Troubleshooting

Use this guide when ControlNet conditioning maps fail, look wrong, or cannot be produced safely. It focuses on preprocessing and annotation only; route generation failures to [gradio-inference-apps](../../gradio-inference-apps/SKILL.md), model file layout to [model-and-weight-utilities](../../model-and-weight-utilities/SKILL.md), and training data questions to [training-and-datasets](../../training-and-datasets/SKILL.md).

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Learned detector fails on first call and mentions a missing `.pth` or `.pt` file | HED, MLSD, MiDaS, OpenPose, or Uniformer checkpoint is absent. | Ask for detector checkpoints or network permission; otherwise switch to a Canny-only workflow. Expected filenames are listed in `annotator-reference.md`. |
| Code unexpectedly tries to download weights | Source detector constructors contain download fallbacks for missing checkpoint files. | Do not instantiate checkpoint-dependent detectors in generated-skill helpers. Confirm network policy and checkpoint cache first. |
| `ModuleNotFoundError: gradio` while inspecting annotator controls | The source UI imports Gradio at module import time. | Use static AST parsing with `scripts/inspect_annotator_inputs.py --repo-root <checkout>` instead of importing or launching the UI. |
| `ModuleNotFoundError` for `cv2` | OpenCV is missing; Canny and resizing depend on it in the source implementation. | Install or provide OpenCV in the working environment, or only perform non-image static inspection. The bundled helper can still run tiny checks without OpenCV using Pillow/numpy fallbacks. |
| CUDA/Torch errors when using HED, MLSD, MiDaS, OpenPose, or Uniformer | Source wrappers call `.cuda()` and assume compatible Torch/CUDA and GPU memory. | Stop and ask for hardware/backend confirmation or use Canny. Do not pretend the helper can run these detectors. |
| Grayscale image causes assertion or shape error in custom code | Detector-style preprocessing expects uint8 HWC arrays and uses `HWC3` before detector calls. | Convert grayscale to a 2D or 1-channel uint8 array, then apply HWC3-style expansion to three channels. |
| RGBA scribble produces faint or odd marks | `HWC3` alpha-composites RGB over white; transparent pixels become white and semi-transparent strokes become pale. | Inspect alpha values and polarity. If the intended conditioning is black-on-white or white-on-black, binarize/invert after compositing deliberately. |
| Non-uint8 image fails or thresholds behave strangely | `HWC3` asserts `np.uint8`; float tensors in `[0, 1]` or `[-1, 1]` are not accepted directly. | Convert to uint8 before detector-style preprocessing; preserve channel order during conversion. |
| Resized output is not exactly requested dimensions | `resize_image` scales the short side to `resolution`, then rounds height and width to nearest multiples of 64. | Report final dimensions explicitly. Do not assume `resolution=512` gives 512×512 for non-square inputs. |
| Edges appear inverted: black lines on white when white-on-black was expected, or vice versa | Edge/scribble polarity differs from the ControlNet app or user-provided scribble. | Check whether the downstream model expects white strokes on black background. Invert only after confirming the expected polarity. |
| Canny edges too dense or too sparse | Thresholds were copied from another resolution/image domain, or resizing changed line thickness. | Tune `low_threshold` and `high_threshold` after resizing. Start near the UI defaults 100/200, then adjust per image set. |
| HED output too soft or preserves too much detail | HED intentionally produces soft learned boundaries suitable for recoloring/stylizing. | Use Canny or MLSD for sharper sparse controls, or threshold HED output only when the target model/task expects sparse edges. |
| MLSD output is blank | Thresholds too strict, image lacks straight line structure, dependency/model failed, or wrapper swallowed an internal exception. | Lower `value_threshold`/`distance_threshold`, test on architecture-like images, and verify checkpoint/dependency availability. If no checkpoint is available, skip MLSD. |
| MiDaS normal colors look wrong | Normal map RGB/BGR interpretation is swapped by a loader/viewer or downstream code. | Keep arrays in RGB-style HWC unless deliberately using OpenCV BGR. Add a small visual sanity check before passing normal maps downstream. |
| MiDaS normal background looks noisy or too flat | Background threshold `bg_th` and alpha-like parameter `a` affect derived normals; UI exposes `alpha`, wrapper default `bg_th` is 0.1. | Adjust `alpha` and document any non-default background threshold if using custom code. Treat depth as relative, not metric. |
| OpenPose hands appear or disappear unexpectedly | The UI has a `detect hand` checkbox; the production-ready model guidance used hand pose off. | Default hand detection to false unless requested. If hand details are needed, confirm `hand_pose_model.pth` and runtime cost. |
| OpenPose or pose colors look swapped | OpenPose wrapper flips channels internally before estimation, and colored pose canvases are sensitive to RGB/BGR display paths. | Trace loader order: PIL/Gradio are RGB, OpenCV is often BGR. Convert once at the boundary, not repeatedly. |
| Uniformer segmentation colors do not match expected labels | Uniformer returns an ADE-palette visualization, not a robust portable class-id tensor. | Use it as a ControlNet segmentation conditioning image. For training labels or custom classes, route to dataset/training guidance. |
| User asks for a batch HED/OpenPose/Uniformer script but has no weights | Request exceeds safe self-contained preprocessing. | Offer Canny-only batch preprocessing and produce a skipped-detector manifest naming the missing checkpoints. Ask whether to proceed with checkpoint setup separately. |

## When To Stop And Ask

Stop instead of guessing when any of these are true:

- The user wants HED, MLSD, MiDaS, OpenPose, or Uniformer output but cannot provide detector checkpoint files, network access, or a prepared environment.
- A detector constructor would need to download files or initialize CUDA and the user has not approved that runtime behavior.
- The task requires full text-to-image generation, ControlNet model conversion, or training datasets rather than preprocessing maps.
- The requested output depends on a semantic label schema, pose JSON contract, or normal-map color convention that is not specified by the user.

## Quick Debug Questions

Ask these before changing code:

1. What is the intended ControlNet model: canny, hed/scribble, mlsd, depth, normal, pose, or segmentation?
2. Is the input RGB, BGR, grayscale, or RGBA? If RGBA, should transparency become white or be thresholded as a mask?
3. Should foreground strokes/edges be white-on-black or black-on-white?
4. What final dimensions were actually produced after 64-multiple resizing?
5. Are the required detector checkpoints and optional dependencies already present, or should this be Canny-only?

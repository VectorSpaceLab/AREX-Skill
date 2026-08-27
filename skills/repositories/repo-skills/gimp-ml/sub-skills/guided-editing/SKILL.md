---
name: guided-editing
description: "Route mask- and layer-conditioned GIMP-ML work for inpainting,
  deep image matting, face parsing and portrait generation preparation, and
  optional color guidance while enforcing exact alignment and pixel contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Guided Editing

Use this sub-skill when an image edit is conditioned by a mask, trimap,
face-label layer, aligned layer trio, or sparse color guidance. It is the
contract and routing layer for these operations, not a general computer-vision
catalog.

## Route by requested operation

| Request signal | Route | Required inputs |
|---|---|---|
| Remove an object or region | Inpainting | Image + binary mask |
| Produce foreground alpha | Deep image matting | RGB image + RGB trimap |
| Prepare a face edit | Face parsing first | Portrait image |
| Render a changed face label map | Face generation | Portrait + original mask + modified mask |
| Color a grayscale RGB image | Deep coloring | RGB-mode grayscale image; optional transparent RGB color mask |

Read [mask-and-layer-contracts.md](references/mask-and-layer-contracts.md)
before accepting or repairing any input. Read
[workflows.md](references/workflows.md) for the operation procedure and
[troubleshooting.md](references/troubleshooting.md) for failure recovery.

## Non-negotiable input rules

- Every participating layer must have the same width and height as the GIMP
  image. In GIMP, use **Layer -> Layer to Image Size** on every layer before
  running a plugin; do not use a visual alignment guess.
- For inpainting, preserve the manual's stated numeric polarity: background is
  `(255,255,255)` and the object to remove is `(0,0,0)`. The manual labels
  these black background/white object, which is visually counterintuitive;
  preserve the numeric triples and do not invert them silently. The checked
  source implementation then normalizes the first channel as `1 - value/255`,
  so observed runtime polarity is an explicit version/host verification gate,
  not a reason to rewrite the documented user input rule.
- For matting, use RGB trimap pixels `(0,0,0)` for black background,
  `(255,255,255)` for white object, and `(128,128,128)` for gray unknown
  boundary. The trimap must be spatially aligned with the image.
- Face generation consumes three aligned layers: portrait, original mask, and
  modified mask. Face parsing creates the original face label mask; it is a
  prerequisite, not an alternative face-generation input.
- Color guidance is optional as a layer, but when supplied it is a transparent
  RGB mask with alpha and sparse local color points. The base image remains
  RGB-mode even when its visible content is grayscale.
- Alpha is optional on ordinary image, inpainting-mask, and trimap files. A
  color-guidance layer must retain alpha so transparent pixels remain absent.
  Static preflight accepts grayscale+alpha for an inpainting mask, but the
  legacy plugin/runtime path should be confirmed before relying on that mode.

## Operating procedure

1. Identify one route from the table and name each input layer explicitly.
2. Run the bundled deterministic preflight before any model or GIMP mutation:

   ```text
   python scripts/validate_mask_inputs.py --help
   ```

   Supply `--image` and `--mask`, `--image` and `--trimap`, the three face
   arguments, or `--image` with `--color-mask` as appropriate. The validator
   reports dimensions, channels, alpha presence, trimap tolerance, and
   inpainting polarity; it never downloads weights, calls a service, or edits
   an image.
3. Fix every alignment, channel, polarity, and trimap error before opening a
   model. Treat a validator warning about no visible color points or no gray
   trimap boundary as a review stop for the intended edit.
4. Follow the selected workflow in [workflows.md](references/workflows.md).
   Preserve the source layer(s), create a separate result layer, and inspect
   the output rather than overwriting the inputs.
5. Record whether the result was model-generated, static-only, or blocked by
   the host, checkpoint, or device. Do not describe a preflight pass as model
   success.

## Execution gates

- The repository's legacy plugin entry points require GIMP integration and
  Python 2-era `gimpfu`; the verified host does not provide GIMP or Python 2.
  This sub-skill therefore supports deterministic contract
  validation here, while plugin execution is host-dependent and unverified.
- No model weights are assumed. Inpainting requires two checkpoints, matting
  requires a matting checkpoint, face parsing requires its segmentation
  checkpoint, and face generation requires its GAN checkpoint/options. Missing
  files are a hard stop, not a reason to download automatically.
- CUDA visibility is not capacity proof. The verification host exposed CUDA
  but a tiny allocation was blocked by CUDA OOM. Prefer an explicit CPU trial
  when weights and a compatible runtime exist; otherwise report the device
  failure and stop.
- Checkpoint load errors, unsupported devices, and GIMP layer-size errors must
  be reported with the affected route and input; do not fall back to a
  different polarity, resize an unaligned mask, or claim completion. If a
  runtime result contradicts the manual polarity, report the source/runtime
  conflict instead of silently changing the mask.

## Safe verification boundary

The validator is the only bundled executable in this sub-skill. It is suitable
for synthetic fixtures and static CI checks. It writes nothing, reads only
explicit paths, and performs no network, credential, weight, GIMP, or model
operation. Use it to verify contracts, not visual quality or recovered model
accuracy.

## Out of scope

Do not use this route for generic segmentation, denoising, deblurring,
super-resolution, or arbitrary image classification. Do not train or repair
model architectures here. Do not invent a face label palette, trimap encoding,
mask polarity, checkpoint location, or device capability when evidence is
missing.

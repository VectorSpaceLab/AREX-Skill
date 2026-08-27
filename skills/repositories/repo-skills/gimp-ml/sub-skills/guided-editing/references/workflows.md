# Guided Editing Workflows

These workflows separate deterministic preparation from model execution. Start
with [mask-and-layer-contracts.md](mask-and-layer-contracts.md), then use the
validator on explicit exported files or equivalent synthetic fixtures. Do not
load a model merely because a file passed static validation.

## Shared preflight

1. Confirm the operation and identify the base image, each conditioning layer,
   and the intended result layer. Never infer a missing layer from a filename.
2. In GIMP, apply **Layer -> Layer to Image Size** to every participating layer.
   This is required even when the layer looks aligned.
3. Export temporary copies if a non-GIMP preflight is needed. Keep the original
   editable image untouched and never replace the source mask in place.
4. Run one applicable validator contract:

   ```text
   python scripts/validate_mask_inputs.py --image image.png --mask mask.png
   python scripts/validate_mask_inputs.py --image image.png --trimap trimap.png
   python scripts/validate_mask_inputs.py --portrait portrait.png \
       --original-mask original-mask.png --modified-mask modified-mask.png
   python scripts/validate_mask_inputs.py --image gray-rgb.png \
       --color-mask color-mask.png
   ```

   A successful report is a shape/channel/value preflight only. It is not a
   model or GIMP execution result.
5. If the report fails, repair the source layer and rerun. Do not use a resize,
   channel drop, inversion, or tolerance as an invisible repair.

## Inpainting

**Inputs:** image layer and binary object-removal mask. The image and mask must
be the same canvas size. Preserve the manual's numeric contract: background is
255 and removal region is 0, even though the manual names those values black
background and white object.

1. Paint the intended removal area as exact `(0,0,0)` and leave the keep area
   exact `(255,255,255)`. Avoid antialiased mask edges; review intermediate
   values as an error.
2. Run the validator and inspect the polarity counts. If the intended object
   has many 255 pixels and the surrounding background has 0 pixels, stop and
   correct the artwork deliberately; do not silently invert it.
3. The checked source implementation normalizes its first mask channel as
   `1 - value/255`, which appears to preserve 255 and remove 0. Because this
   conflicts with the manual's visual labels but not its stated numeric
   triples, a compatible-host fixture is required to establish observed
   behavior before relying on a production edit. Record the result of that
   fixture or mark the route unresolved.
4. In a compatible GIMP/Python runtime, choose the inpainting plugin and its
   image and mask layers. Use a separate output layer.
5. The implementation pads to internal dimensions and runs a DFNet stage then
   a refinement stage, but this is not a guarantee of available memory or
   checkpoint availability. Inspect the output against the preserved source.
6. If the result appears to copy the wrong region, report the manual/source
   polarity conflict and revisit the controlled fixture before changing the
   model or device.

## Deep image matting

**Inputs:** RGB image and RGB trimap with black background, white object, and
gray unknown boundary.

1. Keep the image RGB-mode. Construct a trimap with exact triplets and a
   substantive gray boundary around the foreground; do not use a soft alpha
   image as a substitute.
2. Run the validator. Use `--trimap-tolerance` only to diagnose a known export
   quantization issue; rewrite the trimap to exact 0/128/255 values before
   plugin execution.
3. In a compatible runtime, provide the image and trimap layers and select
   CPU explicitly if CUDA is unavailable or memory is uncertain. The plugin
   produces an RGBA-style result with predicted alpha and clamps known black
   and white trimap regions.
4. Review the alpha around the gray boundary. A completely black or white
   boundary, a shifted edge, or a trimap with no unknown pixels is a
   preparation failure, not evidence that the model is poor.
5. Keep the trimap and source image for reproducibility; do not overwrite them
   with the generated alpha result.

## Face parsing preparation

**Input:** one aligned portrait layer containing a person. Face parsing must
precede face generation when a source label mask is not already available.

1. Confirm the selected layer is the portrait, not a composite with unrelated
   objects. Apply Layer to Image Size.
2. Validate it as a readable RGB/RGBA image if possible. The static validator
   does not decide whether a picture is a suitable portrait.
3. In a compatible runtime, run face parsing with an explicit CPU choice when
   needed. The legacy parser resizes to 512 by 512 for inference, restores the
   portrait size, and emits a 19-class color-coded mask.
4. Preserve the generated original mask as a separate layer. Inspect its
   colors and boundaries; do not claim generation readiness if parsing is
   blocked by missing weights or runtime incompatibility.

## Face portrait generation

**Inputs:** portrait, original faceparse mask, and modified mask, all aligned.

1. Duplicate the original mask to make the modified mask. Change regions with
   supported palette colors only; preserve exact colors and dimensions.
2. Run the three-layer validator. A mismatch in any pair is a hard stop.
3. In a compatible runtime, select the face-generation plugin and supply the
   layers in this order: Original Image, Original Mask, Modified Mask. Keep
   the result on a new layer.
4. The checked options/model configuration uses 19 labels, RGB image/output,
   and 512-pixel transforms. It does not establish that the GAN checkpoint is
   installed. A checkpoint or device error stops the route.
5. Compare the output to the modified mask and original portrait. A visual
   result cannot repair an invalid label color or layer alignment.

## Deep coloring with optional points

**Inputs:** RGB-mode image whose content may be grayscale, plus an optional
aligned transparent RGBA color mask.

1. Convert the image mode to RGB without adding arbitrary color. Confirm the
   image and optional mask are the same canvas size.
2. Place sparse local RGB points, approximately six pixels as described by the
   manual, on the color mask and leave the rest transparent. Do not make a
   full opaque color image unless that is intentionally the conditioning data.
3. Run the validator with `--color-mask`. A missing alpha channel or a fully
   transparent mask is a preparation warning/error; the layer itself remains
   optional, so omit the argument when no points are desired.
4. If the compatible plugin is available, run it with a separate output layer
   and inspect whether points influence nearby regions. Without a supplied
   color mask, report that the result was unguided.

## Static-only and blocked paths

Use the static-only path when GIMP, Python 2-era `gimpfu`, checkpoints, or a
compatible plugin runtime is absent. It consists of validator output,
contract review, and an explicit unresolved-limit note. Do not emulate model
output with a placeholder and do not download weights automatically.

If a checkpoint exists but loading fails, retain the preflight report, record
the exact route and requested device, then use [troubleshooting.md](troubleshooting.md).
A CPU fallback is valid only after confirming a compatible CPU runtime and
successful checkpoint load; CUDA availability alone is not a reason to select
GPU execution.

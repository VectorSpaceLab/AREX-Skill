# Input and output contracts

Validate these contracts before attempting model loading. They are derived from the
manual and plugin guards, not from a successful inference run.

## Common single-layer contract

Deblur, dehaze, denoise, enlighten, monocular depth, semantic segmentation, face
parsing, and super-resolution accept the currently selected GIMP drawable/layer.
The plugin reads the complete pixel region and compares its height and width with the
GIMP image. If the layer is not already the image size, the source tells the user to
run **Layer -> Layer to Image Size** first. Do that before changing device or model
settings.

The source strips a fourth channel for all listed operations before model preprocessing.
Use an RGB layer for the predictable path. Indexed, unusual channel counts, color
profiles, and non-8-bit precision were not verified. Do not silently convert or
mutate a user layer outside the host's established color-management workflow.

Most single-layer filters add a result layer; the source generally calls it
`new_output`, while deblur prefixes the source layer name with `deblur_`. Super-
resolution at scale 1 uses a result layer, while scale other than 1 creates a new
GIMP image containing the enlarged output. Exact GIMP layer APIs are unavailable for this verification.

## Operation-specific inputs

### Deblur, dehaze, denoise, enlighten

- Input: current selected layer only.
- Required controls: **Force CPU** boolean (`fcpu`); default is false in each plugin.
- Asset note: deblur requires both the named `best_fpn.h5` checkpoint and the
  sibling serialized `mymodel.pth` used by the inspected helper.
- Alpha: source removes alpha before inference.
- Expected shape: image-sized HxWx3 `uint8`-like pixels, subject to model helper
  padding/resizing. Exact accepted modes beyond the source's wildcard registration
  are unknown.
- Output intent: same image dimensions for deblur, dehaze, enlighten, and the
  observed denoiser path; output layer insertion is source-observed but unverified.

### Monocular depth

- Input: current selected layer only.
- Control: **Force CPU**.
- The helper scales the largest input dimension toward 640 and makes the network
  input dimensions multiples of 32; the returned normalized 8-bit disparity is
  resized to the source dimensions and repeated across three channels.
- This is a relative/normalized visualization, not calibrated metric depth. The
  source calls it a disparity map; do not promise metric units or geometric scale.

### Semantic segmentation

- Input: current selected layer containing one or more documented classes:
  person, bird, cat, cow, dog, horse, sheep, aeroplane, bicycle, boat, bus, car,
  motorbike, train, bottle, chair, dining table, potted plant, sofa, or tv/monitor.
- Control: **Force CPU**.
- The manual describes these supported classes; the model code predicts an argmax
  over 21 output channels. Unsupported classes, multilabel semantics, instance IDs,
  polygon/vector masks, and confidence calibration are not promised.
- Output intent: a same-size three-channel class-index visualization. The actual
  source path does not apply its declared palette to the returned array, so do not
  describe it as a human-readable class-color legend without checking the host
  result.

### Face parsing

- Input: current selected layer containing **only a portrait image of a person**.
- Control: **Force CPU**.
- Source normalizes a 512x512 resized image and predicts 19 parsing labels, then
  resizes the label map to the source size and applies a fixed color palette.
- A group photo, non-human image, partial unsupported subject, or non-portrait scene
  is outside the documented contract. This route does not perform face detection or
  crop a face automatically.

### Super-resolution

- Input: current selected layer, with **Scale** in the observed range 1 to 4 in
  0.5 increments; **Force CPU**; and **Use as filter** (`ffilter`, default true).
- The implementation loads a 4x SR model and post-resizes by `scale / 4`, so the
  requested scale is the public output-size control. Confirm the resulting size
  before writing or opening a result.
- For images roughly above 400 pixels in height or width, the manual recommends
  **Use as filter = True** to tile work and reduce memory pressure. Tiling does not
  make a large output guaranteed to fit; expect boundary/oom trade-offs to remain.

### Frame interpolation

- Inputs: a distinct start-frame layer and end-frame layer in the same image, plus
  an **Output Location** folder and **Force CPU**.
- Both layer dimensions must match the containing GIMP image. The source checks both
  dimensions and tells the user to run Layer -> Layer to Image Size for both layers.
- Alpha is removed from both frames. The implementation pads to dimensions divisible
  by 32, interpolates four rounds, and intends to write 17 PNG files to the chosen
  folder. It does not add those frames as GIMP layers in the observed path.
- Use a dedicated, writable output directory. Treat existing files with the same
  names as a collision requiring explicit user approval; the source's overwrite
  behavior was not separately verified.

## Preflight checklist

1. Is the requested operation in this route?
2. Is the current layer selected and image-sized? If interpolation, are both named
   layers distinct, RGB-like, and image-sized?
3. Is the semantic input from the documented class set, or is face parsing clearly a
   portrait-only image?
4. For super-resolution, are scale and filter mode explicit, and is the output size
   acceptable?
5. For interpolation, is the folder explicit, writable, and intentionally isolated?
6. Does the explicit weights root contain every required relative asset?
7. Has CPU been selected if CUDA probing fails, memory is limited, or the user asks
   for deterministic low-memory operation?

If any answer is no, stop at actionable remediation. Do not invoke a plugin with a
known-bad layer or silently fabricate a successful output.

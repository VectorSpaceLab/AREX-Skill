# Mask and Layer Contracts

This reference is the acceptance contract for guided editing. It preserves the
legacy plugin's numeric conventions rather than guessing from a layer's name
or visual appearance. Dimensions use `(width, height)`; a pixel channel value
is in the 0--255 range.

## Common representation

| Artifact | Accepted practical representation | Required relationship |
|---|---|---|
| Base image | RGB or RGBA; RGB is safest for the legacy plugins | Exactly the image canvas size |
| Inpainting mask | One-channel, grayscale+alpha, RGB, or RGBA binary image; RGB channels must agree | Exactly the base image size |
| Matting trimap | RGB (RGBA is accepted when alpha is incidental); one-channel files may be preflighted but do not satisfy the manual's RGB presentation rule | Exactly the base image size |
| Face label mask | RGB or RGBA color-coded labels; alpha is discarded by the plugin | Exactly the portrait size and canvas |
| Color mask | RGBA transparent layer with RGB point colors and alpha | Exactly the colorized image size and canvas |

An alpha channel on an ordinary image, mask, trimap, or face label does not
replace spatial alignment and is not used as a substitute for the documented
mask or trimap values. A color mask is different: its alpha is the mechanism
that distinguishes a point from an empty pixel and must be retained.

The plugin code reads layer pixels at the layer's own origin and compares the
height and width to the GIMP image. It does not repair an offset layer. Run
**Layer -> Layer to Image Size** on the base image, every mask, every trimap,
and all three face layers before execution. A same-looking crop, scale, or
manual drag is not evidence of alignment.

## Inpainting mask

The user-facing inpainting contract has two layers:

1. **Image layer:** the source RGB/RGBA image.
2. **Mask layer:** a binary mask of the object to remove.

Use these numeric pixels:

| Numeric pixel | Manual wording | Plugin meaning |
|---|---|---|
| `(255,255,255)` | “black background” | Keep/source region |
| `(0,0,0)` | “white object” | Missing/object-to-remove region |

The manual's words and numeric examples are reversed in ordinary visual RGB
terminology. The checked implementation takes the first mask channel, computes
`1 - mask/255`, and multiplies the image by that internal keep mask. That
source-level path therefore treats zero-valued pixels as holes and 255-valued
pixels as preserved, while the user-facing manual explicitly calls for 255
background and 0 object. Preserve the manual contract for the user and treat
this source/runtime-versus-manual discrepancy as an explicit verification
question on the actual host/version. Do not silently invert a supplied mask;
show the polarity report, run a controlled fixture only when the runtime is
available, and record which convention was observed.

The safe contract is exact binary values only. If a mask has intermediate
values, anti-aliased edges, or disagreeing RGB channels, stop and make the
binary intent explicit before model execution. A grayscale+alpha mask is
accepted for static preflight; the first (grayscale) channel is the mask and
alpha is not a replacement for its values. A mask containing only one
polarity is technically aligned but should be reviewed because it may remove
(or preserve) the entire image. The plugin pads inputs internally and crops
its result back to the original dimensions; preflight alignment still refers
to the unpadded user layers. A static validator report cannot resolve the
manual/source polarity discrepancy or prove visual output.

## Deep image matting trimap

Matting consumes an RGB image and an RGB trimap:

- `(0,0,0)`: known black background; output alpha is clamped to 0.
- `(255,255,255)`: known white foreground/object; output alpha is clamped to
  255.
- `(128,128,128)`: gray unknown boundary; the model estimates alpha here.

A trimap must contain the exact three values unless a caller explicitly uses
the validator's tolerance option for a known encoding artifact. Tolerance is a
preflight aid, not a license to feed arbitrary gray values to the plugin: the
repaired file should use exact triplets. The red/green/blue channels must
agree for an RGB trimap. The implementation uses the first channel, resizes or
crops for inference, then restores the original shape and hard-clamps the
known black and white regions. A trimap with no gray pixels gives the model no
unknown region; treat that as a warning or a hard stop according to the edit
objective.

The training/data path generates gray boundaries by erosion and dilation and
uses 128 as the unknown code. The deploy path also skips crop regions without
unknown pixels. This is why a broad, spatially meaningful gray boundary is more
useful than a one-pixel accidental stripe.

## Face parsing and face generation

**Face parsing is a prerequisite.** It accepts a portrait containing a person
and produces a color-coded 19-class face label layer. Parsing alone does not
render a new portrait. If the parsing checkpoint or compatible runtime is not
available, the workflow ends at preparation and must say so.

Face generation requires exactly these aligned layers:

1. **Portrait:** the original RGB portrait image.
2. **Original mask:** the color label result from face parsing.
3. **Modified mask:** a duplicate of the original mask edited with a paintbrush
   or an equivalent label-preserving operation.

The generator is configured for a 19-class label map, 512-pixel transforms, an
RGB image input, and RGB output. Its label conversion compares exact RGB
triples. Use the following palette (the order is not a visual semantic
ordering; preserve each triple):

```text
(0,0,0)       (204,0,0)     (76,153,0)   (204,204,0)
(51,51,255)   (204,0,204)   (0,255,255)  (51,255,255)
(102,51,0)    (255,0,0)     (102,204,0)  (255,255,0)
(0,0,153)     (0,0,204)     (255,51,153) (0,204,204)
(0,51,0)      (255,153,51)  (0,204,0)
```

Do not paint arbitrary anti-aliased colors into the modified mask. A changed
label should be a complete supported palette color, and the modified mask
should retain the same dimensions and coordinate system as the original.
The generator converts both masks with nearest-neighbor transforms, so
bilinear resampling of labels can create invalid colors. The portrait and
masks may contain alpha at the file boundary, but the legacy entry point drops
it before inference.

The bundled model/options evidence establishes `label_nc=19`, `input_nc=3`,
`output_nc=3`, `loadSize=512`, `fineSize=512`, a pix2pixHD-style generator,
and a named checkpoint experiment. Those are architecture/runtime facts, not
proof that a checkpoint is present in a target installation.

## Deep coloring guidance

Deep coloring expects the visible grayscale image to remain an **RGB-mode**
image; changing the image mode to a single-channel grayscale mode violates the
manual's preparation rule. A color mask layer is optional. When supplied, it
is an RGBA transparent RGB layer containing sparse local colored points (the
manual describes points approximately six pixels in size). Its coordinates
must be aligned to the image. Transparent pixels mean “no color hint”; visible
RGB points are hints, not a complete target image.

The manual permits using the image and color mask as the same layer and still
obtaining a prediction, but a separate transparent layer is easier to audit.
The checked deep-color entry point treats a same-named layer as “no user
points”; when a separate layer is supplied it requires alpha, converts its RGB
points to Lab guidance, and uses nonzero alpha as the point mask. The validator
requires a separate explicit color-mask file to have alpha and reports whether
any visible points exist; it does not infer point size or judge color
plausibility.

## Verification and limits

A passing static contract proves only that files are readable and their
geometry/channels/value encodings meet this reference. It does not prove:

- GIMP can load the legacy `gimpfu` entry point;
- a model checkpoint can be found or loaded;
- CPU or CUDA inference will fit memory;
- a parsed face is actually a suitable portrait;
- a generated image is visually faithful; or
- a color point has the intended semantic effect.

Keep those claims separate in the handoff and use
[troubleshooting.md](troubleshooting.md) for unresolved runtime failures.

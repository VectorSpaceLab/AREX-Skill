# Troubleshooting

Use the smallest applicable remedy and keep the failure visible. This route has no
network recovery, credential handling, checkpoint downloading, or destructive file
repair.

## Missing checkpoint or optional package

**Symptom:** the asset checker reports a missing relative path, or the plugin cannot
import a model/helper package.

**Action:** stop before inference. Ask the operator to provide an explicit weights
root containing the exact observed relative asset(s) and to install the matching
legacy model package in a compatible host. Do not download from `syncWeights.py`,
do not replace a checkpoint with a same-named file, and do not infer a version from a
filename. Deblur requires both `best_fpn.h5` and the helper's sibling `mymodel.pth`;
for denoise and interpolation, all required files are mandatory. For
Enlighten, confirm the checkpoint directory/name convention in the model package as
well as the `enlightening/200_net_G_A.pth` manifest entry.

Common Torch/TorchVision/Pillow/OpenCV Python 3 imports were verified, but that
is not proof that the old Python 2 GIMP plugin dependencies can import. GIMP and
Python 2 are unavailable for this verification.

## CPU versus CUDA

**Symptom:** CUDA is unavailable, `torch.cuda.is_available()` is false, model loading
or allocation raises a CUDA error, or the user prefers low-memory operation.

**Action:** enable **Force CPU** (`fcpu`). The source uses that flag for all nine
operations. Several loaders explicitly use CPU `map_location`; semantic segmentation
loads directly and its CPU checkpoint behavior is not fully explicit, so a compatible
checkpoint/package remains required.

Run:

```text
python scripts/probe_torch_backend.py
```

The probe reports availability and device names without allocating a large tensor.
On the inspected host CUDA was visible, but a tiny device allocation was blocked by
host CUDA OOM. Therefore the route must not report CUDA execution merely because the
availability flag is true. CPU inference was not run because checkpoints are absent.

## Input-size and layer mismatch

**Symptom:** the plugin says to run Layer -> Layer to Image Size, or the layer/image
shape check fails.

**Action:** resize the layer to the containing image in GIMP, then reselect it and
recheck the alpha/channel contract. Do not bypass the guard by changing metadata.
Interpolation requires both start and end layers to match the image dimensions.

**Symptom:** output is too large or memory fails.

**Action:** for super-resolution, lower the requested scale, use **Use as filter**
for roughly 400-pixel-plus dimensions, or use a smaller working copy. For other
filters, try Force CPU and a smaller fixture only as a diagnostic; model quality and
large-image support are unverified. Frame interpolation pads dimensions to multiples
of 32, so working memory can exceed the visible image size.

## Super-resolution output surprise

The source loads a 4x model and post-resizes by the requested-scale/4 factor. At
scale 1 it intends to add a layer; at other scales it intends to create a new GIMP
image. Confirm the output dimensions and destination before execution. Do not treat
the filter flag as a change in model architecture; it selects a tiled processing
path in the observed code.

## Output folder and collisions

**Symptom:** frame interpolation cannot create/write the output directory, or a
file collision is reported.

**Action:** choose a user-approved, writable directory with sufficient space. The
source computes a default output path but runtime instructions must use an explicit
folder. Before a real run, inspect for `img0.png` through `img16.png`; preserve
existing files unless the user explicitly authorizes replacement. The safe scripts in
this skill never create, delete, or overwrite those files.

## Semantic segmentation or face parsing mismatch

Semantic segmentation is documented for the 21-class set listed in
`input-contracts.md`; it is not a general instance-segmentation or object-detection
route. Face parsing is portrait-only and predicts 19 parsing labels after a 512x512
resize; it does not detect or crop faces. Use another workflow or pre-process under
an explicitly supported host if the input is outside those contracts.

## GIMP host absent

**Symptom:** `gimpfu`, GIMP menu registration, layer creation, or `pdb` calls cannot
be exercised.

**Action:** report a static-only result. Verify only file presence, argument/help
behavior, source-derived contracts, and backend probing. Do not mock a successful
GIMP layer mutation as execution. A compatible GIMP/Python 2 host, optional package
set, and exact checkpoints are required for native verification.

## What remains unresolved

- No checkpoint inference was verified because all expected weights are absent.
- CUDA allocation was host-blocked by current-host CUDA OOM; no model-backed GPU
  result exists.
- CPU model inference was not verified without weights.
- GIMP, `gimpfu`, Python 2, menu registration, layer mutation, and progress UI were
  not available.
- Exact model versions, checkpoint schemas, color-management behavior, quality,
  output collision semantics, and legacy dependency compatibility remain unknown.

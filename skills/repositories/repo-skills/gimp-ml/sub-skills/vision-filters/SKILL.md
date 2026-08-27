---
name: vision-filters
description: "Route GIMP-ML model-backed restoration and vision filters with
  explicit input, checkpoint, device, memory, and output-folder checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Vision filters

Use this sub-skill for the model-backed GIMP-ML operations that consume one or two
image layers and produce a restoration, map, mask, enlarged image, or interpolated
frame sequence:

- restoration: deblur, dehaze, denoise, and enlighten;
- analysis maps: monocular depth and semantic segmentation;
- portrait parsing: face parsing;
- enlargement: super-resolution;
- temporal synthesis: frame interpolation.

This is an operating router, not a model zoo. Read only the linked reference needed
for the requested operation:

- [model overview](references/model-overview.md) for checkpoint paths, observed
  preprocessing, device loading, and output details;
- [input contracts](references/input-contracts.md) for layer and parameter checks;
- [workflows](references/workflows.md) for step-by-step routing;
- [troubleshooting](references/troubleshooting.md) when prerequisites or runtime
  behavior fail.

## Hard boundary

The documented plugin contracts and source-level loading behavior are recorded here,
but checkpoint inference was **not verified**: the checkout has no weight files, and
CUDA is visible on the inspection host but a tiny allocation was blocked by host CUDA
OOM. Do not claim a restored image, depth map, segmentation, portrait mask, enlarged
image, or interpolated frame was produced. Do not download weights, call external
model services, or invent a model version. The model asset checker only checks files.

The original integration is a GIMP Python 2 plug-in. GIMP, `gimpfu`, and Python 2
are unavailable for the verified host. Therefore the GIMP menu, layer
mutation, progress display, and actual model execution remain unverified.
Python 3 inspection imports include Torch, TorchVision, Pillow, OpenCV, and the other
packages recorded by the parent skill; those imports do not prove plug-in compatibility.
No OpenAI call, hosted model, or substitute checkpoint is assumed.

## Routing procedure

1. Identify the operation and whether it is restoration, an output map, a portrait
   mask, enlargement, or temporal synthesis.
2. Validate the layer contract before loading anything. Most operations use the
   currently selected layer; interpolation needs distinct start and end layers.
3. Ask for an explicit generic weights root. Run
   `python scripts/check_model_assets.py WEIGHTS_ROOT`; a missing asset is a blocker,
   not a reason to download or substitute a checkpoint.
4. Choose CPU when CUDA is unavailable, when the user sets **Force CPU**, or when
   memory is uncertain. Otherwise CUDA is only an attempted preference, not a success
   guarantee. Run `python scripts/probe_torch_backend.py` for a no-allocation report.
5. For super-resolution, set the requested scale and use the filter/tiled mode for
   images around or above 400 pixels in either dimension. For interpolation, confirm
   the output directory is intentional and writable before starting.
6. Report the intended output layer/file naming and the verification boundary. Preserve
   the input layer; these operations create a result layer or files rather than
   silently proving an in-place edit.

## Route summary

| Request | Required input | First action |
|---|---|---|
| Deblur, dehaze, denoise, enlighten | Current selected layer | Validate layer-to-image size and RGB conversion needs |
| Monocular depth | Current selected layer | Expect a normalized disparity/depth visualization |
| Semantic segmentation | Current selected layer with a supported class | Check the documented 21-class subset |
| Face parsing | Portrait-only current selected layer | Reject non-portrait use as unsupported |
| Super-resolution | Current selected layer, scale, filter flag | Check output size and tiled-memory mode |
| Frame interpolation | Start layer, end layer, output folder | Check matching dimensions and writable destination |

Do not use this route for inpainting, coloring, matting, face generation, clustering,
or text/image service operations; those belong to other sub-skills.

## Verification record

Static review covered the documented input descriptions, the nine named entry points,
selected model/helper loading code, and the weight-sync manifest. The safe scripts
are the only executable artifacts in this subtree. They perform no network access,
credential lookup, checkpoint loading, GIMP mutation, or destructive write.

Native candidates for later verification are one current selected RGB layer for each
single-layer filter, a portrait layer for face parsing, a supported-class scene for
segmentation, a medium/large layer for tiled super-resolution, and two equal-sized
layers plus a temporary output directory for interpolation. See the references for
synthetic difficult cases and known gaps.

---
name: classical-image-ops
description: "Route deterministic, CPU-safe guidance for classical GIMP-ML image
  operations, drawable-to-array validation, clustering, palette behavior, and
  result-layer handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classical image operations

Use this sub-skill for small, non-neural image transformations in GIMP-ML:
inversion, K-means segmentation, palette behavior, and the NumPy/GIMP layer
boundary. It is useful both for a novice who needs a safe preflight checklist
and for an expert diagnosing shape, channel, or result-layer mismatches.

## Scope and boundary

- **In scope:** current drawable/layer selection, byte-array conversion,
  image-size checks, RGB/RGBA handling, K-means arguments, palette facts, and
  result-layer conventions.
- **CPU-safe helper reasoning:** NumPy array inspection, shape checks, byte-range
  checks, and pure-array reasoning do not need a model, network, service, or GPU.
- **Out of scope:** neural plug-ins, training, GIMP installation, remote APIs,
  model weights, and changes to the live router or service.
- **GIMP boundary:** the plug-ins use the legacy `gimpfu`/PDB interface. GIMP and
  Python 2 are unavailable for the verified host, so a live menu invocation,
  PDB mutation, and pixel-region write are not verified here.
  Treat those steps as static-only until tested in a compatible GIMP runtime.

## Choose a route

1. **Validate an input first.** For an `.npy` or image file, run the bundled
   adapted helper; it only reads and reports, and does not write by default.
   See [the workflow](references/workflows.md#array-preflight).
2. **Invert a selected drawable.** Use the plug-in's `Invert` registration only
   when in-place mutation and an undo group are acceptable. The source operation
   calls the PDB invert procedure on the selected layer; it is not a verified
   `createResultLayer` operation. Preserve this exception rather than claiming
   that it creates a new layer.
3. **Segment by color.** Select the source layer, confirm it is image-sized,
   choose a positive cluster count, and decide whether `(x, y)` is a feature.
   The K-means route is CPU-oriented but the source does not seed SciPy's
   initialization, so do not promise reproducible labels without an explicit
   deterministic wrapper.
4. **Inspect palette behavior.** The repository's `colorpalette` plug-in loads
   its bundled palette image, converts OpenCV BGR to RGB, and opens a separate
   image named `palette`. It does not extract colors from the current drawable.
5. **Need the exact contract?** Open [API reference](references/api-reference.md)
   before writing an adapter; open [troubleshooting](references/troubleshooting.md)
   when a run produces no layer, errors on shape, or exhausts memory.

## Safe preflight

- Confirm the intended image and active drawable. A drawable is the actual
  pixel source; the image is the container into which result layers are added.
- Ensure the selected layer has positive height and width and is the same size
  as its image. Use GIMP's **Layer -> Layer to Image Size** before K-means when
  the layer is cropped or offset.
- For K-means, use RGB or RGBA data. RGBA is reduced to RGB by dropping alpha;
  grayscale, indexed, two-channel, or unexpected multi-channel input is not a
  supported K-means shape in the source implementation.
- Check that `1 <= clusters <= height * width`. Small images cannot support a
  large K; duplicate colors can also make a requested K ill-conditioned.
- Estimate memory before flattening: K-means materializes one row per pixel and,
  with position enabled, adds two feature columns. Reduce image size or K when
  the array is too large for the available RAM.
- Keep byte outputs in the inclusive `[0, 255]` range. The shared result helper
  casts to `uint8`; clipping or validating before that cast avoids silent wrap.

## Result conventions

Array-producing plug-ins conventionally convert the result to `uint8` bytes,
create a layer with the image width and height, write the full pixel region, add
the layer at stack position zero, and flush displays. The conventional name is
`new_output`, but it is not a stable identifier. Verify the actual layer after a
live run rather than relying on a name.

The shared `channelData` pattern reads the entire drawable pixel region and
reshapes its bytes as `(layer.height, layer.width, region.bpp)`. It preserves an
alpha channel until the operation explicitly removes it. It does not repair
layer offsets or resample data. A result must have a byte layout compatible with
its destination layer; mismatched dimensions or channel count can fail at the
pixel-region write.

## Determinism and evidence labels

The array validation and conversion guidance is deterministic and CPU-safe. The
K-means source calls SciPy `kmeans2` with its default initialization and no seed;
cluster IDs and borderline assignments may vary. Coordinate features are raw
pixel indices, so enabling position changes the feature space, not just the
rendering. The color-palette behavior is a static asset-display path, not a
verified current-layer extraction algorithm.

Do not infer live GIMP behavior from a successful NumPy/Pillow check. Do not
assume CUDA, OpenCV model weights, OpenAI calls, or a running service are needed
for these classical routes. For source-derived details and failure handling,
follow the linked references.

## Linked materials

- [Workflows](references/workflows.md) — novice and expert procedures,
  array-to-layer contracts, and K-means memory guidance.
- [API reference](references/api-reference.md) — registrations, parameters,
  helper contracts, supported shapes, and output semantics.
- [Troubleshooting](references/troubleshooting.md) — invalid channels,
  layer-size mismatch, cluster failures, position-feature surprises, and
  memory/shape errors.
- [Bundled array validator](scripts/validate_image_array.py) — a read-only,
  adapted helper with `--help`, explicit input, channel, range, dtype, and size
  checks.

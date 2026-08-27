---
name: portrait-workflows
description: "Run U-2-Net portrait drawing, own-image face-crop portrait
  inference, and portrait/original compositing workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Portrait Workflows

Use this sub-skill when the task is portrait drawing/generation with the U-2-Net portrait checkpoint, own-photo face-crop portrait inference, Haar-cascade handling, or portrait/original composite images with explicit blur and blend controls.

## Start here

1. Choose the portrait workflow in [workflows](references/workflows.md): APDrawingGAN-style portrait-set inference, own-image face-crop inference, or portrait/original compositing.
2. Run the bundled helpers instead of original demo scripts:
   - [`scripts/portrait_infer.py`](scripts/portrait_infer.py) for portrait-set and own-image portrait maps.
   - [`scripts/portrait_composite.py`](scripts/portrait_composite.py) for Gaussian-blurred original plus portrait-map composites.
3. Supply explicit `u2net_portrait.pth`-compatible weights with `--weights`; pretrained portrait weights are not bundled.
4. Use [troubleshooting](references/troubleshooting.md) when weights, OpenCV, cascade parsing, CUDA selection, no-face fallback, alpha/sigma validation, or image quality is the problem.

## Common routes

- **APDrawingGAN-style portrait inputs:** use `portrait_infer.py --mode portrait-set`. Inputs should already be split/cropped portrait images, commonly 512x512.
- **Own photos:** use `portrait_infer.py --mode own-images`. It uses the bundled Haar cascade by default, selects the largest face, crops/pads/resizes to 512, and falls back to the whole image if no face is found.
- **Composite style:** use `portrait_composite.py --sigma 20 --alpha 0.5` or other explicit values. It writes `*_sigma_<sigma>_alpha_<alpha>_composite.png` with numeric punctuation sanitized for portability.
- **Plumbing-only smoke checks:** add `--allow-random-weights-for-smoke --max-images 1 --device cpu` only to verify imports, preprocessing, forward pass, and output writing. Do not treat random-weight outputs as portrait quality evidence.

## Quality constraints

For own photos, high-quality portrait drawing requires the head region to be close to or larger than 512x512 and the head background to be relatively clear. Small, blurry, occluded, profile, crowded, or cluttered photos may run but usually produce weak portraits.

## Boundaries

- Generic salient-object masks, background removal, and human/person masks route to `salient-object-inference`.
- Architecture internals, side-output semantics, model variant choice, and checkpoint-shape diagnosis route to `model-architecture`.
- Dataset construction, augmentation, retraining, loss wiring, and long training runs route to `data-and-training`.

## Minimal commands

Portrait-set inference:

```bash
python scripts/portrait_infer.py \
  --weights PATH_TO_WEIGHTS/u2net_portrait.pth \
  --input-dir INPUT_PORTRAITS \
  --output-dir PORTRAIT_RESULTS \
  --mode portrait-set \
  --device auto
```

Own-image inference with the bundled cascade:

```bash
python scripts/portrait_infer.py \
  --weights PATH_TO_WEIGHTS/u2net_portrait.pth \
  --input-dir OWN_IMAGES \
  --output-dir YOUR_PORTRAIT_RESULTS \
  --mode own-images \
  --device auto
```

Composite with README-style parameters:

```bash
python scripts/portrait_composite.py \
  --weights PATH_TO_WEIGHTS/u2net_portrait.pth \
  --input-dir OWN_IMAGES \
  --output-dir COMPOSITE_RESULTS \
  --sigma 20 \
  --alpha 0.5 \
  --device auto
```

# Model Loading and Conversion

## Checkpoint forms

The repo accepts local paths and, in several paths, public URLs. Keep checkpoints in a user-managed directory and preflight them with the root `check_model_assets.py` helper. Do not place multi-gigabyte files under the generated skill directory.

DragGAN’s renderer loads `G_ema` from a network pickle and reconstructs a StyleGAN2, StyleGAN3, or StyleGAN-Human generator based on filename signals. A valid pickle with an uninformative filename can still fail before generation; use a family-preserving filename for the renderer route.

## Legacy conversion

Use the command builder to print a conversion command:

```bash
python sub-skills/stylegan-generation/scripts/build_generation_command.py \
  --repo-root /path/to/DragGAN legacy-convert \
  --source legacy-input.pkl --dest native-output.pkl --force-fp16 False
```

The conversion utility supports the main TensorFlow StyleGAN2/StyleGAN2-ADA network forms and can force FP16. It does not support every comparison-method pickle, StyleGAN2 configs A–D, or StyleGAN1. Treat conversion as a new output file; do not overwrite the only copy of the source pickle.

## Renderer vs batch generation

- The DragGAN renderer uses `G_ema`, reconstructs a generator, creates a latent from `w0_seed`, and optimizes `w` or `w+` during dragging.
- The top-level batch generator samples `z` from a deterministic NumPy random state for each seed, maps/synthesizes it, and saves `seed####.png`.
- StyleGAN-Human generation has its own `legacy.py` and package roots. Keep its command context separate from the top-level `dnnlib`, `legacy`, and `torch_utils` modules because the repository contains overlapping module names.

## Model validation checklist

1. File exists and is a real pickle, not an HTML/error response.
2. Filename contains the family expected by the selected route.
3. Model resolution and available VRAM fit the requested workflow.
4. Conditional models receive a class label.
5. Output directory is writable and does not contain stale outputs from a different model/seed plan.
6. For StyleGAN-Human editing, verify latent direction/statistics assets separately; a checkpoint alone is not enough.

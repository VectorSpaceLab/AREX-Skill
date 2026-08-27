# Assets and layout

This sub-skill treats `download.sh` as reference-only. Do **not** wrap it as an executable helper, because it fetches network-hosted checkpoints and dataset bundles.

## Expected local layout

The sample configs assume a layout like this:

```text
data/
  pretrained/
    celeba256_250000.pt
    256x256_classifier.pt
    256x256_diffusion.pt
    places256_300000.pt
  datasets/
    gts/
      face/
      c256/
      inet256/
      p256/
    gt_keep_masks/
      face/
      thin/
      thick/
      nn2/
      ex64/
      ev2li/
      genhalf/
```

## What the bundle expects

- `model_path` must point at a real checkpoint file.
- `gt_path` and `mask_path` must be directories with the same number of image files.
- `paths.srs`, `paths.lrs`, `paths.gts`, and `paths.gt_keep_masks` are writable output directories.
- The loader accepts `jpg`, `jpeg`, `png`, and `gif` files.
- GT and mask files are paired by sorted recursive traversal, so the directory order must be stable.

## Custom data checklist

- Pick the closest base config: face for aligned faces, ImageNet for diverse class-conditioned content, Places2 for scene images.
- Place one GT image and one keep mask for each example.
- Keep the keep-mask convention consistent: white/255 for known pixels, black/0 for unknown pixels.
- If your masks are the reverse convention, invert them before running.
- If your masks contain values other than 0 or 255, remember the loader will treat them as soft weights.

## Source artifact map

| Source artifact | Bundled use |
| --- | --- |
| `README.md` | workflow summary, dataset families, and output location notes |
| `test.py` | adapted into `scripts/run_inpainting.py` |
| `download.sh` | reference-only asset acquisition script |
| `confs/*.yml` | config templates for face, ImageNet, and Places2 |
| `guided_diffusion/image_datasets.py` | pairing, crop, and mask-scaling behavior |
| `conf_mgt/conf_base.py` | output-directory semantics |

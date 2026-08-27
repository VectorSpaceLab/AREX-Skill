# Troubleshooting

## 1) `ppgan.apps` or a predictor import fails

Run the bundled checker first:

```bash
python scripts/check_image_app_deps.py
```

Typical causes:

- `dlib` is missing for face parsing, portrait alignment, or cartoonization.
- `clip` is missing only for the optional CLIP-guided StyleGAN extension.
- `imageio`, `scipy`, `skimage`, or `natsort` is missing for one of the image predictors.
- The installed Paddle build does not match the requested backend.

## 2) The predictor tries to download weights

Many predictors auto-download when `weight_path=None`. If the user wants offline or reproducible runs, require a local file path and say so explicitly before constructing the predictor.

Examples of common auto-download routes:

- `AnimeGANPredictor`
- `LapStylePredictor`
- `MPRPredictor`
- `NAFNetPredictor`
- `SwinIRPredictor`
- `InvDNPredictor`
- `RealSRPredictor`
- `StyleGANv2Predictor`
- `StyleGANv2FittingPredictor`
- `StyleGANv2MixingPredictor`
- `StyleGANv2EditingPredictor`
- `Pixel2Style2PixelPredictor`
- `MiDaSPredictor`
- `FaceEnhancement` and `gfp_FaceEnhancement`
- `Photo2CartoonPredictor`
- `GPENPredictor`
- `SinGANPredictor` when `pretrained_model` is used

## 3) Face detection or face parsing fails

Symptoms:

- `FaceParsePredictor` returns `None`
- `Pixel2Style2PixelPredictor` cannot align the face
- `Photo2CartoonPredictor` cannot crop the portrait cleanly

Fixes:

- Confirm `dlib` is installed.
- Use a clear, front-facing portrait with one dominant face.
- If the user only wants stylization rather than face-aware logic, route to `AnimeGANPredictor` instead.
- If the image is already cropped and aligned, avoid unnecessary extra alignment steps.

## 4) CLIP is missing

CLIP is optional. It only matters for the non-default CLIP-guided StyleGAN extension. Standard latent fitting, mixing, and editing do not need it.

If the user asks for text-guided editing and CLIP is unavailable, say that the CLIP extension is not a baseline dependency in this sub-skill and ask whether they want to install it.

## 5) Restoration predictors reject the input filename

`MPRPredictor`, `NAFNetPredictor`, `SwinIRPredictor`, and `InvDNPredictor` derive output names by splitting the input filename on `.`. If the stem contains more than one dot, the source code asserts.

Fix: rename the file to a simpler stem such as `input.png` before running the predictor.

## 6) Latent workflows fail on shape or type mismatches

- `StyleGANv2MixingPredictor` requires two latent `.npy` files with the same latent depth.
- The `weights` list must have the same number of levels as the latent depth.
- `StyleGANv2EditingPredictor` expects the latent file path and a direction key, not a direction tensor path.
- `StyleGANv2FittingPredictor` uses latent optimization, so `need_align=True` only makes sense when the input is a face that still needs alignment.
- `Pixel2Style2PixelPredictor` needs a detectable face before it can build the latent.

## 7) `GPENPredictor` is not a good CPU-only default

The predictor computes face restoration and also reports FID/PSNR. Its evaluation path is GPU-oriented, so do not present it as a safe CPU-only verification route.

If the user only needs a face cleanup pass on CPU, prefer the lower-level face enhancement utility when it is sufficient.

## 8) `AOTGANPredictor` and `PhotoPenPredictor` need a config object

These constructors are not plain one-line predictors. They expect a generator config object in addition to weights and paths.

Fix:

- load a user-owned YAML config with `get_config(...)`
- pass the `cfg.predict` object to the constructor
- keep the output argument as a file path, not a folder

## 9) The chosen model family does not match the request

Quick correction rules:

- Use `AnimeGAN` for quick stylization without face logic.
- Use `Photo2Cartoon` for portrait cartoonization.
- Use `StyleGANv2Editing` for attribute edits such as smile or age.
- Use `StyleGANv2Mixing` only when you already have two latents.
- Use `MPR`, `NAFNet`, `SwinIR`, or `InvDN` for restoration.
- Use `RealSR` for super-resolution.
- Use `FaceEnhancement` or `GPEN` for face cleanup.
- Use `PSGAN` for makeup transfer.
- Use `SinGAN` when the user explicitly wants single-image generative behavior.

## 10) Full inference is out of scope without explicit assets

Do not promise a successful image result when the request has no explicit weights, no input media, or no backend choice. In that case, keep the response at the API / selection / troubleshooting level and ask for the missing asset or decision.

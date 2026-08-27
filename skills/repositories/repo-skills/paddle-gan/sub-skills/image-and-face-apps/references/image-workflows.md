# Image and face workflow map

This guide helps you choose the right `ppgan` predictor family before you touch weights or media.

## 1) Choose the family

| Need | Pick | Why |
| --- | --- | --- |
| Quick photo-to-anime stylization without face alignment | `AnimeGANPredictor` | Fast, simple, and works on a single image path. |
| Portrait cartoonization that preserves facial identity more strongly | `Photo2CartoonPredictor` | Uses face alignment and face segmentation around the portrait. |
| Face parsing or component masks | `FaceParsePredictor` | Produces a semantic face mask for downstream face workflows. |
| Blind face restoration / cleanup | `FaceEnhancement` or `GPENPredictor` | Use the face utility when you only want enhancement; use the predictor when you want the evaluated GPEN workflow. |
| Makeup transfer | `PSGANPredictor` | Needs a source portrait, a reference directory, and a config object. |
| Denoising, deblurring, deraining | `MPRPredictor`, `NAFNetPredictor`, `SwinIRPredictor`, or `InvDNPredictor` | Use the model that matches the task and desired restoration behavior. |
| 4x super-resolution on a single image | `RealSRPredictor` | Best when the user wants a super-resolution model rather than a generic restorer. |
| Inpainting with a binary mask | `AOTGANPredictor` | The mask tells the generator what to fill. |
| Semantic-label to photo synthesis | `PhotoPenPredictor` | Needs a semantic label map and a config-backed generator spec. |
| Depth estimation from one RGB image | `MiDaSPredictor` | Returns a depth map and optionally writes depth files. |
| Generate, fit, mix, or edit StyleGAN faces | `StyleGANv2Predictor`, `StyleGANv2FittingPredictor`, `StyleGANv2MixingPredictor`, `StyleGANv2EditingPredictor` | Use the latent family when the task centers on `.npy` latents or attribute edits. |
| Encode a face to a latent first | `Pixel2Style2PixelPredictor` | Produces the latent that StyleGANv2 editing/mixing/fitting expects. |
| Single-image generative modeling from one image | `SinGANPredictor` | Supports random sampling, SR, animation, editing, harmonization, and paint-to-image. |
| Artistic style transfer | `LapStylePredictor` | Best when the user has both a content image and a reference style image. |

## 2) Recommended decision rules

- Use `AnimeGAN` when you want a quick stylized image and you do **not** want to depend on face detection.
- Use `Photo2Cartoon` when you want a portrait cartoon with stronger identity preservation and you can satisfy the face stack.
- Use `Pixel2Style2Pixel -> StyleGANv2Editing` when the user wants attribute edits such as age or smile and you can extract a latent.
- Use `StyleGANv2Mixing` only when you already have two latents and want to blend them.
- Use `StyleGANv2Fitting` when the user already has a face image and wants the latent optimization loop, not a direct encoder.
- Use `MPR`, `NAFNet`, `SwinIR`, or `InvDN` for restoration. Pick the task-specific model first, then the fastest acceptable predictor.
- Use `RealSR` when the request is clearly super-resolution rather than general restoration.
- Use `FaceEnhancement` when the user only wants a cleanup pass and does not need the full GPEN predictor report.
- Use `PSGAN` only when the request is makeup transfer with a source portrait and reference portraits.

## 3) Representative recipes

### A. Photo to anime vs portrait cartoon

```python
from pathlib import Path
from ppgan.apps import AnimeGANPredictor, Photo2CartoonPredictor

out = Path("outputs/image-face")
out.mkdir(parents=True, exist_ok=True)

anime = AnimeGANPredictor(output_path=str(out / "anime"), weight_path="/path/to/animeganv2_weight.pdparams")
anime.run("/path/to/photo.jpg")

cartoon = Photo2CartoonPredictor(output_path=str(out / "cartoon"), weight_path="/path/to/photo2cartoon_weight.pdparams")
cartoon.run("/path/to/portrait.jpg")
```

Use the first path when you want a stylized picture with no face detector dependency. Use the second path when you want portrait cartoonization and can satisfy the face-alignment stack.

### B. Restoration and super-resolution

```python
from ppgan.apps import MPRPredictor, NAFNetPredictor, SwinIRPredictor, InvDNPredictor, RealSRPredictor

mpr = MPRPredictor(output_path="outputs/mpr", task="Denoising", weight_path="/path/to/mpr_denoising.pdparams")
mpr.run("/path/to/noisy_or_blurry_image.png")

naf = NAFNetPredictor(output_path="outputs/nafnet", weight_path="/path/to/nafnet_denoising.pdparams")
af.run("/path/to/noisy_image.png")

sr = RealSRPredictor(output="outputs/realsr", weight_path="/path/to/realsr_weight.pdparams")
pred_img, saved_path = sr.run("/path/to/low_res_image.png")
```

Use `InvDNPredictor` when the user explicitly wants Monte-Carlo self-ensemble denoising. Use `RealSRPredictor` when the question is about super-resolution rather than generic restoration.

### C. Latent editing loop

```python
from ppgan.apps import Pixel2Style2PixelPredictor, StyleGANv2EditingPredictor, StyleGANv2MixingPredictor

p2s = Pixel2Style2PixelPredictor(
    output_path="outputs/pSp",
    model_type="ffhq-inversion",
)
_, _, latent = p2s.run("/path/to/aligned_face.jpg")

editor = StyleGANv2EditingPredictor(
    output_path="outputs/stylegan-edit",
    model_type="ffhq-config-f",
)
editor.run("outputs/pSp/dst.npy", "smile", 2.0)
```

If the user already has two latent files, skip the encoder and go directly to mixing:

```python
mix = StyleGANv2MixingPredictor(output_path="outputs/stylegan-mix", model_type="ffhq-config-f")
mix.run("/path/to/latent_a.npy", "/path/to/latent_b.npy", weights=[0.5] * 18)
```

### D. Face cleanup and makeup transfer

```python
from argparse import Namespace
from ppgan.apps.psgan_predictor import PSGANPredictor
from ppgan.faceutils.face_enhancement import FaceEnhancement
from ppgan.utils.config import get_config

# Face cleanup only.
enhancer = FaceEnhancement()
# enhancer.enhance_from_image(face_array)

# Makeup transfer with a user-owned config.
args = Namespace(
    config_file="/path/to/makeup.yaml",
    source_path="/path/to/source_face.png",
    reference_dir="/path/to/reference_faces",
    model_path="/path/to/psgan_weight.pdparams",
    evaluate_only=True,
    no_cuda=False,
    resume=None,
    load=None,
    val_interval=1,
    opt=None,
    profiler_options=None,
    seed=None,
    amp=False,
    amp_level="O1",
)

cfg = get_config(args.config_file)
PSGANPredictor(args, cfg, output_path="outputs/psgan").run()
```

## 4) SinGAN mode reminders

- `random_sample` needs no reference image.
- `sr`, `harmonization`, `editing`, and `paint2image` need `ref_image`.
- `harmonization` and `editing` also need `mask_image`.
- `pretrained_model` can replace a manual weight file when the model is one of the built-in single-image priors.

## 5) Face enhancement path

```python
from ppgan.faceutils.face_enhancement.gfpgan_enhance import gfp_FaceEnhancement

restorer = gfp_FaceEnhancement()
# out = restorer.enhance_from_image(face_array)
```

Use this when you want the GFPGAN-style restoration helper rather than the full predictor object.

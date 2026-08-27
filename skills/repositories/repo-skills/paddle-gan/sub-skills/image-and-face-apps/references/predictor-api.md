# Predictor API reference

Use the code-verified signatures below when building image or face workflows. When the docs and the current code path disagree, prefer the runtime behavior shown here.

## General import pattern

```python
import paddle
paddle.set_device("cpu")  # or "gpu" when the user explicitly wants GPU

from ppgan.apps import AnimeGANPredictor, StyleGANv2Predictor
```

## Output conventions at a glance

- Most predictors create their output directory automatically.
- Restoration predictors usually write the source copy and a `*_restoration.*` result.
- Latent workflows usually save both `.png` previews and `.npy` latents.
- `AOTGANPredictor` and `PhotoPenPredictor` write to the exact `output_path` you pass in, so treat that argument as a file path, not a folder.

## Generation, transfer, and latent workflows

| Class | Code-verified constructor | `run()` shape | Return / saved files | Notes |
| --- | --- | --- | --- | --- |
| `AnimeGANPredictor` | `(output_path='output', weight_path=None, use_adjust_brightness=True)` | `run(image)` | Saves `anime.png` under `output_path`; current source returns the input image object. | Safe for photo-to-anime style transfer. Path input is the safest choice. Auto-downloads the default AnimeGANv2 weight when `weight_path=None`. |
| `LapStylePredictor` | `(output='output_dir', style='starrynew', weight_path=None)` | `run(content_img_path, style_image_path)` | Saves `content.png`, `style.png`, and `stylized.png` under `output/LapStyle`; returns the stylized tensor. | Built-in style weights cover `starrynew`, `circuit`, `ocean`, and `stars`. |
| `StyleGANv2Predictor` | `(output_path='output_dir', weight_path=None, model_type=None, seed=None, size=1024, style_dim=512, n_mlp=8, channel_multiplier=2)` | `run(n_row=3, n_col=5)` | Saves `sample.png`, `sample_mixing_0.png`, `sample_mixing_1.png`; returns `None`. | Use for random latent sampling and style mixing. `model_type` can auto-download a built-in weight. |
| `StyleGANv2FittingPredictor` | same as `StyleGANv2Predictor` | `run(image, need_align=False, start_lr=0.1, final_lr=0.025, latent_level=[...], step=100, mse_weight=1, pre_latent=None)` | Saves `src.fitting.png`, `dst.fitting.png`, `dst.fitting.npy`; returns source image, fitted image, and latent. | Use when you want to recover a latent from a face and refine it by optimization. |
| `StyleGANv2MixingPredictor` | same as `StyleGANv2Predictor` | `run(latent1, latent2, weights=[0.5] * 18)` | Saves `src1.mixing.png`, `src2.mixing.png`, `dst.mixing.png`; returns three images. | `latent1` and `latent2` must be `.npy` arrays with the same latent depth as `weights`. |
| `StyleGANv2EditingPredictor` | `(model_type=None, direction_path=None, **kwargs)` | `run(latent, direction, offset)` | Saves `src.editing.png`, `dst.editing.png`, `dst.editing.npy`; returns source image, edited image, and edited latent. | `latent` is a `.npy` file path. `direction` is a key in the direction dictionary, not a vector file. |
| `Pixel2Style2PixelPredictor` | `(output_path='output_dir', weight_path=None, model_type=None, seed=None, size=1024, style_dim=512, n_mlp=8, channel_multiplier=2)` | `run(image)` | Saves `src.png`, `dst.png`, `dst.npy`; returns source image, decoded image, and latent. | Best first step when you need a latent for StyleGANv2 editing or mixing. Auto-downloads a built-in model only when `model_type` is known. |
| `SinGANPredictor` | `(output_path='output_dir', weight_path=None, pretrained_model=None, seed=None)` | `run(mode='random_sample', generate_start_scale=0, scale_h=1.0, scale_v=1.0, ref_image=None, mask_image=None, sr_factor=4, animation_alpha=0.9, animation_beta=0.9, animation_frames=20, animation_duration=0.1, n_row=5, n_col=3)` | Writes `random_sample.png`, `sr.png`, `animation.gif`, `editing.png`, `harmonization.png`, or `paint2image.png` depending on mode; returns `None`. | `pretrained_model` can be `trees`, `stone`, `mountains`, `birds`, or `lightning`. |
| `Photo2CartoonPredictor` | `(output_path='output', weight_path=None)` | `run(image_path)` | Saves `p2c_photo.png` and `p2c_cartoon.png`; returns the cartoon ndarray. | Uses face alignment and face segmentation, so it is portrait-oriented and dlib-sensitive. |
| `PhotoPenPredictor` | `(output_path, weight_path, gen_cfg)` | `run(semantic_label_path)` | Saves exactly to `output_path`; returns `None`. | `gen_cfg` is typically a `cfg.predict` object from a YAML config. |
| `AOTGANPredictor` | `(output_path, weight_path, gen_cfg)` | `run(input_image_path, input_mask_path)` | Saves exactly to `output_path`; returns `None`. | The mask uses `0` for known pixels and `1` for the missing region. |
| `PSGANPredictor` | `(args, cfg, output_path='output')` | `run()` | Saves `transfered_ref_<reference-name>` files under `output_path`; returns `None`. | Import from `ppgan.apps.psgan_predictor`. It expects a Namespace-like `args` object plus a config object. |

## Restoration, denoising, super-resolution, and depth

| Class | Code-verified constructor | `run()` shape | Return / saved files | Notes |
| --- | --- | --- | --- | --- |
| `MPRPredictor` | `(output_path='output_dir', weight_path=None, seed=None, task=None)` | `run(images_path=None)` | Saves originals and `*_restoration.*` files under `output_path/<task>`; returns `None`. | `task` must be `Deblurring`, `Denoising`, or `Deraining`. The input can be a file or a directory of images. |
| `NAFNetPredictor` | `(output_path='output_dir', weight_path=None, seed=None, window_size=8)` | `run(images_path=None)` | Same output pattern as `MPRPredictor`; returns `None`. | Current predictor exposes denoising only. |
| `SwinIRPredictor` | `(output_path='output_dir', weight_path=None, seed=None, window_size=8)` | `run(images_path=None)` | Same output pattern as `MPRPredictor`; returns `None`. | Current predictor exposes denoising only. |
| `InvDNPredictor` | `(output_path='output_dir', weight_path=None, seed=None)` | `run(images_path=None, disable_mc=False)` | Same output pattern as `MPRPredictor`; returns `None`. | Monte-Carlo self-ensemble is on unless `disable_mc=True`. |
| `RealSRPredictor` | `(output='output', weight_path=None)` | `run(input)` | Image mode returns `(pred_img, out_path)`; video mode returns frame and mp4 paths. | Image mode is in scope here. Video mode belongs in the video sub-skill. |
| `MiDaSPredictor` | `(output=None, weight_path=None)` | `run(img)` | Returns a depth prediction; if `output` is set, also writes `.pfm` and `.png` under `output/MiDaS`. | The code path is safest with a file path or ndarray. |
| `GPENPredictor` | `(output_path='output_dir', weight_path=None, model_type=None, seed=100, size=256, style_dim=512, n_mlp=8, channel_multiplier=1, narrow=0.5)` | `run(img_path)` | Saves `gpen_predict.png`; prints FID/PSNR; returns `None`. | GPU-oriented evaluation path. `model_type='gpen-ffhq-256'` can auto-download the default weight. |
| `FaceParsePredictor` | `(output_path='output')` | `run(image)` | Saves `face_parse.png`; returns the mask array or `None` when no face is found. | Requires the face detector/parser stack. |
| `FaceEnhancement` | `(path_to_enhance=None, size=512, batch_size=1)` | `enhance_from_image(img)` | Returns an enhanced RGB ndarray; file saving is caller-managed. | This is the GPEN-based face enhancement utility from `ppgan.faceutils`. |
| `gfp_FaceEnhancement` | `(size=512, batch_size=1)` | `enhance_from_image(img)` | Returns an enhanced RGB ndarray; file saving is caller-managed. | This is the GFPGAN-based face enhancement utility from `ppgan.faceutils`. |

## Code-verified input quirks

- `AnimeGANPredictor.run` uses `cv2.imread`, so the safest input is a file path.
- `FaceParsePredictor`, `Photo2CartoonPredictor`, and `GPENPredictor` are path-first workflows.
- `MPRPredictor`, `NAFNetPredictor`, `SwinIRPredictor`, and `InvDNPredictor` split file names on `.` when they build output names; avoid input stems with multiple dots.
- `StyleGANv2FittingPredictor`, `StyleGANv2MixingPredictor`, and `StyleGANv2EditingPredictor` all operate on `.npy` latents.
- `StyleGANv2MixingPredictor` requires the `weights` list length to match the latent depth.
- `Pixel2Style2PixelPredictor` needs a detectable face for its alignment step.
- `AOTGANPredictor` treats the mask as `0 = keep` and `1 = fill`.

## Optional extension note

CLIP-guided StyleGAN editing is optional and not part of the default exported route in this sub-skill. If a user asks for text-guided editing, treat CLIP as an extra dependency rather than a baseline assumption.

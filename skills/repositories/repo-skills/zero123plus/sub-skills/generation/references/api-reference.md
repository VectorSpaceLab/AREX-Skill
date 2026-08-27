# Zero123Plus API reference

This reference captures the verified callable surface for the Zero123Plus
pipeline and the bundled matting helper.

## Verified callables

| Callable | Verified signature | Notes |
| --- | --- | --- |
| `Zero123PlusPipeline.__call__` | `(self, image: PIL.Image.Image = None, prompt='', *args, num_images_per_prompt: Optional[int] = 1, guidance_scale=4.0, depth_image: PIL.Image.Image = None, output_type: Optional[str] = 'pil', width=640, height=960, num_inference_steps=28, return_dict=True, **kwargs)` | Main image-to-multiview entry point. `image` must be a PIL image, not a tensor. `depth_image` is only consumed when a ControlNet has been attached. The bundled workflows keep `output_type='pil'`. |
| `Zero123PlusPipeline.add_controlnet` | `(self, controlnet: Optional[diffusers.models.controlnet.ControlNetModel] = None, conditioning_scale=1.0)` | Attaches a ControlNet branch and mutates the pipeline in place. Copy the pipeline first if you need to keep both the base and control versions. |
| `Zero123PlusPipeline.prepare` | `(self)` | Internal setup step used by the pipeline and by `add_controlnet`. The bundled scripts do not call it directly. |
| `gradio_app.py:preprocess` | `(predictor, input_image, chk_group=None, segment=True, rescale=False)` | UI helper. The source code thumbnails inputs to `1024`, can run background removal + SAM segmentation, and returns the high-resolution image plus a `320 x 320` preview. |
| `gradio_app.py:gen_multiview` | `(pipeline, predictor, input_image, scale_slider, steps_slider, seed, output_processing=False)` | UI helper. It seeds PyTorch, calls the pipeline with a `torch.Generator`, crops the six-view grid row-major, and can run output background removal on each tile. |
| `matting_postprocess.postprocess` | `(rgb_img: PIL.Image.Image, normal_img: PIL.Image.Image) -> Tuple[PIL.Image.Image, PIL.Image.Image]` | Takes the color grid and the normal grid, estimates alpha from the normal magnitude, and returns a cutout plus a matted normal image. Live smoke verified `RGBA` for the cutout and `RGB` for the normal result. |

## Helper behavior

| Helper | Behavior |
| --- | --- |
| `to_rgb_image` | Accepts `RGB` and `RGBA`. RGBA is composited onto a gray background. Other modes should be converted before calling the pipeline. |
| `scale_latents` / `unscale_latents` | Internal latent normalization helpers used before and after diffusion. |
| `scale_image` / `unscale_image` | Internal image-domain normalization helpers used by the custom pipeline. |
| `depth_transforms_multi` | Converts depth/control images with `ToTensor()` and `Normalize([0.5], [0.5])`. |

## Parameter facts you can rely on

- `num_images_per_prompt` defaults to `1`.
- `guidance_scale` defaults to `4.0`.
- `output_type` defaults to `'pil'`.
- `width` defaults to `640`.
- `height` defaults to `960`.
- `num_inference_steps` defaults to `28`.
- `return_dict` defaults to `True`.
- `conditioning_scale` defaults to `1.0`.
- `depth_image` only matters when the pipeline has had `add_controlnet(...)`
  called on it.

## Behavior that matters in the scripts

- `__call__` raises a `ValueError` when `image` is `None`.
- `__call__` first converts the input with `to_rgb_image`.
- If CFG is active, the pipeline creates a negative-latent branch when
  `guidance_scale > 1`.
- `prepare()` is called automatically by the public pipeline methods.
- The normal workflow should copy the pipeline before calling
  `add_controlnet(...)`, because `add_controlnet` replaces the internal UNet
  wrapper.
- The output montage is a fixed six-view grid; the bundled scripts keep it as a
  single image unless you split it yourself.

## Minimal call pattern

1. Load the base pipeline with `DiffusionPipeline.from_pretrained(...,
   custom_pipeline="diffusers-support")` or the checked-in custom pipeline directory.
2. Apply `EulerAncestralDiscreteScheduler.from_config(...,
   timestep_spacing='trailing')` when available.
3. Move the pipeline to CUDA or CPU depending on the runtime.
4. Pass a square PIL image, and for ControlNet flows pass the paired control
   image as `depth_image`.
5. Save the returned grid or feed the grid pair into
   `matting_postprocess.postprocess`.

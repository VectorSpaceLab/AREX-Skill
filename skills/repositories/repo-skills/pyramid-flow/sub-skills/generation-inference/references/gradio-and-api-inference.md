# Gradio and API Inference

This reference distills the repository's public demo apps and the live generation API surface into one place.

## Verified runtime facts

- `gradio` version: `6.17.3`
- `huggingface_hub` version: `0.36.0`
- CUDA availability in the inspection environment: `True`
- CUDA device count in the inspection environment: `8`
- `torch.distributed.is_available()`: `True`
- MPS availability in the inspection environment: `False`

## Live generation API signatures

The checked runtime exposes the following high-level generation entry points:

```python
PyramidDiTForVideoGeneration.__init__(
    self,
    model_path,
    model_dtype='bf16',
    model_name='pyramid_mmdit',
    use_gradient_checkpointing=False,
    return_log=True,
    model_variant='diffusion_transformer_768p',
    timestep_shift=1.0,
    stage_range=[0, 0.3333333333333333, 0.6666666666666666, 1],
    sample_ratios=[1, 1, 1],
    scheduler_gamma=0.3333333333333333,
    use_mixed_training=False,
    use_flash_attn=False,
    load_text_encoder=True,
    load_vae=True,
    max_temporal_length=31,
    frame_per_unit=1,
    use_temporal_causal=True,
    corrupt_ratio=0.3333333333333333,
    interp_condition_pos=True,
    stages=[1, 2, 4],
    video_sync_group=8,
    gradient_checkpointing_ratio=0.6,
    **kwargs,
)
```

```python
PyramidDiTForVideoGeneration.generate(
    self,
    prompt=None,
    height=None,
    width=None,
    temp=1,
    num_inference_steps=28,
    video_num_inference_steps=28,
    guidance_scale=7.0,
    video_guidance_scale=7.0,
    min_guidance_scale=2.0,
    use_linear_guidance=False,
    alpha=0.5,
    negative_prompt='cartoon style, worst quality, low quality, blurry, absolute black, absolute white, low res, extra limbs, extra digits, misplaced objects, mutated anatomy, monochrome, horror',
    num_images_per_prompt=1,
    generator=None,
    output_type='pil',
    save_memory=True,
    cpu_offloading=False,
    inference_multigpu=False,
    callback=None,
)
```

```python
PyramidDiTForVideoGeneration.generate_i2v(
    self,
    prompt='',
    input_image=None,
    temp=1,
    num_inference_steps=28,
    guidance_scale=7.0,
    video_guidance_scale=4.0,
    min_guidance_scale=2.0,
    use_linear_guidance=False,
    alpha=0.5,
    negative_prompt='cartoon style, worst quality, low quality, blurry, absolute black, absolute white, low res, extra limbs, extra digits, misplaced objects, mutated anatomy, monochrome, horror',
    num_images_per_prompt=1,
    generator=None,
    output_type='pil',
    save_memory=True,
    cpu_offloading=False,
    inference_multigpu=False,
    callback=None,
)
```

`enable_sequential_cpu_offload(self)` is also present and is the documented way to push the model toward the lowest-memory single-GPU path.

## Demo behavior summary

| Entry point | Behavior | Important notes |
| --- | --- | --- |
| `app.py` | Single-GPU Gradio demo with text-to-video and image-to-video tabs. | Downloads the checkpoint bundle when the expected local cache is missing, so treat it as reference-only during skill generation. |
| `app_multigpu.py` | Multi-GPU Gradio demo front end. | Text-to-video only in the front-end UI; it shells out to the multi-GPU engine script and moves the result into a local `generated_videos/` folder. |
| `video_generation_demo.ipynb` | Notebook recipe for text-to-video and image-to-video. | Shows checkpoint loading, VAE tiling, prompt/image preparation, and MP4 export. |
| `image_generation_demo.ipynb` | Notebook recipe for the image variant. | Uses `diffusion_transformer_image`, `temp=1`, and returns images rather than a video timeline. |

## `app.py` distilled behavior

- Uses `gradio.Blocks()` to expose both text-to-video and image-to-video tabs.
- Keeps a model cache keyed by resolution so repeated demo runs reuse a loaded model.
- Sets the model repository from `model_name`:
  - `pyramid_flux` → miniFLUX-style checkpoint family.
  - `pyramid_mmdit` → SD3-style checkpoint family.
- Downloads the model bundle into a local cache directory if required files are missing.
- Enables VAE tiling.
- Turns on CPU offloading by default.
- Exports generated frame lists to MP4 at 24 FPS.

### Input behavior in `app.py`

- Text-to-video tab inputs: prompt, duration (`temp`), guidance scale, video guidance scale, resolution, and seed.
- Image-to-video tab inputs: image, prompt, duration, video guidance scale, resolution, and seed.
- The seed value `0` means random seed selection.
- The image path in the example is `assets/the_great_wall.jpg`, but users can upload their own image in the UI.

## `app_multigpu.py` distilled behavior

- Uses `subprocess.run` to invoke the multi-GPU engine shell launcher.
- Only exposes a text-to-video tab in the front-end UI.
- Accepts a GPU-count selector, a resolution selector, the prompt, duration, and guidance controls.
- The shell wrapper writes the output to a temporary location and the demo moves it into a `generated_videos/` directory.

## Direct recipe mapping

| User intent | Recommended path | Notes |
| --- | --- | --- |
| Prompt → video | `generate(...)` | Use `num_inference_steps=[20, 20, 20]` and `video_num_inference_steps=[10, 10, 10]` to mirror the repo examples. |
| Prompt + image → video | `generate_i2v(...)` | Resize the input image to the target resolution before calling the model. |
| Prompt → image | `generate(...)` with `temp=1` and the image variant | Save the first returned image directly. |
| Browser demo | `app.py` or `app_multigpu.py` | Use the single-GPU demo for simple local testing and the multi-GPU demo for sequence-parallel generation. |

## Prompt, image, and output handling

- Prompt strings are ordinary text prompts; the README and demos keep them under roughly 128 words.
- `generate_i2v(...)` expects a PIL image.
- Video outputs are written with `diffusers.utils.export_to_video(..., fps=24)`.
- The image variant returns PIL images, so save them with the usual PIL image methods.

## CPU offload behavior

The repository documents two memory-saving modes for single-GPU generation:

1. `cpu_offloading=True` on the generation call, which the README says can get below roughly 12 GB of GPU memory.
2. `model.enable_sequential_cpu_offload()`, which the README says can get below roughly 8 GB of GPU memory.

Practical rule:

- Use CPU offload only when you are not relying on the multi-GPU sequence-parallel launcher.
- The multi-GPU engine path in the repo explicitly uses `cpu_offloading=False`.

## MPS note

The README mentions an Apple Silicon / MPS path as a community contribution. This skill records it as a documented option rather than a verified runtime path.

- The inspection environment did not expose MPS.
- The repo's demo code is still CUDA-oriented and uses `torch.cuda` calls.
- Treat MPS as a special-case adaptation, not the default path for the bundled launchers.

## Multi-GPU sequence-parallel behavior

The multi-GPU code path expects the number of launched processes to match the sequence-parallel group size.

- The distributed helpers initialize a PyTorch process group and then initialize the sequence-parallel group.
- The source scripts assert that `world_size == sp_group_size`.
- The engine then sets `inference_multigpu=True` on the generation call.
- Rank 0 alone writes the MP4 output.

If a request uses more than one GPU, the bundled runtime should verify the world-size and sequence-parallel counts before launching.

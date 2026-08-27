# Generation Workflows

This reference turns the repo's generation entry points into a usable decision guide.

## Evidence-backed workflow map

| Workflow | Best entry point | Main inputs | Main outputs | Notes |
| --- | --- | --- | --- | --- |
| Text-to-video | `PyramidDiTForVideoGeneration.generate(...)` | prompt, checkpoint path, model name, variant, resolution, temp, guidance scales | MP4 video | Use `output_type="pil"` and export with `diffusers.utils.export_to_video`. |
| Image-to-video | `PyramidDiTForVideoGeneration.generate_i2v(...)` | prompt, input image, checkpoint path, model name, variant, resolution, temp, video guidance | MP4 video | Resize/crop the input image to the target resolution before generation. |
| Text-to-image / image variant | `PyramidDiTForVideoGeneration.generate(...)` with `temp=1` | prompt, checkpoint path, `diffusion_transformer_image`, aspect ratio | PIL image | Save the first image directly; do not use video export. |
| Single-GPU Gradio demo | `app.py` | browser prompt, image upload, seed, resolution, local checkpoint cache | Browser demo + MP4 output | Imports trigger model download if the cache is missing. Treat as reference-only. |
| Multi-GPU Gradio demo | `app_multigpu.py` + `scripts/app_multigpu_engine.sh` | GPU count, prompt, resolution | Browser demo + MP4 output | Text-to-video only in the demo front end. |
| Multi-GPU CLI inference | `inference_multigpu.py` or `scripts/app_multigpu_engine.py` semantics | torchrun world size, prompt, image path for i2v, resolution, temp | MP4 video | Sequence parallelism requires `world_size == sp_group_size`. |

## Model and variant guidance

| Model name | Checkpoint family | Good fit | Variant guidance |
| --- | --- | --- | --- |
| `pyramid_flux` | miniFLUX-style checkpoints | Smaller demo path, 384p flows, and the image variant | Treat `768p` as unsupported in the bundled multi-GPU engine and fail fast with a compatibility explanation. |
| `pyramid_mmdit` | SD3-style checkpoints | 768p generation and the broader multi-GPU path | Use this when the request explicitly asks for 768p or the multi-GPU launcher needs the high-resolution path. |

| Variant | Typical use | Output shape / note |
| --- | --- | --- |
| `diffusion_transformer_384p` | lower-resolution video generation | 640×384 video frames; the README notes a 5s cap in the 384p path. |
| `diffusion_transformer_768p` | higher-resolution video generation | 1280×768 video frames; use the 768p path when the checkpoint supports it. |
| `diffusion_transformer_image` | text-to-image / image variant | Returns images, not a video timeline. |

## Direct text-to-video recipe

1. Download or point to a checkpoint directory that already contains the variant subdirectory.
2. Choose the model name and variant pair that matches the request.
3. Instantiate the model.
4. Enable VAE tiling.
5. Use `model.enable_sequential_cpu_offload()` only when memory is tight and single-process execution is acceptable.
6. Generate frames.
7. Export the frame list to MP4.

```python
from diffusers.utils import export_to_video
from pyramid_dit import PyramidDiTForVideoGeneration
import torch

model = PyramidDiTForVideoGeneration(
    "<checkpoint-dir>",
    model_name="pyramid_mmdit",
    model_dtype="bf16",
    model_variant="diffusion_transformer_768p",
)
model.vae.enable_tiling()
# model.enable_sequential_cpu_offload()

with torch.no_grad(), torch.cuda.amp.autocast(enabled=True, dtype=torch.bfloat16):
    frames = model.generate(
        prompt="<prompt>",
        num_inference_steps=[20, 20, 20],
        video_num_inference_steps=[10, 10, 10],
        height=768,
        width=1280,
        temp=16,
        guidance_scale=7.0,
        video_guidance_scale=5.0,
        output_type="pil",
        save_memory=True,
        cpu_offloading=False,
    )

export_to_video(frames, "<output>.mp4", fps=24)
```

## Direct image-to-video recipe

1. Load the source image.
2. Resize and center-crop it to the target width and height.
3. Call `generate_i2v(...)` with a prompt and the resized image.
4. Export the returned frames to MP4.

```python
from PIL import Image
from diffusers.utils import export_to_video

image = Image.open("<image-path>").convert("RGB").resize((1280, 768))
frames = model.generate_i2v(
    prompt="<prompt>",
    input_image=image,
    num_inference_steps=[10, 10, 10],
    temp=16,
    video_guidance_scale=4.0,
    output_type="pil",
    save_memory=True,
)
export_to_video(frames, "<output>.mp4", fps=24)
```

## Text-to-image / image variant recipe

The notebook recipe uses a different variant and returns images rather than video frames.

```python
model = PyramidDiTForVideoGeneration(
    "<checkpoint-dir>",
    model_name="pyramid_flux",
    model_dtype="bf16",
    model_variant="diffusion_transformer_image",
)
model.vae.enable_tiling()

images = model.generate(
    prompt="<prompt>",
    num_inference_steps=[20, 20, 20],
    height=1024,
    width=1024,
    temp=1,
    guidance_scale=9.0,
    output_type="pil",
    save_memory=False,
)
```

Supported aspect-ratio examples from the notebook: `1:1` → 1024×1024, `5:3` → 1280×768, and `3:5` → 768×1280.

## Multi-GPU launch shape

The repository's multi-GPU launchers use `torchrun` and sequence parallelism.

- `--nproc_per_node` must match `--sp_group_size`.
- The bundled engine only writes the output file on rank 0.
- The model is instantiated once per process and the model components are placed on CUDA.
- The generation call sets `inference_multigpu=True` and disables CPU offload in the multi-GPU path.

Example command shape:

```bash
torchrun --nproc_per_node <gpus> scripts/run_generation.py \
  --mode app-engine \
  --task t2v \
  --model-name pyramid_mmdit \
  --model-path <checkpoint-dir> \
  --variant diffusion_transformer_768p \
  --resolution 768p \
  --prompt "<prompt>" \
  --output-path <output>.mp4 \
  --gpus <gpus> \
  --sp-group-size <gpus>
```

## Gradio launch notes

- `app.py` is the single-GPU browser demo. It auto-downloads the checkpoint bundle if the local cache is missing.
- `app_multigpu.py` is a browser front end for the multi-GPU text-to-video path.
- Both demos are reference-first; the runtime skill should not depend on importing them during inspection.

## Selection hints

- Use the single-GPU API path when the user has one GPU, wants CPU offload, or only needs a small demo.
- Use the multi-GPU path when the user asks for `torchrun`, sequence parallelism, or the browser demo with multiple GPUs.
- Use the image variant when the request is for text-to-image rather than a video timeline.
- If the request names `pyramid_flux` and `768p` together, reject the combination unless the user explicitly changes to the high-resolution-compatible checkpoint family.
